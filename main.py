"""
Entry point của ứng dụng Parking Control System
Khởi tạo QApplication, MainWindow, kiểm tra quyền Administrator
"""
import sys
import os
import ctypes
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

from config_manager import ConfigManager
from logger import ParkingLogger
from main_window import MainWindow


def is_admin():
    """Kiểm tra xem ứng dụng có đang chạy với quyền Administrator không"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def main():
    """Hàm main của ứng dụng"""
    # Kiểm tra quyền Administrator
    if not is_admin():
        # Hiển thị cảnh báo nhưng vẫn cho chạy (có thể không ghi được file)
        print("Cảnh báo: Ứng dụng không chạy với quyền Administrator.")
        print("Có thể không thể ghi file vào ổ D:\\")
    
    # Tạo QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Parking Control System")
    app.setOrganizationName("ParkingControl")
    
    # Load config
    try:
        config_manager = ConfigManager("config.json")
    except Exception as e:
        QMessageBox.critical(None, "Lỗi", f"Không thể load cấu hình: {str(e)}")
        sys.exit(1)
    
    # Khởi tạo logger
    log_file = config_manager.get_log_file()
    try:
        logger = ParkingLogger(log_file, level=logging.INFO)
    except Exception as e:
        # Nếu không tạo được logger, vẫn tiếp tục nhưng chỉ log console
        print(f"Không thể tạo logger: {e}")
        logger = ParkingLogger("", level=logging.INFO)
    
    logger.info("=" * 50)
    logger.info("Khởi động ứng dụng Parking Control System")
    logger.info(f"Thư mục lưu ảnh: {config_manager.get_save_directory()}")
    logger.info(f"File log: {log_file}")
    
    # Kiểm tra quyền Administrator
    if is_admin():
        logger.info("Ứng dụng đang chạy với quyền Administrator")
    else:
        logger.warning("Ứng dụng KHÔNG chạy với quyền Administrator - có thể không ghi được file")
    
    # Tạo và hiển thị MainWindow
    try:
        window = MainWindow(config_manager, logger)
        window.show()
        
        # Chạy ứng dụng
        exit_code = app.exec_()
        
        logger.info("Ứng dụng đã thoát")
        sys.exit(exit_code)
    
    except Exception as e:
        error_msg = f"Lỗi khởi tạo ứng dụng: {str(e)}"
        logger.error(error_msg)
        QMessageBox.critical(None, "Lỗi nghiêm trọng", error_msg)
        sys.exit(1)


if __name__ == "__main__":
    main()

