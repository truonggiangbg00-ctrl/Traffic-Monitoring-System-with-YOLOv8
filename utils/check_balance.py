import os
import glob
from collections import Counter
import matplotlib.pyplot as plt

# Import cấu hình từ file config.py của bạn
import config

def check_class_balance(split_name="train"):
    """
    Kiểm tra độ phân bố các lớp trong tập dữ liệu YOLO.
    :param split_name: Tên thư mục con (ví dụ: 'train', 'valid', 'test')
    """
    print(f"\n[{split_name.upper()}] ĐANG KIỂM TRA ĐỘ CÂN BẰNG DỮ LIỆU...")
    
    # Tạo đường dẫn trỏ tới thư mục labels dựa trên config.DATASET_DIR
    labels_dir = config.DATASET_DIR / split_name / "labels"
    
    if not labels_dir.exists():
        print(f"Lỗi: Không tìm thấy thư mục {labels_dir}")
        print("Hãy kiểm tra lại biến DATASET_NAME trong config.py hoặc cấu trúc thư mục.")
        return

    # Lấy tất cả các file .txt trong thư mục labels
    txt_files = glob.glob(str(labels_dir / "*.txt"))
    
    if not txt_files:
        print(f"Cảnh báo: Không có file .txt nào trong {labels_dir}")
        return

    class_counts = Counter()
    
    # Đọc và đếm nhãn
    for txt_path in txt_files:
        with open(txt_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                if len(parts) > 0:
                    try:
                        class_id = int(parts[0])
                        class_counts[class_id] += 1
                    except ValueError:
                        continue # Bỏ qua các dòng lỗi (nếu có)

    # ==========================================
    # IN KẾT QUẢ RA TERMINAL
    # ==========================================
    total_instances = sum(class_counts.values())
    if total_instances == 0:
        print("Không tìm thấy bounding box nào trong các file nhãn.")
        return
        
    print("-" * 55)
    print(f"{'ID':<5} | {'Tên Lớp (Class)':<15} | {'Số lượng':<10} | {'Tỷ lệ (%)'}")
    print("-" * 55)
    
    names_for_plot = []
    counts_for_plot = []
    
    # In theo thứ tự ID được định nghĩa trong config.py
    for class_id in sorted(config.CLASS_NAMES.keys()):
        count = class_counts.get(class_id, 0)
        name = config.CLASS_NAMES[class_id]
        percentage = (count / total_instances) * 100 if total_instances > 0 else 0
        
        print(f"{class_id:<5} | {name.capitalize():<15} | {count:<10} | {percentage:.1f}%")
        
        names_for_plot.append(name.capitalize())
        counts_for_plot.append(count)
        
    print("-" * 55)
    print(f"TỔNG CỘNG: {total_instances} bounding boxes trong {len(txt_files)} ảnh.")
    print("-" * 55)

    # ==========================================
    # VẼ BIỂU ĐỒ TRỰC QUAN BẰNG MATPLOTLIB
    # ==========================================
    plt.figure(figsize=(10, 6))
    
    # Tạo màu sắc ngẫu nhiên nhưng dịu mắt cho các cột
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0']
    
    bars = plt.bar(names_for_plot, counts_for_plot, color=colors[:len(names_for_plot)])
    
    plt.title(f"Phân bố Class - Tập {split_name.upper()} ({config.DATASET_NAME})", fontsize=14, fontweight='bold')
    plt.xlabel("Lớp (Classes)", fontsize=12)
    plt.ylabel("Số lượng vật thể (Bounding Boxes)", fontsize=12)
    
    # Hiển thị số liệu thực tế trên đỉnh mỗi cột
    for bar in bars:
        yval = bar.get_height()
        # Thêm một chút padding (1% của max_y) để số không dính sát vào cột
        plt.text(bar.get_x() + bar.get_width()/2, yval + (max(counts_for_plot) * 0.01), 
                 int(yval), ha='center', va='bottom', fontsize=11, fontweight='bold')
        
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Đảm bảo đã cài matplotlib: pip install matplotlib
    
    # Chạy kiểm tra cho tập train
    check_class_balance("train")
    
    # Nếu bạn có tập valid, bỏ comment dòng dưới để kiểm tra luôn
    check_class_balance("valid")

    check_class_balance("test")  # Nếu có tập test, kiểm tra luôn