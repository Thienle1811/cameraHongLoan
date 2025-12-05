"""
Widget hiển thị video từ camera
Xử lý click để capture, hiển thị trạng thái kết nối
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QFont
from camera_thread import CameraThread


class CameraWidget(QLabel):
    """Widget hiển thị video stream từ camera"""
    
    # Signal khi click vào widget
    clicked = pyqtSignal()
    
    def __init__(self, camera_key: str = "", label_text: str = "", parent=None):
        """
        Khởi tạo CameraWidget
        
        Args:
            camera_key: Tên camera (để hiển thị)
            label_text: Nhãn hiển thị ở góc trên camera (ví dụ: "CAM RA - TRƯỚC")
            parent: Widget cha
        """
        super().__init__(parent)
        self.camera_key = camera_key
        self.label_text = label_text
        self.camera_thread: CameraThread = None
        self.status = "disconnected"
        
        # Cấu hình widget
        self.setMinimumSize(640, 360)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: black; border: 2px solid gray;")
        self.setText(f"Camera {camera_key}\nĐang kết nối...")
        self.setWordWrap(True)
        
        # Cho phép click
        self.setCursor(Qt.PointingHandCursor)
    
    def set_camera_thread(self, thread: CameraThread):
        """Gán camera thread và kết nối signals"""
        self.camera_thread = thread
        thread.frame_ready.connect(self.update_frame)
        thread.status_changed.connect(self.update_status)
    
    def update_frame(self, qimage: QImage):
        """Cập nhật frame hiển thị"""
        if qimage:
            # Scale ảnh để vừa với widget
            scaled_pixmap = QPixmap.fromImage(qimage).scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
    
    def update_status(self, status: str):
        """Cập nhật trạng thái kết nối"""
        self.status = status
        
        if status == "connected":
            # Ẩn text khi đã kết nối
            pass
        elif status == "connecting":
            self.setText(f"Camera {self.camera_key}\nĐang kết nối...")
            self.setPixmap(QPixmap())
        elif status == "disconnected":
            self.setText(f"Camera {self.camera_key}\nMất kết nối")
            self.setPixmap(QPixmap())
        elif status == "error":
            self.setText(f"Camera {self.camera_key}\nLỗi kết nối")
            self.setPixmap(QPixmap())
    
    def mousePressEvent(self, event):
        """Xử lý sự kiện click chuột"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def get_current_frame(self):
        """Lấy frame hiện tại (để chụp ảnh)"""
        if self.camera_thread:
            return self.camera_thread.get_last_frame()
        return None
    
    def get_status(self) -> str:
        """Lấy trạng thái hiện tại"""
        return self.status
    
    def paintEvent(self, event):
        """Vẽ overlay trạng thái và nhãn lên widget"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Vẽ nhãn camera ở góc trên bên trái (nếu có)
        if self.label_text:
            font = QFont("Arial", 12, QFont.Bold)
            painter.setFont(font)
            font_metrics = painter.fontMetrics()
            text_width = font_metrics.width(self.label_text)
            text_height = font_metrics.height()
            
            # Nền nhãn (bán trong suốt)
            label_bg = QColor(0, 0, 0, 180)  # Đen bán trong suốt
            padding = 8
            painter.fillRect(10, 10, text_width + padding * 2, text_height + padding, label_bg)
            
            # Text nhãn
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(10 + padding, 10 + padding + text_height - font_metrics.descent(), self.label_text)
        
        # Vẽ overlay trạng thái ở góc trên bên phải (nếu không connected)
        if self.status != "connected":
            # Màu nền overlay
            if self.status == "connecting":
                color = QColor(255, 165, 0, 200)  # Cam
            elif self.status == "error":
                color = QColor(255, 0, 0, 200)  # Đỏ
            else:
                color = QColor(128, 128, 128, 200)  # Xám
            
            painter.fillRect(self.width() - 130, 10, 120, 30, color)
            
            # Text trạng thái
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Arial", 10, QFont.Bold)
            painter.setFont(font)
            
            status_text = {
                "connecting": "Đang kết nối...",
                "disconnected": "Mất kết nối",
                "error": "Lỗi"
            }.get(self.status, "")
            
            painter.drawText(self.width() - 125, 30, status_text)
        
        painter.end()

