from __future__ import annotations

import logging
import os
import shutil
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from tqdm import tqdm

from tracker import FaceRecord, Tracklet
from utils import (VideoError, color_for_id, cosine, format_ts, make_contact_sheet,
                   margin_crop_box, normalize, save_json, FONT)

log = logging.getLogger("face_manager")


class Person:
    def __init__(self, tracklets: List[Tracklet], merges: list):
        self.idx = 0
        self.tracklets = tracklets
        self.merges = merges
        self.detections = sum(t.hits for t in tracklets)
        self.first_frame = min(t.first_frame for t in tracklets)
        self.last_frame = max(t.last_frame for t in tracklets)
        self.candidates: List[Tuple[FaceRecord, int]] = []   # (record, tracklet_id)
        self.saved: Dict[int, Tuple[str, FaceRecord, int]] = {}  # rank -> (filename, rec, tid)


class _Group:
    def __init__(self, t: Tracklet, gemb: Dict[int, Optional[np.ndarray]]):
        self.members = [t]
        self.gemb = gemb
        self.frames = set(t.frames)
        self.first, self.last = t.first_frame, t.last_frame
        self.log: list = []
        self._refresh()

    def _refresh(self):
        parts = [(self.gemb[m.id], min(m.hits, 30)) for m in self.members if self.gemb[m.id] is not None]
        self.emb = normalize(sum(e * w for e, w in parts)) if parts else None


def _range_overlap(a: _Group, b: _Group) -> float:
    inter = min(a.last, b.last) - max(a.first, b.first)
    if inter <= 0:
        return 0.0
    return inter / max(min(a.last - a.first, b.last - b.first), 1)


def build_persons(tracklets: List[Tracklet], cfg):
    """Tracklet → Person (conservative agglomerative merge)।
    শর্ত: (১) একই ফ্রেমে একসাথে দেখা গেলে কখনো merge নয় (cannot-link),
          (২) গড় similarity ≥ MERGE_THRESHOLD, (৩) কোনো জোড়া < MERGE_MIN_PAIR_SIM নয়।"""
    kept = [t for t in tracklets if t.hits >= cfg.MIN_TRACK_DETECTIONS]
    log.info("Tracklets: %d total, %d kept (>= %d detections)",
             len(tracklets), len(kept), cfg.MIN_TRACK_DETECTIONS)
    gemb = {t.id: t.gallery_embedding() for t in kept}
    groups = [_Group(t, gemb) for t in kept]

    while True:
        best, best_sim = None, -1.0
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                a, b = groups[i], groups[j]
                if a.emb is None or b.emb is None:
                    continue
                if a.frames & b.frames:
                    continue
                if _range_overlap(a, b) > cfg.MAX_RANGE_OVERLAP:
                    continue
                sim = cosine(a.emb, b.emb)
                if sim < cfg.MERGE_THRESHOLD or sim <= best_sim:
                    continue
                pair_min = min((cosine(gemb[x.id], gemb[y.id])
                                for x in a.members for y in b.members
                                if gemb[x.id] is not None and gemb[y.id] is not None), default=1.0)
                if pair_min < cfg.MERGE_MIN_PAIR_SIM:
                    continue
                best, best_sim = (i, j), sim
        if best is None:
            break
        i, j = best
        a, b = groups[i], groups[j]
        a.log.append({"merged_tracklets_a": [m.id for m in a.members],
                      "merged_tracklets_b": [m.id for m in b.members],
                      "similarity": round(best_sim, 4)})
        a.log.extend(b.log)
        a.members += b.members
        a.frames |= b.frames
        a.first, a.last = min(a.first, b.first), max(a.last, b.last)
        a._refresh()
        groups.pop(j)

    persons = [Person(g.members, g.log) for g in groups]
    persons.sort(key=lambda p: p.first_frame)
    for k, p in enumerate(persons, 1):
        p.idx = k
    log.info("Distinct persons: %d", len(persons))
    return persons, kept


def select_candidates(person: Person, top_k: int, min_gap_frames: int):
    recs = [(r, t.id) for t in person.tracklets for r in t.records]
    recs.sort(key=lambda x: -x[0].quality)
    chosen: List[Tuple[FaceRecord, int]] = []
    for r, tid in recs:
        if all(abs(r.frame_idx - c.frame_idx) >= min_gap_frames for c, _ in chosen):
            chosen.append((r, tid))
            if len(chosen) >= top_k:
                break
    person.candidates = chosen


def _draw_preview(frame, boxes, t2p, pw, ph):
    img = cv2.resize(frame, (pw, ph), interpolation=cv2.INTER_AREA)
    sx, sy = pw / frame.shape[1], ph / frame.shape[0]
    for tid, bb in boxes:
        pid = t2p.get(tid)
        color = color_for_id(pid) if pid else (128, 128, 128)
        label = f"P{pid:03d} T{tid}" if pid else f"T{tid}?"
        x1, y1, x2, y2 = int(bb[0] * sx), int(bb[1] * sy), int(bb[2] * sx), int(bb[3] * sy)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, label, (x1, max(14, y1 - 6)), FONT, 0.55, color, 2, cv2.LINE_AA)
    return img


def _cand_meta(fname, rec: FaceRecord, tid: int, fps: float):
    ts = rec.frame_idx / fps
    return {
        "file": fname, "frame": rec.frame_idx,
        "timestamp_sec": round(ts, 3), "timestamp": format_ts(ts),
        "bbox_xyxy": [int(round(v)) for v in rec.bbox],
        "quality": round(rec.quality, 4), "quality_components": rec.parts,
        "pose_pitch_yaw_roll": None if rec.pose is None else [round(v, 1) for v in rec.pose],
        "detection_confidence": round(rec.det_score, 4), "source_tracklet": tid,
    }


def export_results(cfg, persons: List[Person], kept: List[Tracklet], preview_boxes, info) -> None:
    """দ্বিতীয় পাস: ভিডিও আবার পড়ে *মূল* ফ্রেম থেকে crop সেভ করে (এবং preview বানায়)।"""
    W, H, fps, total = info["W"], info["H"], info["fps"], info["total"]
    out = cfg.OUTPUT_DIR
    os.makedirs(out, exist_ok=True)

    min_gap = max(1, int(cfg.MIN_FRAME_GAP_SEC * fps))
    jobs: Dict[int, list] = defaultdict(list)
    for p in persons:
        select_candidates(p, cfg.SAVE_TOP_K, min_gap)
        pdir = os.path.join(out, f"person_{p.idx:03d}")
        os.makedirs(pdir, exist_ok=True)
        for rank, (rec, tid) in enumerate(p.candidates):
            fname = "best_face.jpg" if rank == 0 else f"face_{rank + 1:02d}.jpg"
            jobs[rec.frame_idx].append({"kind": "person", "p": p, "rank": rank, "rec": rec,
                                        "tid": tid, "fname": fname, "path": os.path.join(pdir, fname)})

    t2p = {t.id: p.idx for p in persons for t in p.tracklets}
    dbg_dir = os.path.join(out, "_debug")
    if cfg.PREVIEW:
        os.makedirs(dbg_dir, exist_ok=True)
        for t in kept:
            best = max(t.records, key=lambda r: r.quality)
            jobs[best.frame_idx].append({"kind": "tracklet", "t": t, "rec": best,
                                         "path": os.path.join(dbg_dir, f"T{t.id:04d}.jpg")})

    last_needed = max(jobs) if jobs else -1
    cap = cv2.VideoCapture(cfg.VIDEO_PATH)
    if not cap.isOpened():
        raise VideoError(f"ভিডিও আবার খোলা যায়নি: {cfg.VIDEO_PATH}")

    writer = None
    pw = ph = 0
    if cfg.PREVIEW:
        pw = int(cfg.PREVIEW_WIDTH) - int(cfg.PREVIEW_WIDTH) % 2
        ph = int(round(H * pw / W))
        ph -= ph % 2
        pv_path = os.path.join(out, "preview.mp4")
        writer = cv2.VideoWriter(pv_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (pw, ph))
        if not writer.isOpened():
            log.warning("preview.mp4 লেখা যাচ্ছে না (mp4v codec সমস্যা?) — preview ভিডিও বাদ।")
            writer = None

    max_frame = int(cfg.MAX_SECONDS * fps) if cfg.MAX_SECONDS else 0
    q = [cv2.IMWRITE_JPEG_QUALITY, int(cfg.JPEG_QUALITY)]
    idx, fails, cur_boxes = -1, 0, []
    bar = tqdm(total=total if total > 0 else None, desc="Export", unit="frame",
               disable=(writer is None and last_needed < 0))
    try:
        while True:
            if max_frame and idx + 1 >= max_frame:
                break
            ok = cap.grab()
            idx += 1
            bar.update(1)
            if not ok:
                fails += 1
                if fails >= cfg.MAX_CONSECUTIVE_FAILS or (total > 0 and idx >= total):
                    break
                continue
            fails = 0
            need = idx in jobs
            if not (need or writer):
                if idx >= last_needed:
                    break
                continue
            ok, frame = cap.retrieve()
            if not ok or frame is None or frame.shape[:2] != (H, W):
                if need:
                    log.warning("Frame %d ডিকোড করা গেল না — এই candidate বাদ।", idx)
                continue
            for job in jobs.get(idx, []):
                rec = job["rec"]
                L, T, R, B = margin_crop_box(rec.bbox, cfg.CROP_MARGIN, W, H)
                crop = frame[T:B, L:R]
                if crop.size == 0 or not cv2.imwrite(job["path"], crop, q):
                    log.warning("সেভ ব্যর্থ: %s", job["path"])
                    continue
                if job["kind"] == "person":
                    job["p"].saved[job["rank"]] = (job["fname"], rec, job["tid"])
                    if job["rank"] == 0 and cfg.SAVE_FULL_FRAME:
                        ann = frame.copy()
                        x1, y1, x2, y2 = [int(v) for v in rec.bbox]
                        cv2.rectangle(ann, (x1, y1), (x2, y2), (0, 255, 0), max(2, W // 500))
                        cv2.imwrite(os.path.join(os.path.dirname(job["path"]),
                                                 "best_frame_annotated.jpg"), ann, q)
            if writer is not None:
                if idx in preview_boxes:
                    cur_boxes = preview_boxes[idx]
                writer.write(_draw_preview(frame, cur_boxes, t2p, pw, ph))
            if writer is None and idx >= last_needed:
                break
    finally:
        bar.close()
        cap.release()
        if writer is not None:
            writer.release()

    # ---- metadata + contact sheet ----
    sheet_items = []
    for p in persons:
        pdir = os.path.join(out, f"person_{p.idx:03d}")
        if p.saved and 0 not in p.saved:  # rank-0 ফ্রেম পড়া না গেলে পরের সেরাটা best_face হবে
            first = min(p.saved)
            shutil.copyfile(os.path.join(pdir, p.saved[first][0]), os.path.join(pdir, "best_face.jpg"))
            log.warning("person_%03d: best frame পড়া যায়নি, face_%02d কে best ধরা হয়েছে", p.idx, first + 1)
        cands = [_cand_meta(f, r, tid, fps) for _, (f, r, tid) in sorted(p.saved.items())]
        if not cands:
            log.warning("person_%03d: কোনো ছবি সেভ হয়নি", p.idx)
            continue
        meta = {
            "person_id": f"person_{p.idx:03d}",
            "frames_detected": p.detections,
            "first_seen_frame": p.first_frame, "first_seen_time": format_ts(p.first_frame / fps),
            "last_seen_frame": p.last_frame, "last_seen_time": format_ts(p.last_frame / fps),
            "tracklet_ids": [t.id for t in p.tracklets],
            "merge_log": p.merges,
            "best": cands[0],
            "candidates": cands,
            "note": "স্বয়ংক্রিয় গ্রুপিং — ম্যানুয়ালি যাচাই করুন। সন্দেহ থাকলে merge_log দেখুন।",
        }
        save_json(os.path.join(pdir, "metadata.json"), meta)
        img = cv2.imread(os.path.join(pdir, "best_face.jpg"))
        if img is not None:
            b = cands[0]
            sheet_items.append((img, f"Person {p.idx:03d}",
                                f"Q={b['quality']:.2f} n={p.detections} t={b['timestamp'][:8]}"))

    if sheet_items:
        sheet = make_contact_sheet(sheet_items, cfg.SHEET_COLS, cfg.SHEET_TILE)
        cv2.imwrite(os.path.join(out, "contact_sheet.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 95])

    if cfg.PREVIEW:
        items = []
        for t in kept:
            img = cv2.imread(os.path.join(dbg_dir, f"T{t.id:04d}.jpg"))
            if img is not None:
                items.append((img, f"Person {t2p[t.id]:03d} / T{t.id}", f"n={t.hits}"))
        items.sort(key=lambda x: x[1])
        if items:
            cv2.imwrite(os.path.join(out, "tracklets_sheet.jpg"),
                        make_contact_sheet(items, cfg.SHEET_COLS + 2, 200),
                        [cv2.IMWRITE_JPEG_QUALITY, 92])