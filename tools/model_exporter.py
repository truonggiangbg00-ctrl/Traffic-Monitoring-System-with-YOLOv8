"""
model_exporter.py: Biên dịch mô hình PyTorch (.pt) sang TensorRT (.engine)
"""
import sys
from pathlib import Path
try:
    from ultralytics import YOLO
except ImportError:
    sys.exit("Thư viện ultralytics chưa được cài đặt.")

def export_to_tensorrt(pt_path, output_name):
    """Hàm lõi để biên dịch một file .pt bất kỳ sang .engine"""
    if not pt_path.exists():
        print(f"Bỏ qua! Không tìm thấy file trọng số tại: {pt_path}")
        return

    print(f"\n🔄 Đang nạp mô hình từ: {pt_path}...")
    model = YOLO(str(pt_path))
    
    print(" Đang gọi NVIDIA TensorRT Compiler (Sẽ mất 5-10 phút, quạt tản nhiệt có thể kêu to)...")
    model.export(
        format='engine', 
        dynamic=False,   # Cố định đầu vào 640x640 để đạt max FPS
        half=True,       # Ép kiểu FP16 giảm 50% VRAM
        workspace=4,     # Cấp tối đa 4GB VRAM để biên dịch
        imgsz=640
    )
    
    # YOLO sẽ tự đẻ ra file .engine nằm ngay cạnh file .pt gốc
    exported_engine = pt_path.with_suffix('.engine')
    
    # Ta sẽ kéo file đó ra thư mục weights ngoài cùng và đổi tên cho gọn
    target_engine = pt_path.parent.parent.parent / output_name
    
    if exported_engine.exists():
        # Xóa file cũ nếu đã tồn tại để tránh xung đột
        if target_engine.exists():
            target_engine.unlink()
            
        exported_engine.rename(target_engine)
        print(f"Xuất thành công! Đã lưu tại: {target_engine}")
    else:
        print(f" Lỗi: Không thể sinh ra file .engine cho {pt_path.name}")

if __name__ == '__main__':
    project_root = Path(__file__).resolve().parent.parent
    
    print("="*80)
    print(" BẮT ĐẦU QUÁ TRÌNH BIÊN DỊCH TENSORRT (MLOps)")
    print("="*80)
    
    # 1. Biên dịch mô hình Baseline (Cơ bản)
    baseline_pt = project_root / 'weights' / 'traffic_baseline' / 'weights' / 'best.pt'
    export_to_tensorrt(baseline_pt, 'yolo_baseline.engine')
    
    # 2. Biên dịch mô hình Optimized (Đã tinh chỉnh tham số khi train)
    optimized_pt = project_root / 'weights' / 'traffic_optimized' / 'weights' / 'best.pt'
    export_to_tensorrt(optimized_pt, 'yolo_optimized.engine')
    
    print("\nHOÀN TẤT! Bạn có thể sử dụng các file .engine này trong config.py")