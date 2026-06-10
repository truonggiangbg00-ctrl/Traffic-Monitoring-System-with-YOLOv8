"""
config.py: Centralized configuration for Real-time Traffic Monitoring System
Định nghĩa toàn bộ đường dẫn, tham số ROI (vùng quan tâm), thông số model và luật giao thông.
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
OPTIMIZED_MODEL_PATH = str(WEIGHTS_DIR / "yolo_optimized.engine")

DEVICE = "cuda"

# ============================================================================
# 3. VIDEO SOURCE & PROPERTIES
# ============================================================================
VIDEO_SOURCE = str(PROJECT_ROOT / "Video Project.mp4")

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
# Số khung hình tối thiểu xe phải tồn tại liên tục để xác nhận đếm (Chống nhiễu AI)
MIN_DETECTION_FRAMES = 3
# ============================================================================
# 5. LANE CONFIGURATION
# ============================================================================
LANE_POLYGONS = {
    "Lane_1": np.array([[489, 400], [721, 395], [518, 1079], [0, 1053]], dtype=np.int32),
    "Lane_2": np.array([[723, 396], [913, 390], [1021, 1077], [528, 1076]], dtype=np.int32),
    "Lane_3": np.array([[918, 390], [1105, 380], [1569, 1077], [1027, 1074]], dtype=np.int32),
    "Lane_4": np.array([[1110, 379], [1285, 350], [1919, 940], [1574, 1076]], dtype=np.int32),
}

LANE_RESTRICTIONS = {
    "Lane_1": ["motorbike"],
    "Lane_2": ["motorbike", "car"],
    "Lane_3": ["car", "bus", "motorbike"],
    "Lane_4": ["car", "truck"],
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
# 7. DATASET CONFIGURATION (CẤU HÌNH DỮ LIỆU HUẤN LUYỆN)
# ============================================================================
# Tên thư mục chứa dữ liệu hiện tại (nằm trong thư mục gốc của project). 
# Khi bạn có bộ data mới (VD: "Data_New", "Data_Ver2"), chỉ cần đổi TÊN ở đây!
DATASET_NAME = "Data_4"  

# Hệ thống tự động nội suy ra các đường dẫn tuyệt đối
DATASET_DIR = PROJECT_ROOT / DATASET_NAME
DATA_YAML_PATH = DATASET_DIR / "data.yaml"