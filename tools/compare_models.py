"""
compare_models.py: Công cụ Trích xuất và Phân tích Hiệu năng Mô hình Toàn diện
Tự động vẽ Learning Curves, gom Confusion Matrix và so sánh Baseline vs Optimized.
"""
import sys
import shutil
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

class ModelComparator:
    def __init__(self, run_dir_1: str, run_dir_2: str, label_1="Baseline", label_2="Optimized"):
        self.dir_1 = Path(run_dir_1)
        self.dir_2 = Path(run_dir_2)
        
        # Đường dẫn trỏ thẳng vào file results.csv của từng thư mục
        self.csv_1 = self.dir_1 / "results.csv"
        self.csv_2 = self.dir_2 / "results.csv"
        
        self.label_1 = label_1
        self.label_2 = label_2
        
        # Tạo thư mục gom toàn bộ báo cáo
        self.out_dir = PROJECT_ROOT / "evaluation" / "comparison"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def plot_learning_curves(self, csv_path, label):
        """Vẽ đường cong học tập (Loss và mAP) cho từng mô hình riêng biệt"""
        if not csv_path.exists():
            print(f"⚠️ Bỏ qua {label}: Không tìm thấy file {csv_path}")
            return

        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip() 
        
        epochs = df['epoch']
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
        
        # 1. Biểu đồ Loss
        ax1.plot(epochs, df['train/box_loss'], label='Train Box Loss', color='#1f77b4', linestyle='-')
        ax1.plot(epochs, df['val/box_loss'], label='Val Box Loss', color='#ff7f0e', linestyle='--')
        ax1.set_title(f'[{label}] - Đồ thị Hội tụ Hàm Mất mát (Loss)', fontweight='bold')
        ax1.set_xlabel('Epochs')
        ax1.set_ylabel('Loss Value')
        ax1.grid(True, linestyle=':', alpha=0.6)
        ax1.legend()

        # 2. Biểu đồ Metrics
        ax2.plot(epochs, df['metrics/mAP50(B)'], label='mAP@0.5', color='#2ca02c', linewidth=2)
        ax2.plot(epochs, df['metrics/mAP50-95(B)'], label='mAP@0.5:0.95', color='#d62728', linewidth=2)
        ax2.set_title(f'[{label}] - Đồ thị Tăng trưởng Độ chính xác (mAP)', fontweight='bold')
        ax2.set_xlabel('Epochs')
        ax2.set_ylabel('Score (0-1)')
        ax2.set_ylim(0, 1.05)
        ax2.grid(True, linestyle=':', alpha=0.6)
        ax2.legend()

        fig.tight_layout()
        save_path = self.out_dir / f"{label.lower()}_learning_curves.png"
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"📈 Đã vẽ xong Learning Curve cho {label}.")

    def gather_yolo_artifacts(self, run_dir, label):
        """Thu hoạch tự động Ma trận nhầm lẫn từ thư mục Train của YOLO"""
        cm_path = run_dir / "confusion_matrix.png"
        cm_norm_path = run_dir / "confusion_matrix_normalized.png"
        
        target_cm = self.out_dir / f"{label.lower()}_confusion_matrix.png"
        
        source_path = cm_norm_path if cm_norm_path.exists() else cm_path
        
        if source_path.exists():
            shutil.copy(source_path, target_cm)
            print(f"🧩 Đã sao chép Confusion Matrix của {label}.")
        else:
            print(f"⚠️ Không tìm thấy Confusion Matrix trong thư mục {run_dir}")

    def extract_best_metrics(self, csv_path):
        """Trích xuất điểm số tại epoch có mAP tổng thể tốt nhất"""
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        best_row = df.loc[df['metrics/mAP50-95(B)'].idxmax()]
        return {
            'Precision': best_row['metrics/precision(B)'],
            'Recall': best_row['metrics/recall(B)'],
            'mAP@50': best_row['metrics/mAP50(B)'],
            'mAP@50-95': best_row['metrics/mAP50-95(B)']
        }

    def compare_bar_chart(self):
        """Vẽ biểu đồ cột ghép so sánh trực diện"""
        if not (self.csv_1.exists() and self.csv_2.exists()):
            return

        metrics_1 = self.extract_best_metrics(self.csv_1)
        metrics_2 = self.extract_best_metrics(self.csv_2)

        categories = list(metrics_1.keys())
        values_1 = list(metrics_1.values())
        values_2 = list(metrics_2.values())

        x = np.arange(len(categories))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))
        rects1 = ax.bar(x - width/2, values_1, width, label=self.label_1, color='lightgray')
        rects2 = ax.bar(x + width/2, values_2, width, label=self.label_2, color='royalblue')

        ax.set_ylabel('Điểm số (0.0 - 1.0)', fontsize=11)
        ax.set_title('SO SÁNH TỔNG THỂ HIỆU SUẤT HAI MÔ HÌNH', fontweight='bold', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_ylim(0, 1.15)
        ax.legend()

        ax.bar_label(rects1, padding=3, fmt='%.3f')
        ax.bar_label(rects2, padding=3, fmt='%.3f')

        fig.tight_layout()
        save_path = self.out_dir / "models_comparison_barchart.png"
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"📊 Đã xuất biểu đồ so sánh cột tại: {save_path}")

    def execute_pipeline(self):
        print("="*60)
        print("🚀 BẮT ĐẦU TRÍCH XUẤT VÀ PHÂN TÍCH DỮ LIỆU MÔ HÌNH")
        print("="*60)
        
        self.plot_learning_curves(self.csv_1, self.label_1)
        self.plot_learning_curves(self.csv_2, self.label_2)
        
        self.gather_yolo_artifacts(self.dir_1, self.label_1)
        self.gather_yolo_artifacts(self.dir_2, self.label_2)
        
        self.compare_bar_chart()
        
        print("="*60)
        print(f"🎉 Hoàn tất! Toàn bộ biểu đồ đã được gom gọn gàng trong thư mục:\n📁 {self.out_dir}")

if __name__ == "__main__":
    # ĐÃ SỬA ĐƯỜNG DẪN KHỚP VỚI ẢNH CỦA BẠN:
    # Trỏ vào đúng thư mục "traffic_baseline" và "traffic_optimized" nằm trong "weights"
    baseline_dir = PROJECT_ROOT / "weights" / "traffic_baseline"
    optimized_dir = PROJECT_ROOT / "weights" / "traffic_optimized"
    
    comparator = ModelComparator(str(baseline_dir), str(optimized_dir))
    comparator.execute_pipeline()