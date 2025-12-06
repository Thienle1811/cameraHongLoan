import os
from datetime import datetime
from typing import Tuple
from PyQt5.QtGui import QImage
from logger import ParkingLogger

class FileManager:
    """
    Quản lý lưu file ảnh từ Camera.
    - Lưu tại: D:\DuLieuBaiXe\YYYY-MM-DD\
    - Tên file: HH-MM-SS_dd-mm-yyyy_LAN_Truoc/Sau.jpg
    """
    
    def __init__(self, save_directory: str, logger: ParkingLogger = None):
        """
        Khởi tạo FileManager
        args:
            save_directory: Thư mục gốc (Ví dụ: D:\DuLieuBaiXe)
        """
        self.save_directory = save_directory
        self.logger = logger
        # Đảm bảo thư mục gốc tồn tại
        self._ensure_directory_exists(save_directory)
    
    def _ensure_directory_exists(self, directory: str):
        """Tạo thư mục nếu chưa có"""
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            if self.logger:
                self.logger.error(f"Không thể tạo thư mục {directory}: {str(e)}")
    
    def save_capture(self, lane: str, card_code: str, front_image: QImage, rear_image: QImage) -> Tuple[bool, str, str]:
        """
        Lưu ảnh chụp từ 2 camera.
        Trả về: (Success, Path_Front, Path_Rear)
        """
        now = datetime.now()
        
        # 1. Tạo tên thư mục theo ngày (Format: YYYY-MM-DD để dễ sort)
        # Ví dụ: D:\DuLieuBaiXe\2025-12-04
        folder_date = now.strftime("%Y-%m-%d")
        day_directory = os.path.join(self.save_directory, folder_date)
        self._ensure_directory_exists(day_directory)
        
        # 2. Tạo tên file theo yêu cầu: Giờ-Phút-Giây_Ngày-Tháng-Năm
        # Lưu ý: Windows không cho phép dấu hai chấm (:) trong tên file
        time_str = now.strftime("%H-%M-%S") 
        date_str = now.strftime("%d-%m-%Y")
        
        lane_prefix = lane.upper() # RA hoặc VAO
        
        # Format: 12-30-05_04-12-2025_RA_Front.jpg
        # Thêm Lane và Front/Rear để tránh trùng tên nếu 2 xe vào cùng lúc
        front_filename = f"{time_str}_{date_str}_{lane_prefix}_Front.jpg"
        rear_filename = f"{time_str}_{date_str}_{lane_prefix}_Rear.jpg"
        
        # Đường dẫn đầy đủ
        front_path = os.path.join(day_directory, front_filename)
        rear_path = os.path.join(day_directory, rear_filename)
        
        try:
            # Lưu ảnh Camera Trước
            if front_image:
                # Quality 85 là đủ đẹp và nhẹ
                front_image.save(front_path, "JPG", quality=85)
            
            # Lưu ảnh Camera Sau
            if rear_image:
                rear_image.save(rear_path, "JPG", quality=85)
                
            return True, front_path, rear_path
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Lỗi lưu file ảnh: {e}")
            return False, "", ""