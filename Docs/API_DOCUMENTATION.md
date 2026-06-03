# 📖 API Documentation

Complete reference for all modules, classes, and functions.

---

## `core/datatypes.py`

Data structures for inter-component communication.

### `ModelConfig`

Configuration for YOLO detection model.

```python
@dataclass
class ModelConfig:
    model_path: str              # Path to model file (.pt, .onnx, .engine)
    model_type: str              # 'pt' (PyTorch), 'onnx', or 'engine' (TensorRT)
    confidence_threshold: float  # Detection confidence threshold (0.0-1.0)
    iou_threshold: float        # NMS IOU threshold (0.0-1.0)
    device: str                 # 'cuda' or 'cpu'
```

**Example**:
```python
config = ModelConfig(
    model_path="weights/best.pt",
    model_type="pt",
    confidence_threshold=0.5,
    iou_threshold=0.45,
    device="cuda"
)
```

---

### `TrackedVehicle`

Single vehicle detection with tracking information.

```python
@dataclass
class TrackedVehicle:
    track_id: int                           # Persistent ID (persists across frames)
    bbox: Tuple[int, int, int, int]        # Bounding box (x1, y1, x2, y2) in pixels
    cls_id: int                            # Class ID (0=motorbike, 1=car, 2=truck, 3=bus)
    cls_name: str                          # Class name ("motorbike", "car", etc.)
    conf: float                            # Detection confidence (0.0-1.0)
    bottom_center: Tuple[int, int]         # Auto-computed: bottom-center point of bbox
    is_violating: bool = False             # Violation flag (set by analyzer)
    violation_lane: str = ""               # Lane name if violating
    violation_type: str = "wrong_lane"     # Type: "wrong_lane", "overspeed", etc.
```

**Properties**:
- `bottom_center` is automatically computed from bbox during initialization

**Example**:
```python
vehicle = TrackedVehicle(
    track_id=123,
    bbox=(100, 200, 250, 450),
    cls_id=1,
    cls_name="car",
    conf=0.92,
    bottom_center=(175, 450),  # Auto-computed
    is_violating=True,
    violation_lane="Lane_1"
)
```

---

### `FrameState`

Complete processing state for one video frame.

```python
@dataclass
class FrameState:
    frame_id: int                    # Frame number (0-indexed)
    original_frame: np.ndarray      # Original video frame (H, W, 3) uint8
    processed_frame: np.ndarray     # Processed/annotated frame (H, W, 3) uint8
    vehicles: List[TrackedVehicle]  # List of detected vehicles
    counts: Dict[str, int]          # Vehicle counts by class
    violations: List[Dict]          # Violation events
    timestamp: float                # Unix timestamp
    fps: float                      # Current FPS
```

**Flow**:
1. Created in `main.py` with frame_id, original_frame, timestamp
2. Updated by `detector.process()` → adds vehicles
3. Updated by `analyzer.process()` → sets is_violating flags
4. Updated by `counter.process()` → updates counts
5. Updated by `visualizer.draw()` → sets processed_frame

**Example**:
```python
frame_state = FrameState(
    frame_id=42,
    original_frame=frame_array,
    processed_frame=np.zeros_like(frame_array),
    vehicles=[],
    counts={},
    violations=[],
    timestamp=1717382400.123,
    fps=0.0
)
```

---

### `DetectionResult`

Raw output from YOLO model.

```python
@dataclass
class DetectionResult:
    boxes: np.ndarray           # Bounding boxes (N, 4) - (x1, y1, x2, y2)
    track_ids: np.ndarray       # Tracking IDs (N,)
    class_ids: np.ndarray       # Class IDs (N,)
    confidences: np.ndarray     # Confidences (N,)
    class_names: Dict[int, str] # {0: "motorbike", 1: "car", ...}
```

---

## `core/detector_tracker.py`

Vehicle detection and tracking using YOLO + BoT-SORT.

### `DetectorTracker`

Main class for detection and tracking.

```python
class DetectorTracker:
    def __init__(self, model_config: ModelConfig):
        """
        Initialize detector and tracker.
        
        Args:
            model_config: ModelConfig with model_path, model_type, thresholds
            
        Raises:
            FileNotFoundError: If model_path doesn't exist
            ValueError: If model_type is invalid
        """
    
    def process(self, frame_state: FrameState) -> FrameState:
        """
        Detect and track vehicles in frame.
        
        Args:
            frame_state: FrameState with original_frame
            
        Returns:
            FrameState with updated vehicles list
            
        Raises:
            RuntimeError: If detection fails
        """
    
    def get_model_info(self) -> Dict:
        """
        Get model configuration information.
        
        Returns:
            Dict with model_path, model_type, device, img_size
        """
```

**Features**:
- ✅ Multi-format model support (.pt, .onnx, .engine)
- ✅ CLAHE preprocessing for low-light
- ✅ BoT-SORT tracking with persistence
- ✅ Handles Vietnamese filenames

**Example**:
```python
config = ModelConfig(
    model_path="weights/best.pt",
    model_type="pt",
    confidence_threshold=0.5,
    iou_threshold=0.45,
    device="cuda"
)
detector = DetectorTracker(config)

# Process frame
frame_state = FrameState(frame_id=0, original_frame=frame, ...)
result = detector.process(frame_state)

# result.vehicles now contains TrackedVehicle objects
for vehicle in result.vehicles:
    print(f"ID {vehicle.track_id}: {vehicle.cls_name} @ {vehicle.bbox}")
```

---

## `core/analyzer.py`

Lane violation detection using spatial analysis.

### `TrafficAnalyzer`

Lane violation detection engine.

```python
class TrafficAnalyzer:
    def __init__(self, lane_polygons: Dict[str, np.ndarray],
                 lane_restrictions: Dict[str, Set[str]]):
        """
        Initialize analyzer with lane definitions.
        
        Args:
            lane_polygons: {"Lane_1": polygon_points, ...}
            lane_restrictions: {"Lane_1": {"car", "truck"}, ...}
        """
    
    def process(self, frame_state: FrameState) -> FrameState:
        """
        Detect violations in frame.
        
        Args:
            frame_state: FrameState with vehicles
            
        Returns:
            FrameState with is_violating flags set
        """
    
    def get_violation_count(self) -> int:
        """
        Get total unique violators detected.
        
        Returns:
            Number of unique vehicles that violated
        """
```

**Logic**:
1. For each vehicle's bottom_center point
2. Test against each lane polygon using cv2.pointPolygonTest
3. If inside lane AND class not in restrictions → violation

**Example**:
```python
analyzer = TrafficAnalyzer(
    lane_polygons={
        "Lane_1": np.array([[0, 0], [100, 0], [100, 100], [0, 100]])
    },
    lane_restrictions={
        "Lane_1": {"car", "truck"}  # Only cars and trucks allowed
    }
)

frame_state = analyzer.process(frame_state)

for vehicle in frame_state.vehicles:
    if vehicle.is_violating:
        print(f"Violation: {vehicle.cls_name} in {vehicle.violation_lane}")
```

---

## `core/counter.py`

Traffic flow counting by vehicle class.

### `TrafficCounter`

Vehicle counting engine.

```python
class TrafficCounter:
    def __init__(self):
        """Initialize counter."""
    
    def process(self, frame_state: FrameState) -> FrameState:
        """
        Count vehicles in frame.
        
        Args:
            frame_state: FrameState with vehicles
            
        Returns:
            FrameState with updated counts
        """
    
    def get_counts(self) -> Dict[str, int]:
        """
        Get current vehicle counts.
        
        Returns:
            {"motorbike": N, "car": M, ...}
        """
    
    def get_total(self) -> int:
        """Get total vehicle count."""
    
    def reset(self):
        """Reset all counts to zero."""
```

**Logic**:
- Each track_id counted exactly once
- First encounter with new ID increments count
- Prevents double-counting across frames

**Example**:
```python
counter = TrafficCounter()

# Process frames
for frame in video:
    frame_state = detector.process(frame_state)
    frame_state = counter.process(frame_state)

counts = counter.get_counts()
print(f"Detected {counts['car']} unique cars")
```

---

## `utils/config.py`

Centralized configuration management.

**Module-level variables**:

```python
# Paths
PROJECT_ROOT: Path              # Auto-computed project root
WEIGHTS_DIR: Path               # Model weights directory
DATA_DIR: Path                  # Training data directory
EVIDENCE_DIR: Path              # Violation evidence directory
OUTPUT_DIR: Path                # Output directory

# Models
BASELINE_MODEL_PATH: Path       # PyTorch baseline model
OPTIMIZED_MODEL_PATH: Path      # ONNX optimized model
FALLBACK_MODEL_PATH: Path       # Fallback if primary unavailable

# Video
VIDEO_SOURCE: Union[str, int]   # Video file path or camera index
FRAME_WIDTH: int                # Target frame width
FRAME_HEIGHT: int               # Target frame height
TARGET_FPS: int                 # Target frames per second

# Detection
CONFIDENCE_THRESHOLD: float     # Detection confidence (0-1)
IOU_THRESHOLD: float           # NMS threshold (0-1)
DEVICE: str                    # 'cuda' or 'cpu'

# Lane Configuration
LANE_POLYGONS: Dict[str, np.ndarray]        # Lane boundaries
LANE_RESTRICTIONS: Dict[str, Set[str]]      # Allowed classes per lane

# Logging
LOG_FILE: Path                  # CSV log file path
SAVE_VIOLATION_IMAGES: bool     # Save evidence images
VIOLATION_IMAGE_FORMAT: str     # Image format (.jpg, .png)

# Output
OUTPUT_VIDEO_PATH: Path         # Output video path
SAVE_OUTPUT_VIDEO: bool         # Save annotated video
```

**Example**:
```python
from utils.config import LANE_POLYGONS, LANE_RESTRICTIONS, CONFIDENCE_THRESHOLD

print(f"Lanes defined: {list(LANE_POLYGONS.keys())}")
print(f"Detection threshold: {CONFIDENCE_THRESHOLD}")
```

---

## `utils/visualizer.py`

Frame annotation and visualization.

### `Visualizer`

Main drawing/visualization engine.

```python
class Visualizer:
    def __init__(self):
        """Initialize visualizer."""
    
    def draw(self, frame_state: FrameState, 
             lane_polygons: Dict[str, np.ndarray],
             draw_stats: bool = True) -> FrameState:
        """
        Draw all annotations on frame.
        
        Args:
            frame_state: FrameState with vehicles
            lane_polygons: Lane boundary polygons
            draw_stats: Whether to draw statistics
            
        Returns:
            FrameState with processed_frame set
        """
```

**Drawing Components**:
- Lane ROI polygons (green boundaries)
- Vehicle bounding boxes (green=normal, red=violation)
- Tracking IDs and confidence scores
- Statistics panel (counts, FPS)
- Violations summary

**Colors**:
- Green `(0, 255, 0)` - Normal vehicles
- Red `(0, 0, 255)` - Violations
- Cyan `(255, 255, 0)` - Text
- Yellow `(0, 255, 255)` - Highlights

**Example**:
```python
visualizer = Visualizer()
frame_state = visualizer.draw(frame_state, LANE_POLYGONS)

# frame_state.processed_frame now contains annotated image
cv2.imshow("Traffic Monitor", frame_state.processed_frame)
```

---

## `utils/logger.py`

Asynchronous violation logging and evidence saving.

### `ViolationLogger`

Async logging engine with background thread.

```python
class ViolationLogger:
    def __init__(self, evidence_dir: Path, log_file: Path):
        """
        Initialize logger with background thread.
        
        Args:
            evidence_dir: Directory for evidence images
            log_file: CSV log file path
        """
    
    def log_violation(self, frame_id: int, timestamp: float,
                      vehicle: TrackedVehicle):
        """
        Log violation event (non-blocking).
        
        Args:
            frame_id: Frame number
            timestamp: Unix timestamp
            vehicle: TrackedVehicle with violation info
        """
    
    def save_violation_image(self, frame: np.ndarray,
                            vehicle: TrackedVehicle,
                            frame_id: int, timestamp: float):
        """
        Save evidence image (queued for async processing).
        
        Args:
            frame: Video frame
            vehicle: Vehicle with violation
            frame_id: Frame number
            timestamp: Unix timestamp
        """
    
    def get_statistics(self) -> Dict:
        """
        Get logging statistics.
        
        Returns:
            {"total_logged": N, "queue_size": M, ...}
        """
    
    def shutdown(self):
        """Stop background thread and flush queues."""
```

**Features**:
- ✅ Non-blocking (uses Queue)
- ✅ Background worker thread
- ✅ CSV auto-initialization with headers
- ✅ Evidence image cropping + padding

**CSV Format**:
```
frame_id,timestamp,vehicle_id,class_name,violation_type,confidence,bbox,violation_lane
1234,1717382400.123,456,car,wrong_lane,0.92,"(100,200,250,450)",Lane_1
```

**Example**:
```python
logger = ViolationLogger(EVIDENCE_DIR, LOG_FILE)

# Log violation (returns immediately)
logger.log_violation(frame_id=42, timestamp=time.time(), vehicle=vehicle)

# Shutdown (waits for queue to process)
logger.shutdown()
```

---

## `main.py`

Main orchestrator pipeline.

### `TrafficMonitoringSystem`

Complete system orchestrator.

```python
class TrafficMonitoringSystem:
    def __init__(self, config: ModelConfig = None):
        """
        Initialize complete system.
        
        Args:
            config: ModelConfig (uses default if None)
        """
    
    def process_frame(self, frame: np.ndarray) -> FrameState:
        """
        Process single video frame through pipeline.
        
        Args:
            frame: Video frame (H, W, 3) uint8
            
        Returns:
            FrameState with all processing complete
        """
    
    def run(self, max_frames: int = None, display: bool = True):
        """
        Main processing loop.
        
        Args:
            max_frames: Max frames to process (None = all)
            display: Whether to display output
        """
    
    def shutdown(self):
        """Graceful shutdown with statistics."""
```

**Pipeline Steps**:
1. Create FrameState with frame_id, original_frame, timestamp
2. detector.process() → detects and tracks
3. analyzer.process() → identifies violations
4. counter.process() → updates counts
5. logger.log_violations() → logs violations
6. visualizer.draw() → annotates frame
7. Display and/or save output

**Keyboard Controls**:
- **Q** - Quit and save logs
- **P** - Pause video
- **S** - Save screenshot

**Example**:
```python
system = TrafficMonitoringSystem()
system.run(max_frames=1000, display=True)
```

---

## Command-Line Interface

### `python main.py [OPTIONS]`

```bash
--model {pt,onnx,engine}    # Model format (default: pt)
--optimized                 # Use optimized model
--max-frames N              # Max frames to process
--no-display               # Run headless
--help                     # Show help
```

**Examples**:
```bash
# Basic run
python main.py

# With optimized model
python main.py --optimized

# Headless, max 5000 frames
python main.py --no-display --max-frames 5000

# Custom model
python main.py --model onnx
```

---

## Error Handling

All components implement:
- ✅ Try-except with informative messages
- ✅ Input validation
- ✅ Graceful error recovery
- ✅ Detailed error logging

**Example**:
```python
try:
    result = detector.process(frame_state)
except Exception as e:
    logger.error(f"Detection failed on frame {frame_state.frame_id}: {e}")
    # Return frame unchanged or use fallback
```

---

## Performance Tips

1. **Faster Processing**:
   - Use ONNX or TensorRT models
   - Reduce frame resolution
   - Increase confidence threshold
   - Use smaller model (nano/small)

2. **Better Accuracy**:
   - Lower confidence threshold
   - Use large model (large/xlarge)
   - Ensure good lighting
   - Update training data

3. **GPU Memory**:
   - Monitor with `nvidia-smi`
   - Reduce batch size if needed
   - Close other GPU applications

---

## Thread Safety

- ✅ Queue-based inter-thread communication (thread-safe)
- ✅ No shared mutable state between threads
- ✅ Proper shutdown sequence
- ✅ Resource cleanup on exit
