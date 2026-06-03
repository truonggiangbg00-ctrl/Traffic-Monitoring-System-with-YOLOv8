# 🛠️ Tools Directory - R&D and Utility Scripts

Independent, standalone scripts for dataset management, model training, evaluation, and optimization.

## 📋 Available Tools

### 1. **data_cleaner.py** - Dataset Cleaning & Validation
Automatically clean and validate YOLO dataset

#### Features:
- Remove corrupted/unreadable images
- Remove orphaned files (images without labels, labels without images)
- Normalize bounding box coordinates to YOLO format
- Validate class IDs and bounding box ranges
- Generate dataset statistics

#### Usage:
```bash
# Basic usage (default 4 classes)
python data_cleaner.py /path/to/dataset

# Specify number of classes
python data_cleaner.py ../Data --classes 5

# Expected dataset structure:
# dataset/
#   ├── train/
#   │   ├── images/
#   │   └── labels/
#   ├── val/
#   │   ├── images/
#   │   └── labels/
#   └── test/
#       ├── images/
#       └── labels/
```

#### Output:
```
📊 CLEANING SUMMARY
✓ Corrupted images removed:    15
✓ Orphaned files removed:      8
✓ Invalid bboxes cleaned:      42
✓ Bboxes converted:           156

Final Statistics:
  Total images:              2500
  Total label files:         2500
  Match ratio:               100.0%
```

---

### 2. **roi_drawer.py** - Interactive ROI Drawing Tool
Manually draw lane boundaries on video frames using mouse clicks

#### Features:
- Interactive polygon drawing on video
- Visual feedback with polygon preview
- Save multiple ROI lanes
- Generate Python code for config.py
- Support for saving to file

#### Usage:
```bash
# Draw on video and print code to console
python roi_drawer.py ../video.mp4

# Draw on video and save to file
python roi_drawer.py ../video.mp4 --output roi_config.py
```

#### Controls:
| Key | Action |
|-----|--------|
| LEFT CLICK | Add polygon point |
| RIGHT CLICK | Remove last point |
| 'N' | Save current lane polygon |
| 'C' | Clear current polygon |
| SPACE | Delete last saved lane |
| 'Q' | Finish and generate code |
| ESC | Cancel without saving |

#### Output Example:
```python
# ROI Polygons (Lane Boundaries)
LANE_POLYGONS = {
    "Lane_1": np.array([[489, 400], [721, 395], [518, 1079], [0, 1053]], dtype=np.int32),
    "Lane_2": np.array([[723, 396], [913, 390], [1021, 1077], [528, 1076]], dtype=np.int32),
}
```

---

### 3. **train_yolo.py** - YOLOv8 Model Training
Train YOLOv8 model with automatic hardware optimization

#### Features:
- Automatic batch size calculation based on GPU VRAM
- Multi-GPU support (scales automatically)
- Early stopping with configurable patience
- Comprehensive logging and visualization
- Automatic best model checkpoint saving

#### Usage:
```bash
# Default training (YOLOv8-s, 100 epochs)
python train_yolo.py

# Custom model size and epochs
python train_yolo.py --model l --epochs 200

# Custom dataset
python train_yolo.py --data ../Data/custom_dataset.yaml

# CPU training (slow!)
python train_yolo.py --device cpu

# Skip evaluation
python train_yolo.py --no-eval
```

#### Model Sizes:
| Size | Speed | Accuracy | VRAM |
|------|-------|----------|------|
| nano (n) | Fastest | Low | < 2GB |
| small (s) | Fast | Medium | 2-4GB |
| medium (m) | Medium | Good | 4-6GB |
| large (l) | Slow | High | 6-10GB |
| xlarge (x) | Slowest | Highest | > 10GB |

#### Output:
```
Training Configuration:
  Model: YOLOv8-s
  Epochs: 100
  Batch size: 16
  Image size: 640x640
  Device: 0

[GPU Info: RTX 3060 with 12.0GB VRAM]
```

---

### 4. **model_exporter.py** - Model Optimization & Export
Export PyTorch model to optimized formats for production

#### Features:
- Export to ONNX (cross-platform, 1.5-2x speedup)
- Export to TensorRT (NVIDIA, 3-4x speedup)
- Export to OpenVINO (Intel, 1.5-2.5x speedup)
- FP16 precision support (lower VRAM)
- Graph simplification

#### Usage:
```bash
# Export to ONNX (default, most compatible)
python model_exporter.py

# Export to TensorRT (NVIDIA GPU only)
python model_exporter.py --format tensorrt

# Export to OpenVINO (Intel optimization)
python model_exporter.py --format openvino

# Export all formats
python model_exporter.py --all

# Custom model path
python model_exporter.py --model /path/to/model.pt --format onnx
```

#### Performance Comparison:
```
Format     | Speed  | Accuracy | VRAM | Compatibility
-----------|--------|----------|------|----------------
PyTorch    | 1.0x   | 100%     | HIGH | Universal
ONNX       | 1.5-2x | 100%     | MED  | Good
TensorRT   | 3-4x   | 100%     | LOW  | NVIDIA only
OpenVINO   | 1.5-2x | ~100%    | MED  | Intel focused
```

#### Requirements:
- **ONNX**: `pip install onnx onnxruntime`
- **TensorRT**: Separate installation (requires NVIDIA CUDA toolkit)
- **OpenVINO**: `pip install openvino`

---

### 5. **model_evaluator.py** - Model Evaluation & Comparison
Evaluate and compare baseline vs optimized models

#### Features:
- Comprehensive metrics (mAP, precision, recall, F1, FPS)
- Baseline vs optimized model comparison
- FPS benchmarking
- Automatic chart generation
- JSON results export

#### Usage:
```bash
# Compare baseline vs ONNX model
python model_evaluator.py

# Custom dataset
python model_evaluator.py --data ../Data/custom.yaml

# Evaluate single model
python model_evaluator.py --baseline model.pt

# Custom output directory
python model_evaluator.py --output-dir my_results

# CPU evaluation
python model_evaluator.py --device cpu
```

#### Output:
```
📊 MODEL COMPARISON RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model              mAP50   mAP50-95  Precision  Recall    F1      FPS
──────────────────────────────────────────────────────────────────────
Baseline-PT        0.9234  0.8765    0.9512    0.9045   0.9275   18.3
Optimized-ONNX     0.9234  0.8765    0.9512    0.9045   0.9275   32.5
Optimized-TENSORRT 0.9233  0.8764    0.9511    0.9044   0.9274   58.2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🚀 Quick Start Workflow

### 1. **Prepare Dataset**
```bash
# Clean and validate dataset
python data_cleaner.py ../Data

# Set up ROI polygons for lanes
python roi_drawer.py ../video.mp4
```

### 2. **Train Model**
```bash
# Train YOLOv8 model
python train_yolo.py --model s --epochs 100
```

### 3. **Export & Optimize**
```bash
# Export to ONNX for deployment
python model_exporter.py --format onnx

# Or export to TensorRT for maximum speed
python model_exporter.py --format tensorrt
```

### 4. **Evaluate Performance**
```bash
# Compare baseline vs optimized models
python model_evaluator.py

# View results in console and JSON file
```

---

## 📊 Performance Optimization Tips

### For Dataset Cleaning
- Run `data_cleaner.py` before training to ensure quality data
- Check output statistics to verify data integrity
- Fix any images with low confidence detections

### For Model Training
- Use `data_cleaner.py` first to avoid training on corrupted data
- Start with small model (yolov8n) for quick experiments
- Use `model_evaluator.py` to find optimal confidence threshold

### For Deployment
1. Train baseline model with `train_yolo.py`
2. Evaluate on test set with `model_evaluator.py`
3. Export to ONNX or TensorRT with `model_exporter.py`
4. Compare performance and choose suitable format

---

## ⚙️ Environment Setup

```bash
# Install all dependencies
pip install -r ../requirements.txt

# Additional for model export (optional)
pip install onnx onnxruntime openvino

# For TensorRT (NVIDIA only, complex setup)
# Follow: https://docs.nvidia.com/deeplearning/tensorrt/
```

---

## 📝 Notes

- All scripts are **standalone** and can be run independently
- Each script has detailed help: `python script.py --help`
- Output is saved to `../output/` or `../runs/` by default
- Supporting Vietnamese filenames on Windows (automatic)
- CUDA GPU recommended for training and optimization

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Model not found" | Check model path with `--model` argument |
| "Dataset config not found" | Ensure `data.yaml` exists in dataset folder |
| "CUDA out of memory" | Reduce batch size with `--batch` or use CPU |
| "Video cannot be opened" | Check video file path and format support |
| "No polygons saved" | Press 'N' to save each lane in roi_drawer.py |

---

## 📞 Support

For issues with specific tools:
- **data_cleaner.py**: Check dataset folder structure
- **roi_drawer.py**: Ensure video file is readable
- **train_yolo.py**: Check GPU memory with `nvidia-smi`
- **model_exporter.py**: Verify model format is correct
- **model_evaluator.py**: Confirm test split exists in dataset
