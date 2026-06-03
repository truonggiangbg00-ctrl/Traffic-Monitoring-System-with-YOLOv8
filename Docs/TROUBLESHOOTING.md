# 🐛 Troubleshooting Guide

Solutions for common problems and issues.

---

## Installation Issues

### ❌ `ModuleNotFoundError: No module named 'ultralytics'`

**Problem**: YOLO library not installed

**Solutions**:
```bash
# Install all requirements
pip install -r requirements.txt

# Or install manually
pip install ultralytics>=8.0.0
```

---

### ❌ `ModuleNotFoundError: No module named 'cv2'`

**Problem**: OpenCV not installed

**Solutions**:
```bash
# Install OpenCV
pip install opencv-python>=4.8.0

# Or for headless systems
pip install opencv-python-headless>=4.8.0
```

---

### ❌ `ModuleNotFoundError: No module named 'torch'`

**Problem**: PyTorch not installed

**Solutions**:
```bash
# Install PyTorch (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Or for CPU only
pip install torch torchvision torchaudio
```

---

### ❌ `CUDA out of memory`

**Problem**: GPU doesn't have enough VRAM

**Solutions**:
1. **Use smaller model**:
   ```python
   # In config.py, use nano instead of large
   MODEL_PATH = "weights/traffic_model/weights/best.pt"
   ```

2. **Use CPU**:
   ```python
   # In config.py
   DEVICE = "cpu"
   ```

3. **Use optimized model**:
   ```bash
   python main.py --optimized  # Uses ONNX (lower VRAM)
   ```

4. **Reduce frame resolution**:
   ```python
   # In config.py
   FRAME_WIDTH = 640    # Instead of 1280
   FRAME_HEIGHT = 360   # Instead of 720
   ```

---

### ❌ `No CUDA devices found`

**Problem**: CUDA not installed or GPU not detected

**Solutions**:
1. **Verify GPU exists**:
   ```bash
   nvidia-smi
   ```

2. **Install CUDA**:
   - Download from https://developer.nvidia.com/cuda-downloads
   - Install CUDA 11.8 or newer

3. **Use CPU fallback**:
   ```python
   # In config.py
   DEVICE = "cpu"
   ```

---

## Video Source Issues

### ❌ `Cannot open video file: file.mp4`

**Problem**: Video file not found or invalid

**Solutions**:
1. **Check file exists**:
   ```bash
   ls -l /path/to/video.mp4  # Linux/Mac
   dir C:\path\to\video.mp4  # Windows
   ```

2. **Use absolute path**:
   ```python
   # In config.py - use full path
   VIDEO_SOURCE = "/home/user/videos/highway.mp4"
   # Not relative path like "video.mp4"
   ```

3. **Check file format**:
   - Supported: MP4, AVI, MOV, MKV, WMV
   - Use ffmpeg to convert if needed:
     ```bash
     ffmpeg -i input.avi -c:v libx264 output.mp4
     ```

---

### ❌ `Cannot open camera device`

**Problem**: Webcam not available

**Solutions**:
1. **Check camera index**:
   ```python
   # In config.py, try different indices
   VIDEO_SOURCE = 0    # First camera
   VIDEO_SOURCE = 1    # Second camera
   ```

2. **Verify camera permissions**:
   ```bash
   # Linux: check device exists
   ls -l /dev/video*
   
   # Windows: check Device Manager for camera
   ```

3. **Test camera**:
   ```python
   import cv2
   cap = cv2.VideoCapture(0)
   ret, frame = cap.read()
   if ret:
       print("Camera works!")
   else:
       print("Camera error!")
   ```

---

### ❌ `RTSP stream connection timeout`

**Problem**: Cannot connect to network camera

**Solutions**:
1. **Check stream URL**:
   ```python
   # In config.py
   VIDEO_SOURCE = "rtsp://camera_ip:554/stream"
   # Verify IP and port are correct
   ```

2. **Test connection**:
   ```bash
   # Use VLC to test stream
   vlc "rtsp://camera_ip:554/stream"
   ```

3. **Increase timeout**:
   ```python
   # In detector_tracker.py
   cap = cv2.VideoCapture(VIDEO_SOURCE, cv2.CAP_PROP_BUFFERSIZE)
   cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffering
   ```

---

## Model & Detection Issues

### ❌ `Model file not found: best.pt`

**Problem**: Model weights file missing

**Solutions**:
1. **Check file path**:
   ```bash
   find . -name "best.pt"  # Search for file
   ```

2. **Download model**:
   ```bash
   # Use pre-trained YOLO model
   python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"
   ```

3. **Verify path in config**:
   ```python
   # In config.py
   BASELINE_MODEL_PATH = Path(__file__).parent.parent / "weights" / "traffic_model" / "weights" / "best.pt"
   ```

---

### ❌ `No vehicles detected (empty violations log)`

**Problem**: System isn't detecting any vehicles

**Solutions**:

1. **Lower confidence threshold**:
   ```python
   # In config.py - be more permissive
   CONFIDENCE_THRESHOLD = 0.4    # Instead of 0.6
   ```

2. **Check video quality**:
   - Ensure video is not too dark
   - Check resolution is sufficient (>640x480)
   - Ensure vehicles are clearly visible

3. **Verify lane polygons**:
   ```bash
   # Re-draw lane polygons
   python tools/roi_drawer.py video.mp4
   ```

4. **Test detection**:
   ```python
   from core.detector_tracker import DetectorTracker
   detector = DetectorTracker(config)
   # Test with frame and check output
   ```

---

### ❌ `Too many false detections`

**Problem**: Many non-vehicles or poor quality detections

**Solutions**:

1. **Raise confidence threshold**:
   ```python
   # In config.py - be more strict
   CONFIDENCE_THRESHOLD = 0.7    # Instead of 0.5
   ```

2. **Increase NMS threshold**:
   ```python
   # In config.py
   IOU_THRESHOLD = 0.5    # Instead of 0.45
   ```

3. **Train custom model**:
   ```bash
   python tools/train_yolo.py
   ```

---

## Lane Configuration Issues

### ❌ `No violations detected (wrong lane polygon)`

**Problem**: Polygons not correctly defining lanes

**Solutions**:

1. **Re-draw polygons**:
   ```bash
   python tools/roi_drawer.py video.mp4
   ```
   Follow on-screen instructions carefully.

2. **Verify restrictions**:
   ```python
   # In config.py - check if classes are correct
   LANE_RESTRICTIONS = {
       "Lane_1": {"motorbike", "car"},  # Check spelling!
   }
   ```

3. **Test polygon**:
   ```python
   import cv2
   import numpy as np
   
   # Manually draw polygon to verify
   polygon = np.array([[x1, y1], [x2, y2], ...])
   cv2.polylines(frame, [polygon], True, (0, 255, 0), 2)
   ```

---

### ❌ `Violations detected in wrong lane`

**Problem**: Vehicle marked as violation in incorrect lane

**Solutions**:

1. **Check point detection**:
   ```python
   # Vehicle's bottom_center point should be center-bottom of bbox
   # Not top, not left-center, but BOTTOM-center
   ```

2. **Verify polygon winding**:
   - Polygons should be clockwise or counter-clockwise (consistent)
   - Use roi_drawer.py for correct order

3. **Add debug output**:
   ```python
   # In analyzer.py, add print statements
   for vehicle in frame_state.vehicles:
       print(f"Vehicle {vehicle.track_id} at {vehicle.bottom_center}")
   ```

---

## Output Issues

### ❌ `CSV file not created / empty`

**Problem**: Violation log file missing or empty

**Solutions**:

1. **Check path**:
   ```bash
   ls -l output/violations.csv  # Linux/Mac
   dir output\violations.csv    # Windows
   ```

2. **Ensure violations exist**:
   - Check screen output for detected violations
   - If none detected, see "No violations detected" section

3. **Check permissions**:
   ```bash
   # Ensure write permissions on output directory
   chmod 755 output/    # Linux/Mac
   ```

4. **Enable violation logging**:
   ```python
   # In config.py
   SAVE_VIOLATION_IMAGES = True
   ```

---

### ❌ `Evidence images not saved`

**Problem**: No violation images in evidence/

**Solutions**:

1. **Enable image saving**:
   ```python
   # In config.py
   SAVE_VIOLATION_IMAGES = True
   ```

2. **Check directory exists**:
   ```bash
   mkdir -p evidence/   # Create if missing
   ```

3. **Verify violations detected**:
   - Check screen output
   - Check CSV file for violation entries

4. **Check file permissions**:
   ```bash
   chmod 755 evidence/    # Linux/Mac
   ```

---

### ❌ `Output video file too large / not created`

**Problem**: Video output file is huge or missing

**Solutions**:

1. **Disable video output**:
   ```python
   # In config.py
   SAVE_OUTPUT_VIDEO = False
   ```

2. **Use video compression**:
   - The system uses default codec (usually MJPEG)
   - For smaller file, use external tool:
     ```bash
     ffmpeg -i VIDEO_OUTPUT.mp4 -c:v libx264 -crf 28 output_compressed.mp4
     ```

3. **Process shorter video**:
   ```bash
   python main.py --max-frames 500
   ```

---

## Performance Issues

### ❌ `FPS too low (<15)`

**Problem**: System running slower than requirement

**Solutions**:

1. **Use optimized model**:
   ```bash
   python main.py --optimized  # ONNX (1.5-2x faster)
   ```

2. **Reduce resolution**:
   ```python
   # In config.py
   FRAME_WIDTH = 640    # Instead of 1280
   FRAME_HEIGHT = 360   # Instead of 720
   ```

3. **Use smaller model**:
   ```python
   # Train with nano model instead of large
   python tools/train_yolo.py --model n
   ```

4. **Monitor GPU usage**:
   ```bash
   nvidia-smi -l 1
   # If GPU utilization <50%, issue is elsewhere (CPU bound)
   # If GPU at 100%, need better GPU or model optimization
   ```

5. **Disable features**:
   ```python
   # In config.py
   SAVE_OUTPUT_VIDEO = False
   SAVE_VIOLATION_IMAGES = False
   ```

---

### ❌ `FPS inconsistent (varies widely)`

**Problem**: FPS jumping between 15 and 50 FPS

**Solutions**:

1. **This is normal** - FPS varies based on scene complexity
   - Complex scenes (many vehicles) = lower FPS
   - Simple scenes = higher FPS

2. **Average FPS should be >15** (production requirement)

3. **To stabilize**, reduce detection complexity:
   ```python
   CONFIDENCE_THRESHOLD = 0.7    # Fewer detections
   ```

---

## File Handling Issues

### ❌ `UnicodeDecodeError: 'utf-8' codec can't decode`

**Problem**: Vietnamese filenames causing errors on Windows

**Solutions**:
- System already handles this using `np.fromfile` byte array method
- Ensure absolute paths are used (not relative)
- Use standard ASCII paths for temporary files

---

### ❌ `Permission denied` when writing to output/

**Problem**: Write permission issue on output directory

**Solutions**:
```bash
# Linux/Mac
chmod 755 output/
chmod 755 evidence/

# Windows (in PowerShell)
icacls output /grant Everyone:F
```

---

## Logging Issues

### ❌ `WARNING: Queue is not empty during shutdown`

**Problem**: Violations still being processed when shutting down

**Solutions**:
- This is normal warning
- System waits for queue to flush before exiting
- If messages keep appearing, violations are being processed (expected)

---

### ❌ `No CSV data at all (blank or no file)`

**Problem**: CSV created but no data written

**Solutions**:

1. **Check system is running correctly**:
   - Verify video is playing
   - Check for vehicles detected on screen
   - Check for violations detected on screen

2. **Wait longer** - logger runs asynchronously
   - Give system 30 seconds to flush queue

3. **Force shutdown properly**:
   ```bash
   # Press Q to exit gracefully
   # Don't use Ctrl+C (may lose data)
   ```

---

## Configuration Issues

### ❌ `AttributeError: config has no attribute 'XYZ'`

**Problem**: Missing or misspelled config variable

**Solutions**:

1. **Check variable name**:
   ```python
   # Correct names (case-sensitive!)
   BASELINE_MODEL_PATH
   LANE_POLYGONS
   LANE_RESTRICTIONS
   CONFIDENCE_THRESHOLD
   # Not BASELINE_MODEL_path or lane_polygons (wrong case)
   ```

2. **Verify import**:
   ```python
   from utils.config import LANE_POLYGONS  # Correct
   ```

---

## Debug Mode

### Enable Verbose Logging

Add to `main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Now use logger.debug() for detailed info
```

---

## Getting Help

1. **Check this guide** first for your specific error
2. **Check console output** - error messages often explain what's wrong
3. **Review configuration** - most issues are config-related
4. **Test components independently**:
   ```bash
   python tools/model_evaluator.py     # Test model
   python tools/roi_drawer.py          # Test video
   python test_setup.py                # Test installation
   ```

---

## Report Issues

Include when reporting problems:
- ✅ Full error message
- ✅ OS and Python version (`python --version`)
- ✅ GPU info (`nvidia-smi`)
- ✅ Your `utils/config.py` (without sensitive paths)
- ✅ Steps to reproduce
- ✅ Output of `test_setup.py`
