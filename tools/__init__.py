"""
tools: Independent R&D and utility scripts for Traffic System

Modules:
  • data_cleaner.py - Dataset cleaning and validation
  • model_exporter.py - Export models to optimized formats (ONNX, TensorRT)
  • model_evaluator.py - Evaluate and compare model performance
  • roi_drawer.py - Interactive ROI polygon drawing tool
  • train_yolo.py - YOLOv8 model training

All scripts are standalone and can be run independently:
  python data_cleaner.py /path/to/dataset
  python model_exporter.py --model model.pt
  python model_evaluator.py --data data.yaml
  python roi_drawer.py video.mp4
  python train_yolo.py --data data.yaml
"""

from pathlib import Path

TOOLS_DIR = Path(__file__).parent

__all__ = [
    'data_cleaner',
    'model_exporter', 
    'model_evaluator',
    'roi_drawer',
    'train_yolo'
]
