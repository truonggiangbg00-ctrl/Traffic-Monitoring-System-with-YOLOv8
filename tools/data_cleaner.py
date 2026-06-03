"""
data_cleaner.py: Dataset cleaning and validation tool
"""
import os
import sys
import cv2
import glob
from pathlib import Path
from typing import Tuple
import argparse
import numpy as np

class DatasetCleaner:
    def __init__(self, dataset_path: str, num_classes: int = 4):
        self.dataset_path = Path(dataset_path)
        self.splits = ['train', 'valid', 'test'] # Chuẩn hóa lại tên thư mục valid theo structure.md
        self.num_classes = num_classes
        
        self.stats = {
            'corrupted_images': 0, 'orphaned_files': 0,
            'invalid_bboxes': 0, 'converted_bboxes': 0,
            'total_images': 0, 'total_labels': 0
        }
        print(f"📂 Dataset path: {self.dataset_path} | Expected classes: {num_classes}")

    def run_all(self):
        print("="*70 + "\n🧹 DATASET CLEANER\n" + "="*70)
        try:
            self.remove_corrupted_images()
            self.remove_orphaned_files()
            self.normalize_coordinates()
            self.collect_statistics()
            self.print_summary()
            return True
        except Exception as e:
            print(f"\n❌ Error during cleaning: {e}")
            return False

    def remove_corrupted_images(self) -> int:
        print("[STEP 1/4] Removing corrupted images...", end=" ", flush=True)
        count = 0
        for split in self.splits:
            img_dir = self.dataset_path / split / 'images'
            label_dir = self.dataset_path / split / 'labels'
            if not img_dir.exists(): continue
            
            for img_path in glob.glob(str(img_dir / '*.*')):
                try:
                    img_array = np.fromfile(img_path, np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if img is None:
                        os.remove(img_path)
                        label_path = label_dir / f'{Path(img_path).stem}.txt'
                        if label_path.exists(): os.remove(str(label_path))
                        count += 1
                except:
                    continue
        self.stats['corrupted_images'] = count
        print(f"✓ Removed {count} images")
        return count

    def remove_orphaned_files(self) -> int:
        print("[STEP 2/4] Removing orphaned files...", end=" ", flush=True)
        count = 0
        for split in self.splits:
            img_dir = self.dataset_path / split / 'images'
            label_dir = self.dataset_path / split / 'labels'
            if not (img_dir.exists() and label_dir.exists()): continue
            
            img_files = {Path(f).stem for f in glob.glob(str(img_dir / '*.*'))}
            label_files = {Path(f).stem for f in glob.glob(str(label_dir / '*.txt'))}
            
            for orphan in (img_files - label_files):
                for f in glob.glob(str(img_dir / f'{orphan}.*')): os.remove(f); count += 1
            for orphan in (label_files - img_files):
                f = label_dir / f'{orphan}.txt'
                if f.exists(): os.remove(str(f)); count += 1
        self.stats['orphaned_files'] = count
        print(f"✓ Removed {count} files")
        return count

    def normalize_coordinates(self) -> Tuple[int, int]:
        print("[STEP 3/4] Normalizing bboxes...", end=" ", flush=True)
        invalid_cnt, conv_cnt = 0, 0
        
        for split in self.splits:
            img_dir = self.dataset_path / split / 'images'
            label_dir = self.dataset_path / split / 'labels'
            if not (img_dir.exists() and label_dir.exists()): continue
            
            for label_file in glob.glob(str(label_dir / '*.txt')):
                base_name = Path(label_file).stem
                img_paths = glob.glob(str(img_dir / f'{base_name}.*'))
                if not img_paths: continue
                
                img_array = np.fromfile(img_paths[0], np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is None: continue
                h_img, w_img = img.shape[:2]
                
                valid_lines = []
                with open(label_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) != 5: invalid_cnt += 1; continue
                        try:
                            cls_id = int(parts[0])
                            v1, v2, v3, v4 = map(float, parts[1:5])
                            if not (0 <= cls_id < self.num_classes): invalid_cnt += 1; continue
                            
                            # Nếu tọa độ > 1.0 (Pixel format), convert sang YOLO format
                            if v1 > 1.0 or v2 > 1.0 or v3 > 1.0 or v4 > 1.0:
                                x_min, y_min = max(0, min(w_img, v1)), max(0, min(h_img, v2))
                                x_max, y_max = max(0, min(w_img, v3)), max(0, min(h_img, v4))
                                if x_max <= x_min or y_max <= y_min: invalid_cnt += 1; continue
                                
                                x_center, y_center = ((x_min + x_max)/2.0)/w_img, ((y_min + y_max)/2.0)/h_img
                                width, height = (x_max - x_min)/w_img, (y_max - y_min)/h_img
                                valid_lines.append(f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                                conv_cnt += 1
                            else:
                                if (0.0 <= v1 <= 1.0) and (0.0 <= v2 <= 1.0) and (0.0 < v3 <= 1.0) and (0.0 < v4 <= 1.0):
                                    valid_lines.append(line)
                                else:
                                    invalid_cnt += 1
                        except ValueError: invalid_cnt += 1
                
                with open(label_file, 'w', encoding='utf-8') as f: f.writelines(valid_lines)
        
        self.stats['invalid_bboxes'], self.stats['converted_bboxes'] = invalid_cnt, conv_cnt
        print(f"✓ Cleaned {invalid_cnt} | Converted {conv_cnt}")
        return invalid_cnt, conv_cnt

    def collect_statistics(self):
        print("[STEP 4/4] Collecting statistics...", end=" ", flush=True)
        t_img, t_lbl = 0, 0
        for split in self.splits:
            img_dir, label_dir = self.dataset_path / split / 'images', self.dataset_path / split / 'labels'
            if img_dir.exists(): t_img += len(glob.glob(str(img_dir / '*.*')))
            if label_dir.exists(): t_lbl += len(glob.glob(str(label_dir / '*.txt')))
        self.stats['total_images'], self.stats['total_labels'] = t_img, t_lbl
        print("✓ Done")

    def print_summary(self):
        print("\n" + "="*70 + "\n📊 FINAL STATISTICS\n" + "="*70)
        print(f" Total images: {self.stats['total_images']} | Total labels: {self.stats['total_labels']}")
        print(f" Match ratio: {100 * self.stats['total_labels'] / max(1, self.stats['total_images']):.1f}%")

if __name__ == '__main__':
    import sys
    from pathlib import Path
    import argparse
    
    # [QUAN TRỌNG] Thêm thư mục gốc vào đường dẫn hệ thống để gọi được module utils
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    sys.path.append(str(PROJECT_ROOT))
    from utils.config import DATASET_DIR  # Gọi trạm cấu hình trung tâm
    
    parser = argparse.ArgumentParser()
    # Gán default = DATASET_DIR từ config
    parser.add_argument('--dataset', default=str(DATASET_DIR), help='Path to dataset root')
    parser.add_argument('--classes', type=int, default=4)
    args = parser.parse_args()
    
    cleaner = DatasetCleaner(args.dataset, args.classes)
    cleaner.run_all()