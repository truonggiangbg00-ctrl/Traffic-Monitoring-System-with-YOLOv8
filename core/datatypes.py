"""
datatypes.py: Core data structures for traffic monitoring system
Defines standardized objects passed between modules
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
import numpy as np


@dataclass
class ModelConfig:
    """Configuration for detector model initialization"""
    model_path: str
    model_type: str  # 'pt' (PyTorch), 'engine' (TensorRT), 'onnx' (ONNX)
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    device: str = "cuda"  # 'cuda' or 'cpu'
    max_detections: int = 300
    imgsz: int = 640  # Input image size for YOLO


@dataclass
class TrackedVehicle:
    """Single tracked vehicle in a frame"""
    track_id: int  # Unique tracking ID
    bbox: Tuple[int, int, int, int]  # [x1, y1, x2, y2]
    cls_id: int  # Class ID from YOLO
    cls_name: str  # Class name (e.g., 'car', 'motorbike', 'bus', 'truck')
    conf: float  # Detection confidence score
    
    # Violation tracking
    is_violating: bool = False
    violation_lane: str = ""
    violation_type: str = ""

    @property
    def bottom_center(self) -> Tuple[int, int]:
        """Dynamically compute bottom-center point of bbox"""
        return (
            int((self.bbox[0] + self.bbox[2]) // 2),
            int(self.bbox[3])
        )


@dataclass
class FrameState:
    """State of a single frame after processing"""
    frame_id: int
    original_frame: np.ndarray 
    processed_frame: Optional[np.ndarray] = None 
    
    vehicles: List[TrackedVehicle] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)
    violations: List[TrackedVehicle] = field(default_factory=list)
    
    timestamp: float = 0.0
    fps: float = 0.0


@dataclass
class DetectionResult:
    """Result from model inference on single frame"""
    boxes: np.ndarray 
    track_ids: Optional[np.ndarray] = None
    
    class_ids: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.int32))
    confidences: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    class_names: Dict[int, str] = field(default_factory=dict)