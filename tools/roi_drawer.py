"""
roi_drawer.py: Interactive ROI (Region of Interest) drawing tool
"""

import cv2
import numpy as np
from pathlib import Path
import argparse
import sys

class ROIDrawer:
    """Interactive ROI polygon drawing tool"""
    
    def __init__(self, video_path: str):
        self.video_path = Path(video_path)
        
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
            
        print(f"🎬 Loading video: {self.video_path}")
        cap = cv2.VideoCapture(str(self.video_path))
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise RuntimeError("Cannot read first frame from video")
            
        self.base_frame = frame
        self.frame_h, self.frame_w = frame.shape[:2]
        
        self.current_polygon = []
        self.all_polygons = {}
        self.lane_counter = 1
        self.mouse_pos = (0, 0)
        
        self.window_name = "ROI Drawer - Draw Lane Boundaries"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        # Tự động thu nhỏ cửa sổ hiển thị nếu video gốc quá to (VD: 4K)
        display_w = min(self.frame_w, 1280)
        display_h = int(self.frame_h * (display_w / self.frame_w))
        cv2.resizeWindow(self.window_name, display_w, display_h)
        cv2.setMouseCallback(self.window_name, self._mouse_callback)
    
    def _mouse_callback(self, event, x: int, y: int, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            self.mouse_pos = (x, y)
        elif event == cv2.EVENT_LBUTTONDOWN:
            self.current_polygon.append([x, y])
            print(f"   📍 Point added: ({x}, {y}). Total points: {len(self.current_polygon)}")
        elif event == cv2.EVENT_RBUTTONDOWN:
            if self.current_polygon:
                removed = self.current_polygon.pop()
                print(f"   ↩️ Point removed: {removed}. Remaining: {len(self.current_polygon)}")
    
    def _draw_frame(self) -> np.ndarray:
        display = self.base_frame.copy()
        
        for lane_name, polygon in self.all_polygons.items():
            pts = np.array(polygon, np.int32).reshape((-1, 1, 2))
            cv2.polylines(display, [pts], isClosed=True, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
            
            # Làm nổi bật tên làn đường
            text_pos = tuple(polygon[0])
            cv2.rectangle(display, (text_pos[0]-5, text_pos[1]-25), (text_pos[0]+100, text_pos[1]+5), (0,0,0), -1)
            cv2.putText(display, lane_name, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        
        if self.current_polygon:
            for i, pt in enumerate(self.current_polygon):
                cv2.circle(display, tuple(pt), 5, (0, 0, 255), -1)
                if i > 0:
                    cv2.line(display, tuple(self.current_polygon[i-1]), tuple(pt), (0, 0, 255), 2, cv2.LINE_AA)
            
            if len(self.current_polygon) > 2:
                cv2.line(display, tuple(self.current_polygon[-1]), tuple(self.current_polygon[0]), (0, 165, 255), 1, cv2.LINE_AA)
            
            # Vẽ đường dẫn hướng (Guide line)
            cv2.line(display, tuple(self.current_polygon[-1]), self.mouse_pos, (255, 255, 255), 1, cv2.LINE_AA)
        
        self._draw_instructions(display)
        return display
    
    def _draw_instructions(self, frame: np.ndarray):
        instructions = [
            f"Lanes saved: {len(self.all_polygons)} | Current pts: {len(self.current_polygon)}",
            "",
            "Controls:",
            "  LEFT CLICK : Add point",
            "  RIGHT CLICK: Remove point",
            "  'N'        : Save lane",
            "  'C'        : Clear polygon",
            "  'SPACE'    : Delete last lane",
            "  'Q' / 'ESC': Finish & save",
        ]
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 5), (320, 20 + len(instructions)*25), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        y_offset = 30
        for inst in instructions:
            cv2.putText(frame, inst, (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            y_offset += 25
            
    def run(self) -> dict:
        print("="*70 + "\n🎯 INTERACTIVE ROI DRAWER\n" + "="*70)
        try:
            while True:
                display_frame = self._draw_frame()
                cv2.imshow(self.window_name, display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('n'), ord('N')):
                    if len(self.current_polygon) >= 3:
                        # Chuẩn hóa tên làn thành chữ IN HOA (VD: LANE_1)
                        lane_name = f"LANE_{self.lane_counter}"
                        self.all_polygons[lane_name] = self.current_polygon.copy()
                        print(f"✅ Đã lưu: {lane_name}")
                        self.current_polygon.clear()
                        self.lane_counter += 1
                    else:
                        print("❌ Cần ít nhất 3 điểm để tạo thành vùng (polygon)!")
                elif key in (ord('c'), ord('C')):
                    self.current_polygon.clear()
                    print("🧹 Đã xóa vùng hiện tại")
                elif key == 32:  # SPACE
                    if self.all_polygons:
                        removed = self.all_polygons.popitem()
                        print(f"🗑️ Đã xóa: {removed[0]}")
                        self.lane_counter -= 1
                elif key in (ord('q'), ord('Q'), 27):  # Q or ESC
                    if self.current_polygon:
                        print("⚠️ Bạn đang vẽ dở. Nhấn 'N' để lưu hoặc 'C' để hủy trước khi thoát.")
                    else: 
                        break
        finally:
            cv2.destroyAllWindows()
        return self.all_polygons
    
    def save_config(self):
        if not self.all_polygons: 
            print("⚠️ Không có vùng ROI nào được vẽ. Thoát chương trình.")
            return
            
        code =  "import numpy as np\n\n"
        code += "# " + "="*65 + "\n"
        code += "# 🎯 CẤU HÌNH VÙNG ROI (Hãy copy đè đoạn này vào utils/config.py)\n"
        code += "# " + "="*65 + "\n\n"
        
        # 1. Block LANE_POLYGONS
        code += "LANE_POLYGONS = {\n"
        for lane_name, polygon in self.all_polygons.items():
            # Format mảng đẹp mắt trên 1 dòng
            pts_str = ", ".join([f"[{x}, {y}]" for x, y in polygon])
            code += f'    "{lane_name}": np.array([{pts_str}], dtype=np.int32),\n'
        code += "}\n\n"
        
        # 2. Block LANE_RESTRICTIONS tự động
        code += "# Quy định loại xe ĐƯỢC PHÉP chạy trên từng làn\n"
        code += "# (Các xe không có trong danh sách này sẽ bị tính là Vi phạm đè/sai làn)\n"
        code += "LANE_RESTRICTIONS = {\n"
        for lane_name in self.all_polygons.keys():
            # Tạo danh sách mẫu gồm các class phổ biến
            code += f'    "{lane_name}": ["car", "bus", "truck"],  # Sửa lại tùy theo logic thực tế\n'
        code += "}\n"
        
        # In ra màn hình
        print("\n" + "="*70)
        print("🎉 ĐÃ TẠO XONG CẤU HÌNH! DƯỚI ĐÂY LÀ CODE CỦA BẠN:")
        print("="*70 + "\n")
        print(code)
        print("="*70)
        
        # Tự động xuất ra file để tránh mất dữ liệu
        output_file = Path("roi_output.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"📁 Code cũng đã được lưu an toàn tại file: {output_file.absolute()}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('video', help='Đường dẫn tới video cần vẽ ROI (VD: data/test_video.mp4)')
    args = parser.parse_args()
    drawer = ROIDrawer(args.video)
    if drawer.run():
        drawer.save_config()