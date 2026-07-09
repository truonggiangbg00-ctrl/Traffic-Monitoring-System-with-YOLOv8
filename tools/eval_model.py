"""
eval_model.py: Phân tích đường cong học tập và các chỉ số (mAP, F1, Loss) của mô hình
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

class ModelEvaluator:
    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir)
        self.csv_path = self.run_dir / "results.csv"
        self.weights_path = self.run_dir / "weights" / "best.pt"
        self.out_dir = PROJECT_ROOT / "evaluation" / self.run_dir.name
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def plot_learning_curves(self):
        if not self.csv_path.exists():
            print(f"❌ Không tìm thấy {self.csv_path}")
            return
            
        print(f"📈 Đang vẽ biểu đồ Learning Curves cho {self.run_dir.name}...")
        df = pd.read_csv(self.csv_path)
        df.columns = df.columns.str.strip() # Dọn dẹp khoảng trắng tên cột
        
        epochs = df['epoch']
        
        # 1. Vẽ Loss Curve (Train vs Val)
        plt.figure(figsize=(10, 5))
        plt.plot(epochs, df['train/box_loss'], label='Train Box Loss', color='blue')
        plt.plot(epochs, df['val/box_loss'], label='Val Box Loss', color='orange')
        plt.title("Đường cong Box Loss qua các Epoch")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.legend()
        plt.grid(True)
        plt.savefig(self.out_dir / "learning_curve_loss.png", dpi=300)
        plt.close()

        # 2. Vẽ mAP Curve
        plt.figure(figsize=(10, 5))
        plt.plot(epochs, df['metrics/mAP50(B)'], label='mAP@0.5', color='green')
        plt.plot(epochs, df['metrics/mAP50-95(B)'], label='mAP@0.5:0.95', color='red')
        plt.title("Độ chính xác trung bình (mAP)")
        plt.xlabel("Epoch")
        plt.ylabel("Score")
        plt.legend()
        plt.grid(True)
        plt.savefig(self.out_dir / "learning_curve_map.png", dpi=300)
        plt.close()
        
        print(f"✅ Đã lưu Learning Curves tại: {self.out_dir}")

    def run_validation(self, data_yaml: str):
        """Chạy lại quá trình tính F1-Score, Precision, Recall"""
        if not self.weights_path.exists():
            print("❌ Không tìm thấy model weights!")
            return
            
        print("⚙️ Đang chạy bộ đánh giá chuyên sâu (Validation)...")
        model = YOLO(str(self.weights_path))
        # Quá trình này sẽ tự động lưu Confusion Matrix, F1 Curve vào thư mục run của Ultralytics
        metrics = model.val(data=data_yaml, split='val', project=str(self.out_dir), name='val_results')
        print(f"✅ Kết quả Validation hoàn chỉnh được lưu tại: {self.out_dir / 'val_results'}")

if __name__ == "__main__":
    # Trỏ đến thư mục chứa kết quả train của Baseline hoặc Optimized
    baseline_dir = PROJECT_ROOT / "weights" / "traffic_baseline"
    optimized_dir = PROJECT_ROOT / "weights" / "traffic_optimized"
    yaml_file = PROJECT_ROOT / "Data_4" / "data.yaml"
    
    evaluator = ModelEvaluator(str(baseline_dir))
    evaluator.plot_learning_curves()
    evaluator.run_validation(str(yaml_file))