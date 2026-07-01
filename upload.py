from roboflow import Roboflow

# Khởi tạo kết nối với Roboflow bằng API Key của bạn
rf = Roboflow(api_key="nnx2gEMlYI9CqnGAAELr")

# Truy cập vào Workspace của bạn
workspace = rf.workspace("giangs-workspace-sycgt")

# Tải toàn bộ thư mục lên project đích
workspace.upload_dataset(
    dataset_path="./Data_4/", # Đường dẫn root chứa dataset
    project_name="hmmm",              # Tên/ID của project 
    num_workers=10,                                  # Số lượng luồng xử lý song song (Khuyến nghị < 25)
    project_type="object-detection"                  # Loại bài toán
)

print("Tải dữ liệu lên hoàn tất!")