"""সব গুরুত্বপূর্ণ সেটিং এক জায়গায়। CLI আর্গুমেন্ট দিয়ে override করা যায়।"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Config:
    # ---------- I/O ----------
    VIDEO_PATH: str = "video.mp4"
    OUTPUT_DIR: str = "output"

    # ---------- Performance ----------
    FRAME_SKIP: int = 2                      # প্রতি N-তম ফ্রেম প্রসেস হবে (বাকিগুলো শুধু grab)
    DETECTION_SCALE: Optional[float] = None  # None = অটো (লম্বা দিক ~1280px)। ছোট মুখ হলে বাড়ান (যেমন 1.0)
    MAX_SECONDS: Optional[float] = None      # খুব লম্বা ভিডিওতে শুধু প্রথম N সেকেন্ড
    MAX_CONSECUTIVE_FAILS: int = 30          # এতবার পরপর frame পড়া ব্যর্থ হলে থামবে
    MODEL_NAME: str = "buffalo_l"            # হালকা চাইলে "buffalo_s"
    FORCE_CPU: bool = False

    # ---------- Detection filters ----------
    MIN_FACE_SIZE: int = 40                  # মূল ফ্রেমে বক্সের ছোট দিক (px)
    MIN_DETECTION_CONFIDENCE: float = 0.5
    EMB_MIN_SIDE: int = 56                   # এর চেয়ে ছোট মুখের embedding অবিশ্বস্ত → identity-তে ব্যবহার হবে না
    EMB_MAX_YAW: float = 75.0                # প্রায় প্রোফাইল মুখের embedding-ও ব্যবহার হবে না

    # ---------- Tracking ----------
    TRACK_MAX_AGE_SEC: float = 2.0           # এতক্ষণ দেখা না গেলে track বন্ধ
    TRACK_IOU_MIN: float = 0.10
    TRACK_IOU_HIGH: float = 0.60
    TRACK_IOU_ONLY: float = 0.40             # embedding না থাকলে এই IoU লাগবে
    EMB_STRONG: float = 0.55                 # শুধু embedding-ই যথেষ্ট
    EMB_ACCEPT: float = 0.35                 # embedding + কিছুটা IoU
    EMB_LOOSE: float = 0.20                  # দুর্বল embedding + অনেক বেশি IoU

    # ---------- Identity merge (conservative) ----------
    MIN_TRACK_DETECTIONS: int = 3            # এর কম হলে noise ধরে বাদ
    MERGE_THRESHOLD: float = 0.55            # group-গড় cosine similarity
    MERGE_MIN_PAIR_SIM: float = 0.35         # কোনো tracklet-জোড়া এর নিচে হলে merge নয়
    MAX_RANGE_OVERLAP: float = 0.25          # সময়-পরিসর বেশি overlap করলে merge নয়

    # ---------- Best-face selection ----------
    SAVE_TOP_K: int = 1
    MIN_FRAME_GAP_SEC: float = 0.5           # top-k এর মধ্যে ন্যূনতম সময়ের ব্যবধান (প্রায় একই ছবি এড়াতে)

    # ---------- Crop / output ----------
    CROP_MARGIN: float = 0.45                # বক্স-সাইজের অনুপাতে প্রতি পাশে margin
    JPEG_QUALITY: int = 98
    SAVE_FULL_FRAME: bool = True             # best_frame_annotated.jpg
    SHEET_COLS: int = 4
    SHEET_TILE: int = 256

    # ---------- Preview ----------
    PREVIEW: bool = False
    PREVIEW_WIDTH: int = 960

    # ---------- Quality score ----------
    # quality = Σ(w_i * c_i) / Σ(w_i),  প্রতিটি c_i ∈ [0,1], ফলে quality ∈ [0,1]
    QUALITY_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "lap_sharpness": 0.22,   # Laplacian variance
        "edge_sharpness": 0.10,  # Sobel gradient (motion/defocus blur-এর দ্বিতীয় মাপ)
        "size": 0.20,
        "exposure": 0.08,
        "pose": 0.18,
        "det_conf": 0.08,
        "visibility": 0.14,      # ফ্রেমের কিনারা/অন্য মুখের আড়াল (occlusion proxy)
    })
    QUALITY_NORM_SIZE: int = 160  # sharpness মাপার আগে crop এই সাইজে আনা হয়
    LAP_REF: float = 250.0
    EDGE_REF: float = 25.0
    SIZE_REF: float = 160.0       # এই সাইজ বা বেশি হলে size_score = 1
    YAW_MAX: float = 70.0
    PITCH_MAX: float = 50.0
    ROLL_MAX: float = 45.0