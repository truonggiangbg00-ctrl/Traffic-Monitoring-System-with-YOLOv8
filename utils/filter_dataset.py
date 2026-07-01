import os
import random
from pathlib import Path

# Nhúng file config.py của bạn
import config

# ============================================================================
# 1. CẤU HÌNH THUẬT TOÁN LỌC
# ============================================================================

# Tập dữ liệu cần lọc (Thường chỉ nên lọc tập 'train', giữ nguyên 'valid' và 'test')
SPLIT_NAME = "train" 

# Tỷ lệ xóa bỏ (0.6 = Xóa đi 60% số ảnh CHỈ CHỨA các lớp dư thừa)
DROP_RATE = 0.6

# CHẾ ĐỘ AN TOÀN (Bật True để chạy nháp, tắt False để XÓA THẬT)
DRY_RUN = False

# ============================================================================
# 2. TỰ ĐỘNG LẤY ID TỪ CONFIG
# ============================================================================
IMAGES_DIR = config.DATASET_DIR / SPLIT_NAME / "images"
LABELS_DIR = config.DATASET_DIR / SPLIT_NAME / "labels"

# Tạo một dictionary đảo ngược từ config để lấy ID bằng tên chữ
# Ví dụ: {'bike': 0, 'bus': 1, 'car': 2...}
NAME_TO_ID = {name: id for id, name in config.CLASS_NAMES.items()}

# Khai báo tự động bằng tên (Không sợ nhầm lẫn ID nữa)
PROTECTED_CLASSES = [NAME_TO_ID["bus"], NAME_TO_ID["bike"], NAME_TO_ID["truck"]]
REDUCE_CLASSES = [NAME_TO_ID["car"], NAME_TO_ID["motorbike"]]

# ============================================================================
# 3. HÀM XỬ LÝ LÕI
# ============================================================================

def get_classes_from_txt(txt_path):
    """Đọc file YOLO txt và trả về danh sách các class ID (unique)"""
    classes_in_file = set()
    try:
        with open(txt_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    classes_in_file.add(int(parts[0]))
    except Exception as e:
        print(f"Lỗi đọc file {txt_path}: {e}")
    return list(classes_in_file)

def main():
    print(f"\n🚀 BẮT ĐẦU QUÁ TRÌNH LỌC DỮ LIỆU: {config.DATASET_NAME} ({SPLIT_NAME.upper()})")
    if DRY_RUN:
        print("⚠️  CHÚ Ý: ĐANG Ở CHẾ ĐỘ DRY_RUN (CHẠY THỬ). SẼ KHÔNG CÓ FILE NÀO BỊ XÓA THẬT.\n")
    else:
        print("🚨 CẢNH BÁO: ĐANG XÓA DỮ LIỆU THẬT! HÃY CHẮC CHẮN BẠN ĐÃ BACKUP.\n")

    if not LABELS_DIR.exists() or not IMAGES_DIR.exists():
        print(f"❌ Không tìm thấy thư mục: \n- {LABELS_DIR}\n- {IMAGES_DIR}")
        return

    # Lấy danh sách tất cả file .txt
    txt_files = list(LABELS_DIR.glob("*.txt"))
    
    deleted_count = 0
    kept_count = 0
    missing_img_count = 0

    for txt_path in txt_files:
        base_name = txt_path.stem # Tên file không có đuôi
        
        # Tìm file ảnh tương ứng (Hỗ trợ nhiều định dạng)
        img_path = None
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            temp_path = IMAGES_DIR / f"{base_name}{ext}"
            if temp_path.exists():
                img_path = temp_path
                break
                
        if not img_path:
            missing_img_count += 1
            continue
            
        classes_present = get_classes_from_txt(txt_path)
        
        # Bỏ qua nếu ảnh rỗng (không chứa nhãn)
        if not classes_present:
            kept_count += 1
            continue

        # KIỂM TRA 1: Ảnh có chứa class CẦN BẢO VỆ (Bus, Bike)? -> GIỮ!
        if any(c in PROTECTED_CLASSES for c in classes_present):
            kept_count += 1
            continue
            
        # KIỂM TRA 2: Ảnh CHỈ CHỨA các class CẦN GIẢM BỚT (Car, Motorbike)?
        # (Nếu nó có lẫn Truck vào thì biến này sẽ thành False và được giữ lại)
        only_contains_reduce_classes = all(c in REDUCE_CLASSES for c in classes_present)
        
        if only_contains_reduce_classes:
            # Tung xúc xắc ngẫu nhiên với tỷ lệ DROP_RATE
            if random.random() < DROP_RATE:
                # Đã trúng tỷ lệ xóa
                if not DRY_RUN:
                    os.remove(txt_path)
                    os.remove(img_path)
                deleted_count += 1
            else:
                # Trượt tỷ lệ -> May mắn được giữ lại
                kept_count += 1
        else:
            # Thuộc các trường hợp khác (vd: Chỉ có Truck) -> Giữ lại
            kept_count += 1

    # ============================================================================
    # 4. TỔNG KẾT BÁO CÁO
    # ============================================================================
    print("=" * 50)
    print("📊 BÁO CÁO KẾT QUẢ LỌC")
    print("=" * 50)
    print(f"Tổng số file nhãn đã quét: {len(txt_files)}")
    print(f"✅ Số ảnh được GIỮ LẠI:    {kept_count}")
    
    if DRY_RUN:
        print(f"🗑️  Số ảnh DỰ KIẾN XÓA:    {deleted_count} (Chưa xóa thật do DRY_RUN=True)")
    else:
        print(f"🗑️  Số ảnh ĐÃ XÓA THẬT:    {deleted_count}")
        
    if missing_img_count > 0:
        print(f"⚠️  Số nhãn bị mất file ảnh: {missing_img_count} (Bị bỏ qua)")
    print("=" * 50)
    
    if DRY_RUN:
        print("\n💡 Hướng dẫn: Nếu bạn hài lòng với con số 'DỰ KIẾN XÓA', hãy sửa lại:")
        print("   DRY_RUN = False (ở đầu file) và chạy lại script này một lần nữa.")

if __name__ == "__main__":
    main()