"""
Hệ thống logging cho ứng dụng Parking Control System
Ghi log với format: [YYYY-MM-DD HH:MM:SS] [LEVEL] [LAN] Message
"""
import logging
import os
from datetime import datetime
from typing import Optional


class ParkingLogger:
    """Logger tùy chỉnh cho hệ thống bãi xe"""
    
    def __init__(self, log_file: str, level=logging.INFO):
        self.log_file = log_file
        self.logger = logging.getLogger('ParkingControl')
        self.logger.setLevel(level)
        
        # Tạo thư mục log nếu chưa có
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except OSError:
                pass  # Nếu không tạo được, sẽ ghi vào console
        
        # Handler ghi vào file
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(level)
                file_formatter = logging.Formatter(
                    '[%(asctime)s] [%(levelname)s] [%(lane)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
            except (IOError, OSError):
                pass  # Nếu không ghi được file, chỉ ghi console
        
        # Handler ghi vào console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(lane)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def _log(self, level: int, message: str, lane: str = "SYSTEM"):
        """Ghi log với lane information"""
        extra = {'lane': lane}
        self.logger.log(level, message, extra=extra)
    
    def info(self, message: str, lane: str = "SYSTEM"):
        """Ghi log INFO"""
        self._log(logging.INFO, message, lane)
    
    def warning(self, message: str, lane: str = "SYSTEM"):
        """Ghi log WARNING"""
        self._log(logging.WARNING, message, lane)
    
    def error(self, message: str, lane: str = "SYSTEM"):
        """Ghi log ERROR"""
        self._log(logging.ERROR, message, lane)
    
    def debug(self, message: str, lane: str = "SYSTEM"):
        """Ghi log DEBUG"""
        self._log(logging.DEBUG, message, lane)
    
    def log_capture(self, lane: str, success: bool, front_path: str = "", rear_path: str = ""):
        """Ghi log sự kiện chụp ảnh"""
        status = "OK" if success else "FAIL"
        message = f"Capture {status}"
        if success and front_path and rear_path:
            message += f" - Front: {front_path}, Rear: {rear_path}"
        elif not success:
            message += " - Không thể lưu ảnh"
        self.info(message, lane)
    
    def log_rtsp_connection(self, camera_key: str, connected: bool, error: str = ""):
        """Ghi log kết nối RTSP"""
        lane = camera_key.upper().replace("_", " ")
        if connected:
            self.info(f"RTSP connected: {camera_key}", lane)
        else:
            error_msg = f"RTSP disconnected: {camera_key}"
            if error:
                error_msg += f" - {error}"
            self.error(error_msg, lane)
    
    def log_file_error(self, message: str, lane: str = "SYSTEM"):
        """Ghi log lỗi file"""
        self.error(f"File error: {message}", lane)

