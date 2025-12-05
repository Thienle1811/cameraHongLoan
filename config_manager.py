"""
Quản lý cấu hình ứng dụng - đọc/ghi file config.json
"""
import json
import os
from typing import Dict, Any


class ConfigManager:
    """Quản lý cấu hình từ file JSON"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Đọc file config, tạo file mặc định nếu chưa có"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Lỗi đọc config: {e}. Sử dụng config mặc định.")
                return self._get_default_config()
        else:
            # Tạo file config mặc định
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Trả về cấu hình mặc định"""
        return {
            "rtsp_urls": {
                "ra_front": "rtsp://admin2:123321abc@192.168.1.108:554/cam/realmonitor?channel=1&subtype=1",
                "ra_rear": "rtsp://admin2:123321abc@192.168.1.108:554/cam/realmonitor?channel=2&subtype=1",
                "vao_front": "rtsp://admin2:123321abc@192.168.1.108:554/cam/realmonitor?channel=3&subtype=1",
                "vao_rear": "rtsp://admin2:123321abc@192.168.1.108:554/cam/realmonitor?channel=4&subtype=1"
            },
            "save_directory": "D:\\DuLieuBaiXe",
            "log_file": "D:\\DuLieuBaiXe\\app.log"
        }
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Lưu config vào file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Lỗi ghi config: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Lấy giá trị config theo key (hỗ trợ nested key như 'rtsp_urls.ra_front')"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Đặt giá trị config (hỗ trợ nested key)"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        return self._save_config(self.config)
    
    def get_rtsp_url(self, camera_key: str) -> str:
        """Lấy RTSP URL của camera"""
        return self.get(f"rtsp_urls.{camera_key}", "")
    
    def get_save_directory(self) -> str:
        """Lấy thư mục lưu ảnh"""
        return self.get("save_directory", "D:\\DuLieuBaiXe")
    
    def get_log_file(self) -> str:
        """Lấy đường dẫn file log"""
        return self.get("log_file", "D:\\DuLieuBaiXe\\app.log")
    
    def save(self) -> bool:
        """Lưu config hiện tại"""
        return self._save_config(self.config)

