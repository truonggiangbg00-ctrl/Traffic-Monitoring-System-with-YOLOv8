"""
train_yolo.py: Huấn luyện phân tách Baseline (Raw) và Optimized (Advanced Tuning)
"""

import sys
import argparse
import shutil
import torch
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    sys.exit("❌ ultralytics not installed. Install with: pip install ultralytics")

# Import các đường dẫn từ trạm điều khiển trung tâm
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from utils.config import DATA_YAML_PATH, WEIGHTS_DIR, DEVICE


class YOLOTrainer:
    def __init__(self, model_size: str = 's'):
        self.data_yaml = Path(DATA_YAML_PATH)
        self.weights_dir = Path(WEIGHTS_DIR)
        self.model_size = model_size.replace('yolov8', '')
        
        self.weights_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.data_yaml.exists():
            sys.exit(f"❌ Lỗi: Không tìm thấy file {self.data_yaml}.")

    def train_baseline(self, epochs: int, imgsz: int):
        """
        [MÔ HÌNH RAW]: Để mặc định 100% mọi tham số của Ultralytics.
        Mục đích: Đo lường sức mạnh gốc của tập dữ liệu.
        """
        print("\n" + "="*70)
        print("🚀 ĐANG HUẤN LUYỆN BASELINE MODEL (RAW & DEFAULT)")
        print("="*70)
        
        model = YOLO(f'yolov8{self.model_size}.pt')
        run_name = 'traffic_baseline'
        
        # Chỉ truyền đúng 3 tham số sống còn: data, epochs, imgsz
        # Mọi tham số về augmentation, learning rate, optimizer đều bị khóa ở mức mặc định
        model.train(
            data=str(self.data_yaml),
            epochs=epochs,
            imgsz=imgsz,
            device=DEVICE,
            project=str(self.weights_dir),
            name=run_name,
            exist_ok=True
        )
        
        best_model_path = self.weights_dir / run_name / 'weights' / 'best.pt'
        target_path = self.weights_dir / "yolo_basic.pt"
        
        if best_model_path.exists():
            shutil.copy(best_model_path, target_path)
            print(f"\n✅ Đã lưu mô hình Baseline nguyên bản tại: {target_path}")

    def train_optimized(self, epochs: int, imgsz: int, skip_train: bool = False):
        """
        [MÔ HÌNH TỐI ƯU HÓA]: Can thiệp sâu vào Hyperparameters.
        Nếu skip_train=True, sẽ bỏ qua huấn luyện và lấy file .pt có sẵn để biên dịch.
        """
        run_name = 'traffic_optimized'
        optimized_pt_path = self.weights_dir / "yolo_optimized.pt"
        
        if not skip_train:
            print("\n" + "="*70)
            print("⚡ ĐANG HUẤN LUYỆN OPTIMIZED MODEL (ADVANCED TUNING)")
            print("="*70)
            
            model = YOLO(f'yolov8{self.model_size}.pt')
            
            # Huấn luyện hạng nặng
            model.train(
                data=str(self.data_yaml),
                epochs=epochs,
                imgsz=imgsz,
                device=DEVICE,
                project=str(self.weights_dir),
                name=run_name,
                exist_ok=True,
                optimizer='AdamW',
                lr0=0.001, lrf=0.01, warmup_epochs=3.0,
                mosaic=1.0, mixup=0.1, copy_paste=0.1, degrees=10.0,
                hsv_s=0.7, hsv_v=0.4,
                close_mosaic=10, patience=25
            )
            
            # Lưu file PyTorch đã tối ưu
            best_model_path = self.weights_dir / run_name / 'weights' / 'best.pt'
            if best_model_path.exists():
                shutil.copy(best_model_path, optimized_pt_path)
                print(f"\n✅ Đã lưu mô hình Optimized (.pt) tại: {optimized_pt_path}")
        else:
            print("\n⏭️ Đã chọn Bỏ qua huấn luyện. Sử dụng file .pt có sẵn...")
            
        # --- BƯỚC BIÊN DỊCH TENSORRT ---
        if not optimized_pt_path.exists():
            sys.exit(f"❌ Không tìm thấy file {optimized_pt_path}. Bạn phải train ít nhất 1 lần trước khi skip.")
            
        print("\n⚙️ Đang biên dịch mô hình sang TensorRT FP16 để tăng tốc độ FPS...")
        model_export = YOLO(str(optimized_pt_path))
        model_export.export(
            format='engine', 
            dynamic=False,   
            half=True,
            workspace=4,     
            imgsz=imgsz,
            device=DEVICE
        )
        
        exported_engine = self.weights_dir / 'yolo_optimized.engine'
        if exported_engine.exists():
            print(f"✅ Đã lưu mô hình TensorRT siêu tốc tại: {exported_engine}")
        else:
            print("⚠️ Train/Export xong nhưng bước xuất file TensorRT gặp sự cố. Vui lòng kiểm tra lại log.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Công cụ huấn luyện YOLOv8 - Baseline vs Optimized")
    parser.add_argument('--mode', choices=['baseline', 'optimized', 'all'], required=True, 
                        help="Chọn luồng huấn luyện")
    parser.add_argument('--model', choices=['n', 's', 'm', 'l', 'x'], default='s')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--imgsz', type=int, default=640)
    
    # [ĐÃ THÊM] Cờ skip-train để bỏ qua huấn luyện
    parser.add_argument('--skip-train', action='store_true', help="Bỏ qua huấn luyện, chỉ chạy tối ưu hóa TensorRT")
    
    args = parser.parse_args()
    trainer = YOLOTrainer(model_size=args.model)
    
    try:
        if args.mode in ['baseline', 'all'] and not args.skip_train:
            trainer.train_baseline(epochs=args.epochs, imgsz=args.imgsz)
            
        if args.mode in ['optimized', 'all']:
            optimized_epochs = args.epochs if args.mode == 'optimized' else int(args.epochs * 1.5)
            # Truyền cờ skip_train vào hàm
            trainer.train_optimized(epochs=optimized_epochs, imgsz=args.imgsz, skip_train=args.skip_train)
            
    except Exception as e:
        print(f"\n❌ Đã xảy ra lỗi: {e}")
        sys.exit(1)