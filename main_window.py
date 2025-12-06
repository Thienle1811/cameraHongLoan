import time
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QMessageBox, QFrame, QSplitter)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QKeyEvent, QColor

from camera_widget import CameraWidget
from camera_thread import CameraThread
from config_manager import ConfigManager
from file_manager import FileManager
from logger import ParkingLogger
from sound_player import SoundPlayer

# --- MODULE MỚI ---
from database import ParkingDatabase
from serial_manager import SerialThread

class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng - Đã tích hợp RFID và Database"""
    
    def __init__(self, config_manager: ConfigManager, logger: ParkingLogger):
        super().__init__()
        self.config_manager = config_manager
        self.logger = logger
        
        # 1. Khởi tạo Database
        db_path = config_manager.get_database_path()
        self.db = ParkingDatabase(db_path)
        
        # 2. Khởi tạo Sound & File Manager
        sound_file = config_manager.get("sound_file")
        self.sound_player = SoundPlayer(sound_file)
        
        save_dir = config_manager.get_save_directory()
        self.file_manager = FileManager(save_dir, logger)
        
        # 3. Biến quản lý Camera và Serial
        self.camera_threads = {}
        self.camera_widgets = {}
        self.serial_threads = []
        
        # Biến UI để cập nhật thông tin thẻ
        self.info_labels = {} 
        self.status_frames = {} 

        # Timer cho đồng hồ
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        
        self.init_ui()
        self.init_cameras()
        self.init_serial_readers()
        
        self.logger.info("Hệ thống đã khởi động hoàn tất")
    
    def init_ui(self):
        """Khởi tạo giao diện người dùng"""
        self.setWindowTitle("Hệ Thống Quản Lý Bãi Xe (RFID Integrated)")
        self.setMinimumSize(1600, 900)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # === HEADER ===
        main_layout.addWidget(self.create_header())
        
        # === CONTENT AREA (Chia đôi màn hình) ===
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # LÀN RA (Trái)
        self.lane_ra_ui = self.create_lane_panel("RA", "LÀN XE RA", "#FF4444")
        content_layout.addWidget(self.lane_ra_ui, 1)
        
        # LÀN VÀO (Phải)
        self.lane_vao_ui = self.create_lane_panel("VAO", "LÀN XE VÀO", "#4488FF")
        content_layout.addWidget(self.lane_vao_ui, 1)
        
        main_layout.addWidget(content_widget, 1)

    def create_header(self):
        """Tạo thanh tiêu đề"""
        header = QFrame()
        header.setStyleSheet("background-color: #2d2d2d; border-bottom: 2px solid #555;")
        header.setFixedHeight(60)
        layout = QHBoxLayout(header)
        
        lbl_company = QLabel("BÃI XE THÔNG MINH")
        lbl_company.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(lbl_company)
        
        layout.addStretch()
        
        self.clock_label = QLabel()
        self.clock_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.clock_label.setStyleSheet("color: #00FF00;")
        self.update_clock()
        layout.addWidget(self.clock_label)
        
        layout.addStretch()
        
        lbl_app = QLabel("Parking Control System v2.0")
        lbl_app.setFont(QFont("Arial", 12))
        layout.addWidget(lbl_app)
        
        return header

    def create_lane_panel(self, lane_key, title, color_code):
        """Tạo giao diện cho một làn xe"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        self.status_frames[lane_key] = panel 
        panel.setStyleSheet(f"border: 2px solid {color_code}; background-color: #252525;")
        
        layout = QVBoxLayout(panel)
        
        # 1. Tiêu đề làn
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setFont(QFont("Arial", 16, QFont.Bold))
        lbl_title.setStyleSheet(f"background-color: {color_code}; color: white; padding: 5px;")
        layout.addWidget(lbl_title)
        
        # 2. Camera (Trước & Sau)
        cam_front = CameraWidget(f"{lane_key.lower()}_front", "CAM TRƯỚC", self)
        cam_rear = CameraWidget(f"{lane_key.lower()}_rear", "CAM SAU", self)
        
        self.camera_widgets[f"{lane_key.lower()}_front"] = cam_front
        self.camera_widgets[f"{lane_key.lower()}_rear"] = cam_rear
        
        layout.addWidget(cam_front, 1)
        layout.addWidget(cam_rear, 1)
        
        # 3. Khu vực thông tin thẻ
        info_group = QFrame()
        info_group.setStyleSheet("background-color: #333; border-radius: 5px;")
        info_layout = QVBoxLayout(info_group)
        
        lbl_card_code = QLabel("Mã thẻ: ---")
        lbl_card_code.setFont(QFont("Arial", 12, QFont.Bold))
        
        lbl_status = QLabel("Trạng thái: Đang chờ...")
        lbl_status.setFont(QFont("Arial", 14, QFont.Bold))
        lbl_status.setWordWrap(True)
        
        lbl_price = QLabel("") 
        lbl_price.setFont(QFont("Arial", 18, QFont.Bold))
        lbl_price.setStyleSheet("color: yellow;")
        
        info_layout.addWidget(lbl_card_code)
        info_layout.addWidget(lbl_status)
        info_layout.addWidget(lbl_price)
        
        self.info_labels[lane_key] = {
            "code": lbl_card_code,
            "status": lbl_status,
            "price": lbl_price
        }
        
        # 4. Nút bấm thủ công
        btn_manual = QPushButton(f"CHỤP ẢNH THỦ CÔNG ({'SPACE' if lane_key == 'RA' else 'ENTER'})")
        btn_manual.setStyleSheet(f"background-color: {color_code}; font-weight: bold; padding: 10px;")
        btn_manual.clicked.connect(lambda: self.process_transaction(lane_key, "MANUAL_TRIGGER"))
        layout.addWidget(btn_manual)
        
        return panel

    def init_cameras(self):
        """Khởi tạo luồng camera RTSP"""
        camera_keys = ["ra_front", "ra_rear", "vao_front", "vao_rear"]
        for key in camera_keys:
            url = self.config_manager.get_rtsp_url(key)
            if url:
                thread = CameraThread(url, key)
                # --- ĐÂY LÀ ĐOẠN ĐÃ FIX LỖI TYPE ERROR ---
                thread.status_changed.connect(lambda status, k=key: self.on_camera_status(status, k))
                
                self.camera_threads[key] = thread
                if key in self.camera_widgets:
                    self.camera_widgets[key].set_camera_thread(thread)
                thread.start()

    def init_serial_readers(self):
        """Khởi tạo luồng đọc thẻ RFID"""
        serial_cfg = self.config_manager.get_serial_config()
        
        if serial_cfg.get("port_in"):
            t_in = SerialThread(serial_cfg["port_in"], serial_cfg["baud_rate"], "VAO")
            t_in.rfid_scanned.connect(self.on_rfid_scanned)
            t_in.error_occurred.connect(lambda msg: self.logger.error(msg))
            self.serial_threads.append(t_in)
            t_in.start()
            
        if serial_cfg.get("port_out"):
            t_out = SerialThread(serial_cfg["port_out"], serial_cfg["baud_rate"], "RA")
            t_out.rfid_scanned.connect(self.on_rfid_scanned)
            t_out.error_occurred.connect(lambda msg: self.logger.error(msg))
            self.serial_threads.append(t_out)
            t_out.start()

    @pyqtSlot(str, str)
    def on_rfid_scanned(self, lane, card_code):
        self.logger.info(f"Phát hiện thẻ {card_code} tại làn {lane}")
        self.process_transaction(lane, card_code)

    def process_transaction(self, lane, card_code):
        front_key = f"{lane.lower()}_front"
        rear_key = f"{lane.lower()}_rear"
        
        img_front = self.camera_widgets[front_key].get_current_frame()
        img_rear = self.camera_widgets[rear_key].get_current_frame()
        
        if not img_front or not img_rear:
            self.show_message(lane, "LỖI CAMERA", "Không lấy được hình ảnh!", False)
            return

        success, path_front, path_rear = self.file_manager.save_capture(lane, img_front, img_rear)
        if not success:
            self.show_message(lane, "LỖI LƯU FILE", "Không thể ghi ảnh vào ổ cứng", False)
            return

        if lane == "VAO":
            self.handle_check_in(card_code, path_front, path_rear)
        else:
            self.handle_check_out(card_code, path_front, path_rear)

    def handle_check_in(self, card_code, img_front, img_rear):
        success, msg = self.db.check_in(card_code, img_front, img_rear)
        self.show_message("VAO", card_code, msg, success)
        if success:
            self.logger.info(f"Xe vào thành công: {card_code}")

    def handle_check_out(self, card_code, img_front, img_rear):
        success, msg, info = self.db.check_out(card_code, img_front, img_rear)
        if success:
            price = info.get('price', 0)
            msg_full = f"{msg}\nGiờ vào: {info['checkin_time']}"
            self.show_message("RA", card_code, msg_full, True, price)
            self.logger.info(f"Xe ra thành công: {card_code}, Phí: {price}")
        else:
            self.show_message("RA", card_code, msg, False)

    def show_message(self, lane, code, status, is_success, price=None):
        labels = self.info_labels.get(lane)
        frame = self.status_frames.get(lane)
        
        if not labels or not frame:
            return
            
        labels["code"].setText(f"Mã thẻ: {code}")
        labels["status"].setText(status)
        
        if price is not None:
            labels["price"].setText(f"THU TIỀN: {price:,} VNĐ")
        else:
            labels["price"].setText("")

        if is_success:
            style = "border: 4px solid #00FF00; background-color: #252525;"
            labels["status"].setStyleSheet("color: #00FF00;")
            self.sound_player.play_capture_sound() 
        else:
            style = "border: 4px solid #FF0000; background-color: #330000;"
            labels["status"].setStyleSheet("color: #FF0000; font-weight: bold; font-size: 16px;")
            
        frame.setStyleSheet(style)
        QTimer.singleShot(5000, lambda: self.reset_ui(lane))

    def reset_ui(self, lane):
        frame = self.status_frames.get(lane)
        labels = self.info_labels.get(lane)
        if frame:
            color = "#FF4444" if lane == "RA" else "#4488FF"
            frame.setStyleSheet(f"border: 2px solid {color}; background-color: #252525;")
        if labels:
            labels["code"].setText("Mã thẻ: ---")
            labels["status"].setText("Đang chờ xe...")
            labels["status"].setStyleSheet("color: white;")
            labels["price"].setText("")

    def update_clock(self):
        now = datetime.now()
        self.clock_label.setText(now.strftime("%d/%m/%Y %H:%M:%S"))

    def on_camera_status(self, status, key):
        pass

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            self.process_transaction("RA", "TEST_KEY_RA")
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.process_transaction("VAO", "TEST_KEY_VAO")
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        for t in self.serial_threads:
            t.stop()
        for t in self.camera_threads.values():
            t.stop()
        event.accept()