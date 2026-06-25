"""
visualizer.py: Draws bounding boxes, labels, and ROI on the video frame
"""
import cv2
import numpy as np

class Visualizer:
    def __init__(self, draw_roi=True):
        self.draw_roi = draw_roi

    def draw(self, frame_state, lane_polygons):
        img = frame_state.original_frame.copy()

        if self.draw_roi and lane_polygons:
            for lane_name, polygon in lane_polygons.items():
                pts = np.array(polygon, np.int32).reshape((-1, 1, 2))
                cv2.polylines(img, [pts], isClosed=True, color=(0, 165, 255), thickness=2)
                cv2.putText(img, lane_name, tuple(pts[0][0]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        if hasattr(frame_state, 'vehicles'):
            for v in frame_state.vehicles:
                x1, y1, x2, y2 = v.bbox
                
                detected_lane = getattr(v, 'current_lane', None)
                allowed = getattr(v, 'allowed_classes', [])
                
                # Text mặc định
                if detected_lane:
                    label = f"{v.cls_name} | {detected_lane} | PHEP: {','.join(allowed)}"
                else:
                    label = f"{v.cls_name} | NGOAI LAN"

                color = (0, 255, 0) # Xanh lá: Đúng luật

                # [QUAN TRỌNG]: Đổi sang ĐỎ nếu AI báo vi phạm
                if getattr(v, 'is_violating', False):
                    color = (0, 0, 255) # Đỏ
                    label = f"PHAT NGUOI: {v.cls_name} | {detected_lane}"

                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                
                (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(img, (x1, y1 - 20), (x1 + w, y1), color, -1)
                cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                if hasattr(v, 'check_point'):
                    cv2.circle(img, v.check_point, 5, (0, 255, 255), -1)

        frame_state.processed_frame = img
        return img