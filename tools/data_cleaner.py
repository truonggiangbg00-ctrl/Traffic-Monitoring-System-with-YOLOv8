"""
data_cleaner.py: Siêu công cụ dọn dẹp và chuẩn hóa nhãn YOLO (All-in-One)
Phiên bản Tối ưu hóa: Nhanh, An toàn và Chống mất dữ liệu.
"""

import os
import glob
import cv2
import numpy as np
from pathlib import Path
import argparse
import sys

def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Ép giá trị nằm gọn trong khoảng cho phép (dùng để gọt Bounding Box tràn viền)"""
    return max(min_val, min(value, max_val))

class UltimateDatasetCleaner:
    def __init__(self, dataset_path: str, num_classes: int = 4):
        self.dataset_path = Path(dataset_path)
        self.splits = ['train', 'valid', 'test']
        self.num_classes = num_classes
        
        self.stats = {
            'orphaned_files': 0,
            'corrupted_images': 0,
            'boxes_fixed': 0,
            'duplicates_removed': 0,
            'empty_labels_removed': 0
        }
        
        print("\n" + "=".center(80, "="))
        print("🚀 ULTIMATE DATASET CLEANER (YOLO FORMAT)".center(80))
        print(f"📂 Dataset: {self.dataset_path}".center(80))
        print("=".center(80, "=") + "\n")

    def run_all(self):
        """Chạy tuần tự toàn bộ 4 bước dọn dẹp"""
        if not self.dataset_path.exists():
            print(f"❌ Không tìm thấy thư mục: {self.dataset_path}")
            return
            
        self.step1_remove_orphans()
        self.step2_check_corrupted_images()
        self.step3_clean_and_clamp_labels()
        self.step4_remove_empty_labels()
        self.print_summary()

    def step1_remove_orphans(self):
        """BƯỚC 1: Xóa các file mồ côi (Ảnh không có nhãn, hoặc Nhãn không có ảnh)"""
        print("[BƯỚC 1/4] Đang quét và xóa các file mồ côi (Orphaned files)...")
        
        for split in self.splits:
            img_dir = self.dataset_path / split / 'images'
            label_dir = self.dataset_path / split / 'labels'
            
            if not (img_dir.exists() and label_dir.exists()):
                continue
                
            # Lấy tên file (không kèm đuôi)
            img_stems = {Path(f).stem for f in glob.glob(str(img_dir / '*.*'))}
            label_stems = {Path(f).stem for f in glob.glob(str(label_dir / '*.txt'))}
            
            # Ảnh không có nhãn -> Xóa ảnh
            for orphan_img in (img_stems - label_stems):
                for f in glob.glob(str(img_dir / f"{orphan_img}.*")):
                    os.remove(f)
                    self.stats['orphaned_files'] += 1
                    
            # Nhãn không có ảnh -> Xóa nhãn
            for orphan_label in (label_stems - img_stems):
                f = label_dir / f"{orphan_label}.txt"
                if f.exists():
                    os.remove(str(f))
                    self.stats['orphaned_files'] += 1
                    
        print(f"  ✓ Đã dọn dẹp {self.stats['orphaned_files']} file mồ côi.\n")

    def step2_check_corrupted_images(self):
        """BƯỚC 2: Quét ảnh lỗi (Corrupted). Chỉ kiểm tra Header để chạy siêu nhanh."""
        print("[BƯỚC 2/4] Đang kiểm tra tính toàn vẹn của file ảnh...")
        
        for split in self.splits:
            img_dir = self.dataset_path / split / 'images'
            if not img_dir.exists(): continue
            
            images = list(glob.glob(str(img_dir / '*.*')))
            if not images: continue
            
            print(f"  -> Đang quét {len(images)} ảnh trong '{split}'...")
            for img_path in images:
                try:
                    # Kiểm tra xem file có thực sự là ảnh không bằng cách đọc 100 byte đầu
                    with open(img_path, 'rb') as f:
                        header = f.read(100)
                    if not header:
                        raise ValueError("File rỗng")
                except Exception:
                    # Nếu lỗi, xóa cả ảnh và nhãn
                    os.remove(img_path)
                    label_path = self.dataset_path / split / 'labels' / f"{Path(img_path).stem}.txt"
                    if label_path.exists():
                        os.remove(str(label_path))
                    self.stats['corrupted_images'] += 1
                    
        print(f"  ✓ Đã phát hiện và xóa {self.stats['corrupted_images']} ảnh lỗi.\n")

    def step3_clean_and_clamp_labels(self):
        """BƯỚC 3: Gọt Bounding Box tràn viền, chuẩn hóa tọa độ và xóa dòng trùng."""
        print("[BƯỚC 3/4] Đang chuẩn hóa tọa độ và gọt Bounding Box (Clamp)...")
        
        for split in self.splits:
            label_dir = self.dataset_path / split / 'labels'
            img_dir = self.dataset_path / split / 'images'
            if not label_dir.exists(): continue
            
            label_files = list(glob.glob(str(label_dir / '*.txt')))
            if not label_files: continue
            
            print(f"  -> Đang xử lý {len(label_files)} file nhãn trong '{split}'...")
            
            for file_path in label_files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 1. Xóa dòng trùng lặp (Duplicate)
                unique_lines = list(set(lines))
                if len(unique_lines) < len(lines):
                    self.stats['duplicates_removed'] += (len(lines) - len(unique_lines))
                
                new_lines = []
                needs_rewrite = False
                
                for line in unique_lines:
                    parts = line.strip().split()
                    if len(parts) != 5: continue
                        
                    try:
                        cls_id = int(parts[0])
                        v1, v2, v3, v4 = map(float, parts[1:5])
                        
                        # Failsafe: Ép Class ID về khoảng an toàn [0, num_classes-1]
                        if cls_id >= self.num_classes or cls_id < 0:
                            cls_id = max(0, min(self.num_classes - 1, cls_id))
                            needs_rewrite = True
                        
                        # Phát hiện Pixel Format (Tọa độ > 2.0)
                        if any(v > 2.0 for v in [v1, v2, v3, v4]):
                            # Nếu là Pixel Format, BẮT BUỘC phải mở ảnh để tính tỷ lệ
                            img_path = glob.glob(str(img_dir / f"{Path(file_path).stem}.*"))
                            if img_path:
                                img = cv2.imdecode(np.fromfile(img_path[0], np.uint8), cv2.IMREAD_COLOR)
                                if img is not None:
                                    h, w = img.shape[:2]
                                    v1, v2 = v1 / w, v2 / h
                                    v3, v4 = v3 / w, v4 / h
                                    needs_rewrite = True
                                else: continue
                            else: continue

                        # Logic Gọt (Clamp) Bounding Box YOLO (v1=xc, v2=yc, v3=w, v4=h)
                        x_min = v1 - (v3 / 2)
                        y_min = v2 - (v4 / 2)
                        x_max = v1 + (v3 / 2)
                        y_max = v2 + (v4 / 2)
                        
                        # Kiểm tra xem có bị tràn viền không
                        if x_min < 0 or y_min < 0 or x_max > 1 or y_max > 1:
                            needs_rewrite = True
                            self.stats['boxes_fixed'] += 1
                            
                            x_min = clamp(x_min)
                            y_min = clamp(y_min)
                            x_max = clamp(x_max)
                            y_max = clamp(y_max)
                        
                        # Nếu Box sau khi gọt quá nhỏ (gần như biến mất) -> Bỏ qua dòng này
                        if (x_max - x_min) <= 0.001 or (y_max - y_min) <= 0.001:
                            needs_rewrite = True
                            continue 
                            
                        # Chuyển về chuẩn YOLO
                        new_xc = (x_min + x_max) / 2
                        new_yc = (y_min + y_max) / 2
                        new_w = x_max - x_min
                        new_h = y_max - y_min
                        
                        new_lines.append(f"{cls_id} {new_xc:.6f} {new_yc:.6f} {new_w:.6f} {new_h:.6f}\n")
                        
                    except ValueError:
                        needs_rewrite = True
                        continue
                
                if needs_rewrite or len(unique_lines) < len(lines):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                        
        print(f"  ✓ Đã gọt {self.stats['boxes_fixed']} Boxes và xóa {self.stats['duplicates_removed']} dòng trùng.\n")

    def step4_remove_empty_labels(self):
        """BƯỚC 4: Xóa các file nhãn rỗng (File 0 KB) để tránh lỗi Background của YOLO"""
        print("[BƯỚC 4/4] Đang quét và xóa các file nhãn rỗng...")
        
        for split in self.splits:
            label_dir = self.dataset_path / split / 'labels'
            if not label_dir.exists(): continue
            
            for file_path in glob.glob(str(label_dir / '*.txt')):
                if os.path.getsize(file_path) == 0:
                    os.remove(file_path)
                    
                    # Xóa luôn ảnh tương ứng để không bị thành mồ côi
                    img_path = glob.glob(str(self.dataset_path / split / 'images' / f"{Path(file_path).stem}.*"))
                    if img_path:
                        os.remove(img_path[0])
                        
                    self.stats['empty_labels_removed'] += 1
                    
        print(f"  ✓ Đã xóa {self.stats['empty_labels_removed']} file rỗng (Backgrounds).\n")

    def print_summary(self):
        print("=".center(80, "="))
        print("🎉 HOÀN TẤT DỌN DẸP! (SẴN SÀNG TRAIN)".center(80))
        print("=".center(80, "="))
        print(f" 🗑️  File mồ côi đã xóa:          {self.stats['orphaned_files']}")
        print(f" 🖼️  Ảnh lỗi đã xóa:              {self.stats['corrupted_images']}")
        print(f" ✂️  Bounding Box tràn viền:      {self.stats['boxes_fixed']} (Đã gọt)")
        print(f" 📋 Dòng dữ liệu trùng lặp:      {self.stats['duplicates_removed']} (Đã xóa)")
        print(f" 🈳 File nhãn rỗng (Background): {self.stats['empty_labels_removed']} (Đã xóa)")
        print("=".center(80, "=") + "\n")

if __name__ == '__main__':
    # Tự động lấy cấu hình đường dẫn từ utils/config.py
    try:
        PROJECT_ROOT = Path(__file__).resolve().parent.parent
        sys.path.append(str(PROJECT_ROOT))
        from utils.config import DATASET_DIR
        default_dataset = str(DATASET_DIR)
    except:
        # Failsafe nếu không import được config
        default_dataset = str(Path(__file__).resolve().parent.parent / 'Data_3')
        
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default=default_dataset, help='Đường dẫn tới thư mục Dataset')
    parser.add_argument('--classes', type=int, default=4, help='Số lượng Classes')
    args = parser.parse_args()
    
    cleaner = UltimateDatasetCleaner(args.dataset, args.classes)
    cleaner.run_all()