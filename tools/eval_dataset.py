"""
eval_dataset.py: Công cụ phân tích và vẽ biểu đồ thống kê bộ dữ liệu YOLO
Hỗ trợ cả định dạng Object Detection (BBox) và Instance Segmentation (Polygon)
"""
import sys
import glob
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

class DatasetEvaluator:
    def __init__(self, yaml_path: str):
        self.yaml_path = Path(yaml_path)
        self.dataset_dir = self.yaml_path.parent
        self.out_dir = PROJECT_ROOT / "evaluation" / "dataset"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.names = data.get('names', {})
            if isinstance(self.names, list):
                self.names = {i: name for i, name in enumerate(self.names)}

    def analyze(self):
        print(f"🔍 Đang tìm kiếm nhãn trong thư mục: {self.dataset_dir}")
        labels_files = list(self.dataset_dir.rglob("labels/*.txt"))
        
        if not labels_files:
            print("❌ Lỗi: Không tìm thấy bất kỳ file .txt nào!")
            return
            
        print(f"✅ Đã tìm thấy {len(labels_files)} file nhãn. Đang tiến hành trích xuất...")
        
        data_rows = []
        detection_count = 0
        segmentation_count = 0
        
        for file in labels_files:
            if file.stat().st_size == 0:
                continue
                
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 5: 
                        continue
                        
                    try:
                        cls_id = int(parts[0])
                        class_name = self.names.get(cls_id, f"Class {cls_id}")
                        
                        # TRƯỜNG HỢP 1: Chuẩn Object Detection (Đúng 5 cột)
                        if len(parts) == 5:
                            w = float(parts[3])
                            h = float(parts[4])
                            detection_count += 1
                        
                        # TRƯỜNG HỢP 2: Chuẩn Instance Segmentation / Đa giác (> 5 cột)
                        else:
                            coords = list(map(float, parts[1:]))
                            xs = coords[0::2] # Lấy các vị trí lẻ (x)
                            ys = coords[1::2] # Lấy các vị trí chẵn (y)
                            if xs and ys:
                                w = max(xs) - min(xs) # Tính toán Width tương đối
                                h = max(ys) - min(ys) # Tính toán Height tương đối
                                segmentation_count += 1
                            else:
                                continue
                                
                        data_rows.append({
                            'Class': class_name,
                            'Width': w,
                            'Height': h
                        })
                    except ValueError:
                        pass
        
        df = pd.DataFrame(data_rows)
        if df.empty:
            print("❌ Không thể trích xuất dữ liệu. File lỗi cấu trúc hoặc sai định dạng số!")
            return

        print(f"📊 Thống kê loại nhãn: BBox thông thường: {detection_count} | Đa giác (Segmentation): {segmentation_count}")
        print("📊 Đang vẽ và xuất biểu đồ...")

        # 1. Vẽ phân bố Class (Class Distribution)
        plt.figure(figsize=(10, 6))
        sns.countplot(data=df, x='Class', order=df['Class'].value_counts().index, palette='viridis')
        plt.title("Phân bố số lượng đối tượng trong Dataset")
        plt.ylabel("Số lượng nhãn")
        plt.xlabel("Tên lớp dữ liệu (Class)")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        dist_path = self.out_dir / "class_distribution.png"
        plt.savefig(dist_path, dpi=300, bbox_inches='tight')
        plt.close()

        # 2. Vẽ kích thước Bounding Box (BBox Size Scatter)
        plt.figure(figsize=(8, 8))
        sns.scatterplot(data=df, x='Width', y='Height', hue='Class', alpha=0.4, s=12)
        plt.title("Phân bố kích thước Bounding Box (Chuẩn hóa 0-1)")
        plt.xlabel("Chiều rộng (Width)")
        plt.ylabel("Chiều cao (Height)")
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.grid(True, linestyle=':', alpha=0.6)
        bbox_path = self.out_dir / "bbox_size_distribution.png"
        plt.savefig(bbox_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"🎉 Xuất biểu đồ thành công! Kết quả được lưu tại thư mục: {self.out_dir}")

if __name__ == "__main__":
    # Tự động đồng bộ với cấu hình Data_4 của bạn
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    yaml_file = PROJECT_ROOT / "Data_4" / "data.yaml"
    
    evaluator = DatasetEvaluator(str(yaml_file))
    evaluator.analyze()