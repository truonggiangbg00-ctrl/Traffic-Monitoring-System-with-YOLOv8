"""
visualizer.py: Frame visualization with annotations
Draws bounding boxes, tracking IDs, violations, and traffic statistics
"""

import cv2
import numpy as np
from typing import Dict, List
from core.datatypes import FrameState

class Visualizer:
    """
    Handles all frame visualization and drawing operations
    Enforces separation of concerns: visualization logic only, no core logic
    """
    
    def __init__(self, draw_roi: bool = True, thickness: int = 2):
        self.draw_roi = draw_roi
        self.thickness = thickness
        
        # Color definitions (BGR format - OpenCV standard)
        self.color_normal = (0, 255, 0)      # Green - normal vehicle
        self.color_violation = (0, 0, 255)   # Red - violating vehicle
        self.color_roi = (255, 255, 0)       # Cyan - ROI boundaries
        self.color_text_bg = (0, 0, 0)       # Black - text background
        self.color_text = (255, 255, 255)    # White - text
        self.color_stats = (0, 255, 255)     # Yellow - statistics highlight
        
        # UI configuration
        self.panel_alpha = 0.6  # Độ mờ của dashboard thống kê
    
    def draw(self, frame_state: FrameState, 
             lane_polygons: Dict = None, draw_stats: bool = True) -> np.ndarray:
        """Draw all annotations on frame"""
        # Bắt buộc copy frame để không làm thay đổi frame gốc đang dùng cho Logic/AI
        img_draw = frame_state.original_frame.copy()
        
        # 1. Vẽ đa giác ROI phân làn
        if self.draw_roi and lane_polygons:
            img_draw = self._draw_roi_polygons(img_draw, lane_polygons)
        
        # 2. Vẽ Bounding Boxes và thông tin phương tiện
        img_draw = self._draw_vehicles(img_draw, frame_state.vehicles)
        
        # 3. Vẽ Dashboard thống kê và cảnh báo vi phạm
        if draw_stats or frame_state.violations:
            img_draw = self._draw_dashboard(
                img_draw, 
                frame_state.counts, 
                frame_state.fps, 
                frame_state.violations if frame_state.violations else []
            )
            
        return img_draw
    
    def _draw_roi_polygons(self, frame: np.ndarray, lane_polygons: Dict) -> np.ndarray:
        for lane_name, polygon in lane_polygons.items():
            # Reshape polygon thành định dạng [N, 1, 2] mà OpenCV yêu cầu
            pts = polygon.reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], isClosed=True, 
                          color=self.color_roi, thickness=self.thickness)
            
            # Vẽ tên làn đường với nền đen để hiển thị rõ trên nền đường nhựa sáng/tối
            text_pos = tuple(polygon[0])
            self._draw_text_with_background(
                frame, lane_name, text_pos, self.color_roi, 
                bg_color=self.color_text_bg, alpha=0.7
            )
        return frame
    
    def _draw_vehicles(self, frame: np.ndarray, vehicles: list) -> np.ndarray:
        for vehicle in vehicles:
            # Ép kiểu int an toàn
            x1, y1, x2, y2 = map(int, vehicle.bbox)
            color = self.color_violation if vehicle.is_violating else self.color_normal
            
            # Khung BBox chính
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, self.thickness)
            
            # Tâm đáy (bottom_center) - điểm dùng để xét logic vi phạm
            cv2.circle(frame, tuple(map(int, vehicle.bottom_center)), 5, color, -1)
            # Tâm xe
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            cv2.circle(frame, center, 3, color, -1)
            
            # Nhãn ID, Class và cảnh báo
            label = f"#{vehicle.track_id} {vehicle.cls_name}"
            if vehicle.is_violating:
                label += f" [VIOL: {vehicle.violation_lane}]"
            
            self._draw_text_with_background(frame, label, (x1, max(20, y1 - 10)), color)
            
            # Điểm tin cậy (Confidence score)
            conf_text = f"{vehicle.conf:.2f}"
            self._draw_text_with_background(frame, conf_text, (x1, min(frame.shape[0]-10, y2 + 20)), self.color_text)
            
        return frame

    def _draw_dashboard(self, frame: np.ndarray, counts: Dict[str, int], 
                        fps: float, violations: list) -> np.ndarray:
        """Tạo bảng UI mờ hiển thị thông số để không che khuất hoàn toàn video"""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        # Bảng thống kê (Góc trên, bên trái)
        cv2.rectangle(overlay, (10, 10), (280, 200 + len(counts)*30), self.color_text_bg, -1)
        
        # Bảng cảnh báo vi phạm (Góc trên, bên phải)
        if violations:
            cv2.rectangle(overlay, (w - 350, 10), (w - 10, 80 + min(5, len(violations))*30), self.color_text_bg, -1)
            
        # Alpha blending
        cv2.addWeighted(overlay, self.panel_alpha, frame, 1 - self.panel_alpha, 0, frame)
        
        # --- Viết chữ lên Dashboard ---
        # 1. Cột trái: FPS & Đếm số lượng
        y_offset = 40
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.color_stats, self.thickness)
        y_offset += 35
        cv2.putText(frame, "Traffic Count:", (20, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.color_stats, self.thickness)
        y_offset += 30
        
        total = 0
        for class_name, count in sorted(counts.items()):
            text = f"  - {class_name}: {count}"
            cv2.putText(frame, text, (20, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.color_text, self.thickness-1)
            y_offset += 25
            total += count
            
        cv2.putText(frame, f"TOTAL: {total}", (20, y_offset + 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.color_stats, self.thickness)
        
        # 2. Cột phải: Danh sách vi phạm (Real-time)
        if violations:
            v_y_offset = 40
            cv2.putText(frame, f"⚠ VIOLATIONS: {len(violations)}", (w - 330, v_y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.color_violation, self.thickness)
            v_y_offset += 35
            
            for vehicle in violations[:5]:  # Chỉ hiện tối đa 5 xe để tránh tràn bảng
                text = f"#{vehicle.track_id} - {vehicle.violation_lane}"
                cv2.putText(frame, text, (w - 330, v_y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.color_violation, self.thickness-1)
                v_y_offset += 25
                
        return frame
    
    @staticmethod
    def _draw_text_with_background(frame: np.ndarray, text: str, 
                                  position: tuple, color: tuple,
                                  bg_color: tuple = (0, 0, 0),
                                  font_scale: float = 0.6,
                                  alpha: float = 0.6) -> None:
        """Vẽ text có nền mờ (semi-transparent) và kiểm soát tọa độ ngoài khung hình"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 1
        padding = 4
        
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        x, y = position
        
        x1 = x - padding
        y1 = y - text_size[1] - padding
        x2 = x + text_size[0] + padding
        y2 = y + padding
        
        # Clamp: Giới hạn tọa độ vẽ trong kích thước khung hình, chống lỗi 'index out of bounds'
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        if x2 > x1 and y2 > y1:
            sub_img = frame[y1:y2, x1:x2]
            rect = np.full(sub_img.shape, bg_color, dtype=np.uint8)
            res = cv2.addWeighted(sub_img, 1 - alpha, rect, alpha, 0)
            frame[y1:y2, x1:x2] = res
        
        text_y = max(y, text_size[1] + padding)
        cv2.putText(frame, text, (x, text_y), font, font_scale, color, thickness)