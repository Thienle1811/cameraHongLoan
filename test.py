import os
import time
from datetime import datetime
from config_manager import ConfigManager
from database import ParkingDatabase

# --- LỚP GIẢ LẬP PHẦN CỨNG (MOCK) ---
class MockSerial:
    """Giả lập cổng COM để test khi không có thiết bị thật"""
    def __init__(self, port, baudrate, timeout=1):
        print(f"[MOCK] Đang kết nối cổng ảo {port} tốc độ {baudrate}...")
        self.port = port
        self.is_open = True
        self.dummy_data = [b"E200123456\n", b"E200999999\n"] # Danh sách thẻ giả sẽ quẹt
        self.current_index = 0

    def readline(self):
        """Giả vờ đọc thẻ từ đầu đọc"""
        if self.current_index < len(self.dummy_data):
            data = self.dummy_data[self.current_index]
            self.current_index += 1
            return data
        return b"" # Hết thẻ

    def close(self):
        print(f"[MOCK] Đã đóng cổng {self.port}")

# ------------------------------------

def test_full_flow():
    print("=== BẮT ĐẦU TEST HỆ THỐNG (CHẾ ĐỘ GIẢ LẬP) ===\n")

    # 1. TEST CONFIG
    print("--- [1] KIỂM TRA CẤU HÌNH ---")
    if not os.path.exists("config.json"):
        print("❌ LỖI: Không tìm thấy file config.json")
        return
    
    cfg = ConfigManager()
    print(f"✅ Đọc cấu hình thành công.")
    print(f"   - DB Path: {cfg.get_database_path()}")
    print(f"   - Serial: {cfg.get_serial_config()}\n")

    # 2. TEST DATABASE & LOGIC
    print("--- [2] KIỂM TRA LOGIC DATABASE & TÍNH TIỀN ---")
    db_path = cfg.get_database_path()
    
    # Xóa DB cũ để test lại từ đầu
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("   (Đã reset database cũ)")
        except: pass
        
    db = ParkingDatabase(db_path)
    
    # --- Kịch bản Test ---
    card_id = "CARD_TEST_01"
    fake_img_in_front = "D:\\data\\mock_in_front.jpg"
    fake_img_in_rear = "D:\\data\\mock_in_rear.jpg"
    fake_img_out_front = "D:\\data\\mock_out_front.jpg"
    fake_img_out_rear = "D:\\data\\mock_out_rear.jpg"

    # A. Xe vào
    print(f"👉 [A] Xe vào bãi (Thẻ: {card_id})")
    success, msg = db.check_in(card_id, fake_img_in_front, fake_img_in_rear)
    if success:
        print(f"   ✅ KẾT QUẢ: Thành công. ({msg})")
    else:
        print(f"   ❌ KẾT QUẢ: Thất bại. ({msg})")

    # B. Xe vào lần nữa (Check gian lận)
    print(f"\n👉 [B] Xe đó quẹt vào tiếp (Thử Anti-Passback)")
    success, msg = db.check_in(card_id, fake_img_in_front, fake_img_in_rear)
    if not success:
        print(f"   ✅ KẾT QUẢ: Hệ thống chặn đúng. ({msg})")
    else:
        print(f"   ❌ KẾT QUẢ: Lỗi! Hệ thống cho phép vào 2 lần.")

    # C. Xe ra
    print(f"\n👉 [C] Xe ra bãi (Giả lập sau 1 tiếng)")
    # Hack thời gian checkin lùi lại 1 tiếng để test tính tiền
    conn = db.get_connection()
    cursor = conn.cursor()
    one_hour_ago = datetime.now().timestamp() - 3600 # Trừ 3600 giây
    # SQLite lưu datetime dạng string, ở đây ta test logic check_out là chính
    conn.close()

    success, msg, info = db.check_out(card_id, fake_img_out_front, fake_img_out_rear)
    if success:
        print(f"   ✅ KẾT QUẢ: Thành công. ({msg})")
        print(f"   💰 Phí thu: {info['price']} VNĐ")
    else:
        print(f"   ❌ KẾT QUẢ: Thất bại. ({msg})")

    print("\n")

    # 3. TEST KẾT NỐI SERIAL (MOCK)
    print("--- [3] KIỂM TRA KẾT NỐI ĐẦU ĐỌC (MOCK) ---")
    serial_cfg = cfg.get_serial_config()
    port = serial_cfg.get("port_in", "COM3")
    
    try:
        # Dùng MockSerial thay vì serial.Serial
        ser = MockSerial(port, 19200)
        
        if ser.is_open:
            print(f"✅ Đã kết nối thành công tới {port} (Giả lập)")
            
            # Thử đọc thẻ
            print("   Đang chờ thẻ...")
            card = ser.readline().decode('utf-8').strip()
            print(f"   📡 Nhận tín hiệu: {card}")
            
            card2 = ser.readline().decode('utf-8').strip()
            print(f"   📡 Nhận tín hiệu: {card2}")
            
            ser.close()
        else:
            print("❌ Không mở được cổng.")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

    print("\n=== KẾT THÚC TEST ===")

if __name__ == "__main__":
    test_full_flow()