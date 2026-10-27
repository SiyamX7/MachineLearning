from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import cv2
import numpy as np

log = logging.getLogger("detector")


@dataclass
class FaceDetection:
    bbox: np.ndarray                 # [x1,y1,x2,y2] মূল ফ্রেমের স্কেলে
    kps: np.ndarray                  # (5,2)
    score: float
    emb: Optional[np.ndarray]        # normalized ArcFace embedding (বা None)
    pose: Optional[np.ndarray]       # [pitch, yaw, roll] ডিগ্রিতে
    quality: float = 0.0
    parts: Dict[str, float] = field(default_factory=dict)


def _ceil32(v: float) -> int:
    return int(math.ceil(v / 32.0) * 32)


def pose_from_kps(kps: np.ndarray) -> np.ndarray:
    """Fallback: 5-point landmark থেকে মোটামুটি pose (নির্ভুল নয়, শুধু ranking-এর জন্য)।"""
    le, re_, nose, ml, mr = kps
    eye_c = (le + re_) / 2.0
    eye_d = float(np.linalg.norm(re_ - le)) + 1e-6
    yaw = float(np.clip((nose[0] - eye_c[0]) / eye_d, -1, 1)) * 70.0
    mouth_c = (ml + mr) / 2.0
    ratio = (nose[1] - eye_c[1]) / (mouth_c[1] - eye_c[1] + 1e-6)
    pitch = float((ratio - 0.58) * 100.0)
    roll = math.degrees(math.atan2(re_[1] - le[1], re_[0] - le[0]))
    return np.array([pitch, yaw, roll], np.float32)


class FaceDetector:
    """InsightFace SCRFD + ArcFace + 3D landmark (pose)।
    ফ্রেম DETECTION_SCALE-এ ছোট করে, 32-এর গুণিতকে pad করে detector-এ দেওয়া হয়;
    ফলাফল আবার মূল ফ্রেমের স্কেলে ফেরত আসে।"""

    def __init__(self, cfg, frame_w: int, frame_h: int):
        self.cfg = cfg
        self.W, self.H = frame_w, frame_h
        scale = cfg.DETECTION_SCALE or min(1.0, 1280.0 / max(frame_w, frame_h))
        scale = min(max(float(scale), 0.1), 2.0)
        self.sw = max(32, int(round(frame_w * scale)))
        self.sh = max(32, int(round(frame_h * scale)))
        self.pw, self.ph = _ceil32(self.sw), _ceil32(self.sh)
        self.fx, self.fy = self.sw / frame_w, self.sh / frame_h
        log.info("Detection resolution: %dx%d (padded %dx%d, scale≈%.2f)",
                 self.sw, self.sh, self.pw, self.ph, self.fx)
        self.app = self._build_app()

    def _build_app(self):
        try:
            import onnxruntime as ort
            from insightface.app import FaceAnalysis
        except ImportError as e:
            raise RuntimeError(
                "insightface/onnxruntime ইনস্টল নেই। README-র ইনস্টল ধাপ দেখুন।") from e

        avail = ort.get_available_providers()
        gpu = [p for p in ("CUDAExecutionProvider", "ROCMExecutionProvider") if p in avail]
        attempts = []
        if gpu and not self.cfg.FORCE_CPU:
            attempts.append((gpu + ["CPUExecutionProvider"], 0))
        else:
            if not self.cfg.FORCE_CPU:
                log.info("GPU provider পাওয়া যায়নি, CPU ব্যবহার হবে।")
        attempts.append((["CPUExecutionProvider"], -1))

        last_err = None
        for providers, ctx in attempts:
            try:
                app = FaceAnalysis(
                    name=self.cfg.MODEL_NAME,
                    allowed_modules=["detection", "recognition", "landmark_3d_68"],
                    providers=providers,
                )
                app.prepare(ctx_id=ctx, det_thresh=self.cfg.MIN_DETECTION_CONFIDENCE,
                            det_size=(self.pw, self.ph))
                active = app.models["detection"].session.get_providers()
                log.info("ONNX providers in use: %s", active)
                return app
            except Exception as e:  # noqa: BLE001
                last_err = e
                log.warning("Providers %s ব্যর্থ: %s", providers, e)
        raise RuntimeError(f"Face model চালু করা গেল না: {last_err}") from last_err

    def detect(self, frame: np.ndarray) -> List[FaceDetection]:
        h, w = frame.shape[:2]
        if (w, h) != (self.W, self.H):
            raise ValueError(f"frame size {w}x{h} != expected {self.W}x{self.H}")
        img = frame
        if (self.sw, self.sh) != (w, h):
            interp = cv2.INTER_AREA if self.fx < 1 else cv2.INTER_LINEAR
            img = cv2.resize(frame, (self.sw, self.sh), interpolation=interp)
        if (self.pw, self.ph) != (self.sw, self.sh):
            img = cv2.copyMakeBorder(img, 0, self.ph - self.sh, 0, self.pw - self.sw,
                                     cv2.BORDER_CONSTANT, value=(0, 0, 0))
        out: List[FaceDetection] = []
        for f in self.app.get(img):
            b = np.asarray(f.bbox, np.float32).copy()
            b[[0, 2]] /= self.fx
            b[[1, 3]] /= self.fy
            kps = np.asarray(f.kps, np.float32).copy()
            kps[:, 0] /= self.fx
            kps[:, 1] /= self.fy
            emb = getattr(f, "normed_embedding", None)
            pose = getattr(f, "pose", None)
            pose = np.asarray(pose, np.float32) if pose is not None else pose_from_kps(kps)
            out.append(FaceDetection(bbox=b, kps=kps, score=float(f.det_score),
                                     emb=None if emb is None else np.asarray(emb, np.float32),
                                     pose=pose))
        return out