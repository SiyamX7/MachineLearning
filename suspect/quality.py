from __future__ import annotations

import math
from typing import Dict, Tuple

import cv2
import numpy as np

from utils import clip01


def compute_quality(frame, bbox, det_score, pose, other_boxes, cfg) -> Tuple[float, Dict[str, float]]:
    """মূল রেজোলিউশনের ফ্রেমে মুখের মান মাপে। প্রতিটি উপাদান [0,1]।

    quality = Σ w_i*c_i / Σ w_i

      lap_sharpness  : 1 - exp(-LaplacianVar / LAP_REF)   (crop 160x160-এ নামিয়ে মাপা,
                       তাই রেজোলিউশন-নিরপেক্ষ; ছোট মুখ upscale হয়ে স্বাভাবিকভাবেই কম পায়)
      edge_sharpness : 1 - exp(-mean Sobel magnitude / EDGE_REF)  (motion/defocus blur)
      size           : min(face_side / SIZE_REF, 1)
      exposure       : গড় উজ্জ্বলতা 125-এর কাছে + কম clipped পিক্সেল + পর্যাপ্ত contrast
      pose           : 1 - (0.6*|yaw|/YAW_MAX + 0.3*|pitch|/PITCH_MAX + 0.1*|roll|/ROLL_MAX)
      det_conf       : detector confidence, [MIN_CONF, 0.9] → [0,1]
      visibility     : (ফ্রেমের ভেতরের বক্স-অংশ) × (1 - অন্য মুখের বক্স দ্বারা ঢাকা অংশ)
                       ⚠ এটা occlusion-এর *আনুমানিক* মাপ; হাত/মাস্কের আড়াল ধরে না
                       (তবে সেগুলোতে det_conf সাধারণত কমে)।
    """
    H, W = frame.shape[:2]
    x1, y1, x2, y2 = [float(v) for v in bbox]
    bw, bh = x2 - x1, y2 - y1
    if bw <= 1 or bh <= 1:
        return 0.0, {}
    ix1, iy1 = int(max(0, math.floor(x1))), int(max(0, math.floor(y1)))
    ix2, iy2 = int(min(W, math.ceil(x2))), int(min(H, math.ceil(y2)))
    if ix2 - ix1 < 8 or iy2 - iy1 < 8:
        return 0.0, {}

    gray = cv2.cvtColor(frame[iy1:iy2, ix1:ix2], cv2.COLOR_BGR2GRAY)
    n = cfg.QUALITY_NORM_SIZE
    interp = cv2.INTER_AREA if max(gray.shape) > n else cv2.INTER_CUBIC
    gray = cv2.resize(gray, (n, n), interpolation=interp)
    smooth = cv2.GaussianBlur(gray, (3, 3), 0)  # sensor noise/JPEG block কমাতে

    lap = float(cv2.Laplacian(smooth, cv2.CV_32F).var())
    gx = cv2.Sobel(smooth, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(smooth, cv2.CV_32F, 0, 1, ksize=3)
    edge = float(np.sqrt(gx * gx + gy * gy).mean())

    mean, std = float(gray.mean()), float(gray.std())
    lum = 1.0 - min(1.0, abs(mean - 125.0) / 125.0)
    clipped = float(((gray <= 8) | (gray >= 247)).mean())
    contrast = min(1.0, max(0.4, std / 30.0))

    if pose is not None:
        pitch, yaw, roll = [float(v) for v in pose]
        pose_pen = (0.6 * clip01(abs(yaw) / cfg.YAW_MAX)
                    + 0.3 * clip01(abs(pitch) / cfg.PITCH_MAX)
                    + 0.1 * clip01(abs(roll) / cfg.ROLL_MAX))
        pose_score = clip01(1.0 - pose_pen)
    else:
        pose_score = 0.5

    area = bw * bh
    inside = (max(0.0, min(x2, W) - max(x1, 0.0)) * max(0.0, min(y2, H) - max(y1, 0.0)))
    border = inside / area
    ov = 0.0
    for o in other_boxes:
        ox1, oy1, ox2, oy2 = [float(v) for v in o]
        inter = (max(0.0, min(x2, ox2) - max(x1, ox1)) * max(0.0, min(y2, oy2) - max(y1, oy1)))
        ov = max(ov, inter / area)

    lo = cfg.MIN_DETECTION_CONFIDENCE
    parts = {
        "lap_sharpness": 1.0 - math.exp(-lap / cfg.LAP_REF),
        "edge_sharpness": 1.0 - math.exp(-edge / cfg.EDGE_REF),
        "size": clip01(min(bw, bh) / cfg.SIZE_REF),
        "exposure": clip01(lum * (1.0 - clipped) * contrast),
        "pose": pose_score,
        "det_conf": clip01((det_score - lo) / max(0.9 - lo, 1e-3)),
        "visibility": clip01(border * (1.0 - min(1.0, 1.5 * ov))),
    }
    wsum = sum(cfg.QUALITY_WEIGHTS.values()) or 1.0
    score = sum(cfg.QUALITY_WEIGHTS.get(k, 0.0) * v for k, v in parts.items()) / wsum
    return float(score), {k: round(float(v), 4) for k, v in parts.items()}