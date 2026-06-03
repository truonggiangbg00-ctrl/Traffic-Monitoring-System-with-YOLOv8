# 🚀 Usage Guide

Complete examples and tutorials for using the system.

---

## Basic Usage

### 1. Simple Run

```bash
python main.py
```

This runs the system with default configuration:
- Uses baseline PyTorch model
- Reads from VIDEO_SOURCE defined in config.py
- Displays live output
- Saves violations to CSV
- Saves evidence images

**Output**:
```
Starting Traffic Monitoring System...
✓ Model loaded: best.pt
✓ Video source: video.mp4
✓ Lane config: 2 lanes
✓ FPS target: 25

[Processing frames...]
Frame 0100: 12 vehicles, 2 violations, FPS: 18.5
Frame 0200: 15 vehicles, 3 violations, FPS: 19.2
...

[FINISHED]
Total frames: 1000
Processing time: 52.3s
Average FPS: 19.1
Violations detected: 45
Evidence images saved: 45
CSV log: output/violations.csv
```

---

### 2. Run with Optimized Model

```bash
python main.py --optimized
```

Uses ONNX model (1.5-2x faster) if available:
```
✓ Model loaded: best.onnx (ONNX optimized)
...
Average FPS: 32.4
```

---

### 3. Headless Mode (No Display)

```bash
python main.py --no-display > log.txt 2>&1 &
```

Useful for:
- Running on servers without GPU display
- Processing multiple videos in parallel
- Deploying in production

**Output**: Only CSV logs and evidence images (no screen display)

---

### 4. Limit Processing

```bash
python main.py --max-frames 500
```

Process only first 500 frames (useful for testing).

---

## Interactive Controls

While video is playing, press:

| Key | Effect |
|-----|--------|
| **Q** | Quit and save all logs |
| **P** | Pause video (press again to resume) |
| **S** | Save current frame as screenshot |
| **ESC** | Same as Q |

---

## Configuration

### Basic Configuration

Edit `utils/config.py`:

```python
# 1. Set video source
VIDEO_SOURCE = "C:/videos/highway.mp4"  # or 0 for webcam

# 2. Set lane configuration
LANE_POLYGONS = {
    "Lane_1": np.array([[489, 400], [721, 395], [518, 1079], [0, 1053]]),
    "Lane_2": np.array([[723, 396], [913, 390], [1021, 1077], [528, 1076]]),
}

# 3. Set restrictions
LANE_RESTRICTIONS = {
    "Lane_1": {"motorbike", "car"},           # Only bikes and cars
    "Lane_2": {"car", "truck", "bus"},        # Not bikes
}

# 4. Adjust detection threshold
CONFIDENCE_THRESHOLD = 0.6  # Higher = fewer detections
```

---

## Advanced Configuration

### Model Selection

```python
# Baseline PyTorch (highest accuracy)
BASELINE_MODEL_PATH = "weights/best.pt"

# Or ONNX (faster)
OPTIMIZED_MODEL_PATH = "weights/best.onnx"

# Or TensorRT (fastest, NVIDIA only)
TENSORRT_MODEL_PATH = "weights/best.engine"
```

### Video Settings

```python
# Frame resolution
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Processing speed
TARGET_FPS = 25

# Video output
SAVE_OUTPUT_VIDEO = True
OUTPUT_VIDEO_PATH = "output/VIDEO_OUTPUT.mp4"
```

### Detection Fine-tuning

```python
# Lower = more sensitive, slower
CONFIDENCE_THRESHOLD = 0.4

# Lower = keep more detections
IOU_THRESHOLD = 0.4

# Device
DEVICE = "cuda"  # or "cpu"
```

---

## Setting Up Lane Polygons

### Interactive Drawing

```bash
python tools/roi_drawer.py video.mp4
```

This opens an interactive tool:

**Controls**:
- **LEFT CLICK** - Add polygon point
- **RIGHT CLICK** - Remove last point
- **'N'** - Save current lane
- **'C'** - Clear current polygon
- **'Q'** - Finish and generate code
- **'SPACE'** - Delete last saved lane

**Example Output**:
```python
# ROI Polygons (Lane Boundaries)
LANE_POLYGONS = {
    "Lane_1": np.array([
        [489, 400], [721, 395], [518, 1079], [0, 1053]
    ], dtype=np.int32),
    "Lane_2": np.array([
        [723, 396], [913, 390], [1021, 1077], [528, 1076]
    ], dtype=np.int32),
}
```

Copy this code to `utils/config.py`.

---

## Dataset Cleaning & Training

### Clean Dataset

```bash
python tools/data_cleaner.py ../Data
```

This:
- Removes corrupted images
- Removes orphaned files
- Normalizes bbox coordinates
- Reports statistics

### Train Custom Model

```bash
python tools/train_yolo.py --model s --epochs 100
```

Options:
- `--model` - Model size (n/s/m/l/x)
- `--epochs` - Number of epochs
- `--batch` - Batch size
- `--no-eval` - Skip evaluation

---

## Model Export & Optimization

### Export to ONNX

```bash
python tools/model_exporter.py --format onnx
```

Creates `weights/best.onnx` (1.5-2x speedup)

### Export to TensorRT

```bash
python tools/model_exporter.py --format tensorrt
```

Creates `weights/best.engine` (3-4x speedup, NVIDIA only)

### Export All Formats

```bash
python tools/model_exporter.py --all
```

---

## Model Evaluation

### Compare Models

```bash
python tools/model_evaluator.py
```

Output example:
```
📊 MODEL COMPARISON RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model         mAP50  mAP50-95  Precision  Recall   F1    FPS
──────────────────────────────────────────────────────────
Baseline-PT   0.923  0.876     0.951      0.904   0.927  18.3
Optimized-ONNX 0.923 0.876     0.951      0.904   0.927  32.5
Optimized-TRT 0.923  0.876     0.951      0.904   0.927  58.2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Output Interpretation

### CSV Log File

**Location**: `output/violations.csv`

**Format**:
```csv
frame_id,timestamp,vehicle_id,class_name,violation_type,confidence,bbox,violation_lane
1234,1717382400.123,456,car,wrong_lane,0.92,"(100,200,250,450)",Lane_1
1235,1717382400.144,457,motorbike,wrong_lane,0.88,"(500,300,650,500)",Lane_2
```

**Fields**:
- `frame_id` - Frame number
- `timestamp` - Unix timestamp
- `vehicle_id` - Tracking ID
- `class_name` - Vehicle type
- `violation_type` - Type of violation
- `confidence` - Detection confidence (0-1)
- `bbox` - Bounding box (x1,y1,x2,y2)
- `violation_lane` - Lane where violation occurred

### Evidence Images

**Location**: `evidence/violation_*.jpg`

**Naming**: `violation_vid{ID}_frm{FRAME}_{TYPE}_{TIMESTAMP}.jpg`

Example: `violation_vid456_frm1234_wrong_lane_1717382400.jpg`

**Content**: Vehicle image with 20px padding around detection box

### Video Output

**Location**: `output/VIDEO_OUTPUT.mp4`

Annotated video with:
- Green boxes - Normal vehicles
- Red boxes - Violations
- Tracking IDs
- Statistics overlay
- FPS counter

---

## Real-World Examples

### Example 1: Highway Toll Booth

Monitor incoming traffic for violations:

```python
# config.py
VIDEO_SOURCE = "rtsp://toll_booth_camera:554/stream"

LANE_POLYGONS = {
    "Toll_Lane_1": np.array([...]),
    "Toll_Lane_2": np.array([...]),
    "Toll_Lane_3": np.array([...]),
}

LANE_RESTRICTIONS = {
    "Toll_Lane_1": {"motorbike"},
    "Toll_Lane_2": {"car"},
    "Toll_Lane_3": {"truck", "bus"},
}

CONFIDENCE_THRESHOLD = 0.6
SAVE_VIOLATION_IMAGES = True
```

```bash
# Run continuously
python main.py &
```

---

### Example 2: Lane Discipline Monitoring

Monitor wrong-lane usage:

```python
LANE_POLYGONS = {
    "Lane_1": np.array([...]),
    "Lane_2": np.array([...]),
    "Lane_3": np.array([...]),
    "Lane_4": np.array([...]),
}

# Motorcycles not allowed in fast lanes
LANE_RESTRICTIONS = {
    "Lane_1": {"car", "truck", "bus"},
    "Lane_2": {"car", "truck", "bus"},
    "Lane_3": {"motorbike", "car"},
    "Lane_4": {"motorbike"},
}
```

---

### Example 3: Traffic Statistics

Count vehicle flows by class:

```python
# Process entire video and collect statistics
python main.py --max-frames all

# Analyze CSV
import pandas as pd
df = pd.read_csv("output/violations.csv")

# Vehicle count by class
print(df.groupby("class_name").size())

# Violations by class
violations = df.groupby("class_name").size()
print(f"Motorbike violations: {violations.get('motorbike', 0)}")
print(f"Car violations: {violations.get('car', 0)}")
```

---

## Batch Processing

### Process Multiple Videos

```bash
#!/bin/bash
for video in videos/*.mp4; do
    echo "Processing $video"
    python main.py --no-display
    # Copy CSV and evidence to archive
    mv output/violations.csv "archive/$(basename $video).csv"
    mv evidence/* "archive/video_$(basename $video)/"
done
```

---

## Performance Monitoring

### Check System Status

```bash
# Monitor GPU usage
nvidia-smi -l 1

# In another terminal, run system
python main.py
```

**Expected**:
- GPU Memory: 6-8GB (baseline), 3-5GB (ONNX)
- GPU Utilization: 70-95%
- FPS: >15 (production requirement)

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for:
- Common errors and solutions
- Performance issues
- Configuration problems
- File handling issues

---

## Best Practices

1. **Always clean dataset first**:
   ```bash
   python tools/data_cleaner.py ../Data
   ```

2. **Test on short video first**:
   ```bash
   python main.py --max-frames 100
   ```

3. **Optimize for your hardware**:
   - Use ONNX/TensorRT if available
   - Adjust batch size for GPU memory

4. **Monitor output regularly**:
   ```bash
   tail -f output/violations.csv
   ```

5. **Back up evidence images**:
   ```bash
   cp -r evidence/ backup/
   ```

---

## Next Steps

- **Learn more**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Tune performance**: See [PERFORMANCE_TUNING.md](PERFORMANCE_TUNING.md)
- **Debug issues**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **API reference**: See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
