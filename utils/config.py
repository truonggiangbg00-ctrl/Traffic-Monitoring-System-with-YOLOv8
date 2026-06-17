"""
config.py: Centralized configuration for Real-time Traffic Monitoring System
"""

import numpy as np
from pathlib import Path

# ============================================================================
# 1. PROJECT ROOT & PATHS
# ============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent

WEIGHTS_DIR = PROJECT_ROOT / "weights"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
OUTPUT_DIR = PROJECT_ROOT / "output"

EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# 2. MODEL PATHS & HARDWARE
# ============================================================================
USE_OPTIMIZED_MODEL = True  

BASELINE_MODEL_PATH = str(WEIGHTS_DIR / "yolo_basic.pt")
OPTIMIZED_MODEL_PATH = str(WEIGHTS_DIR / "yolo_optimized.pt")

DEVICE = "cuda"

# ============================================================================
# 3. VIDEO SOURCE & PROPERTIES
# ============================================================================
# Mặc định file nằm cùng cấp thư mục config hoặc project root
VIDEO_SOURCE = str(PROJECT_ROOT / "Video_Project.mp4")

FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
MIN_FPS = 15

# ============================================================================
# 4. CLASSES & DETECTION PARAMETERS
# ============================================================================
CLASS_NAMES = {
    0: "Bike",
    1: "Bus",
    2: "Car",
    3: "Motorbike",
    4: "Truck"
}

CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45
MIN_DETECTION_FRAMES = 3

# ============================================================================
# 5. LANE CONFIGURATION
# ============================================================================
LANE_POLYGONS = {
    "LANE_1": np.array([[441, 450], [706, 452], [561, 1074], [2, 1064]], dtype=np.int32),
    "LANE_2": np.array([[706, 453], [921, 448], [1005, 1076], [558, 1072]], dtype=np.int32),
    "LANE_3": np.array([[921, 447], [1138, 441], [1485, 1077], [1006, 1072]], dtype=np.int32),
    "LANE_4": np.array([[1143, 438], [1374, 441], [1917, 927], [1918, 1068], [1497, 1074]], dtype=np.int32),
}

# ĐỒNG BỘ: Sửa lại phím chữ thường để khớp logic chuẩn lớp Detector
LANE_RESTRICTIONS = {
    "LANE_1": ["motorbike", "bike"],
    "LANE_2": ["motorbike", "car"],
    "LANE_3": ["car", "bus", "motorbike"],
    "LANE_4": ["car", "truck"],
}

# ============================================================================
# 6. LOGGING, VISUALIZATION & EVIDENCE
# ============================================================================
DRAW_ROI_POLYGONS = True
SAVE_OUTPUT_VIDEO = True
OUTPUT_VIDEO_PATH = str(OUTPUT_DIR / "traffic_monitoring_output.mp4")

SAVE_VIOLATION_IMAGES = True
VIOLATION_IMAGE_FORMAT = "jpg"

LOG_FILE = str(OUTPUT_DIR / "traffic_violations.csv")
LOG_COLUMNS = [
    "frame_id", "timestamp", "vehicle_id", "class_name", 
    "violation_type", "confidence", "bbox_bottom_center", "violation_lane"
]

# ============================================================================
# 7. DATASET CONFIGURATION
# ============================================================================
DATASET_NAME = "Data_4"  
DATASET_DIR = PROJECT_ROOT / DATASET_NAME
DATA_YAML_PATH = DATASET_DIR / "data.yaml"