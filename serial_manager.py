import serial
import time
from PyQt5.QtCore import QThread, pyqtSignal

class SerialThread(QThread):
    # Signal gửi mã thẻ về Main Window: (tên làn, mã thẻ)
    rfid_scanned = pyqtSignal(str, str) 
    error_occurred = pyqtSignal(str)

    def __init__(self, port, baud_rate, lane_name):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.lane_name = lane_name # "VAO" hoặc "RA"
        self.is_running = True
        self.serial_connection = None

    def run(self):
        while self.is_running:
            try:
                if self.serial_connection is None or not self.serial_connection.is_open:
                    self.serial_connection = serial.Serial(
                        port=self.port,
                        baudrate=self.baud_rate,
                        timeout=1
                    )
                
                if self.serial_connection.in_waiting > 0:
                    # Đọc dữ liệu từ cổng COM
                    raw_data = self.serial_connection.readline()
                    try:
                        # Decode và bỏ ký tự thừa
                        card_code = raw_data.decode('utf-8').strip()
                        if card_code:
                            self.rfid_scanned.emit(self.lane_name, card_code)
                            # Chống lặp thẻ quá nhanh (Delay 2s)
                            time.sleep(2) 
                    except UnicodeDecodeError:
                        pass
                        
                time.sleep(0.1) # Giảm tải CPU

            except serial.SerialException:
                # Nếu không có cổng COM thật (đang test trên laptop), ta bỏ qua lỗi
                # Để không spam log lỗi liên tục
                time.sleep(5)
            except Exception as e:
                self.error_occurred.emit(f"Lỗi {self.lane_name}: {str(e)}")
                time.sleep(2)

    def stop(self):
        self.is_running = False
        if self.serial_connection:
            self.serial_connection.close()
        self.wait()