"""
counter.py: Traffic flow counting logic
Counts unique vehicles passing through detection area
"""

from typing import Dict, Set
from collections import defaultdict
from .datatypes import FrameState
from utils.config import MIN_DETECTION_FRAMES 


class TrafficCounter:
    """
    Counts unique vehicles by class type
    Ensures each tracked vehicle is counted only once
    """
    
    def __init__(self):
        self.counts: Dict[str, int] = defaultdict(int)
        
        self.counted_ids: Set[int] = set()              
        self.id_last_seen: Dict[int, int] = {}          
        self.frame_count = 0                            
        
        # Bộ đệm lọc nhiễu (Debouncing buffer)
        self.track_buffer: Dict[int, int] = defaultdict(int) 
        
        self.total_vehicles = 0
    
    def process(self, frame_state: FrameState) -> FrameState:
        self.frame_count += 1
        current_frame_ids = set()
        
        for vehicle in frame_state.vehicles:
            tid = vehicle.track_id
            cls_name = vehicle.cls_name.lower() 
            current_frame_ids.add(tid)
            
            # Xe đã đếm -> Chỉ cập nhật thời gian nhìn thấy lần cuối
            if tid in self.counted_ids:
                self.id_last_seen[tid] = self.frame_count
                continue
            
            # Xe chưa đếm -> Đưa vào bộ đệm tích lũy
            self.track_buffer[tid] += 1
            
            # Vượt ngưỡng tin cậy -> Ghi nhận đếm
            if self.track_buffer[tid] >= MIN_DETECTION_FRAMES:
                self.counts[cls_name] += 1
                self.total_vehicles += 1
                
                self.counted_ids.add(tid)
                self.id_last_seen[tid] = self.frame_count
                
                if tid in self.track_buffer:
                    del self.track_buffer[tid]
        
        # Chu kỳ dọn rác RAM (mỗi 300 frames)
        if self.frame_count % 300 == 0:
            self._cleanup_memory(current_frame_ids)
        
        frame_state.counts = dict(self.counts)
        
        return frame_state
    
    def _cleanup_memory(self, current_frame_ids: Set[int]):
        """Giải phóng RAM bằng cách xóa thông tin các ID đã biến mất lâu"""
        max_idle_frames = 900  # Khoảng 30s với video 30FPS
        
        for tid in list(self.counted_ids):
            if tid not in current_frame_ids:
                last_seen = self.id_last_seen.get(tid, 0)
                if self.frame_count - last_seen > max_idle_frames:
                    self.counted_ids.remove(tid)
                    if tid in self.id_last_seen:
                        del self.id_last_seen[tid]
        
        for tid in list(self.track_buffer.keys()):
            if tid not in current_frame_ids:
                del self.track_buffer[tid]

    def get_counts(self) -> Dict[str, int]:
        return dict(self.counts)
    
    def get_total(self) -> int:
        return self.total_vehicles
    
    def reset(self):
        self.counts.clear()
        self.counted_ids.clear()
        self.id_last_seen.clear()
        self.track_buffer.clear()
        self.total_vehicles = 0
        self.frame_count = 0