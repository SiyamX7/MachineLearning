from __future__ import annotations

import argparse
import logging
import os
import sys
import time

import cv2
from tqdm import tqdm

from config import Config
from detector import FaceDetector
from face_manager import build_persons, export_results
from quality import compute_quality
from tracker import FaceTracker
from utils import VideoError, save_json, setup_logging

log = logging.getLogger("main")


def parse_args():
    ap = argparse.ArgumentParser(description="ভিডিও থেকে প্রতিটি ব্যক্তির সবচেয়ে স্পষ্ট মুখ বের করা")
    ap.add_argument("--video")
    ap.add_argument("--output")
    ap.add_argument("--top-k", type=int, help="প্রতি ব্যক্তির সেরা K টি ছবি")
    ap.add_argument("--preview", action="store_true", help="preview.mp4 + tracklets_sheet.jpg")
    ap.add_argument("--frame-skip", type=int)
    ap.add_argument("--detection-scale", type=float)
    ap.add_argument("--min-face-size", type=int)
    ap.add_argument("--min-conf", type=float)
    ap.add_argument("--min-track-detections", type=int)
    ap.add_argument("--merge-threshold", type=float)
    ap.add_argument("--max-seconds", type=float)
    ap.add_argument("--model", help="buffalo_l | buffalo_s")
    ap.add_argument("--cpu", action="store_true")
    ap.add_argument("--no-full-frame", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    return ap.parse_args()


def build_config(a) -> Config:
    c = Config()
    pairs = [("VIDEO_PATH", a.video), ("OUTPUT_DIR", a.output), ("SAVE_TOP_K", a.top_k),
             ("FRAME_SKIP", a.frame_skip), ("DETECTION_SCALE", a.detection_scale),
             ("MIN_FACE_SIZE", a.min_face_size), ("MIN_DETECTION_CONFIDENCE", a.min_conf),
             ("MIN_TRACK_DETECTIONS", a.min_track_detections),
             ("MERGE_THRESHOLD", a.merge_threshold), ("MAX_SECONDS", a.max_seconds),
             ("MODEL_NAME", a.model)]
    for k, v in pairs:
        if v is not None:
            setattr(c, k, v)
    c.FRAME_SKIP = max(1, c.FRAME_SKIP)
    c.SAVE_TOP_K = max(1, c.SAVE_TOP_K)
    c.PREVIEW = a.preview
    c.FORCE_CPU = a.cpu
    if a.no_full_frame:
        c.SAVE_FULL_FRAME = False
    return c


def analyze_video(cfg: Config):
    if not os.path.isfile(cfg.VIDEO_PATH):
        raise VideoError(f"ভিডিও ফাইল পাওয়া যায়নি: {cfg.VIDEO_PATH}")
    cap = cv2.VideoCapture(cfg.VIDEO_PATH)
    if not cap.isOpened():
        raise VideoError("ভিডিও খোলা যায়নি (কোডেক/ফাইল নষ্ট?). ffmpeg দিয়ে re-encode করে দেখুন।")
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if W <= 0 or H <= 0:
        cap.release()
        raise VideoError("ভিডিওর রেজোলিউশন পড়া যায়নি — ফাইলটি অবৈধ।")
    if not (0 < fps < 1000):
        log.warning("FPS পড়া যায়নি, 30 ধরা হচ্ছে (timestamp আনুমানিক হবে)।")
        fps = 30.0
    total = total if total > 0 else 0
    duration = total / fps if total else 0
    log.info("Video: %dx%d @ %.2f fps, frames=%s (~%.1f min)", W, H, fps, total or "?", duration / 60)
    if duration > 1800 and cfg.FRAME_SKIP < 5 and not cfg.MAX_SECONDS:
        log.warning("ভিডিও অনেক লম্বা (%.0f মিনিট)। দ্রুত করতে --frame-skip 5 বা বেশি, "
                    "অথবা --max-seconds ব্যবহার করুন।", duration / 60)

    detector = FaceDetector(cfg, W, H)
    tracker = FaceTracker(cfg, fps)
    preview_boxes = {}
    max_frame = int(cfg.MAX_SECONDS * fps) if cfg.MAX_SECONDS else 0

    idx, fails, corrupted, processed, n_det, err_logged = -1, 0, 0, 0, 0, 0
    t0 = time.time()
    bar = tqdm(total=total or None, desc="Analyze", unit="frame")
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
            if idx % cfg.FRAME_SKIP:
                continue
            ok, frame = cap.retrieve()
            if not ok or frame is None or frame.size == 0 or frame.shape[:2] != (H, W):
                corrupted += 1
                continue
            try:
                dets = detector.detect(frame)
            except Exception as e:  # noqa: BLE001
                corrupted += 1
                if err_logged < 3:
                    log.warning("Frame %d-এ detection ব্যর্থ: %s", idx, e)
                    err_logged += 1
                continue
            processed += 1

            good = []
            for d in dets:
                bw, bh = d.bbox[2] - d.bbox[0], d.bbox[3] - d.bbox[1]
                if min(bw, bh) >= cfg.MIN_FACE_SIZE and d.score >= cfg.MIN_DETECTION_CONFIDENCE:
                    good.append(d)
            for i, d in enumerate(good):
                others = [g.bbox for j, g in enumerate(good) if j != i]
                d.quality, d.parts = compute_quality(frame, d.bbox, d.score, d.pose, others, cfg)
                side = min(d.bbox[2] - d.bbox[0], d.bbox[3] - d.bbox[1])
                yaw = abs(float(d.pose[1])) if d.pose is not None else 0.0
                if side < cfg.EMB_MIN_SIDE or yaw > cfg.EMB_MAX_YAW:
                    d.emb = None  # অবিশ্বস্ত embedding identity-তে ঢুকবে না
            tracks = tracker.update(idx, good)
            for d, t in zip(good, tracks):
                t.add(idx, d)
            n_det += len(good)
            if cfg.PREVIEW:
                preview_boxes[idx] = [(t.id, tuple(float(v) for v in d.bbox)) for d, t in zip(good, tracks)]
    except KeyboardInterrupt:
        log.warning("Ctrl-C — এ পর্যন্ত পাওয়া ফলাফল দিয়ে শেষ করছি।")
    finally:
        bar.close()
        cap.release()

    el = time.time() - t0
    log.info("Analyzed %d frames (corrupted/skipped-bad: %d), %d detections, %d tracklets, %.1fs",
             processed, corrupted, n_det, len(tracker.all), el)
    return {"tracklets": tracker.all, "preview_boxes": preview_boxes,
            "info": {"W": W, "H": H, "fps": fps, "total": total}}


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)
    cfg = build_config(args)
    try:
        res = analyze_video(cfg)
    except VideoError as e:
        log.error("%s", e)
        return 2
    except RuntimeError as e:
        log.error("%s", e)
        return 3

    if not res["tracklets"]:
        log.error("কোনো মুখ পাওয়া যায়নি। চেষ্টা করুন: --detection-scale 1.0, --min-face-size 24, "
                  "--min-conf 0.4, --frame-skip 1")
        return 1
    persons, kept = build_persons(res["tracklets"], cfg)
    if not persons:
        log.error("মুখ পাওয়া গেছে কিন্তু কোনো টেকসই track হয়নি। --min-track-detections 2 দিয়ে দেখুন।")
        return 1
    try:
        export_results(cfg, persons, kept, res["preview_boxes"], res["info"])
    except VideoError as e:
        log.error("%s", e)
        return 2
    save_json(os.path.join(cfg.OUTPUT_DIR, "summary.json"), {
        "video": cfg.VIDEO_PATH, "persons": len(persons), "tracklets_total": len(res["tracklets"]),
        "tracklets_kept": len(kept), "frame_skip": cfg.FRAME_SKIP,
        "merge_threshold": cfg.MERGE_THRESHOLD, "top_k": cfg.SAVE_TOP_K})
    log.info("সম্পন্ন: %d জন ব্যক্তি → %s (contact_sheet.jpg দেখে যাচাই করুন)",
             len(persons), os.path.abspath(cfg.OUTPUT_DIR))
    return 0


if __name__ == "__main__":
    sys.exit(main())