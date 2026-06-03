"""
model_exporter.py: Optimize PyTorch baseline model to TensorRT (.engine) format
"""
import sys
from pathlib import Path
try:
    from ultralytics import YOLO
except ImportError:
    sys.exit("❌ ultralytics not installed.")

def export_optimized_model():
    project_root = Path(__file__).resolve().parent.parent
    baseline_path = project_root / 'weights' / 'yolo_basic.pt'
    
    if not baseline_path.exists():
        sys.exit(f"❌ Baseline model not found at {baseline_path}. Run train_yolo.py first.")
        
    print(f"🔄 Loading baseline model from {baseline_path}...")
    model = YOLO(str(baseline_path))
    
    print("⚡ Exporting to TensorRT Engine format (this may take 5-10 minutes)...")
    # Biến đổi mô hình sang FP16 (nửa độ chính xác) để tăng tối đa FPS
    model.export(
        format='engine', 
        dynamic=False,   # Cố định kích thước đầu vào để suy luận nhanh nhất
        half=True,       # Bật FP16 optimization
        workspace=4,     # Cấp phát 4GB VRAM để biên dịch
        imgsz=640
    )
    
    # YOLO sẽ sinh ra file .engine ở cùng thư mục. Ta đổi tên lại cho đúng chuẩn config.
    exported_engine = project_root / 'weights' / 'yolo_basic.engine'
    target_engine = project_root / 'weights' / 'yolo_optimized.engine'
    
    if exported_engine.exists():
        exported_engine.rename(target_engine)
        print(f"✅ Optimized model successfully saved to: {target_engine}")
    else:
        print("❌ Export process failed to generate .engine file.")

if __name__ == '__main__':
    export_optimized_model()