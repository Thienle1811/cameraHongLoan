"""
Quản lý lưu file ảnh theo cấu trúc thư mục quy định
Format: D:\DuLieuBaiXe\[LAN]_[yyyyMMdd]\[LAN]_[yyyyMMdd_HHmmss]_front/rear.jpg
"""
import os
from datetime import datetime
from typing import Optional, Tuple
from PyQt5.QtGui import QImage
from logger import ParkingLogger


class FileManager:
    """Quản lý lưu file ảnh chụp từ camera"""
    
    def __init__(self, save_directory: str, logger: Optional[ParkingLogger] = None):
        """
        Khởi tạo FileManager
        
        Args:
            save_directory: Thư mục gốc lưu ảnh
            logger: Logger để ghi log
        """
        self.save_directory = save_directory
        self.logger = logger
        
        # Tạo thư mục gốc nếu chưa có
        self._ensure_directory_exists(save_directory)
    
    def _ensure_directory_exists(self, directory: str):
        """Đảm bảo thư mục tồn tại"""
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            if self.logger:
                self.logger.log_file_error(f"Không thể tạo thư mục {directory}: {str(e)}")
    
    def save_capture(self, lane: str, front_image: Optional[QImage], 
                     rear_image: Optional[QImage]) -> Tuple[bool, str, str]:
        """
        Lưu ảnh chụp từ 2 camera của một làn
        
        Args:
            lane: Tên làn ("RA" hoặc "VAO")
            front_image: Ảnh từ camera trước
            rear_image: Ảnh từ camera sau
        
        Returns:
            Tuple (success, front_path, rear_path)
        """
        # Chuẩn hóa tên làn
        lane_upper = lane.upper()
        if lane_upper not in ["RA", "VAO"]:
            lane_upper = "RA"  # Mặc định
        
        # Tạo timestamp
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%Y%m%d_%H%M%S")
        
        # Tạo thư mục theo ngày
        day_directory = os.path.join(self.save_directory, f"{lane_upper}_{date_str}")
        self._ensure_directory_exists(day_directory)
        
        # Đường dẫn file
        front_path = os.path.join(day_directory, f"{lane_upper}_{time_str}_front.jpg")
        rear_path = os.path.join(day_directory, f"{lane_upper}_{time_str}_rear.jpg")
        
        success = True
        front_saved = False
        rear_saved = False
        
        # Lưu ảnh trước
        if front_image:
            try:
                front_image.save(front_path, "JPEG", quality=95)
                front_saved = True
                if self.logger:
                    self.logger.debug(f"Đã lưu ảnh trước: {front_path}", lane_upper)
            except Exception as e:
                success = False
                if self.logger:
                    self.logger.log_file_error(f"Không thể lưu ảnh trước: {str(e)}", lane_upper)
        else:
            success = False
            if self.logger:
                self.logger.log_file_error("Không có ảnh từ camera trước", lane_upper)
        
        # Lưu ảnh sau
        if rear_image:
            try:
                rear_image.save(rear_path, "JPEG", quality=95)
                rear_saved = True
                if self.logger:
                    self.logger.debug(f"Đã lưu ảnh sau: {rear_path}", lane_upper)
            except Exception as e:
                success = False
                if self.logger:
                    self.logger.log_file_error(f"Không thể lưu ảnh sau: {str(e)}", lane_upper)
        else:
            success = False
            if self.logger:
                self.logger.log_file_error("Không có ảnh từ camera sau", lane_upper)
        
        # Nếu một trong hai ảnh không lưu được, xóa ảnh đã lưu để đảm bảo tính nhất quán
        if not success:
            if front_saved and os.path.exists(front_path):
                try:
                    os.remove(front_path)
                except:
                    pass
            if rear_saved and os.path.exists(rear_path):
                try:
                    os.remove(rear_path)
                except:
                    pass
            return False, "", ""
        
        return True, front_path, rear_path

