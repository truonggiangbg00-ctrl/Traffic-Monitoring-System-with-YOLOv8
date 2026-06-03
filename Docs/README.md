# 🚗 Real-time Highway Traffic Monitoring System

**Advanced AI-powered lane violation detection and traffic counting for Vietnamese highways**

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Detection-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success?style=flat-square)

---

## 📋 Overview

A sophisticated real-time traffic monitoring system that:
- **Detects vehicles** (motorbike, car, truck, bus) using YOLOv8
- **Tracks vehicles** across frames using BoT-SORT with persistent IDs
- **Identifies lane violations** using spatial analysis (cv2.pointPolygonTest)
- **Counts traffic flow** by unique vehicle IDs per class
- **Logs violations** with evidence images and timestamps
- **Maintains >15 FPS** on RTX 3060 (12GB VRAM)

## 🎯 Key Features

### 🎬 Real-time Processing
- ✅ >15 FPS on RTX 3060
- ✅ Live video stream or file input
- ✅ Keyboard controls for pause/screenshot
- ✅ Optional video output recording

### 🔍 Advanced Detection
- ✅ YOLOv8 baseline accuracy (100% reference)
- ✅ ONNX optimization (1.5-2x faster)
- ✅ TensorRT support (3-4x faster, NVIDIA only)
- ✅ CLAHE preprocessing for low-light robustness

### 🚘 Vehicle Tracking
- ✅ BoT-SORT multi-object tracking
- ✅ Persistent vehicle IDs across frames
- ✅ Handles occlusions and fast motion
- ✅ Automatic tracking persistence via botsort.yaml

### 📍 Lane Violation Detection
- ✅ Configurable lane boundaries (polygon ROI)
- ✅ Per-lane vehicle restrictions
- ✅ Pure spatial analysis (NO deep learning)
- ✅ Unique violator counting

### 📊 Traffic Analytics
- ✅ Vehicle counting by class
- ✅ FPS monitoring (min/max/average)
- ✅ Real-time statistics overlay
- ✅ Violation evidence collection

### 💾 Asynchronous I/O
- ✅ Background thread for CSV logging
- ✅ Evidence image saving with padding
- ✅ No FPS drops from I/O operations
- ✅ Thread-safe queue system

## 🚀 Quick Start

### 1️⃣ **Installation**

```bash
# Navigate to project
cd Traffic_system_3

# Install dependencies
pip install -r requirements.txt

# Verify installation
python test_setup.py
```

### 2️⃣ **Configure System**

Edit `utils/config.py`:

```python
# Video source
VIDEO_SOURCE = "path/to/video.mp4"

# Lane polygons (define using roi_drawer.py)
LANE_POLYGONS = {
    "Lane_1": np.array([[489, 400], [721, 395], ...]),
    "Lane_2": np.array([[723, 396], [913, 390], ...]),
}

# Lane restrictions
LANE_RESTRICTIONS = {
    "Lane_1": {"motorbike", "car"},
    "Lane_2": {"car", "truck", "bus"},
}
```

### 3️⃣ **Set Up Lane Polygons**

```bash
# Interactive ROI drawing
python tools/roi_drawer.py path/to/video.mp4

# Follow instructions:
# - LEFT CLICK to add points
# - 'N' to save lane
# - 'Q' to finish
```

### 4️⃣ **Run System**

```bash
# Basic run
python main.py

# With optimized ONNX model
python main.py --optimized

# Headless mode
python main.py --no-display
```

### 5️⃣ **Keyboard Controls**

| Key | Action |
|-----|--------|
| **Q** | Quit and save |
| **P** | Pause |
| **S** | Screenshot |

---

## 📁 Project Structure

```
Traffic_system_3/
├── main.py                          # Main orchestrator
├── requirements.txt                 # Dependencies
├── test_setup.py                   # Verify installation
├── README.md                        # This file
│
├── core/                            # Core algorithms (NO graphics/I/O)
│   ├── datatypes.py                # Data structures
│   ├── detector_tracker.py         # YOLO + BoT-SORT
│   ├── analyzer.py                 # Violation detection
│   └── counter.py                  # Traffic counting
│
├── utils/                           # Helpers & utilities
│   ├── config.py                   # Configuration
│   ├── logger.py                   # Async CSV logging
│   ├── visualizer.py               # Frame annotation
│   └── __init__.py
│
├── tools/                           # Standalone scripts
│   ├── data_cleaner.py             # Dataset cleaning
│   ├── model_exporter.py           # Export models
│   ├── model_evaluator.py          # Evaluate models
│   ├── roi_drawer.py               # Draw ROI
│   ├── train_yolo.py               # Train models
│   └── README.md                   # Tools documentation
│
├── Data/                            # Training dataset
│   ├── train/, val/, test/
│   └── data.yaml
│
├── weights/                         # Model checkpoints
│   └── traffic_model/
│       └── weights/
│           ├── best.pt
│           └── best.onnx
│
├── output/                          # Generated outputs
│   ├── VIDEO_OUTPUT.mp4
│   └── violations.csv
│
└── evidence/                        # Violation images
    └── violation_*.jpg
```
     │   ├── images/
     │   └── labels/
     ├── valid/
     │   ├── images/
     │   └── labels/
     └── data.yaml
     ```

5. **Download pre-trained weights**
   - Place YOLO weights in `weights/traffic_model/weights/`

## 🚀 Quick Start

### Option 1: Using Windows Batch Script
```bash
RUN_SYSTEM.bat
```

### Option 2: Using Python directly
```bash
# Using baseline PyTorch model
python main.py --model pt

# Using optimized TensorRT model (if available)
python main.py --model engine --optimized

# Process video file (set VIDEO_SOURCE in config.py)
python main.py --max-frames 1000

# Headless mode (no display)
python main.py --headless
```

## ⚙️ Configuration

Edit `utils/config.py` to customize:

```python
# Video input
VIDEO_SOURCE = 0  # Webcam: 0, or video file path, or RTSP stream

# Detection parameters
CONFIDENCE_THRESHOLD = 0.45
IOU_THRESHOLD = 0.50

# Lane definitions
LANE_POLYGONS = [LANE_1_POLYGON, LANE_2_POLYGON, LANE_3_POLYGON]

# Output paths
OUTPUT_DIR = "output/"
EVIDENCE_DIR = "evidence/"
```

### Define Custom ROI Polygons

Use the interactive ROI drawer tool:
```bash
python tools/roi_drawer.py frame.jpg 1.0
```
Then define your lane polygons in `config.py`

## 🔧 Tools & Scripts

### 1. Train YOLO Model
```bash
python tools/train_yolo.py
```
- Automatically detects optimal batch size for 12GB VRAM
- Saves weights to `weights/traffic_model/`

### 2. Export Model to ONNX/TensorRT
```bash
python tools/model_exporter.py
```
- Converts baseline PyTorch to optimized formats
- Benchmarks model performance

### 3. Compare Baseline vs. Optimized Model
```bash
python tools/model_evaluator.py
```
- Runs inference on test dataset
- Generates FPS comparison charts
- Outputs performance metrics

### 4. Draw ROI Polygons
```bash
python tools/roi_drawer.py input_frame.jpg 0.8
```
- Interactive tool to define lane boundaries
- Generates Python code for `config.py`

## 📊 Output & Logging

### Traffic Log (`output/traffic_log.csv`)
Columns: `timestamp`, `frame_id`, `vehicle_id`, `vehicle_class`, `violation_type`, `bbox`, `confidence`

### Evidence Images (`evidence/`)
Auto-saved violation images with format:
`violation_<vehicle_id>_<frame_id>_<violation_type>_<timestamp>.jpg`

### Statistics
Printed to console with:
- Average FPS
- Total vehicles processed
- Violation count
- Vehicle class distribution

## 🔍 Data Flow

```
Video Frame
    ↓
Detection & Tracking (YOLO + DeepSORT)
    ↓
Lane Violation Analysis (cv2.pointPolygonTest)
    ↓
Traffic Counting
    ↓
Violation Logging (async threading)
    ↓
Visualization & Display
```

## ⚡ Performance

**Target Performance**: > 15 FPS on RTX 3060 (12GB VRAM)

- Baseline model (PyTorch): ~12-15 FPS
- Optimized model (TensorRT): ~25-30 FPS

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| CUDA out of memory | Reduce `CONFIDENCE_THRESHOLD` or batch size in `config.py` |
| Slow FPS | Use optimized TensorRT model instead of PyTorch |
| Can't open video | Check `VIDEO_SOURCE` path and permissions |
| Model not loading | Ensure weights file exists and has correct format |
| No violations detected | Verify lane polygons defined correctly in `config.py` |

## 📝 Key Design Principles

1. **Separation of Concerns**: Core logic separate from visualization
2. **Async I/O**: Non-blocking violation logging with threading
3. **Modular**: Each component can be tested/replaced independently
4. **Spatial Logic**: Lane detection uses geometry, NOT Deep Learning
5. **Dual-Model Support**: Both baseline and optimized formats supported

## 🛠️ Custom Modifications

### Add New Vehicle Class
1. Update `VEHICLE_CLASSES` in `config.py`
2. Retrain YOLO model with new class
3. Update `CLASS_COLORS` for visualization

### Add New Violation Type
1. Implement new detection logic in `core/analyzer.py`
2. Add violation logging in `main.py`
3. Update visualization in `utils/visualizer.py`

## 📚 References

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [DeepSORT Paper](https://arxiv.org/abs/1703.07402)
- [OpenCV Documentation](https://opencv.org/)

## 📄 License

[Specify your license here]

## 👤 Author

[Your name/organization]

---

**Last Updated**: June 2026

For issues or questions, please refer to the project documentation or contact the development team.
