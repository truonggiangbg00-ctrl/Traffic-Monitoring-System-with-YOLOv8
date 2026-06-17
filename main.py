"""
main.py: Main orchestrator for Real-time Traffic Monitoring System
"""

import cv2
import numpy as np
import time
import sys
import argparse
import queue

# Core logic
from core.datatypes import FrameState, ModelConfig
from core.detector_tracker import DetectorTracker
from core.analyzer import TrafficAnalyzer
from core.counter import TrafficCounter

# Utilities
from utils.config import (
    VIDEO_SOURCE, BASELINE_MODEL_PATH, OPTIMIZED_MODEL_PATH, DEVICE,
    CONFIDENCE_THRESHOLD, IOU_THRESHOLD, LANE_POLYGONS, LANE_RESTRICTIONS,
    DRAW_ROI_POLYGONS, SAVE_OUTPUT_VIDEO, OUTPUT_VIDEO_PATH, MIN_FPS
)
from utils.visualizer import Visualizer
from utils.logger import ViolationLogger

class TrafficMonitoringSystem:
    """Main orchestrator for real-time traffic monitoring pipeline"""
    
    # CẬP NHẬT: Thêm tham số video_path để nhận nguồn động từ GUI
    def __init__(self, video_path=None, model_type='pt', use_optimized=False):
        print("\n" + "="*80)
        print("🚗 REAL-TIME HIGHWAY TRAFFIC MONITORING SYSTEM")
        print("="*80)
        
        self.model_type = model_type
        self.use_optimized = use_optimized
        self.video_path = video_path or VIDEO_SOURCE
        
        self.frame_count = 0
        self.start_time = time.time()
        self.fps_history = []
        
        try:
            self._init_components()
        except Exception as e:
            print(f"\n❌ Initialization failed: {e}")
            raise

    def _init_components(self):
        # 1. Detector
        model_path = OPTIMIZED_MODEL_PATH if self.use_optimized else BASELINE_MODEL_PATH
        print(f"[1/5] Loading detection model ({self.model_type})...")
        config = ModelConfig(
            model_path=model_path, model_type=self.model_type,
            confidence_threshold=CONFIDENCE_THRESHOLD, iou_threshold=IOU_THRESHOLD, device=DEVICE
        )
        self.detector = DetectorTracker(config)
        
        # 2. Logic Analyzers
        print("[2/5] Initializing analyzers & counters...")
        self.analyzer = TrafficAnalyzer(LANE_POLYGONS, LANE_RESTRICTIONS)
        self.counter = TrafficCounter()
        
        # 3. Utilities
        print("[3/5] Initializing I/O utilities...")
        self.visualizer = Visualizer(draw_roi=DRAW_ROI_POLYGONS)
        self.logger = ViolationLogger()
        
        
        # 4. Video Source (Sử dụng đường dẫn động)
        print(f"[4/5] Opening video source: {self.video_path}")
        
        # CẬP NHẬT: Xử lý thông minh để nhận Webcam (số) hoặc File/Link (chuỗi)
        if str(self.video_path).isdigit():
            vid_src = int(self.video_path)  # Webcam ID: 0, 1, 2...
        else:
            vid_src = str(self.video_path)  # Link RTSP hoặc File MP4
            
        self.cap = cv2.VideoCapture(vid_src)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {self.video_path}")
        
        # ===> 3 DÒNG QUAN TRỌNG BỊ THIẾU LÀ Ở ĐÂY <===
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 5. Output Writer
        print("[5/5] Setup video writer...")
        self.video_writer = None
        if SAVE_OUTPUT_VIDEO:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                str(OUTPUT_VIDEO_PATH), fourcc, self.video_fps, (self.video_width, self.video_height)
            )

    def process_frame(self, frame: np.ndarray) -> FrameState:
        # Khởi tạo FrameState
        frame_state = FrameState(frame_id=self.frame_count, original_frame=frame.copy(), timestamp=time.time())
        
        # === PIPELINE CỐT LÕI ===
        frame_state = self.detector.process(frame_state)       # Nhận diện & Theo dõi
        frame_state = self.analyzer.process(frame_state)       # Phân tích vi phạm
        frame_state = self.counter.process(frame_state)        # Đếm lưu lượng
        
        # Đẩy dữ liệu ra Worker ngầm (I/O)
        for viol in frame_state.violations:
            self.logger.log_violation(
                frame_state.frame_id, viol.track_id, viol.cls_name, 
                viol.violation_type, viol.conf, viol.bbox, viol.violation_lane
            )
            self.logger.save_violation_image(
                frame, viol.track_id, viol.bbox, viol.violation_type, frame_state.frame_id
            )
            
        # Vẽ giao diện hiển thị
        frame_state.processed_frame = self.visualizer.draw(frame_state, LANE_POLYGONS)
        frame_state.fps = self.fps_history[-1] if self.fps_history else 0
        return frame_state

    def run(self, display: bool = True):
        """Hàm chạy chế độ Terminal (CLI)"""
        print("\n" + "="*80)
        print("▶ Monitoring Started (Controls: Q=Quit, P=Pause)")
        print("="*80)
        
        paused = False
        try:
            while True:
                if not paused:
                    ret, frame = self.cap.read()
                    if not ret:
                        print("\n✓ Video stream ended.")
                        break
                    
                    frame_start = time.time()
                    frame_state = self.process_frame(frame)
                    process_time = time.time() - frame_start
                    
                    # Đo đạc FPS
                    current_fps = 1.0 / process_time if process_time > 0 else 0
                    self.fps_history.append(current_fps)
                    
                    if display:
                        cv2.imshow("Traffic Monitoring", frame_state.processed_frame)
                    if self.video_writer:
                        self.video_writer.write(frame_state.processed_frame)
                        
                    self.frame_count += 1

                # Xử lý phím tắt
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'): break
                elif key == ord('p'): paused = not paused

        except KeyboardInterrupt:
            print("\n⚠ Interrupted by user")
        finally:
            self.shutdown()

    def shutdown(self):
        """Kịch bản Tắt An Toàn (Graceful Shutdown)"""
        print("\n" + "="*80)
        print("SHUTTING DOWN SYSTEM...")
        
        if hasattr(self, 'cap'): self.cap.release()
        if hasattr(self, 'video_writer') and self.video_writer: self.video_writer.release()
        cv2.destroyAllWindows()
        
        if hasattr(self, 'logger'): self.logger.stop()
        
        total_time = time.time() - self.start_time
        avg_fps = np.mean(self.fps_history) if self.fps_history else 0
        total_veh = self.counter.get_total() if hasattr(self, 'counter') else 0
        total_viol = self.analyzer.get_violation_count() if hasattr(self, 'analyzer') else 0
        
        print(f"\n📊 FINAL REPORT:")
        print(f"  Frames Processed : {self.frame_count}")
        print(f"  Total Time       : {total_time:.1f}s")
        print(f"  Average FPS      : {avg_fps:.1f} (Target Min: {MIN_FPS})")
        print(f"  Total Vehicles   : {total_veh}")
        print(f"  Total Violations : {total_viol}")
        print("="*80)

# ============================================================================
# LUỒNG AI KẾT NỐI VỚI GUI (ĐÃ CẬP NHẬT)
# ============================================================================
def ai_engine_worker(video_source, frame_queue, stats_queue, command_queue, is_running_func):
    """
    Luồng chạy AI thực tế: Chịu trách nhiệm giao tiếp an toàn với GUI.
    """
    system = None
    try:
        # Khởi tạo trực tiếp với video_source từ GUI
        system = TrafficMonitoringSystem(video_path=video_source, model_type='pt', use_optimized=True)
    except Exception as e:
        stats_queue.put({'action': 'engine_stopped', 'error': str(e)})
        return

    try:
        while system.cap.isOpened() and is_running_func():
            # 1. Đọc lệnh cấu hình từ GUI (nếu có)
            try:
                cmd = command_queue.get_nowait()
                if cmd.get("action") == "set_confidence":
                    new_val = cmd.get("value")
                    if hasattr(system, 'detector') and hasattr(system.detector, 'config'):
                        system.detector.config.confidence_threshold = new_val
            except queue.Empty:
                pass

            # 2. Đọc và xử lý Frame
            ret, frame = system.cap.read()
            if not ret: 
                break
            
            frame_start = time.time()
            frame_state = system.process_frame(frame)
            
            process_time = time.time() - frame_start
            current_fps = 1.0 / process_time if process_time > 0 else 0
            
            total_cars = system.counter.get_total() if hasattr(system, 'counter') else 0
            violations = system.analyzer.get_violation_count() if hasattr(system, 'analyzer') else 0
            
            # 3. Đẩy kết quả về GUI
            if not frame_queue.full():
                frame_queue.put(frame_state.processed_frame)
                
            if not stats_queue.full():
                stats_queue.put({
                    'action': 'processing',
                    'fps': current_fps,
                    'total_vehicles': total_cars,
                    'violations': violations
                })
                
    except Exception as e:
        stats_queue.put({'action': 'engine_stopped', 'error': f"Lỗi runtime: {str(e)}"})
    finally:
        if system:
            system.shutdown()
        # Báo cho GUI biết đã dừng an toàn
        stats_queue.put({'action': 'engine_stopped'})

if __name__ == "__main__":
    # Import Dashboard từ thư mục UI
    from ui.dashboard import TrafficDashboard
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--cli', action='store_true', help="Chạy chế độ Terminal (Không mở GUI)")
    parser.add_argument('--model', choices=['pt', 'engine'], default='pt')
    parser.add_argument('--optimized', action='store_true')
    args = parser.parse_args()
    
    if args.cli:
        system = TrafficMonitoringSystem(model_type=args.model, use_optimized=args.optimized)
        system.run(display=True)
    else:
        app = TrafficDashboard(ai_engine_callback=ai_engine_worker)
        app.mainloop()