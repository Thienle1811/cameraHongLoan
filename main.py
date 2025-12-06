import sys
import os
import ctypes
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox

from config_manager import ConfigManager
from logger import ParkingLogger
from main_window import MainWindow

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    # Kiểm tra Admin để có quyền ghi file ổ D
    if not is_admin():
        print("Cảnh báo: Nên chạy ứng dụng với quyền Administrator để ghi file ổn định.")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Parking Control System")
    
    # Load config
    try:
        config_manager = ConfigManager("config.json")
    except Exception as e:
        QMessageBox.critical(None, "Lỗi", f"Lỗi config: {str(e)}")
        sys.exit(1)
    
    # Logger
    log_file = config_manager.get_log_file()
    try:
        logger = ParkingLogger(log_file, level=logging.INFO)
    except:
        logger = ParkingLogger("app.log", level=logging.INFO)
    
    logger.info("=" * 30)
    logger.info("KHỞI ĐỘNG HỆ THỐNG")
    
    # Hiển thị MainWindow
    try:
        window = MainWindow(config_manager, logger)
        window.show()
        sys.exit(app.exec_())
    
    except Exception as e:
        logger.error(f"Crash: {str(e)}")
        QMessageBox.critical(None, "Lỗi nghiêm trọng", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()