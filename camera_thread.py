"""
QThread xử lý RTSP stream từ camera
Tự động reconnect khi mất kết nối, emit frame và status signals
"""
import cv2
import time
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from typing import Optional


class CameraThread(QThread):
    """Thread xử lý video stream từ camera RTSP"""
    
    # Signals
    frame_ready = pyqtSignal(QImage)  # Emit frame khi có ảnh mới
    status_changed = pyqtSignal(str)  # Emit trạng thái: "connecting", "connected", "disconnected", "error"
    error_occurred = pyqtSignal(str)  # Emit thông báo lỗi
    
    def __init__(self, rtsp_url: str, camera_key: str = "", reconnect_delay: int = 3):
        """
        Khởi tạo CameraThread
        
        Args:
            rtsp_url: Đường dẫn RTSP
            camera_key: Tên camera (để log)
            reconnect_delay: Thời gian chờ trước khi reconnect (giây)
        """
        super().__init__()
        self.rtsp_url = rtsp_url
        self.camera_key = camera_key
        self.reconnect_delay = reconnect_delay
        self.running = False
        self.cap: Optional[cv2.VideoCapture] = None
        self.current_status = "disconnected"
        self.last_frame: Optional[QImage] = None
    
    def run(self):
        """Chạy thread, kết nối và đọc frame từ RTSP"""
        self.running = True
        
        while self.running:
            try:
                # Kết nối RTSP
                self._update_status("connecting")
                self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                
                # Cấu hình buffer nhỏ để giảm độ trễ
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if not self.cap.isOpened():
                    self._update_status("error")
                    self.error_occurred.emit(f"Không thể mở RTSP: {self.rtsp_url}")
                    time.sleep(self.reconnect_delay)
                    continue
                
                self._update_status("connected")
                
                # Đọc frame liên tục
                while self.running and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    
                    if not ret:
                        # Mất kết nối
                        self._update_status("disconnected")
                        break
                    
                    # Chuyển đổi frame sang QImage
                    qimage = self._cv2_to_qimage(frame)
                    if qimage:
                        self.last_frame = qimage
                        self.frame_ready.emit(qimage)
                    
                    # Điều chỉnh tốc độ đọc frame (khoảng 30 FPS)
                    time.sleep(0.033)
                
                # Đóng kết nối
                if self.cap:
                    self.cap.release()
                    self.cap = None
                
                # Nếu đang chạy nhưng mất kết nối, chờ và reconnect
                if self.running:
                    self._update_status("disconnected")
                    time.sleep(self.reconnect_delay)
            
            except Exception as e:
                self._update_status("error")
                error_msg = f"Lỗi camera {self.camera_key}: {str(e)}"
                self.error_occurred.emit(error_msg)
                if self.cap:
                    try:
                        self.cap.release()
                    except:
                        pass
                    self.cap = None
                time.sleep(self.reconnect_delay)
    
    def _update_status(self, status: str):
        """Cập nhật trạng thái và emit signal"""
        if self.current_status != status:
            self.current_status = status
            self.status_changed.emit(status)
    
    def _cv2_to_qimage(self, frame):
        """Chuyển đổi OpenCV frame (BGR) sang QImage (RGB)"""
        try:
            if frame is None or frame.size == 0:
                return None
            
            # Chuyển BGR sang RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            return qt_image
        except Exception as e:
            return None
    
    def stop(self):
        """Dừng thread"""
        self.running = False
        
        # Đóng camera capture trước
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None
        
        # Chờ thread kết thúc với timeout (3 giây)
        if self.isRunning():
            self.wait(3000)  # Timeout 3 giây
            if self.isRunning():
                # Nếu thread vẫn chạy sau timeout, terminate nó
                self.terminate()
                self.wait(1000)  # Chờ thêm 1 giây để terminate hoàn tất
    
    def get_last_frame(self) -> Optional[QImage]:
        """Lấy frame cuối cùng (để chụp ảnh)"""
        return self.last_frame
    
    def get_status(self) -> str:
        """Lấy trạng thái hiện tại"""
        return self.current_status

