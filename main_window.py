"""
Giao diện chính của ứng dụng Parking Control System
Layout 2 cột: Làn RA (trái) và Làn VÀO (phải) - Giao diện đơn giản hóa
"""
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QKeyEvent

from camera_widget import CameraWidget
from camera_thread import CameraThread
from config_manager import ConfigManager
from file_manager import FileManager
from logger import ParkingLogger
from sound_player import SoundPlayer


class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng"""
    
    def __init__(self, config_manager: ConfigManager, logger: ParkingLogger):
        super().__init__()
        self.config_manager = config_manager
        self.logger = logger
        
        # Sound player với đường dẫn từ config
        sound_file = config_manager.get("sound_file")
        self.sound_player = SoundPlayer(sound_file)
        
        # File manager
        save_dir = config_manager.get_save_directory()
        self.file_manager = FileManager(save_dir, logger)
        
        # Camera threads và widgets
        self.camera_threads = {}
        self.camera_widgets = {}
        
        # Timer cho đồng hồ
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)  # Cập nhật mỗi giây
        
        self.init_ui()
        self.init_cameras()
        
        # Log khởi động
        self.logger.info("Ứng dụng đã khởi động")
    
    def init_ui(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle("Hệ Thống Quản Lý Bãi Xe - Parking Control System")
        self.setMinimumSize(1600, 900)
        
        # Áp dụng dark theme cho toàn bộ cửa sổ
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)
        
        # Widget trung tâm
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #1e1e1e;")
        
        # Layout chính (dọc: Header + Content)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # === HEADER ===
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # === CONTENT (2 cột) ===
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #1e1e1e;")
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # === LÀN XE RA (Bên trái) ===
        lane_ra_widget = self.create_lane_widget("RA", "XÁC NHẬN XE RA", 
                                                 "#FF4444", "#FF6666", 
                                                 "CAM RA - TRƯỚC", "CAM RA - SAU",
                                                 "(Nhấn SPACE hoặc Click)")
        content_layout.addWidget(lane_ra_widget, 1)
        
        # === LÀN XE VÀO (Bên phải) ===
        lane_vao_widget = self.create_lane_widget("VAO", "XÁC NHẬN XE VÀO", 
                                                  "#4488FF", "#6699FF",
                                                  "CAM VÀO - TRƯỚC", "CAM VÀO - SAU",
                                                  "(Nhấn ENTER hoặc Click)")
        content_layout.addWidget(lane_vao_widget, 1)
        
        main_layout.addWidget(content_widget, 1)
    
    def create_header(self) -> QWidget:
        """Tạo header với tên công ty, đồng hồ, và tên phần mềm"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-bottom: 2px solid #444;
            }
        """)
        header.setFixedHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Tên công ty (góc trái)
        company_label = QLabel("Quản lý bãi xe")  # Có thể thay đổi tên công ty
        company_font = QFont("Arial", 14, QFont.Bold)
        company_label.setFont(company_font)
        company_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(company_label)
        
        # Spacer
        layout.addStretch()
        
        # Đồng hồ (giữa)
        self.clock_label = QLabel()
        clock_font = QFont("Arial", 16, QFont.Bold)
        self.clock_label.setFont(clock_font)
        self.clock_label.setStyleSheet("color: #4CAF50;")
        self.clock_label.setAlignment(Qt.AlignCenter)
        self.update_clock()  # Cập nhật ngay lần đầu
        layout.addWidget(self.clock_label)
        
        # Spacer
        layout.addStretch()
        
        # Tên phần mềm (góc phải)
        app_label = QLabel("Parking Control System")
        app_font = QFont("Arial", 12, QFont.Bold)
        app_label.setFont(app_font)
        app_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(app_label)
        
        return header
    
    def update_clock(self):
        """Cập nhật đồng hồ realtime"""
        now = datetime.now()
        time_str = now.strftime("%d/%m/%Y %H:%M:%S")
        self.clock_label.setText(time_str)
    
    def create_lane_widget(self, lane_key: str, button_text: str, 
                           border_color: str, button_color: str,
                           front_label: str, rear_label: str,
                           shortcut_hint: str) -> QWidget:
        """Tạo widget cho một làn xe với layout mới"""
        lane_widget = QFrame()
        lane_widget.setFrameStyle(QFrame.Box)
        lane_widget.setStyleSheet(f"""
            QFrame {{
                border: 3px solid {border_color};
                background-color: #1e1e1e;
            }}
        """)
        
        layout = QVBoxLayout(lane_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # === PHẦN CAMERA (70% chiều cao) ===
        camera_container = QWidget()
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setSpacing(5)
        camera_layout.setContentsMargins(0, 0, 0, 0)
        
        # Widget camera trước
        front_widget = CameraWidget(f"{lane_key.lower()}_front", front_label, self)
        front_widget.setMinimumHeight(250)
        camera_layout.addWidget(front_widget, 1)
        self.camera_widgets[f"{lane_key.lower()}_front"] = front_widget
        
        # Widget camera sau
        rear_widget = CameraWidget(f"{lane_key.lower()}_rear", rear_label, self)
        rear_widget.setMinimumHeight(250)
        camera_layout.addWidget(rear_widget, 1)
        self.camera_widgets[f"{lane_key.lower()}_rear"] = rear_widget
        
        layout.addWidget(camera_container, 7)  # 70% chiều cao
        
        # === PHẦN NÚT (30% chiều cao) ===
        # Nút bấm lớn
        btn_confirm = QPushButton()
        btn_confirm.setMinimumHeight(100)
        btn_confirm.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_color};
                color: white;
                font-size: 24px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                padding: 15px;
            }}
            QPushButton:hover {{
                background-color: {border_color};
            }}
            QPushButton:pressed {{
                background-color: {border_color};
                border: 3px solid white;
            }}
        """)
        
        # Text nút với 2 dòng (sử dụng \n)
        button_text_full = f"{button_text}\n{shortcut_hint}"
        btn_confirm.setText(button_text_full)
        btn_confirm.setToolTip(f"Phím tắt: {'SPACE' if lane_key == 'RA' else 'ENTER'}")
        
        # Kết nối signal
        btn_confirm.clicked.connect(lambda: self.capture_lane(lane_key))
        
        layout.addWidget(btn_confirm, 3)  # 30% chiều cao
        
        return lane_widget
    
    def keyPressEvent(self, event: QKeyEvent):
        """Xử lý phím tắt"""
        if event.key() == Qt.Key_Space:
            # SPACE cho XE RA
            self.capture_lane("RA")
            event.accept()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # ENTER cho XE VÀO
            self.capture_lane("VAO")
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def init_cameras(self):
        """Khởi tạo và kết nối các camera"""
        camera_keys = ["ra_front", "ra_rear", "vao_front", "vao_rear"]
        
        for camera_key in camera_keys:
            rtsp_url = self.config_manager.get_rtsp_url(camera_key)
            if not rtsp_url:
                self.logger.error(f"Không tìm thấy RTSP URL cho {camera_key}")
                continue
            
            # Tạo camera thread
            thread = CameraThread(rtsp_url, camera_key, reconnect_delay=3)
            thread.error_occurred.connect(
                lambda msg, key=camera_key: self.logger.log_rtsp_connection(key, False, msg)
            )
            thread.status_changed.connect(
                lambda status, key=camera_key: self.on_camera_status_changed(key, status)
            )
            
            self.camera_threads[camera_key] = thread
            
            # Gán thread cho widget
            if camera_key in self.camera_widgets:
                self.camera_widgets[camera_key].set_camera_thread(thread)
            
            # Bắt đầu thread
            thread.start()
            self.logger.info(f"Đã khởi động camera thread: {camera_key}")
    
    @pyqtSlot(str, str)
    def on_camera_status_changed(self, camera_key: str, status: str):
        """Xử lý khi trạng thái camera thay đổi"""
        connected = (status == "connected")
        self.logger.log_rtsp_connection(camera_key, connected)
    
    def capture_lane(self, lane_key: str):
        """Chụp ảnh từ 2 camera của một làn"""
        lane_name = "RA" if lane_key == "RA" else "VAO"
        
        # Lấy frame từ 2 camera
        front_key = f"{lane_key.lower()}_front"
        rear_key = f"{lane_key.lower()}_rear"
        
        front_widget = self.camera_widgets.get(front_key)
        rear_widget = self.camera_widgets.get(rear_key)
        
        if not front_widget or not rear_widget:
            self.logger.error(f"Không tìm thấy camera widget cho làn {lane_name}", lane_name)
            return
        
        front_image = front_widget.get_current_frame()
        rear_image = rear_widget.get_current_frame()
        
        if not front_image or not rear_image:
            self.logger.warning(f"Không có frame để chụp - Làn {lane_name}", lane_name)
            QMessageBox.warning(self, "Cảnh báo", 
                              f"Không thể chụp ảnh. Vui lòng kiểm tra kết nối camera của Làn {lane_name}.")
            return
        
        # Lưu ảnh
        success, front_path, rear_path = self.file_manager.save_capture(
            lane_name, front_image, rear_image
        )
        
        if success:
            # Phát âm thanh
            self.sound_player.play_capture_sound()
            
            # Ghi log
            self.logger.log_capture(lane_name, True, front_path, rear_path)
        else:
            # Ghi log lỗi
            self.logger.log_capture(lane_name, False)
            QMessageBox.critical(self, "Lỗi", 
                               f"Không thể lưu ảnh cho Làn {lane_name}. Vui lòng kiểm tra quyền ghi file.")
    
    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        # Chấp nhận event trước để UI không bị đơ
        event.accept()
        
        # Dừng timer
        if self.clock_timer:
            self.clock_timer.stop()
            self.clock_timer = None
        
        # Cleanup sound player
        if self.sound_player and hasattr(self.sound_player, 'sound_effect'):
            if self.sound_player.sound_effect:
                try:
                    self.sound_player.sound_effect.stop()
                except Exception:
                    pass
        
        # Dừng tất cả camera threads (với timeout)
        for camera_key, thread in list(self.camera_threads.items()):
            try:
                self.logger.info(f"Dừng camera thread: {camera_key}")
                thread.stop()
            except Exception as e:
                self.logger.error(f"Lỗi khi dừng thread {camera_key}: {e}")
        
        self.logger.info("Ứng dụng đã đóng")
