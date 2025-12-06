import json
import os

class ConfigManager:
    """
    Quản lý file cấu hình config.json.
    Nhiệm vụ: Đọc các thông số Camera, Cổng COM, Database, Đường dẫn lưu ảnh từ file JSON.
    """
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self):
        """
        Đọc file cấu hình.
        Sử dụng encoding='utf-8' để hỗ trợ đường dẫn tiếng Việt.
        """
        if not os.path.exists(self.config_path):
            print(f"[Config] Cảnh báo: Không tìm thấy file {self.config_path}")
            return {}
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                return config_data
        except Exception as e:
            print(f"[Config] Lỗi khi đọc file cấu hình: {str(e)}")
            return {}

    def get(self, key, default=None):
        """Lấy giá trị cấu hình theo key bất kỳ"""
        return self.config.get(key, default)
        
    def get_rtsp_url(self, camera_key):
        """
        Lấy luồng RTSP của camera cụ thể.
        Keys: ra_front, ra_rear, vao_front, vao_rear
        """
        urls = self.config.get("rtsp_urls", {})
        return urls.get(camera_key)
        
    def get_save_directory(self):
        """Lấy thư mục lưu ảnh (Mặc định: parking_data)"""
        return self.config.get("save_directory", "parking_data")
    
    def get_log_file(self):
        """Lấy đường dẫn file log (Hàm bị thiếu trước đó)"""
        return self.config.get("log_file", "app.log")
        
    # --- CÁC HÀM MỚI (Dành cho RFID và Database) ---

    def get_serial_config(self):
        """
        Lấy cấu hình cổng COM cho đầu đọc thẻ.
        Trả về dict gồm: port_in, port_out, baud_rate
        """
        # Giá trị mặc định nếu trong file json chưa có
        default_serial = {
            "port_in": "COM3", 
            "port_out": "COM1", 
            "baud_rate": 19200
        }
        return self.config.get("serial", default_serial)
        
    def get_database_path(self):
        """Lấy đường dẫn file Database (Mặc định: parking.db)"""
        db_conf = self.config.get("database", {})
        return db_conf.get("path", "parking.db")