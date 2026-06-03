"""
analyzer.py: Traffic violation detection using spatial analysis
Detects lane violations using cv2.pointPolygonTest against ROI polygons
Does NOT use Deep Learning - pure mathematical spatial logic
"""

import cv2
import numpy as np
from typing import Dict, List, Set
from .datatypes import FrameState, TrackedVehicle


class TrafficAnalyzer:
    """
    Analyzes vehicle positions against lane restrictions
    Uses cv2.pointPolygonTest to determine if vehicle is in a lane
    Detects violations when a vehicle is in a restricted lane
    """
    
    def __init__(self, lane_polygons: Dict[str, np.ndarray], 
                 lane_restrictions: Dict[str, List[str]]):
        self.lane_polygons = lane_polygons
        
        # Tiền xử lý (Pre-compute) danh sách xe cho phép
        # Chuyển đổi list thành TẬP HỢP (Set) và đưa về chữ thường để lookup O(1)
        self.lane_restrictions: Dict[str, Set[str]] = {
            lane: {v.lower() for v in allowed}
            for lane, allowed in lane_restrictions.items()
        }
        
        self.violation_history: Set[int] = set()  # Lưu vết các ID đã vi phạm
        self.current_violations: Dict[int, str] = {}  # Cache trạng thái lỗi hiện tại để chống nhấp nháy UI
    
    def process(self, frame_state: FrameState) -> FrameState:
        """Analyze frame for lane violations"""
        violations = []
        
        for vehicle in frame_state.vehicles:
            # Ép kiểu float cho tọa độ điểm xét duyệt
            test_point = (
                float(vehicle.bottom_center[0]), 
                float(vehicle.bottom_center[1])
            )
            
            detected_lane = ""
            is_violating_now = False
            
            # Kiểm tra xe đang nằm trong làn nào
            for lane_name, polygon in self.lane_polygons.items():
                if cv2.pointPolygonTest(polygon, test_point, measureDist=False) >= 0:
                    detected_lane = lane_name
                    break  # Tìm thấy làn thì dừng vòng lặp ngay
            
            if detected_lane:
                allowed_classes = self.lane_restrictions.get(detected_lane, set())
                
                # Logic vi phạm: Xe không nằm trong danh sách cho phép của làn
                if vehicle.cls_name.lower() not in allowed_classes:
                    is_violating_now = True
                    vehicle.violation_lane = detected_lane
                    vehicle.violation_type = "wrong_lane"
                    
                    self.violation_history.add(vehicle.track_id)
                    self.current_violations[vehicle.track_id] = detected_lane
            
            # Logic chống nhấp nháy (Anti-flickering)
            # Khắc phục đặc tính rung lắc BBox của YOLO trong môi trường giao thông phức tạp
            if is_violating_now:
                vehicle.is_violating = True
                violations.append(vehicle)
            elif vehicle.track_id in self.current_violations:
                vehicle.is_violating = True
                vehicle.violation_lane = self.current_violations[vehicle.track_id]
                vehicle.violation_type = "wrong_lane"
                violations.append(vehicle)
        
        # Dọn dẹp bộ nhớ (Garbage Collection): Xóa cache của các xe đã rời khung hình
        current_track_ids = {v.track_id for v in frame_state.vehicles}
        self.current_violations = {
            tid: lane for tid, lane in self.current_violations.items() 
            if tid in current_track_ids
        }
        
        frame_state.violations = violations
        
        return frame_state
    
    def get_violation_count(self) -> int:
        return len(self.violation_history)