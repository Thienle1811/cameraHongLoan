import sqlite3
import os
from datetime import datetime

class ParkingDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Tạo bảng dữ liệu nếu chưa có"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Bảng Cards: Danh sách thẻ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                card_id TEXT PRIMARY KEY,
                plate_number TEXT,
                customer_name TEXT,
                card_type INTEGER DEFAULT 0, -- 0: Vãng lai, 1: Tháng
                is_locked INTEGER DEFAULT 0
            )
        ''')
        
        # Bảng Sessions: Lịch sử ra vào
        # status: 1 (Đang gửi), 0 (Đã ra)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT,
                checkin_time DATETIME,
                checkin_image_front TEXT,
                checkin_image_rear TEXT,
                checkout_time DATETIME,
                checkout_image_front TEXT,
                checkout_image_rear TEXT,
                price INTEGER DEFAULT 0,
                status INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()

    def check_in(self, card_id, img_front, img_rear):
        """Xử lý xe vào. Trả về (Success, Message)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Kiểm tra Anti-Passback
            cursor.execute('SELECT id FROM sessions WHERE card_id = ? AND status = 1', (card_id,))
            existing_session = cursor.fetchone()
            
            if existing_session:
                return False, f"CẢNH BÁO: Thẻ {card_id} đang ở trong bãi (Chưa quẹt ra)!"
            
            # 2. Ghi nhận xe vào
            now = datetime.now()
            cursor.execute('''
                INSERT INTO sessions (card_id, checkin_time, checkin_image_front, checkin_image_rear, status)
                VALUES (?, ?, ?, ?, 1)
            ''', (card_id, now, img_front, img_rear))
            
            conn.commit()
            return True, f"Mời xe vào (Thẻ: {card_id})"
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def check_out(self, card_id, img_front, img_rear):
        """Xử lý xe ra. Trả về (Success, Message, CheckinInfo)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Tìm lượt xe đang gửi
            cursor.execute('''
                SELECT id, checkin_time, checkin_image_front 
                FROM sessions 
                WHERE card_id = ? AND status = 1
                ORDER BY checkin_time DESC LIMIT 1
            ''', (card_id,))
            session = cursor.fetchone()
            
            if not session:
                return False, f"CẢNH BÁO: Thẻ {card_id} chưa quẹt vào (Hoặc đã ra rồi)!", None
            
            session_id = session[0]
            checkin_time = session[1] # Dạng string nếu sqlite
            checkin_img = session[2]
            
            # 2. Cập nhật xe ra
            now = datetime.now()
            # Logic tính tiền đơn giản (Có thể nâng cấp sau)
            price = 5000 
            
            cursor.execute('''
                UPDATE sessions 
                SET checkout_time = ?, 
                    checkout_image_front = ?, 
                    checkout_image_rear = ?,
                    price = ?,
                    status = 0
                WHERE id = ?
            ''', (now, img_front, img_rear, price, session_id))
            
            conn.commit()
            
            info = {
                "checkin_time": checkin_time,
                "checkin_img": checkin_img,
                "price": price
            }
            return True, f"Mời xe ra (Phí: {price}đ)", info
            
        except Exception as e:
            return False, str(e), None
        finally:
            conn.close()
            
    def get_card_info(self, card_id):
        """Lấy thông tin biển số đăng ký của thẻ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT plate_number, card_type FROM cards WHERE card_id = ?', (card_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {"plate": result[0], "type": result[1]}
        return None