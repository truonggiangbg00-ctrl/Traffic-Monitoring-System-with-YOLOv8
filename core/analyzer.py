"""
analyzer.py: Traffic violation detection using spatial analysis
"""

import cv2
import numpy as np
from .datatypes import FrameState, TrackedVehicle, Violation

class TrafficAnalyzer:
    def __init__(self, lane_polygons: dict, lane_restrictions: dict):
        self.lane_polygons = {}
        if lane_polygons:
            for name, pts in lane_polygons.items():
                self.lane_polygons[name] = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))

        self.lane_restrictions = {}
        if lane_restrictions:
            for lane, allowed_classes in lane_restrictions.items():
                self.lane_restrictions[lane] = [cls.lower() for cls in allowed_classes]

        self.violation_history = set()

    def process(self, frame_state: FrameState) -> FrameState:
        if not hasattr(frame_state, 'vehicles') or not frame_state.vehicles:
            return frame_state

        for vehicle in frame_state.vehicles:
            vehicle_id = vehicle.track_id
            cls_name_lower = vehicle.cls_name.strip().lower()

            x1, y1, x2, y2 = vehicle.bbox
            check_y = int(y2 - (y2 - y1) * 0.2)
            check_point = (int((x1 + x2) / 2), check_y)
            vehicle.check_point = check_point

            current_lane = None
            for lane_name, polygon in self.lane_polygons.items():
                if cv2.pointPolygonTest(polygon, check_point, False) >= 0:
                    current_lane = lane_name
                    break
            
            # Lưu lại tên làn để in ra GUI
            vehicle.current_lane = current_lane

            if current_lane and current_lane in self.lane_restrictions:
                allowed_classes = self.lane_restrictions[current_lane]
                # Lưu lại luật lệ để in ra GUI
                vehicle.allowed_classes = allowed_classes

                if cls_name_lower not in allowed_classes:
                    vehicle.is_violating = True
                    vehicle.violation_lane = current_lane
                    vehicle.violation_type = "Đi Sai Làn"

                    if vehicle_id not in self.violation_history:
                        viol = Violation(
                            track_id=vehicle_id,
                            cls_name=vehicle.cls_name,
                            violation_type="Đi Sai Làn",
                            conf=vehicle.conf,
                            bbox=vehicle.bbox,
                            violation_lane=current_lane
                        )
                        frame_state.violations.append(viol)
                        self.violation_history.add(vehicle_id)

        return frame_state

    def get_violation_count(self):
        return len(self.violation_history)