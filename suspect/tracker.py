from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment

from utils import cosine, iou, normalize


@dataclass
class FaceRecord:
    frame_idx: int
    bbox: Tuple[float, float, float, float]
    quality: float
    parts: Dict[str, float]
    pose: Optional[Tuple[float, float, float]]
    det_score: float


class Tracklet:
    GALLERY_SIZE = 10
    MAX_RECORDS = 300

    def __init__(self, tid: int):
        self.id = tid
        self.hits = 0
        self.frames: Set[int] = set()
        self.first_frame: Optional[int] = None
        self.last_frame: int = -1
        self.last_bbox: Optional[np.ndarray] = None
        self.mean_emb: Optional[np.ndarray] = None
        self.gallery: List[Tuple[float, np.ndarray]] = []
        self.records: List[FaceRecord] = []

    def add(self, frame_idx: int, det) -> None:
        self.hits += 1
        self.frames.add(frame_idx)
        if self.first_frame is None:
            self.first_frame = frame_idx
        self.last_frame = frame_idx
        self.last_bbox = det.bbox.copy()
        self.records.append(FaceRecord(
            frame_idx, tuple(float(v) for v in det.bbox), det.quality, det.parts,
            tuple(float(v) for v in det.pose) if det.pose is not None else None, det.score))
        if len(self.records) > 2 * self.MAX_RECORDS:  # মেমরি সীমিত রাখতে সেরাগুলো রাখি
            self.records.sort(key=lambda r: -r.quality)
            del self.records[self.MAX_RECORDS:]
        if det.emb is not None:
            e = det.emb
            if self.mean_emb is None:
                self.mean_emb = normalize(e.copy())
            elif cosine(self.mean_emb, e) >= 0.35:      # সন্দেহজনক embedding দিয়ে drift নয়
                self.mean_emb = normalize(0.85 * self.mean_emb + 0.15 * e)
            self.gallery.append((det.quality, e))
            if len(self.gallery) > 2 * self.GALLERY_SIZE:
                self.gallery.sort(key=lambda x: -x[0])
                del self.gallery[self.GALLERY_SIZE:]

    def gallery_embedding(self) -> Optional[np.ndarray]:
        if not self.gallery:
            return None
        top = sorted(self.gallery, key=lambda x: -x[0])[: self.GALLERY_SIZE]
        return normalize(np.mean([e for _, e in top], axis=0))


class FaceTracker:
    """IoU + embedding ভিত্তিক tracker (Hungarian matching)।
    অনিশ্চিত হলে match করে না → নতুন tracklet। (ভুল merge-এর চেয়ে বাড়তি tracklet ভালো)"""

    def __init__(self, cfg, fps: float):
        self.cfg = cfg
        self.max_age = max(1, int(cfg.TRACK_MAX_AGE_SEC * fps))
        self.active: List[Tracklet] = []
        self.all: List[Tracklet] = []
        self.next_id = 1

    def _pair_cost(self, t: Tracklet, d) -> Optional[float]:
        c = self.cfg
        iou_v = iou(t.last_bbox, d.bbox)
        if t.mean_emb is None or d.emb is None:
            return (1.0 - iou_v) if iou_v >= c.TRACK_IOU_ONLY else None
        sim = cosine(t.mean_emb, d.emb)
        ok = (sim >= c.EMB_STRONG
              or (sim >= c.EMB_ACCEPT and iou_v >= c.TRACK_IOU_MIN)
              or (sim >= c.EMB_LOOSE and iou_v >= c.TRACK_IOU_HIGH))
        return (1.0 - (0.6 * sim + 0.4 * iou_v)) if ok else None

    def update(self, frame_idx: int, dets) -> List[Tracklet]:
        """প্রতিটি detection-এর জন্য একটি Tracklet ফেরত দেয় (একই ফ্রেমে দুই detection কখনো এক track পায় না)।"""
        self.active = [t for t in self.active if frame_idx - t.last_frame <= self.max_age]
        n_t, n_d = len(self.active), len(dets)
        assigned: List[Optional[Tracklet]] = [None] * n_d
        if n_t and n_d:
            BIG = 10.0
            cost = np.full((n_t, n_d), BIG)
            for i, t in enumerate(self.active):
                for j, d in enumerate(dets):
                    c = self._pair_cost(t, d)
                    if c is not None:
                        cost[i, j] = c
            rows, cols = linear_sum_assignment(cost)
            for i, j in zip(rows, cols):
                if cost[i, j] < BIG:
                    assigned[j] = self.active[i]
        out = []
        for t in assigned:
            if t is None:
                t = Tracklet(self.next_id)
                self.next_id += 1
                self.active.append(t)
                self.all.append(t)
            out.append(t)
        return out