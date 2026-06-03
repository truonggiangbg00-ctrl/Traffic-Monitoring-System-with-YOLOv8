# 🛠️ Setup & Installation Guide

Complete step-by-step setup instructions.

---

## System Requirements

### Hardware (Minimum)
- **GPU**: NVIDIA RTX 3060 (12GB VRAM) - highly recommended
- **CPU**: Intel i7 / AMD Ryzen 7 or better
- **RAM**: 16GB minimum
- **Storage**: 100GB SSD (for dataset)

### Hardware (Recommended)
- **GPU**: NVIDIA RTX 4090 (24GB VRAM)
- **CPU**: Intel i9-13900K / AMD Ryzen 9 7950X
- **RAM**: 32GB+
- **Storage**: 500GB NVMe SSD

### Software
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS
- **Python**: 3.8, 3.9, 3.10, or 3.11
- **CUDA**: 11.8+ (for GPU support)
- **cuDNN**: 8.x (for GPU support)
- **Git**: For version control

---

## Pre-Installation Checklist

Before you start:

- [ ] GPU drivers installed (`nvidia-smi` works)
- [ ] CUDA installed (11.8 or newer)
- [ ] Python 3.8+ installed
- [ ] Virtual environment ready
- [ ] Git installed (optional but recommended)
- [ ] 100GB+ storage available

---

## Installation Steps

### Step 1: Prepare Environment

#### Windows PowerShell

```powershell
# Check Python version
python --version           # Should be 3.8+

# Check GPU
nvidia-smi                # GPU should be visible

# Navigate to project
cd C:\Users\YourName\CamChiu\Traffic_system_3
```

#### Linux / macOS

```bash
# Check Python
python3 --version          # Should be 3.8+

# Check GPU
nvidia-smi                # GPU should be visible

# Navigate to project
cd ~/CamChiu/Traffic_system_3
```

---

### Step 2: Create Virtual Environment

**Option A: venv** (built-in)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

**Option B: conda** (recommended for data science)

```bash
# Create environment
conda create -n traffic python=3.10

# Activate
conda activate traffic
```

**Verify activation**:
```bash
# You should see (venv) or (traffic) in prompt
python --version        # Should be 3.10 or higher
```

---

### Step 3: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

**Expected output**:
```
Successfully installed ultralytics-8.x.x
Successfully installed opencv-python-4.x.x
Successfully installed torch-2.x.x
... (many more packages)
```

**Installation time**: 5-15 minutes (depends on internet)

---

### Step 4: Verify Installation

```bash
# Run verification script
python test_setup.py
```

**Expected output**:
```
✓ Python 3.10 available
✓ PyTorch installed (GPU available)
✓ CUDA 11.8 available
✓ OpenCV installed
✓ YOLO available
✓ Botsort available
✓ GPU memory: 12GB RTX 3060

All checks passed! ✅
```

**If failed**, see [Troubleshooting](#troubleshooting) section.

---

### Step 5: Prepare Data & Models

#### Option A: Use Pre-trained Model

```bash
# Download YOLOv8 pre-trained model
python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"

# Model saved automatically to: ~/.cache/hub/
```

#### Option B: Use Your Own Model

```bash
# Place your best.pt in weights/traffic_model/weights/
mkdir -p weights/traffic_model/weights
cp your_best.pt weights/traffic_model/weights/best.pt
```

#### Option C: Train Custom Model

```bash
# First, prepare dataset
python tools/data_cleaner.py ../Data

# Then train
python tools/train_yolo.py --model s --epochs 100

# Best model saved to: runs/detect/train/weights/best.pt
```

---

### Step 6: Configure System

Edit `utils/config.py`:

```python
# 1. Set video source
VIDEO_SOURCE = "path/to/your/video.mp4"  # or 0 for webcam

# 2. Define lane polygons (use roi_drawer.py)
LANE_POLYGONS = {
    "Lane_1": np.array([[...], [...], [...], [...]]),
    "Lane_2": np.array([[...], [...], [...], [...]]),
}

# 3. Set restrictions
LANE_RESTRICTIONS = {
    "Lane_1": {"motorbike", "car"},
    "Lane_2": {"car", "truck", "bus"},
}

# 4. Verify output directories exist
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
```

---

### Step 7: Draw Lane Polygons

```bash
# Interactive tool to define lanes
python tools/roi_drawer.py path/to/video.mp4
```

**Instructions**:
1. LEFT CLICK to add point
2. RIGHT CLICK to remove last point
3. 'N' to save lane
4. 'Q' to finish
5. Copy generated code to `utils/config.py`

---

### Step 8: Test System

```bash
# Quick test with 10 frames
python main.py --max-frames 10
```

**Expected**:
- Video plays on screen
- FPS counter visible
- CSV file created: `output/violations.csv`
- Evidence images saved (if violations detected)

---

### Step 9: Run Full Processing

```bash
# Process entire video
python main.py

# Or with optimizations
python main.py --optimized  # Use ONNX if available
```

---

## GPU Optimization (Optional)

### Export to ONNX (Recommended)

```bash
# Export model
python tools/model_exporter.py --format onnx

# Verify ONNX model created
ls -l weights/best.onnx

# Run with ONNX
python main.py --optimized
```

**Benefits**: 1.5-2x faster, no accuracy loss

### Export to TensorRT (Advanced)

```bash
# Export model
python tools/model_exporter.py --format tensorrt

# Run with TensorRT
python main.py --model engine
```

**Benefits**: 3-4x faster, <0.1% accuracy loss
**Requirements**: TensorRT installation (complex)

---

## Troubleshooting Installation

### ❌ `CUDA out of memory`

**During installation?** This shouldn't happen.

**During runtime?** See [Performance Tuning](PERFORMANCE_TUNING.md)

---

### ❌ `No module named 'ultralytics'`

```bash
# Ensure virtual environment activated
which python           # Should show venv path

# Reinstall
pip install ultralytics>=8.0.0
```

---

### ❌ `ImportError: No module named 'cv2'`

```bash
# Install OpenCV
pip install opencv-python>=4.8.0

# For headless systems (servers)
pip install opencv-python-headless>=4.8.0
```

---

### ❌ `CUDA is not available`

**Option 1: Install CUDA**
- Download from https://developer.nvidia.com/cuda-downloads
- Install CUDA 11.8 or newer
- Restart system

**Option 2: Use CPU** (slower)
```python
# In utils/config.py
DEVICE = "cpu"
```

---

### ❌ `GPU shows 0GB memory`

```bash
# Verify GPU
nvidia-smi

# Check PyTorch GPU support
python -c "import torch; print(torch.cuda.is_available())"

# If False:
pip install torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu118
```

---

## Validation Checklist

After installation, verify:

- [ ] `python --version` shows 3.8+
- [ ] `nvidia-smi` shows your GPU
- [ ] `python test_setup.py` passes all checks
- [ ] `utils/config.py` is configured
- [ ] Lane polygons defined (`tools/roi_drawer.py` run)
- [ ] `python main.py --max-frames 10` runs successfully
- [ ] Violations detected and CSV created
- [ ] Evidence images saved

✅ **All checks pass?** System is ready for deployment!

---

## File Structure After Setup

```
Traffic_system_3/
├── main.py                              ✅ Ready
├── test_setup.py                        ✅ Ready
├── requirements.txt                     ✅ Ready
├── README.md                            ✅ Ready
│
├── core/                                ✅ Ready
│   ├── __init__.py
│   ├── datatypes.py
│   ├── detector_tracker.py
│   ├── analyzer.py
│   └── counter.py
│
├── utils/                               ⚙️ Configure
│   ├── __init__.py
│   ├── config.py                        ← Edit this!
│   ├── logger.py
│   ├── visualizer.py
│   └── botsort.yaml                     (auto-created)
│
├── tools/                               ✅ Ready
│   ├── data_cleaner.py
│   ├── model_exporter.py
│   ├── model_evaluator.py
│   ├── roi_drawer.py                    ← Use this!
│   ├── train_yolo.py
│   └── README.md
│
├── weights/                             📥 Add models here
│   └── traffic_model/
│       └── weights/
│           ├── best.pt                  (need to add)
│           └── best.onnx                (optional)
│
├── Data/                                📥 Training data (if training)
│   ├── data.yaml
│   ├── train/
│   ├── val/
│   └── test/
│
├── output/                              📁 Auto-created
│   ├── VIDEO_OUTPUT.mp4                 (generated)
│   └── violations.csv                   (generated)
│
└── evidence/                            📁 Auto-created
    └── violation_*.jpg                  (generated)
```

---

## Quick Start Recap

```bash
# 1. Setup environment
python -m venv venv
venv\Scripts\activate              # or: source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify installation
python test_setup.py

# 4. Configure system
# Edit utils/config.py

# 5. Draw lanes
python tools/roi_drawer.py video.mp4

# 6. Run system
python main.py
```

**Time required**: 30-60 minutes (mostly automatic)

---

## Configuration Tips

### For Different Hardware

#### RTX 4090 (24GB) - Maximum Performance
```python
CONFIDENCE_THRESHOLD = 0.4      # Lower = more accurate
DEVICE = "cuda"
SAVE_OUTPUT_VIDEO = True
SAVE_VIOLATION_IMAGES = True
```

#### RTX 3060 (12GB) - Balanced (Recommended)
```python
CONFIDENCE_THRESHOLD = 0.5
DEVICE = "cuda"
# Use ONNX export for speed
```

#### RTX 2060 (6GB) - Limited Resources
```python
CONFIDENCE_THRESHOLD = 0.6      # Higher = faster
DEVICE = "cuda"
FRAME_WIDTH = 960
FRAME_HEIGHT = 540
SAVE_OUTPUT_VIDEO = False
```

#### CPU Only - Minimum
```python
CONFIDENCE_THRESHOLD = 0.7
DEVICE = "cpu"
FRAME_WIDTH = 640
FRAME_HEIGHT = 360
SAVE_OUTPUT_VIDEO = False
```

---

## Next Steps

1. **Review documentation**:
   - [USAGE_GUIDE.md](USAGE_GUIDE.md) - How to use
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System design
   - [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Code reference

2. **Process your data**:
   - Run `python main.py` with your video
   - Check `output/violations.csv` for results
   - Review evidence images in `evidence/`

3. **Optimize performance** (if needed):
   - See [PERFORMANCE_TUNING.md](PERFORMANCE_TUNING.md)
   - Export to ONNX or TensorRT for faster processing

4. **Troubleshoot issues**:
   - See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common problems

---

## Support

If you encounter issues:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Verify `test_setup.py` passes all checks
3. Review system logs for error messages
4. Check hardware compatibility

---

## Uninstallation

To remove the virtual environment:

```bash
# Deactivate
deactivate

# Remove environment (Windows)
rmdir /s venv

# Remove environment (Linux/Mac)
rm -rf venv
```

**Note**: This does NOT affect your data or configuration!

---

**Status**: ✅ Ready for deployment!

For detailed usage, see [USAGE_GUIDE.md](USAGE_GUIDE.md)
