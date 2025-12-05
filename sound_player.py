"""
Phát âm thanh cảnh báo khi chụp ảnh thành công
Hỗ trợ WAV files và system sounds
Lưu ý: MP3 cần thư viện bổ sung (pygame hoặc playsound)
"""
import os
import winsound
from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtMultimedia import QSoundEffect


class SoundPlayer(QObject):
    """Phát âm thanh PÍP khi chụp ảnh"""
    
    def __init__(self, sound_file_path: str = None):
        """
        Khởi tạo SoundPlayer
        
        Args:
            sound_file_path: Đường dẫn đến file âm thanh (WAV). 
                           Nếu None, sẽ tìm trong thư mục sounds/
                           Lưu ý: MP3 cần thư viện bổ sung
        """
        super().__init__()
        self.sound_file_path = sound_file_path
        self.sound_effect = None
        
        # Tìm file âm thanh
        if not self.sound_file_path:
            self.sound_file_path = self._find_sound_file()
            if self.sound_file_path:
                print(f"Đã tìm thấy file âm thanh: {self.sound_file_path}")
        
        # Khởi tạo QSoundEffect nếu có file WAV
        if self.sound_file_path and os.path.exists(self.sound_file_path):
            file_ext = os.path.splitext(self.sound_file_path)[1].lower()
            if file_ext == '.wav':
                try:
                    self.sound_effect = QSoundEffect()
                    self.sound_effect.setSource(QUrl.fromLocalFile(self.sound_file_path))
                    self.sound_effect.setVolume(1.0)  # Volume tối đa
                    print(f"Đã load file âm thanh: {self.sound_file_path}")
                except Exception as e:
                    print(f"Không thể load file WAV: {e}")
                    self.sound_effect = None
            elif file_ext == '.mp3':
                # MP3 cần xử lý đặc biệt - sẽ dùng winsound hoặc system sound
                print("Lưu ý: MP3 không được hỗ trợ trực tiếp. Vui lòng chuyển sang WAV hoặc dùng system sound.")
                self.sound_file_path = None
    
    def _find_sound_file(self) -> str:
        """Tìm file âm thanh trong thư mục sounds/ hoặc thư mục hiện tại"""
        # Các tên file có thể có (ưu tiên WAV)
        possible_names = [
            "beep.wav", "pip.wav", "capture.wav", "sound.wav",
            "beep.mp3", "pip.mp3", "capture.mp3", "sound.mp3"
        ]
        
        # Thư mục để tìm
        search_dirs = [
            "sounds",  # Thư mục sounds trong project
            ".",       # Thư mục hiện tại
            os.path.dirname(os.path.abspath(__file__))  # Thư mục chứa file này
        ]
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
            for name in possible_names:
                file_path = os.path.join(search_dir, name)
                if os.path.exists(file_path):
                    return file_path
        
        return None
    
    def play_file_sound(self):
        """Phát âm thanh từ file WAV"""
        if self.sound_effect:
            try:
                self.sound_effect.play()
                return True
            except Exception as e:
                print(f"Lỗi phát file âm thanh: {e}")
                return False
        
        # Fallback: thử dùng winsound cho WAV files
        if self.sound_file_path and os.path.exists(self.sound_file_path):
            try:
                winsound.PlaySound(self.sound_file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return True
            except Exception as e:
                print(f"Lỗi phát file với winsound: {e}")
        
        return False
    
    def play_system_beep(self):
        """Phát system beep"""
        # Thử nhiều cách phát system sound
        methods = [
            # Method 1: Beep với tần số
            lambda: winsound.Beep(800, 200),
            # Method 2: System Asterisk
            lambda: winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC),
            # Method 3: System Exclamation
            lambda: winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC),
            # Method 4: MessageBeep
            lambda: winsound.MessageBeep(winsound.MB_OK),
            # Method 5: System Hand
            lambda: winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC),
        ]
        
        for method in methods:
            try:
                method()
                return True
            except Exception:
                continue
        
        return False
    
    def play_capture_sound(self):
        """
        Phát âm thanh khi chụp ảnh thành công (PÍP)
        Thử file trước, nếu không có thì dùng system sound
        """
        # Thử phát file âm thanh trước
        if self.play_file_sound():
            return
        
        # Fallback: dùng system sound
        if not self.play_system_beep():
            print("Không thể phát âm thanh. Kiểm tra cài đặt âm thanh hệ thống.")
