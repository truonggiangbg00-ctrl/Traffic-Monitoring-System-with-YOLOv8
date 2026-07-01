"""
dashboard.py: Giao diện người dùng (GUI) phiên bản Ultimate (Refactored UI)
Tích hợp biểu đồ, Bảng CSV Live, Chụp ảnh vi phạm, và Quản lý file xuất.
"""

import customtkinter as ctk
from PIL import Image
import cv2
import numpy as np
import threading
import queue
import time
import os
import sys
import subprocess
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections

from utils.config import OUTPUT_DIR, EVIDENCE_DIR

# Cấu hình Theme tổng thể
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

# Định nghĩa hằng số UI
UI_FONT_MAIN = ("Segoe UI", 13)
UI_FONT_TITLE = ("Segoe UI", 16, "bold")
UI_FONT_STATS = ("Segoe UI", 20, "bold")
BG_CARD_COLOR = "#232323"
BG_PANEL_COLOR = "#1A1A1A"

class TrafficDashboard(ctk.CTk):
    def __init__(self, ai_engine_callback):
        super().__init__()
        
        self.title("🚦 Hệ thống AI Giám sát Giao thông & Cảnh báo Vi phạm")
        self.geometry("1450x850") 
        self.minsize(1280, 720)
        self.start_ai_engine = ai_engine_callback
        
        self.frame_queue = queue.Queue(maxsize=5)
        self.stats_queue = queue.Queue(maxsize=5)
        self.command_queue = queue.Queue()
        
        self.is_running = False
        self.recorded_violation_ids = set()
        
        self.custom_polygons = None
        self.custom_restrictions = None
        
        self.current_bgr_frame = None 
        
        self.history_time = collections.deque(maxlen=50)
        self.history_vehicles = collections.deque(maxlen=50)
        self.start_app_time = time.time()
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Thiết lập tỷ lệ màn hình chính
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)
        
        # --- BẢNG TRÁI: HIỂN THỊ VIDEO ---
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        self.video_frame = ctk.CTkFrame(self.left_panel, corner_radius=15, fg_color=BG_PANEL_COLOR)
        self.video_frame.grid(row=0, column=0, sticky="nsew")
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_columnconfigure(0, weight=1)
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="Vui lòng chọn nguồn Video để bắt đầu...", 
                                        font=UI_FONT_TITLE, text_color="#666666")
        self.video_label.grid(row=0, column=0)

        self.status_bar = ctk.CTkLabel(self.left_panel, text="🟢 Hệ thống sẵn sàng", 
                                       font=UI_FONT_MAIN, text_color="#888888", anchor="w")
        self.status_bar.grid(row=1, column=0, pady=(10, 0), sticky="ew")

        # --- BẢNG PHẢI: TABS ---
        self.right_panel = ctk.CTkTabview(self, corner_radius=15, fg_color=BG_PANEL_COLOR, 
                                          segmented_button_selected_color="#1f538d")
        self.right_panel.grid(row=0, column=1, padx=(10, 20), pady=15, sticky="nsew")
        
        self.right_panel.add("🎮 Điều khiển")
        self.right_panel.add("📊 Phân tích")
        self.right_panel.add("📸 Phạt Nguội") 
        self.right_panel.add("⚙️ Cài đặt")
        
        self._build_control_tab()
        self._build_analytics_tab()
        self._build_data_table_tab()
        self._build_settings_tab()

    def _build_control_tab(self):
        tab = self.right_panel.tab("🎮 Điều khiển")
        
        # Section: Nguồn dữ liệu
        ctk.CTkLabel(tab, text="NGUỒN DỮ LIỆU", font=UI_FONT_TITLE, text_color="#A0A0A0").pack(pady=(20, 10), anchor="w", padx=20)
        
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=5)
        
        self.btn_select_file = ctk.CTkButton(btn_frame, text="📂 File Video", command=self.select_file, 
                                             height=40, fg_color="#333333", hover_color="#444444")
        self.btn_select_file.pack(side="left", padx=(0, 5), expand=True, fill="x")
        
        self.btn_select_cam = ctk.CTkButton(btn_frame, text="📷 Webcam", command=self.select_webcam, 
                                            height=40, fg_color="#333333", hover_color="#444444")
        self.btn_select_cam.pack(side="right", padx=(5, 0), expand=True, fill="x")
        
        self.lbl_source = ctk.CTkLabel(tab, text="Trạng thái: Chưa chọn", text_color="#777777", font=("Segoe UI", 12, "italic"))
        self.lbl_source.pack(pady=(5, 15))
        
        # Section: Điều khiển chính
        ctk.CTkLabel(tab, text="VẬN HÀNH", font=UI_FONT_TITLE, text_color="#A0A0A0").pack(pady=(10, 10), anchor="w", padx=20)
        
        self.btn_draw_roi = ctk.CTkButton(tab, text="🖍️ 1. Vẽ Làn Đường (ROI)", command=self.launch_roi_drawer, 
                                          height=40, fg_color="#2b2b2b", border_width=1, border_color="#555555", hover_color="#3a3a3a")
        self.btn_draw_roi.pack(fill="x", padx=20, pady=(0, 10))
        
        self.btn_start = ctk.CTkButton(tab, text="▶ 2. KHỞI ĐỘNG AI", command=self.start_processing, 
                                       height=45, font=("Segoe UI", 14, "bold"), fg_color="#28a745", hover_color="#218838")
        self.btn_start.pack(pady=5, padx=20, fill="x")
        
        self.btn_stop = ctk.CTkButton(tab, text="⏹ TẠM DỪNG", command=self.stop_processing, 
                                      height=45, font=("Segoe UI", 14, "bold"), fg_color="transparent", 
                                      border_width=2, border_color="#fd7e14", text_color="#fd7e14", hover_color="#332211", state="disabled")
        self.btn_stop.pack(pady=5, padx=20, fill="x")

        # Divider
        ctk.CTkFrame(tab, height=1, fg_color="#333333").pack(fill="x", padx=20, pady=20)
        
        # Section: Thống kê nhanh
        ctk.CTkLabel(tab, text="THỐNG KÊ NHANH", font=UI_FONT_TITLE, text_color="#A0A0A0").pack(pady=(0, 10), anchor="w", padx=20)
        self.lbl_fps = self._create_stat_card(tab, "⚡ Tốc độ khung hình (FPS)", "0.0", "#4da6ff")
        self.lbl_total_vehicles = self._create_stat_card(tab, "🚗 Tổng lưu lượng", "0", "#ffc107")
        self.lbl_violations = self._create_stat_card(tab, "🚨 Ca vi phạm", "0", "#ff4d4d")

        # Nút tiện ích ở dưới cùng
        bottom_frame = ctk.CTkFrame(tab, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        self.btn_open_folder = ctk.CTkButton(bottom_frame, text="📁 Mở File Xuất", command=self.open_output_folder, 
                                             height=35, fg_color="#333333", hover_color="#444444", width=120)
        self.btn_open_folder.pack(side="left")

        self.btn_exit = ctk.CTkButton(bottom_frame, text="🛑 Tắt Hệ Thống", command=self.hard_exit, 
                                      height=35, fg_color="#dc3545", hover_color="#b02a37", width=120)
        self.btn_exit.pack(side="right")

    def _build_analytics_tab(self):
        tab = self.right_panel.tab("📊 Phân tích")
        ctk.CTkLabel(tab, text="BIỂU ĐỒ LƯU LƯỢNG THỰC TẾ", font=UI_FONT_TITLE).pack(pady=(20, 10))
        
        self.chart_frame = ctk.CTkFrame(tab, fg_color=BG_CARD_COLOR, corner_radius=10)
        self.chart_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.fig, self.ax = plt.subplots(figsize=(4, 3), dpi=100)
        self.fig.patch.set_facecolor(BG_CARD_COLOR) 
        self.ax.set_facecolor(BG_CARD_COLOR)
        
        self.ax.tick_params(colors='#AAAAAA', labelsize=9)
        self.ax.spines['bottom'].set_color('#555555')
        self.ax.spines['left'].set_color('#555555')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        self.line, = self.ax.plot([], [], color='#4da6ff', linewidth=2.5)
        self.ax.set_ylabel("Số lượng xe", color='#AAAAAA', fontsize=10)
        self.ax.grid(True, linestyle='--', alpha=0.2)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

    def _build_data_table_tab(self):
        tab = self.right_panel.tab("📸 Phạt Nguội")
        
        # Bố cục Trên-Dưới thay vì Trái-Phải cho tab hẹp
        img_frame = ctk.CTkFrame(tab, height=180, fg_color=BG_CARD_COLOR, corner_radius=10)
        img_frame.pack(side="top", fill="x", padx=15, pady=(15, 10))
        img_frame.pack_propagate(False)
        
        table_frame = ctk.CTkFrame(tab, fg_color="transparent")
        table_frame.pack(side="bottom", fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Khung ảnh
        ctk.CTkLabel(img_frame, text="BẰNG CHỨNG GẦN NHẤT", font=("Segoe UI", 11, "bold"), text_color="#A0A0A0").pack(pady=(10, 0))
        self.lbl_snapshot = ctk.CTkLabel(img_frame, text="[ Chưa ghi nhận vi phạm ]", text_color="#555555")
        self.lbl_snapshot.pack(expand=True)

        # Khung Bảng
        ctk.CTkLabel(table_frame, text="NHẬT KÝ TRỰC TIẾP", font=("Segoe UI", 11, "bold"), text_color="#ff4d4d").pack(pady=(5, 10), anchor="w")
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=BG_CARD_COLOR, foreground="white", rowheight=35, fieldbackground=BG_CARD_COLOR, borderwidth=0, font=UI_FONT_MAIN)
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#2b2b2b", foreground="white", relief="flat", font=("Segoe UI", 11, "bold"))
        style.map("Treeview.Heading", background=[('active', '#3a3a3a')])

        inner_table = ctk.CTkFrame(table_frame, corner_radius=10)
        inner_table.pack(fill="both", expand=True)
        
        columns = ("time", "id", "class", "lane")
        self.tree = ttk.Treeview(inner_table, columns=columns, show="headings")
        self.tree.heading("time", text="THỜI GIAN")
        self.tree.heading("id", text="ID")
        self.tree.heading("class", text="LOẠI")
        self.tree.heading("lane", text="VỊ TRÍ")
        
        self.tree.column("time", width=90, anchor="center")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("class", width=70, anchor="center")
        self.tree.column("lane", width=70, anchor="center")

        scrollbar = ctk.CTkScrollbar(inner_table, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side="right", fill="y", padx=5, pady=5)

    def _build_settings_tab(self):
        tab = self.right_panel.tab("⚙️ Cài đặt")
        ctk.CTkLabel(tab, text="THÔNG SỐ MÔ HÌNH", font=UI_FONT_TITLE).pack(pady=(25, 20), anchor="w", padx=20)
        
        card = ctk.CTkFrame(tab, fg_color=BG_CARD_COLOR, corner_radius=10)
        card.pack(fill="x", padx=20)
        
        ctk.CTkLabel(card, text="Ngưỡng tin cậy (Confidence):", font=UI_FONT_MAIN).pack(fill="x", padx=20, pady=(15, 5), anchor="w")
        
        slider_frame = ctk.CTkFrame(card, fg_color="transparent")
        slider_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.conf_slider = ctk.CTkSlider(slider_frame, from_=0.1, to=0.9, number_of_steps=16, command=self.update_conf)
        self.conf_slider.set(0.5) 
        self.conf_slider.pack(side="left", fill="x", expand=True, padx=(0, 15))
        
        self.lbl_conf_val = ctk.CTkLabel(slider_frame, text="50%", font=UI_FONT_TITLE, width=40)
        self.lbl_conf_val.pack(side="right")

    def _create_stat_card(self, parent, title, default_val, text_color):
        frame = ctk.CTkFrame(parent, fg_color=BG_CARD_COLOR, corner_radius=10)
        frame.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(frame, text=title, font=UI_FONT_MAIN, text_color="#DDDDDD").pack(side="left", padx=15, pady=12)
        val_label = ctk.CTkLabel(frame, text=default_val, font=UI_FONT_STATS, text_color=text_color)
        val_label.pack(side="right", padx=15, pady=12)
        return val_label

    # ================= LOGIC HỆ THỐNG GIỮ NGUYÊN BÊN DƯỚI =================
    # ... (Phần logic open_output_folder, hard_exit, _save_and_display_snapshot, start/stop_processing, update_gui_loop giữ nguyên mã code như cũ của bạn) ...
    def open_output_folder(self):
        try:
            folder_path = str(OUTPUT_DIR)
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin": 
                subprocess.Popen(["open", folder_path])
            else: 
                subprocess.Popen(["xdg-open", folder_path])
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở thư mục: {e}")

    def hard_exit(self):
        confirm = messagebox.askyesno("Cảnh báo", "Bạn có chắc chắn muốn TẮT HOÀN TOÀN phần mềm không?\nTiến trình AI sẽ bị ép dừng lập tức.")
        if confirm:
            self.is_running = False
            self.quit()
            self.destroy()
            sys.exit(0)

    # (Lưu ý: copy phần logic còn lại của bạn vào đây)

    def hard_exit(self):
        """Ép buộc dập tắt toàn bộ phần mềm và luồng Terminal"""
        confirm = messagebox.askyesno("Cảnh báo", "Bạn có chắc chắn muốn TẮT HOÀN TOÀN phần mềm không?\nTiến trình AI sẽ bị ép dừng lập tức.")
        if confirm:
            self.is_running = False
            self.quit()
            self.destroy()
            sys.exit(0) # Giết process Python

    def _save_and_display_snapshot(self, viol_id, viol_time):
        """Chụp frame hiện tại, hiển thị lên GUI và Lưu vào thư mục evidence/"""
        if self.current_bgr_frame is not None:
            # 1. Lưu file ảnh (.jpg)
            safe_time = viol_time.replace(":", "-") # Tránh lỗi tên file trên Windows
            filename = EVIDENCE_DIR / f"violation_ID{viol_id}_{safe_time}.jpg"
            cv2.imwrite(str(filename), self.current_bgr_frame)
            
            # 2. Hiển thị Thumbnail lên GUI
            rgb_img = cv2.cvtColor(self.current_bgr_frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img)
            
            # Thay đổi kích thước ảnh cho vừa panel bên phải
            thumb = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 112)) # Tỷ lệ 16:9
            self.lbl_snapshot.configure(image=thumb, text="")

    # ================= LOGIC HỆ THỐNG CŨ =================
    def launch_roi_drawer(self):
        if hasattr(self, 'ai_thread') and self.ai_thread.is_alive():
            self.status_bar.configure(text="⏳ Đang dọn dẹp luồng xử lý cũ... Xin chờ 2 giây.")
            self.update()
            self.ai_thread.join(timeout=2.0)
            
        if not hasattr(self, 'video_source') or self.video_source is None:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn Video hoặc Webcam trước khi vẽ!")
            return
            
        if self.is_running:
            messagebox.showwarning("Cảnh báo", "Hệ thống đang chạy. Vui lòng bấm '⏹ TẠM DỪNG' trước khi vẽ!")
            return
            
        try:
            from tools.roi_drawer import ROIDrawer
            self.status_bar.configure(text="🖍️ Đang mở công cụ vẽ ROI...")
            self.update()
            cv2.destroyAllWindows()
            cv2.waitKey(1)
            
            drawer = ROIDrawer(self.video_source)
            polygons, restrictions = drawer.run()
            
            if polygons:
                self.custom_polygons = {k: np.array(v, dtype=np.int32) for k, v in polygons.items()}
                self.custom_restrictions = restrictions
                start_now = messagebox.askyesno("Hoàn tất Vẽ Làn", "Đã nạp vùng ROI và Luật lệ mới vào hệ thống!\n\nBạn có muốn KHỞI ĐỘNG AI để phân tích ngay bây giờ không?")
                if start_now:
                    self.start_processing()
                else:
                    self.status_bar.configure(text="🟢 Đã nạp ROI. Hệ thống sẵn sàng!")
            else:
                self.status_bar.configure(text="🟢 Đã hủy bản vẽ ROI.")
                
        except Exception as e:
            messagebox.showerror("Lỗi kỹ thuật", f"Không thể mở công cụ vẽ ROI.\nChi tiết: {e}")

    def _create_stat_card(self, parent, title, default_val, text_color):
        frame = ctk.CTkFrame(parent, fg_color="#333333", corner_radius=8)
        frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(frame, text=title, font=("Arial", 14)).pack(side="left", padx=15, pady=10)
        val_label = ctk.CTkLabel(frame, text=default_val, font=("Arial", 18, "bold"), text_color=text_color)
        val_label.pack(side="right", padx=15, pady=10)
        return val_label

    def update_conf(self, value):
        self.lbl_conf_val.configure(text=f"{int(value * 100)}%")
        self.command_queue.put({"action": "set_confidence", "value": float(value)})

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Chọn Video", filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
        if file_path:
            self.video_source = file_path
            self.lbl_source.configure(text=f"...{file_path[-35:]}")
            self.btn_start.configure(state="normal")
            self.status_bar.configure(text=f"📂 Đã nạp file: {file_path.split('/')[-1]}")
            self.custom_polygons = None
            self.custom_restrictions = None

    def select_webcam(self):
        self.video_source = 0  
        self.lbl_source.configure(text="Nguồn: Webcam (Live)")
        self.btn_start.configure(state="normal")
        self.status_bar.configure(text="📷 Đã chọn Webcam. Hãy bấm Khởi động!")
        self.custom_polygons = None
        self.custom_restrictions = None

    def start_processing(self):
        if not hasattr(self, 'video_source') or self.video_source is None or self.video_source == "":
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn nguồn dữ liệu (Video hoặc Webcam) trước khi khởi động!")
            return
            
        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_select_file.configure(state="disabled")
        self.btn_select_cam.configure(state="disabled")
        self.btn_draw_roi.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        
        self.status_bar.configure(text="⏳ Đang cấu hình TensorRT Engine/VRAM... Xin chờ vài giây.")
        self.update()
        
        while not self.frame_queue.empty(): self.frame_queue.get()
        while not self.stats_queue.empty(): self.stats_queue.get()
        while not self.command_queue.empty(): self.command_queue.get()
        
        self.history_time.clear()
        self.history_vehicles.clear()
        self.start_app_time = time.time()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.recorded_violation_ids.clear()
        
        from utils.config import LANE_POLYGONS, LANE_RESTRICTIONS
        if self.custom_polygons:
            polygons_to_send = self.custom_polygons
            restrictions_to_send = self.custom_restrictions
        else:
            polygons_to_send = LANE_POLYGONS
            restrictions_to_send = LANE_RESTRICTIONS
        
        self.ai_thread = threading.Thread(
            target=self.start_ai_engine, 
            args=(self.video_source, polygons_to_send, restrictions_to_send, self.frame_queue, self.stats_queue, self.command_queue, lambda: self.is_running)
        )
        self.ai_thread.daemon = True
        self.ai_thread.start()
        
        self.update_gui_loop()

    def stop_processing(self):
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_select_file.configure(state="normal")
        self.btn_select_cam.configure(state="normal")
        self.btn_draw_roi.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        
        while not self.frame_queue.empty(): self.frame_queue.get_nowait()
        
        self.video_label.configure(image=None, text="⏹ Đã dừng hệ thống.")
        self.status_bar.configure(text="🔴 Hệ thống tạm nghỉ.")

    def update_gui_loop(self):
        if not self.is_running: return
        
        # Lấy Frame hình ảnh
        try:
            frame = self.frame_queue.get_nowait()
            
            # [CHỤP ẢNH]: Lưu lại bản copy BGR để xuất file nét nhất nếu cần
            self.current_bgr_frame = frame.copy() 
            
            cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(cv2_image)
            
            frame_width = max(100, self.video_frame.winfo_width() - 10)
            frame_height = max(100, self.video_frame.winfo_height() - 10)
            
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(frame_width, frame_height))
            self.video_label.configure(image=ctk_image, text="")
            self.status_bar.configure(text="🟢 Đang giám sát luồng giao thông trực tiếp...")
        except queue.Empty: pass
        except Exception as e: print(f"Lỗi hiển thị Frame: {e}")

        # Lấy Dữ liệu Vi phạm & Logic
        try:
            stats = self.stats_queue.get_nowait()
            if stats.get('action') == 'engine_stopped':
                self.stop_processing()
                if "error" in stats:
                    messagebox.showerror("Lỗi Luồng AI", f"Luồng AI bị sập: {stats['error']}")
                else:
                    self.status_bar.configure(text="✓ Phân tích hoàn tất.")
                return

            current_total = stats.get('total_vehicles', 0)
            self.lbl_fps.configure(text=f"{stats.get('fps', 0):.1f}")
            self.lbl_total_vehicles.configure(text=str(current_total))
            self.lbl_violations.configure(text=str(stats.get('violations', 0)))
            
            if 'live_viol_data' in stats:
                for v in stats['live_viol_data']:
                    if v['id'] not in self.recorded_violation_ids:
                        self.tree.insert("", "0", values=(v['time'], v['id'], v['class'], v['lane']))
                        self.recorded_violation_ids.add(v['id'])
                        
                        # Kích hoạt hàm Chụp ảnh và hiển thị lên GUI ngay lập tức
                        self._save_and_display_snapshot(v['id'], v['time'])
            
            current_time = time.time() - self.start_app_time
            self.history_time.append(current_time)
            self.history_vehicles.append(current_total)
            
            if len(self.history_time) % 5 == 0:
                self.line.set_data(self.history_time, self.history_vehicles)
                self.ax.set_xlim(max(0, current_time - 60), current_time + 5) 
                self.ax.set_ylim(0, max(self.history_vehicles) + 5 if self.history_vehicles else 10)
                self.canvas.draw_idle()
                
        except queue.Empty: pass

        self.after(30, self.update_gui_loop)