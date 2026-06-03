# 🏗️ System Architecture

Detailed technical design and component responsibilities.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    TRAFFIC MONITORING SYSTEM                 │
└─────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Video   │    │ Camera   │    │  Stream  │
    │  File    │    │  (RTSP)  │    │  (HTTP)  │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │                │               │
         └────────────────┼───────────────┘
                          │
                    ┌─────▼─────┐
                    │   main.py  │  (Orchestrator)
                    │ (Pipeline) │
                    └─────┬─────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │  Detection   │ │Violation │ │   Traffic    │
    │  & Tracking  │ │ Analysis │ │   Counting   │
    │   (YOLO+     │ │(Spatial) │ │  (Unique ID) │
    │   BoT-SORT)  │ │          │ │              │
    └──────────────┘ └──────────┘ └──────────────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
         ┌─────────────┐      ┌─────────────┐
         │   Logging   │      │Visualization│
         │  (Async)    │      │   (Draw)    │
         │ CSV + Images│      │ Annotations │
         └─────────────┘      └─────────────┘
              │                       │
              └───────────┬───────────┘
                          ▼
            ┌─────────────────────────┐
            │  Display + Video Output │
            │   (Screen + File)       │
            └─────────────────────────┘
```

---

## 5-Step Pipeline

### Step 1: **Detection & Tracking** (`core/detector_tracker.py`)

**Purpose**: Detect vehicles and assign persistent IDs

**Input**: Raw video frame (numpy array)

**Process**:
1. Optional CLAHE preprocessing for low-light robustness
2. YOLO inference for bounding boxes + class predictions
3. BoT-SORT tracking for persistent ID assignment
4. Convert detections to `TrackedVehicle` objects

**Output**: 
```python
FrameState(
    vehicles=[
        TrackedVehicle(track_id=123, bbox=(...), cls_id=0, ...),
        TrackedVehicle(track_id=124, bbox=(...), cls_id=1, ...),
        ...
    ]
)
```

**Key Methods**:
- `process(frame_state)` - Run detection/tracking on frame
- `get_model_info()` - Return model configuration

**Key Features**:
- Multi-format model support (.pt, .onnx, .engine)
- Automatic device selection (GPU/CPU)
- Handles Vietnamese filenames on Windows

---

### Step 2: **Violation Analysis** (`core/analyzer.py`)

**Purpose**: Identify lane violations

**Input**: `FrameState` with vehicles

**Process**:
1. For each vehicle's bottom-center point:
2. Use `cv2.pointPolygonTest` to test point against each lane polygon
3. If inside lane polygon:
   - Check if vehicle class is in `LANE_RESTRICTIONS[lane]`
   - If NOT allowed, mark as violation
4. Track unique violators across frames

**Output**:
```python
FrameState(
    vehicles=[
        TrackedVehicle(..., is_violating=True, violation_lane="Lane_1"),
        ...
    ],
    violations=[...]
)
```

**Key Methods**:
- `process(frame_state)` - Analyze violations
- `get_violation_count()` - Return unique violators

**Key Logic**:
- **Not** using deep learning for this step
- **Pure spatial** analysis with polygons
- **Efficient** and deterministic

---

### Step 3: **Traffic Counting** (`core/counter.py`)

**Purpose**: Count unique vehicles by class

**Input**: `FrameState` with vehicles

**Process**:
1. For each vehicle:
2. If track_id not in `counted_ids`:
   - Add to `counted_ids` set
   - Increment count for vehicle class
3. Return updated counts dictionary

**Output**:
```python
FrameState(
    counts={
        "motorbike": 156,
        "car": 234,
        "truck": 45,
        "bus": 12
    }
)
```

**Key Methods**:
- `process(frame_state)` - Update counts
- `get_counts()` - Get current counts
- `reset()` - Clear counts

**Key Logic**:
- Each track_id counted **exactly once**
- Prevents double-counting across frames
- Independent of violations

---

### Step 4: **Violation Logging** (`utils/logger.py`)

**Purpose**: Asynchronously save CSV logs and evidence images

**Input**: Violation events from analyzer

**Process**:
1. **Main thread**: Queue violation events (non-blocking)
2. **Worker thread**:
   - Dequeue violation events
   - Write CSV log entries
   - Extract vehicle bbox + 20px padding
   - Save evidence image
   - Never blocks main pipeline

**Output**:
```
output/violations.csv:
frame_id,timestamp,vehicle_id,class_name,violation_type,confidence,bbox,violation_lane

evidence/
├── violation_vid123_frm456_wrong_lane_1717382400.jpg
├── violation_vid124_frm457_wrong_lane_1717382410.jpg
└── ...
```

**Key Methods**:
- `log_violation(violation_event)` - Queue violation
- `save_violation_image(vehicle, frame)` - Save evidence
- `get_statistics()` - Get logging stats

**Key Features**:
- **Non-blocking**: Uses Queue + threading
- **Thread-safe**: Queue handles synchronization
- **Efficient**: 0.01s sleep prevents busy-waiting

---

### Step 5: **Visualization & Output** (`utils/visualizer.py`)

**Purpose**: Draw annotations and save output video

**Input**: `FrameState` with vehicles and violations

**Process**:
1. Draw lane ROI polygons (green boundaries)
2. Draw vehicle bounding boxes:
   - Green = normal vehicle
   - Red = violation
3. Draw tracking IDs and confidence scores
4. Draw statistics panel (vehicle counts, FPS)
5. Draw violations summary

**Output**: Annotated frame (display + video file)

**Key Methods**:
- `draw(frame_state, lane_polygons)` - Main drawing orchestrator
- `_draw_roi_polygons()` - Draw lane boundaries
- `_draw_vehicles()` - Draw bboxes and IDs
- `_draw_statistics()` - Draw stats overlay

**Colors**:
- `(0, 255, 0)` - Green: normal vehicles
- `(0, 0, 255)` - Red: violations
- `(255, 255, 0)` - Cyan: tracking IDs
- `(0, 255, 255)` - Yellow: stats text

---

## Data Structures

### `ModelConfig` (`core/datatypes.py`)

Configuration for detection model

```python
@dataclass
class ModelConfig:
    model_path: str                    # Path to model file
    model_type: str                    # 'pt', 'onnx', or 'engine'
    confidence_threshold: float        # Detection threshold (0-1)
    iou_threshold: float              # NMS threshold
    device: str                        # 'cuda' or 'cpu'
```

### `TrackedVehicle` (`core/datatypes.py`)

Single detected and tracked vehicle

```python
@dataclass
class TrackedVehicle:
    track_id: int                      # Persistent tracking ID
    bbox: Tuple[int, int, int, int]    # (x1, y1, x2, y2) in pixels
    cls_id: int                        # Class ID (0-3)
    cls_name: str                      # Class name
    conf: float                        # Confidence (0-1)
    bottom_center: Tuple[int, int]     # Auto-computed from bbox
    is_violating: bool                 # Violation flag
    violation_lane: str                # Lane name if violating
    violation_type: str                # Type of violation
```

### `FrameState` (`core/datatypes.py`)

Complete state after processing one frame

```python
@dataclass
class FrameState:
    frame_id: int                      # Frame number
    original_frame: np.ndarray         # Original video frame
    processed_frame: np.ndarray        # Processed/annotated frame
    vehicles: List[TrackedVehicle]     # Detected vehicles
    counts: Dict[str, int]             # Counts by class
    violations: List[Dict]             # Violation events
    timestamp: float                   # Unix timestamp
    fps: float                         # Current FPS
```

### `DetectionResult` (`core/datatypes.py`)

Output from YOLO model

```python
@dataclass
class DetectionResult:
    boxes: np.ndarray                  # Bounding boxes (n, 4)
    track_ids: np.ndarray              # Tracking IDs (n,)
    class_ids: np.ndarray              # Class IDs (n,)
    confidences: np.ndarray            # Confidences (n,)
    class_names: Dict[int, str]        # ID → name mapping
```

---

## Configuration

### `utils/config.py`

Centralized configuration with auto-created directories

```python
# Paths
PROJECT_ROOT = Path(__file__).parent.parent
WEIGHTS_DIR = PROJECT_ROOT / 'weights'
DATA_DIR = PROJECT_ROOT / 'Data'
EVIDENCE_DIR = PROJECT_ROOT / 'evidence'
OUTPUT_DIR = PROJECT_ROOT / 'output'

# Models
BASELINE_MODEL_PATH = WEIGHTS_DIR / 'traffic_model' / 'weights' / 'best.pt'
OPTIMIZED_MODEL_PATH = WEIGHTS_DIR / 'best.onnx'

# Video
VIDEO_SOURCE = 0                       # File path or camera index
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 25

# Detection
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45
DEVICE = 'cuda'

# Lane Polygons
LANE_POLYGONS = {
    "Lane_1": np.array([...]),
    "Lane_2": np.array([...]),
}

# Lane Restrictions
LANE_RESTRICTIONS = {
    "Lane_1": {"motorbike", "car"},
    "Lane_2": {"car", "truck", "bus"},
}

# Logging
SAVE_VIOLATION_IMAGES = True
OUTPUT_VIDEO_PATH = OUTPUT_DIR / 'VIDEO_OUTPUT.mp4'
```

---

## Dependency Flow

```
main.py
├── core.detector_tracker (YOLO + tracking)
│   └── ultralytics.YOLO
│   └── cv2 (image processing)
│   └── numpy
│
├── core.analyzer (violation detection)
│   └── cv2.pointPolygonTest
│   └── numpy
│
├── core.counter (traffic counting)│   └── (no external deps)
│
├── utils.logger (async logging)
│   └── threading
│   └── queue
│   └── csv
│   └── cv2 (image I/O)
│
├── utils.visualizer (drawing)
│   └── cv2 (drawing functions)
│   └── numpy
│
└── utils.config (configuration)
    └── pathlib
    └── numpy
```

---

## Threading Model

### Main Thread
- Reads video frames
- Runs detection/tracking/analysis
- Calls visualizer
- Displays/writes output
- Handles keyboard input

### Worker Thread (Logger)
```
┌─────────────────┐
│  Main Pipeline  │
│  (Add to queue) │
└────────┬────────┘
         │
    ┌────▼────┐
    │  Queue  │  (thread-safe)
    └────┬────┘
         │
┌────────▼───────────┐
│  Worker Thread     │
│  (Process queue)   │
│  - Write CSV       │
│  - Save images     │
│  - No FPS impact   │
└────────────────────┘
```

**Benefits**:
- ✅ No blocking on disk I/O
- ✅ Maintains consistent FPS
- ✅ Thread-safe via Queue
- ✅ Graceful shutdown handling

---

## Performance Characteristics

### Time Per Frame (RTX 3060)

| Component | PyTorch | ONNX | TensorRT |
|-----------|---------|------|----------|
| Detection | 30ms | 15ms | 8ms |
| Tracking | 5ms | 5ms | 5ms |
| Analysis | 2ms | 2ms | 2ms |
| Counting | 1ms | 1ms | 1ms |
| Logging | 0.5ms | 0.5ms | 0.5ms |
| Drawing | 8ms | 8ms | 8ms |
| **Total** | **~47ms** | **~32ms** | **~25ms** |
| **FPS** | **21 FPS** | **31 FPS** | **40 FPS** |

---

## Error Handling

All components include:
- ✅ Try-except blocks with informative messages
- ✅ Validation of input data types
- ✅ Graceful degradation on errors
- ✅ Logging of exceptions

Example:
```python
try:
    result = detector.process(frame_state)
except Exception as e:
    logger.error(f"Detection failed: {e}")
    # Return frame unchanged or use fallback
```

---

## Scalability

### Single Lane to Multiple Lanes
```python
LANE_POLYGONS = {
    "Lane_1": np.array([...]),
    "Lane_2": np.array([...]),
    "Lane_3": np.array([...]),
    "Lane_4": np.array([...]),
}
```
System automatically scales with number of lanes.

### Different Model Sizes
```python
# Small (nano)
python main.py --model n

# Large (xlarge)
python main.py --model x
```
Easy switching between model architectures.

### Video Sources
```python
# File
VIDEO_SOURCE = "video.mp4"

# Webcam
VIDEO_SOURCE = 0

# RTSP Stream (network camera)
VIDEO_SOURCE = "rtsp://camera_ip:554/stream"
```

---

## Security Considerations

1. **Input Validation**: Validate all model paths and video sources
2. **Error Handling**: Catch and log all errors
3. **File Permissions**: Ensure write access to output directories
4. **Resource Limits**: Monitor GPU/CPU usage
5. **No Sensitive Data**: Don't log personal information

---

## Future Extensions

- [ ] Multi-GPU support
- [ ] Distributed processing across multiple machines
- [ ] Web dashboard for real-time monitoring
- [ ] REST API for integration
- [ ] Database logging (PostgreSQL, MongoDB)
- [ ] Custom model support
- [ ] Mobile app for violation review
