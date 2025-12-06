import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, date, timedelta
import pandas as pd
import os

class ParkingDatabase:
    """
    Lớp xử lý logic nghiệp vụ với PostgreSQL:
    - Quản lý thẻ tháng/ngày
    - Tính tiền
    - Xuất báo cáo Excel
    """
    def __init__(self, db_config):
        self.config = db_config
        self.init_db()

    def get_connection(self):
        try:
            conn = psycopg2.connect(**self.config)
            return conn
        except Exception as e:
            print(f"Database Connect Error: {e}")
            return None

    def init_db(self):
        """Tạo bảng dữ liệu nếu chưa có"""
        conn = self.get_connection()
        if not conn: return
        
        with conn:
            with conn.cursor() as cursor:
                # Bảng Cards: Danh sách thẻ tháng
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cards (
                        card_id VARCHAR(50) PRIMARY KEY,
                        plate_number VARCHAR(20),
                        customer_name VARCHAR(100),
                        is_active BOOLEAN DEFAULT TRUE,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Bảng Sessions: Lịch sử ra vào
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id SERIAL PRIMARY KEY,
                        card_id VARCHAR(50),
                        vehicle_type VARCHAR(20) DEFAULT 'DAY', 
                        checkin_time TIMESTAMP,
                        checkin_img_front TEXT,
                        checkin_img_rear TEXT,
                        checkout_time TIMESTAMP,
                        checkout_img_front TEXT,
                        checkout_img_rear TEXT,
                        price INTEGER DEFAULT 0,
                        status INTEGER DEFAULT 1
                    );
                """)
        conn.close()

    def import_from_csv(self, csv_path):
        """
        Nhập danh sách thẻ tháng từ file CSV (Chỉ cần cột đầu tiên là mã thẻ).
        """
        conn = self.get_connection()
        if not conn: return False, "Lỗi kết nối DB"
        
        try:
            # Đọc CSV không cần header, coi tất cả là string
            df = pd.read_csv(csv_path, header=None, dtype=str)
            
            count = 0
            with conn:
                with conn.cursor() as cursor:
                    for index, row in df.iterrows():
                        # Lấy mã thẻ ở cột đầu tiên
                        if pd.isna(row[0]): continue
                        c_id = str(row[0]).strip()
                        if not c_id: continue

                        # Các thông tin khác để trống (vì file csv chỉ có mã)
                        plate = ""
                        name = ""
                        
                        # Upsert: Nếu thẻ đã có thì cập nhật lại là Active
                        cursor.execute("""
                            INSERT INTO cards (card_id, plate_number, customer_name, is_active)
                            VALUES (%s, %s, %s, TRUE)
                            ON CONFLICT (card_id) 
                            DO UPDATE SET is_active = TRUE,
                                          updated_at = CURRENT_TIMESTAMP;
                        """, (c_id, plate, name))
                        count += 1
            
            return True, f"Đã cập nhật {count} thẻ tháng vào hệ thống."
            
        except Exception as e:
            return False, f"Lỗi nhập file: {str(e)}"
        finally:
            conn.close()

    def check_in(self, card_id, img_front, img_rear):
        """
        Xử lý xe vào:
        - Kiểm tra xem thẻ có đang ở trong bãi không (Anti-passback)
        - Kiểm tra xem là thẻ tháng hay thẻ ngày
        """
        conn = self.get_connection()
        if not conn: return False, "Mất kết nối DB"
        
        try:
            with conn:
                with conn.cursor() as cursor:
                    # 1. Anti-Passback
                    cursor.execute("SELECT id FROM sessions WHERE card_id = %s AND status = 1", (card_id,))
                    if cursor.fetchone():
                        return False, f"Thẻ {card_id} chưa quẹt ra!"

                    # 2. Kiểm tra Thẻ Tháng
                    cursor.execute("SELECT card_id FROM cards WHERE card_id = %s AND is_active = TRUE", (card_id,))
                    row = cursor.fetchone()
                    
                    vehicle_type = 'DAY'
                    msg_extra = "VÃNG LAI"
                    
                    if row:
                        vehicle_type = 'MONTH'
                        msg_extra = "XE THÁNG"

                    # 3. Lưu vào DB
                    cursor.execute("""
                        INSERT INTO sessions (card_id, vehicle_type, checkin_time, checkin_img_front, checkin_img_rear, status)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, 1)
                    """, (card_id, vehicle_type, img_front, img_rear))
            
            return True, f"Mời vào ({msg_extra})"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def calculate_parking_fee(self, checkin_time, checkout_time, vehicle_type):
        """
        Logic tính tiền:
        - Tháng: 0đ
        - Ngày: 3000đ (trong ngày), 5000đ/đêm (qua đêm)
        """
        if vehicle_type == 'MONTH':
            return 0
            
        d_in = checkin_time.date()
        d_out = checkout_time.date()
        
        delta = d_out - d_in
        nights = delta.days
        
        if nights == 0:
            return 3000 # Trong ngày
        else:
            return 5000 * nights # Qua bao nhiêu đêm tính bấy nhiêu

    def check_out(self, card_id, img_front, img_rear):
        """
        Xử lý xe ra:
        - Tính tiền
        - Cập nhật giờ ra và ảnh ra
        """
        conn = self.get_connection()
        if not conn: return False, "Mất kết nối DB", None
        
        try:
            info = {}
            with conn:
                with conn.cursor(cursor_factory=DictCursor) as cursor:
                    # Tìm lượt xe đang gửi
                    cursor.execute("""
                        SELECT * FROM sessions 
                        WHERE card_id = %s AND status = 1 
                        ORDER BY checkin_time DESC LIMIT 1
                    """, (card_id,))
                    session = cursor.fetchone()
                    
                    if not session:
                        return False, f"Thẻ {card_id} chưa check-in!", None
                    
                    sid = session['id']
                    checkin_time = session['checkin_time']
                    v_type = session['vehicle_type']
                    now = datetime.now()
                    
                    # Tính tiền
                    fee = self.calculate_parking_fee(checkin_time, now, v_type)
                    
                    # Cập nhật DB (Kết thúc phiên gửi xe)
                    cursor.execute("""
                        UPDATE sessions 
                        SET checkout_time = %s,
                            checkout_img_front = %s,
                            checkout_img_rear = %s,
                            price = %s,
                            status = 0
                        WHERE id = %s
                    """, (now, img_front, img_rear, fee, sid))
                    
                    info = {
                        "checkin_time": checkin_time.strftime("%d/%m %H:%M"),
                        "price": fee,
                        "type": v_type
                    }
            
            msg = f"Phí: {info['price']}"
            return True, msg, info
            
        except Exception as e:
            return False, str(e), None
        finally:
            conn.close()

    def export_daily_report(self):
        """
        Xuất báo cáo 2 Sheet (Doanh Thu & Lưu Lượng)
        Lưu tại D:\BaoCao hoặc thư mục hiện tại/BaoCao
        """
        conn = self.get_connection()
        if not conn: return False, "Mất kết nối DB"

        try:
            # Xác định ngày báo cáo (Hôm qua nếu chạy lúc 0h sáng)
            now = datetime.now()
            if now.hour == 0 and now.minute <= 30: 
                report_date = now.date() - timedelta(days=1)
            else:
                report_date = now.date()
            
            date_str = report_date.strftime("%d-%m-%Y")
            
            # Tạo đường dẫn lưu file
            save_folder = r"D:\BaoCao"
            if not os.path.exists("D:\\"):
                save_folder = os.path.join(os.getcwd(), "BaoCao")
            
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)

            file_path = os.path.join(save_folder, f"{date_str}.xlsx")

            # --- SHEET 1: DOANH THU (Xe Ra) ---
            query_out = """
                SELECT 
                    card_id as "Mã Thẻ",
                    CASE WHEN vehicle_type = 'MONTH' THEN 'Xe Tháng' ELSE 'Vãng Lai' END as "Loại Xe",
                    to_char(checkin_time, 'DD/MM/YYYY HH24:MI:SS') as "Giờ Vào",
                    to_char(checkout_time, 'DD/MM/YYYY HH24:MI:SS') as "Giờ Ra",
                    price as "Số Tiền"
                FROM sessions
                WHERE status = 0 
                AND DATE(checkout_time) = %s
                ORDER BY checkout_time ASC
            """
            df_out = pd.read_sql_query(query_out, conn, params=(report_date,))
            
            # Tính tổng tiền
            if not df_out.empty:
                total_money = df_out["Số Tiền"].sum()
                row_total = pd.DataFrame([{
                    "Mã Thẻ": "TỔNG CỘNG", 
                    "Loại Xe": "", "Giờ Vào": "", "Giờ Ra": "", 
                    "Số Tiền": total_money
                }])
                df_out = pd.concat([df_out, row_total], ignore_index=True)

            # --- SHEET 2: LƯU LƯỢNG (Xe Vào) ---
            query_in = """
                SELECT 
                    card_id as "Mã Thẻ",
                    CASE WHEN vehicle_type = 'MONTH' THEN 'Xe Tháng' ELSE 'Vãng Lai' END as "Loại Xe",
                    to_char(checkin_time, 'DD/MM/YYYY HH24:MI:SS') as "Giờ Vào",
                    CASE WHEN status = 1 THEN 'Đang gửi' ELSE 'Đã ra' END as "Trạng Thái"
                FROM sessions
                WHERE DATE(checkin_time) = %s
                ORDER BY checkin_time ASC
            """
            df_in = pd.read_sql_query(query_in, conn, params=(report_date,))

            # Ghi ra Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                if not df_out.empty:
                    df_out.to_excel(writer, sheet_name='Xe Ra (Doanh Thu)', index=False)
                else:
                    pd.DataFrame({"Note": ["Không có dữ liệu"]}).to_excel(writer, sheet_name='Xe Ra (Doanh Thu)')
                
                if not df_in.empty:
                    df_in.to_excel(writer, sheet_name='Xe Vào (Lưu Lượng)', index=False)
                else:
                    pd.DataFrame({"Note": ["Không có dữ liệu"]}).to_excel(writer, sheet_name='Xe Vào (Lưu Lượng)')
            
            return True, f"Đã xuất báo cáo: {file_path}"

        except Exception as e:
            return False, f"Lỗi xuất Excel: {str(e)}"
        finally:
            if conn: conn.close()