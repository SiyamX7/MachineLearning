from __future__ import annotations

import json
import logging
import math

import cv2
import numpy as np

FONT = cv2.FONT_HERSHEY_SIMPLEX


class VideoError(Exception):
    pass


def setup_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def clip01(x: float) -> float:
    return float(min(1.0, max(0.0, x)))


def normalize(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else v


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = [float(v) for v in a]
    bx1, by1, bx2, by2 = [float(v) for v in b]
    iw = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    ih = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = iw * ih
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union > 0 else 0.0


def format_ts(sec: float) -> str:
    sec = max(0.0, float(sec))
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def margin_crop_box(bbox, margin: float, W: int, H: int):
    """মুখের বক্সের চারপাশে margin দিয়ে *বর্গাকার* crop বক্স (aspect ratio অক্ষুণ্ণ)।
    ফ্রেমের বাইরে গেলে চেপে না ধরে window সরিয়ে আনা হয়।
    কপাল কেটে না যাওয়ার জন্য কেন্দ্র সামান্য উপরে সরানো।"""
    x1, y1, x2, y2 = [float(v) for v in bbox]
    bw, bh = x2 - x1, y2 - y1
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0 - 0.06 * bh
    side = min(max(bw, bh) * (1 + 2 * margin), float(min(W, H)))
    left = min(max(cx - side / 2, 0.0), W - side)
    top = min(max(cy - side / 2, 0.0), H - side)
    L, T, S = int(round(left)), int(round(top)), int(round(side))
    return L, T, min(L + S, W), min(T + S, H)


def color_for_id(i: int):
    hue = int((i * 37) % 180)
    c = cv2.cvtColor(np.uint8([[[hue, 220, 255]]]), cv2.COLOR_HSV2BGR)[0, 0]
    return tuple(int(v) for v in c)


def fit_into(img: np.ndarray, w: int, h: int, bg=(30, 30, 30)) -> np.ndarray:
    canvas = np.full((h, w, 3), bg, np.uint8)
    ih, iw = img.shape[:2]
    s = min(w / iw, h / ih)
    nw, nh = max(1, int(iw * s)), max(1, int(ih * s))
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC
    resized = cv2.resize(img, (nw, nh), interpolation=interp)
    y0, x0 = (h - nh) // 2, (w - nw) // 2
    canvas[y0:y0 + nh, x0:x0 + nw] = resized
    return canvas


def make_contact_sheet(items, cols=4, tile=256, label_h=52, pad=8) -> np.ndarray:
    """items: [(bgr_image, title, subtitle), ...]"""
    n = len(items)
    cols = max(1, min(cols, n))
    rows = math.ceil(n / cols)
    cw, ch = tile + 2 * pad, tile + label_h + 2 * pad
    sheet = np.full((rows * ch, cols * cw, 3), 30, np.uint8)
    for k, (img, title, sub) in enumerate(items):
        r, c = divmod(k, cols)
        x0, y0 = c * cw + pad, r * ch + pad
        sheet[y0:y0 + tile, x0:x0 + tile] = fit_into(img, tile, tile)
        cv2.putText(sheet, title, (x0, y0 + tile + 20), FONT, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(sheet, sub, (x0, y0 + tile + 42), FONT, 0.45, (180, 180, 180), 1, cv2.LINE_AA)
    return sheet


class _NumpyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, set):
            return sorted(o)
        return super().default(o)


def save_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, cls=_NumpyEncoder)