import json
import os

class ConfigManager:
    """Quản lý file cấu hình config.json"""
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self):
        if not os.path.exists(self.config_path):
            return {}
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Lỗi đọc config: {e}")
            return {}

    def get(self, key, default=None):
        return self.config.get(key, default)
        
    def get_rtsp_url(self, camera_key):
        urls = self.config.get("rtsp_urls", {})
        return urls.get(camera_key)
        
    def get_save_directory(self):
        # Mặc định lưu D:\DuLieuBaiXe nếu config không có
        return self.config.get("save_directory", r"D:\DuLieuBaiXe")
    
    def get_log_file(self):
        return self.config.get("log_file", "app.log")

    def get_serial_config(self):
        default_serial = {"port_in": "COM3", "port_out": "COM1", "baud_rate": 19200}
        return self.config.get("serial", default_serial)
        
    def get_database_config(self):
        """Lấy thông tin kết nối PostgreSQL"""
        default_db = {
            "host": "localhost",
            "port": "5432",
            "user": "postgres",
            "password": "123",
            "dbname": "parking_db"
        }
        return self.config.get("database", default_db)