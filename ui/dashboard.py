"""
dashboard.py: Giao diện người dùng (GUI) phiên bản Pro cho Hệ thống Giám sát Giao thông
Tích hợp biểu đồ thời gian thực và bảng điều khiển tham số AI.
"""

import customtkinter as ctk
from PIL import Image
import cv2
import threading
import queue
import time
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections

# Thiết lập giao diện
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class TrafficDashboard(ctk.CTk):
    def __init__(self, ai_engine_callback):
        super().__init__()
        
        self.title("🚦 Hệ thống AI Giám sát Giao thông & Cảnh báo Vi phạm")
        self.geometry("1400x850") # Mở rộng không gian cho biểu đồ
        self.minsize(1200, 700)
        
        self.start_ai_engine = ai_engine_callback
        self.frame_queue = queue.Queue(maxsize=10)
        self.stats_queue = queue.Queue(maxsize=10)
        
        self.is_running = False
        
        # Dữ liệu lưu trữ cho biểu đồ (Lưu 50 mốc thời gian gần nhất)
        self.history_time = collections.deque(maxlen=50)
        self.history_vehicles = collections.deque(maxlen=50)
        self.start_app_time = time.time()
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Layout tổng thể: 70% Video (Trái) - 30% Bảng điều khiển (Phải)
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)
        
        # ==========================================
        # CỘT TRÁI: VIDEO & THANH TRẠNG THÁI
        # ==========================================
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        self.video_frame = ctk.CTkFrame(self.left_panel, corner_radius=15, border_width=2, border_color="#3a3a3a")
        self.video_frame.grid(row=0, column=0, sticky="nsew")
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_columnconfigure(0, weight=1)
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="Vui lòng chọn nguồn Video để bắt đầu...", 
                                        font=("Arial", 22, "bold"), text_color="#555555")
        self.video_label.grid(row=0, column=0)

        # Thanh trạng thái dưới video
        self.status_bar = ctk.CTkLabel(self.left_panel, text="🟢 Hệ thống sẵn sàng", text_color="gray", anchor="w")
        self.status_bar.grid(row=1, column=0, pady=(10, 0), sticky="ew")

        # ==========================================
        # CỘT PHẢI: BẢNG ĐIỀU KHIỂN ĐA NHIỆM (TABVIEW)
        # ==========================================
        self.right_panel = ctk.CTkTabview(self, corner_radius=15)
        self.right_panel.grid(row=0, column=1, padx=(0, 20), pady=10, sticky="nsew")
        
        self.right_panel.add("🎮 Điều khiển")
        self.right_panel.add("📊 Phân tích")
        self.right_panel.add("⚙️ Cài đặt AI")
        
        self._build_control_tab()
        self._build_analytics_tab()
        self._build_settings_tab()

    def _build_control_tab(self):
        tab = self.right_panel.tab("🎮 Điều khiển")
        
        # Nguồn Video
        ctk.CTkLabel(tab, text="NGUỒN DỮ LIỆU", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        self.btn_select = ctk.CTkButton(tab, text="📂 Duyệt File / Webcam", command=self.select_source, height=45)
        self.btn_select.pack(pady=5, padx=20, fill="x")
        self.lbl_source = ctk.CTkLabel(tab, text="Chưa chọn", text_color="gray", font=("Arial", 12))
        self.lbl_source.pack(pady=(0, 15))
        
        # Nút Hành động
        self.btn_start = ctk.CTkButton(tab, text="▶ KHỞI ĐỘNG HỆ THỐNG", command=self.start_processing, 
                                       height=50, font=("Arial", 15, "bold"), fg_color="#28a745", hover_color="#218838")
        self.btn_start.pack(pady=10, padx=20, fill="x")
        
        self.btn_stop = ctk.CTkButton(tab, text="⏹ TẠM DỪNG", command=self.stop_processing, 
                                      height=40, font=("Arial", 14, "bold"), fg_color="#dc3545", hover_color="#c82333", state="disabled")
        self.btn_stop.pack(pady=5, padx=20, fill="x")

        ctk.CTkFrame(tab, height=2, fg_color="#444444").pack(fill="x", padx=20, pady=20)

        # Thống kê nhanh
        ctk.CTkLabel(tab, text="THỐNG KÊ NHANH", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        self.lbl_fps = self._create_stat_card(tab, "⚡ Tốc độ (FPS):", "0.0", "#17a2b8")
        self.lbl_total_vehicles = self._create_stat_card(tab, "🚗 Lưu lượng xe:", "0", "#ffc107")
        self.lbl_violations = self._create_stat_card(tab, "🚨 Số ca vi phạm:", "0", "#ff4d4d")

    def _build_analytics_tab(self):
        tab = self.right_panel.tab("📊 Phân tích")
        ctk.CTkLabel(tab, text="BIỂU ĐỒ LƯU LƯỢNG THỰC TẾ", font=("Arial", 14, "bold")).pack(pady=(15, 10))
        
        # Vùng chứa biểu đồ Matplotlib
        self.chart_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Khởi tạo Matplotlib Figure (Giao diện Dark Mode)
        self.fig, self.ax = plt.subplots(figsize=(4, 3), dpi=100)
        self.fig.patch.set_facecolor('#242424') # Khớp với màu nền CustomTkinter
        self.ax.set_facecolor('#242424')
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.spines['bottom'].set_color('gray')
        self.ax.spines['top'].set_color('#242424') 
        self.ax.spines['right'].set_color('#242424')
        self.ax.spines['left'].set_color('gray')
        
        self.line, = self.ax.plot([], [], color='#00d2ff', linewidth=2)
        self.ax.set_ylabel("Số lượng xe", color='white', fontsize=10)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _build_settings_tab(self):
        tab = self.right_panel.tab("⚙️ Cài đặt AI")
        
        ctk.CTkLabel(tab, text="THAM SỐ NHẬN DIỆN", font=("Arial", 14, "bold")).pack(pady=(15, 20))
        
        # Slider Confidence
        ctk.CTkLabel(tab, text="Ngưỡng tin cậy (Confidence):", anchor="w").pack(fill="x", padx=20)
        self.conf_slider = ctk.CTkSlider(tab, from_=0.1, to=0.9, number_of_steps=80, command=self.update_conf)
        self.conf_slider.set(0.4)
        self.conf_slider.pack(fill="x", padx=20, pady=5)
        self.lbl_conf_val = ctk.CTkLabel(tab, text="40%")
        self.lbl_conf_val.pack()

        ctk.CTkLabel(tab, text="Giao diện hiển thị", font=("Arial", 14, "bold")).pack(pady=(30, 10))
        self.switch_theme = ctk.CTkSwitch(tab, text="Chế độ Sáng (Light Mode)", command=self.toggle_theme)
        self.switch_theme.pack(pady=10)

    def _create_stat_card(self, parent, title, default_val, text_color):
        frame = ctk.CTkFrame(parent, fg_color="#333333", corner_radius=8)
        frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(frame, text=title, font=("Arial", 14)).pack(side="left", padx=15, pady=10)
        val_label = ctk.CTkLabel(frame, text=default_val, font=("Arial", 18, "bold"), text_color=text_color)
        val_label.pack(side="right", padx=15, pady=10)
        return val_label

    def update_conf(self, value):
        self.lbl_conf_val.configure(text=f"{int(value * 100)}%")
        # Ghi chú: Bạn có thể truyền biến này vào Queue để lõi AI cập nhật ngưỡng trực tiếp

    def toggle_theme(self):
        if self.switch_theme.get() == 1:
            ctk.set_appearance_mode("Light")
            self.fig.patch.set_facecolor('#ebebeb')
            self.ax.set_facecolor('#ebebeb')
            self.ax.tick_params(colors='black')
        else:
            ctk.set_appearance_mode("Dark")
            self.fig.patch.set_facecolor('#242424')
            self.ax.set_facecolor('#242424')
            self.ax.tick_params(colors='white')
        self.canvas.draw()

    def select_source(self):
        file_path = filedialog.askopenfilename(title="Chọn Video", filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
        if file_path:
            self.video_source = file_path
            self.lbl_source.configure(text=f"...{file_path[-25:]}")
            self.btn_start.configure(state="normal")
            self.status_bar.configure(text=f"📂 Đã nạp file: {file_path.split('/')[-1]}")

    def start_processing(self):
        if not hasattr(self, 'video_source') or not self.video_source:
            return
            
        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_select.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        
        self.status_bar.configure(text="⏳ Đang khởi tạo TensorRT Engine và nạp VRAM... Xin chờ vài giây.")
        self.video_label.configure(text="Đang kết nối luồng AI...")
        self.update()
        
        self.history_time.clear()
        self.history_vehicles.clear()
        self.start_app_time = time.time()
        
        self.ai_thread = threading.Thread(target=self.start_ai_engine, 
                                          args=(self.video_source, self.frame_queue, self.stats_queue, lambda: self.is_running))
        self.ai_thread.daemon = True
        self.ai_thread.start()
        
        self.update_gui_loop()

    def stop_processing(self):
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_select.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.video_label.configure(image="", text="⏹ Đã dừng hệ thống.")
        self.status_bar.configure(text="🔴 Hệ thống đang nghỉ.")

    def update_gui_loop(self):
        if not self.is_running: return
            
        # 1. Cập nhật Frame Video
        try:
            frame = self.frame_queue.get_nowait()
            cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(cv2_image)
            
            frame_width = self.video_frame.winfo_width() - 10
            frame_height = self.video_frame.winfo_height() - 10
            if frame_width > 0 and frame_height > 0:
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(frame_width, frame_height))
                self.video_label.configure(image=ctk_image, text="")
                self.status_bar.configure(text="🟢 Đang phân tích luồng giao thông trực tiếp...")
        except queue.Empty: pass

        # 2. Cập nhật Thống kê & Biểu đồ (Mỗi khi có data mới)
        try:
            stats = self.stats_queue.get_nowait()
            current_total = stats.get('total_vehicles', 0)
            
            self.lbl_fps.configure(text=f"{stats.get('fps', 0):.1f}")
            self.lbl_total_vehicles.configure(text=str(current_total))
            self.lbl_violations.configure(text=str(stats.get('violations', 0)))
            
            # Cập nhật dữ liệu biểu đồ
            current_time = time.time() - self.start_app_time
            self.history_time.append(current_time)
            self.history_vehicles.append(current_total)
            
            # Chỉ vẽ lại biểu đồ sau mỗi 10 frame để tránh giật lag GUI
            if len(self.history_time) % 10 == 0:
                self.line.set_data(self.history_time, self.history_vehicles)
                self.ax.set_xlim(max(0, current_time - 60), current_time + 5) # Hiển thị 60 giây gần nhất
                self.ax.set_ylim(0, max(self.history_vehicles) + 5 if self.history_vehicles else 10)
                self.canvas.draw_idle()
                
        except queue.Empty: pass

        self.after(30, self.update_gui_loop)