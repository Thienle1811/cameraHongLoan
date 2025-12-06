import time
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QAction, QFileDialog, QMessageBox, QMenuBar)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QKeyEvent

from camera_widget import CameraWidget
from camera_thread import CameraThread
from config_manager import ConfigManager
from file_manager import FileManager
from logger import ParkingLogger
from sound_player import SoundPlayer

# Import module Database & Serial
from database import ParkingDatabase
from serial_manager import SerialThread

class MainWindow(QMainWindow):
    """
    Cửa sổ chính - Phiên bản Tự động hóa (Touchless)
    - Tích hợp PostgreSQL
    - Auto Report 00:00
    - Popup thu tiền khách vãng lai
    - Cảnh báo âm thanh (Không Barie)
    """
    
    def __init__(self, config_manager: ConfigManager, logger: ParkingLogger):
        super().__init__()
        self.config_manager = config_manager
        self.logger = logger
        
        # 1. Kết nối Database PostgreSQL
        db_config = config_manager.get_database_config()
        self.db = ParkingDatabase(db_config)
        
        # 2. Khởi tạo tiện ích
        sound_file = config_manager.get("sound_file")
        self.sound_player = SoundPlayer(sound_file)
        
        save_dir = config_manager.get_save_directory()
        self.file_manager = FileManager(save_dir, logger)
        
        # 3. Quản lý Thread
        self.camera_threads = {}
        self.camera_widgets = {}
        self.serial_threads = []
        
        # Biến UI
        self.info_labels = {} 
        self.status_frames = {} 

        # 4. Timer Đồng hồ & Báo cáo tự động
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock_and_report)
        self.clock_timer.start(1000) # Check mỗi giây
        
        self.last_report_date = None # Tránh xuất lặp lại

        self.init_ui()
        self.init_cameras()
        self.init_serial_readers()
        
        self.logger.info("Hệ thống khởi động hoàn tất (Mode: No Barrier + Auto Popup)")
    
    def init_ui(self):
        self.setWindowTitle("Hệ Thống Quản Lý Bãi Xe (Auto Touchless)")
        self.setMinimumSize(1600, 900)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
        # === MENU BAR ===
        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: #2d2d2d; color: white;")
        
        sys_menu = menubar.addMenu('Hệ Thống')
        
        import_action = QAction('Nhập danh sách thẻ tháng (CSV)', self)
        import_action.triggered.connect(self.import_cards)
        sys_menu.addAction(import_action)
        
        # === GIAO DIỆN CHÍNH ===
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        main_layout.addWidget(self.create_header())
        
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

    def import_cards(self):
        """Nhập thẻ tháng từ CSV"""
        fname, _ = QFileDialog.getOpenFileName(self, 'Chọn file CSV', '', 'CSV Files (*.csv)')
        if fname:
            success, msg = self.db.import_from_csv(fname)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.logger.info(f"Import CSV thành công: {fname}")
            else:
                QMessageBox.critical(self, "Lỗi", msg)

    def create_header(self):
        header = QFrame()
        header.setStyleSheet("background-color: #2d2d2d; border-bottom: 2px solid #555;")
        header.setFixedHeight(60)
        layout = QHBoxLayout(header)
        
        lbl_company = QLabel("BÃI XE HỒNG LOAN")
        lbl_company.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(lbl_company)
        
        layout.addStretch()
        self.clock_label = QLabel()
        self.clock_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.clock_label.setStyleSheet("color: #00FF00;")
        self.update_clock_and_report() # Update lần đầu
        layout.addWidget(self.clock_label)
        layout.addStretch()
        
        return header

    def create_lane_panel(self, lane_key, title, color_code):
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        self.status_frames[lane_key] = panel 
        panel.setStyleSheet(f"border: 2px solid {color_code}; background-color: #252525;")
        
        layout = QVBoxLayout(panel)
        
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setFont(QFont("Arial", 16, QFont.Bold))
        lbl_title.setStyleSheet(f"background-color: {color_code}; color: white; padding: 5px;")
        layout.addWidget(lbl_title)
        
        cam_front = CameraWidget(f"{lane_key.lower()}_front", "CAM TRƯỚC", self)
        cam_rear = CameraWidget(f"{lane_key.lower()}_rear", "CAM SAU", self)
        
        self.camera_widgets[f"{lane_key.lower()}_front"] = cam_front
        self.camera_widgets[f"{lane_key.lower()}_rear"] = cam_rear
        
        layout.addWidget(cam_front, 1)
        layout.addWidget(cam_rear, 1)
        
        # Khu vực thông tin
        info_group = QFrame()
        info_group.setStyleSheet("background-color: #333; border-radius: 5px;")
        info_layout = QVBoxLayout(info_group)
        
        lbl_card_code = QLabel("Mã thẻ: ---")
        lbl_card_code.setFont(QFont("Arial", 12, QFont.Bold))
        
        lbl_status = QLabel("Trạng thái: Đang chờ...")
        lbl_status.setFont(QFont("Arial", 14, QFont.Bold))
        lbl_status.setWordWrap(True)
        
        lbl_price = QLabel("") 
        lbl_price.setFont(QFont("Arial", 26, QFont.Bold))
        lbl_price.setStyleSheet("color: yellow;")
        
        info_layout.addWidget(lbl_card_code)
        info_layout.addWidget(lbl_status)
        info_layout.addWidget(lbl_price)
        
        self.info_labels[lane_key] = {
            "code": lbl_card_code,
            "status": lbl_status,
            "price": lbl_price
        }
        
        # Nút bấm thủ công (Backup)
        btn_manual = QPushButton(f"CHỤP THỦ CÔNG ({'SPACE' if lane_key == 'RA' else 'ENTER'})")
        btn_manual.setStyleSheet(f"background-color: {color_code}; font-weight: bold; padding: 10px;")
        btn_manual.clicked.connect(lambda: self.process_transaction(lane_key, "MANUAL_TRIGGER"))
        layout.addWidget(btn_manual)
        
        return panel

    def init_cameras(self):
        camera_keys = ["ra_front", "ra_rear", "vao_front", "vao_rear"]
        for key in camera_keys:
            url = self.config_manager.get_rtsp_url(key)
            if url:
                thread = CameraThread(url, key)
                thread.status_changed.connect(lambda status, k=key: self.on_camera_status(status, k))
                self.camera_threads[key] = thread
                if key in self.camera_widgets:
                    self.camera_widgets[key].set_camera_thread(thread)
                thread.start()

    def init_serial_readers(self):
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
        self.logger.info(f"Quẹt thẻ: {card_code} tại làn {lane}")
        # Tự động thực hiện quy trình khi nhận thẻ
        self.process_transaction(lane, card_code)

    def process_transaction(self, lane, card_code):
        """Xử lý logic chính: Chụp ảnh -> Lưu File -> Gọi Database -> Hiện Popup"""
        
        # 1. Chụp ảnh từ Camera
        front_key = f"{lane.lower()}_front"
        rear_key = f"{lane.lower()}_rear"
        img_front = self.camera_widgets[front_key].get_current_frame()
        img_rear = self.camera_widgets[rear_key].get_current_frame()
        
        if not img_front or not img_rear:
            self.show_message(lane, "LỖI CAMERA", "Mất tín hiệu hình ảnh!", False)
            return

        # 2. Lưu ảnh (Format tên file: HH-MM-SS_DD-MM-YYYY...)
        success, path_front, path_rear = self.file_manager.save_capture(lane, card_code, img_front, img_rear)
        if not success:
            self.show_message(lane, "LỖI Ổ CỨNG", "Không lưu được file ảnh", False)
            return

        # 3. Xử lý nghiệp vụ
        if lane == "VAO":
            self.handle_check_in(card_code, path_front, path_rear)
        else:
            self.handle_check_out(card_code, path_front, path_rear)

    def handle_check_in(self, card_code, img_front, img_rear):
        """Xử lý xe vào"""
        success, msg = self.db.check_in(card_code, img_front, img_rear)
        self.show_message("VAO", card_code, msg, success)
        
        if success:
            # Phát loa Bíp xác nhận
            self.sound_player.play_capture_sound()
        else:
            # Cảnh báo âm thanh lỗi (nếu có file sound lỗi, tạm thời dùng beep)
            # self.sound_player.play_error() 
            pass

    def handle_check_out(self, card_code, img_front, img_rear):
        """Xử lý xe ra - Có Popup thu tiền"""
        success, msg, info = self.db.check_out(card_code, img_front, img_rear)
        
        if success:
            price = info.get('price', 0)
            v_type = info.get('type', 'DAY')
            type_display = "XE THÁNG" if v_type == 'MONTH' else "VÃNG LAI"
            
            # Hiển thị thông tin lên giao diện trước
            msg_full = f"{type_display}\nVào: {info['checkin_time']}"
            self.show_message("RA", card_code, msg_full, True, price)
            self.sound_player.play_capture_sound()
            
            # === LOGIC POPUP THU TIỀN ===
            # Chỉ hiện popup nếu là khách vãng lai (có phí)
            if v_type == 'DAY':
                self.show_payment_popup(price, card_code)
            
        else:
            self.show_message("RA", card_code, msg, False)

    def show_payment_popup(self, price, card_code):
        """Hiển thị hộp thoại thu tiền bắt buộc"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("THU TIỀN KHÁCH VÃNG LAI")
        msg_box.setText(f"Xe Vãng Lai - Mã: {card_code}")
        msg_box.setInformativeText(f"Vui lòng thu phí:\n\n{price:,} VNĐ")
        
        # Tăng kích thước font chữ trong popup
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        msg_box.setFont(font)
        
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.button(QMessageBox.Ok).setText("Đã Thu Tiền")
        
        # Hộp thoại này sẽ chặn tương tác cho đến khi bấm OK
        msg_box.exec_()

    def show_message(self, lane, code, status, is_success, price=None):
        """Cập nhật giao diện"""
        labels = self.info_labels.get(lane)
        frame = self.status_frames.get(lane)
        if not labels or not frame: return
            
        labels["code"].setText(f"Mã: {code}")
        labels["status"].setText(status)
        
        if price is not None:
            labels["price"].setText(f"{price:,} VNĐ")
        else:
            labels["price"].setText("")

        if is_success:
            style = "border: 4px solid #00FF00; background-color: #252525;"
            labels["status"].setStyleSheet("color: #00FF00;")
        else:
            style = "border: 4px solid #FF0000; background-color: #330000;"
            labels["status"].setStyleSheet("color: #FF0000; font-weight: bold;")
            
        frame.setStyleSheet(style)
        
        # Reset màu sau 5s (hoặc giữ nguyên nếu muốn)
        QTimer.singleShot(10000, lambda: self.reset_ui(lane))

    def reset_ui(self, lane):
        frame = self.status_frames.get(lane)
        labels = self.info_labels.get(lane)
        if frame:
            color = "#FF4444" if lane == "RA" else "#4488FF"
            frame.setStyleSheet(f"border: 2px solid {color}; background-color: #252525;")
        if labels:
            labels["code"].setText("Mã thẻ: ---")
            labels["status"].setText("Mời quẹt thẻ...")
            labels["status"].setStyleSheet("color: white;")
            labels["price"].setText("")

    def update_clock_and_report(self):
        """Cập nhật đồng hồ và kiểm tra giờ báo cáo"""
        now = datetime.now()
        # 1. Cập nhật đồng hồ
        self.clock_label.setText(now.strftime("%d/%m/%Y %H:%M:%S"))
        
        # 2. Kiểm tra auto report lúc 00:00:xx
        if now.hour == 0 and now.minute == 0:
            current_date_str = now.strftime("%Y-%m-%d")
            
            # Chỉ xuất 1 lần mỗi ngày
            if self.last_report_date != current_date_str:
                self.logger.info("Bắt đầu xuất báo cáo tự động...")
                success, msg = self.db.export_daily_report()
                if success:
                    self.logger.info(msg)
                else:
                    self.logger.error(msg)
                
                self.last_report_date = current_date_str
    
    def on_camera_status(self, status, key):
        pass

    def keyPressEvent(self, event: QKeyEvent):
        # Phím tắt thủ công (dự phòng)
        if event.key() == Qt.Key_Space:
            self.process_transaction("RA", "TEST_KEY_RA")
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.process_transaction("VAO", "TEST_KEY_VAO")
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        for t in self.serial_threads: t.stop()
        for t in self.camera_threads.values(): t.stop()
        event.accept()