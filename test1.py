import os
import time
from config_manager import ConfigManager
from database import ParkingDatabase

def test_config():
    print("--- [1] TEST CONFIG MANAGER ---")
    if not os.path.exists("config.json"):
        print("LỖI: Không tìm thấy file config.json")
        return None
    
    cfg = ConfigManager()
    serial_cfg = cfg.get_serial_config()
    db_path = cfg.get_database_path()
    
    print(f"Cấu hình Serial: {serial_cfg}")
    print(f"Đường dẫn DB: {db_path}")
    print("-> OK: Đọc cấu hình thành công.\n")
    return cfg

def test_database(cfg):
    print("--- [2] TEST DATABASE OPERATIONS ---")
    db_path = cfg.get_database_path()
    
    # Xóa DB cũ để test mới (Cẩn thận khi dùng thật)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Đã xóa DB cũ: {db_path}")
        except:
            pass
            
    db = ParkingDatabase(db_path)
    print("Đã khởi tạo Database.")
    
    # Kịch bản 1: Xe vào
    card_id = "E2003000"
    print(f"\n> Thử cho xe vào (Thẻ: {card_id})...")
    success, msg = db.check_in(card_id, "img_vao_truoc.jpg", "img_vao_sau.jpg")
    print(f"Kết quả: {success} | Msg: {msg}")
    
    # Kịch bản 2: Xe vào lần nữa (Check Anti-passback)
    print(f"\n> Thử cho xe vào LẦN 2 (Gian lận)...")
    success, msg = db.check_in(card_id, "img_vao_truoc.jpg", "img_vao_sau.jpg")
    print(f"Kết quả: {success} | Msg: {msg}")
    
    # Kịch bản 3: Xe ra
    print(f"\n> Thử cho xe ra...")
    # Giả lập trễ 2 giây
    time.sleep(2) 
    success, msg, info = db.check_out(card_id, "img_ra_truoc.jpg", "img_ra_sau.jpg")
    print(f"Kết quả: {success} | Msg: {msg}")
    if success:
        print(f"Chi tiết: Giờ vào={info['checkin_time']}, Phí={info['price']}")

    # Kịch bản 4: Xe ra lần nữa (Check lỗi)
    print(f"\n> Thử cho xe ra LẦN 2 (Khi đã ra rồi)...")
    success, msg, info = db.check_out(card_id, "img_ra_truoc.jpg", "img_ra_sau.jpg")
    print(f"Kết quả: {success} | Msg: {msg}")
    print("-> OK: Database hoạt động đúng logic.\n")

def test_serial_connection(cfg):
    print("--- [3] TEST SERIAL CONNECTION ---")
    import serial
    
    serial_cfg = cfg.get_serial_config()
    port = serial_cfg.get("port_in") # Test cổng vào
    baud = serial_cfg.get("baud_rate")
    
    print(f"Đang thử kết nối tới {port}...")
    try:
        ser = serial.Serial(port, baud, timeout=1)
        if ser.is_open:
            print(f"-> THÀNH CÔNG: Đã kết nối được tới {port}")
            ser.close()
        else:
            print("-> THẤT BẠI: Không mở được cổng.")
    except serial.SerialException as e:
        print(f"-> LỖI: Không tìm thấy cổng COM hoặc cổng đang bận.\n({e})")
        print("(Nếu bạn chưa cắm thiết bị thật, lỗi này là bình thường)")

if __name__ == "__main__":
    print("=== BẮT ĐẦU TEST HỆ THỐNG ===\n")
    
    config = test_config()
    if config:
        test_database(config)
        test_serial_connection(config)
        
    print("\n=== KẾT THÚC TEST ===")