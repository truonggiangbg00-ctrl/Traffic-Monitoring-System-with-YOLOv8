"""
compare_models.py: So sánh trực diện hiệu năng giữa 2 mô hình (Baseline vs Optimized)
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

class ModelComparator:
    def __init__(self, run_dir_1: str, run_dir_2: str, label_1="Baseline", label_2="Optimized"):
        self.csv_1 = Path(run_dir_1) / "results.csv"
        self.csv_2 = Path(run_dir_2) / "results.csv"
        self.label_1 = label_1
        self.label_2 = label_2
        self.out_dir = PROJECT_ROOT / "evaluation" / "comparison"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def extract_best_metrics(self, csv_path):
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        # Lấy epoch có mAP50-95 cao nhất
        best_row = df.loc[df['metrics/mAP50-95(B)'].idxmax()]
        return {
            'Precision': best_row['metrics/precision(B)'],
            'Recall': best_row['metrics/recall(B)'],
            'mAP@50': best_row['metrics/mAP50(B)'],
            'mAP@50-95': best_row['metrics/mAP50-95(B)']
        }

    def compare(self):
        if not (self.csv_1.exists() and self.csv_2.exists()):
            print("❌ Phải có đủ 2 file results.csv để so sánh!")
            return

        print(f"⚖️ Đang so sánh {self.label_1} vs {self.label_2}...")
        metrics_1 = self.extract_best_metrics(self.csv_1)
        metrics_2 = self.extract_best_metrics(self.csv_2)

        # Trích xuất tên chỉ số và giá trị
        categories = list(metrics_1.keys())
        values_1 = list(metrics_1.values())
        values_2 = list(metrics_2.values())

        # Thiết lập biểu đồ cột ghép (Grouped Bar Chart)
        x = np.arange(len(categories))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))
        rects1 = ax.bar(x - width/2, values_1, width, label=self.label_1, color='lightgray')
        rects2 = ax.bar(x + width/2, values_2, width, label=self.label_2, color='royalblue')

        ax.set_ylabel('Điểm số (0.0 - 1.0)')
        ax.set_title('So sánh các chỉ số hiệu suất Mô hình')
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1.1)
        ax.legend()

        # Thêm text giá trị trên đầu cột
        ax.bar_label(rects1, padding=3, fmt='%.3f')
        ax.bar_label(rects2, padding=3, fmt='%.3f')

        fig.tight_layout()
        save_path = self.out_dir / "models_comparison.png"
        plt.savefig(save_path, dpi=300)
        plt.close()
        
        print(f"✅ Đã lưu biểu đồ so sánh tại: {save_path}")

if __name__ == "__main__":
    baseline_dir = PROJECT_ROOT / "weights" / "traffic_baseline"
    optimized_dir = PROJECT_ROOT / "weights" / "traffic_optimized"
    
    comparator = ModelComparator(str(baseline_dir), str(optimized_dir))
    comparator.compare()