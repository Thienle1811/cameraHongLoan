# Hệ Thống Quản Lý Bãi Xe - Parking Control System

Ứng dụng Python portable để quản lý và chụp ảnh từ 4 camera RTSP của hệ thống bãi xe.

## Yêu cầu hệ thống

- Windows Server (hoặc Windows 10/11)
- Python 3.12+ (nếu chạy từ source code)
- Kết nối mạng đến DVR Dahua (192.168.1.108)

## Cài đặt và chạy từ source code

### 1. Thiết lập môi trường ảo

```bash
# Tạo môi trường ảo (đã có sẵn .venv)
.venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Cấu hình

Chỉnh sửa file `config.json` nếu cần thay đổi:
- RTSP URLs của các camera
- Thư mục lưu ảnh (mặc định: `D:\DuLieuBaiXe`)
- Đường dẫn file log

### 3. Chạy ứng dụng

```bash
python main.py
```

**Lưu ý quan trọng:** Chạy với quyền Administrator để đảm bảo có quyền ghi file vào ổ D:\

## Đóng gói thành .exe

### Cách 1: Sử dụng script build.bat (Windows)

```bash
build.bat
```

File .exe sẽ được tạo trong thư mục `dist\ParkingControlSystem.exe`

### Cách 2: Sử dụng PyInstaller trực tiếp

```bash
# Activate virtual environment
.venv\Scripts\activate

# Build
pyinstaller build_exe.spec --clean
```

### Sau khi build

1. File `config.json` và thư mục `sounds/` sẽ được tự động copy vào `dist/` (nếu có)
2. Nếu chưa có, copy thủ công:
   - `config.json` vào cùng thư mục với file .exe
   - Thư mục `sounds/` (chứa file beep.wav) vào cùng thư mục với file .exe
3. Copy toàn bộ thư mục `dist` lên máy server
4. Chạy file .exe với quyền Administrator

**Cấu trúc thư mục dist sau khi build:**
```
dist/
├── ParkingControlSystem.exe
├── config.json
└── sounds/
    └── beep.wav
```

## Cấu trúc thư mục dự án

```
basicCam/
├── main.py                 # Entry point
├── main_window.py          # Giao diện chính
├── camera_thread.py        # Thread xử lý RTSP stream
├── camera_widget.py        # Widget hiển thị video
├── config_manager.py       # Quản lý cấu hình
├── file_manager.py         # Xử lý lưu file ảnh
├── logger.py              # Hệ thống logging
├── sound_player.py        # Phát âm thanh
├── config.json            # File cấu hình
├── requirements.txt       # Dependencies
├── build_exe.spec        # PyInstaller spec file
├── build.bat             # Script build cho Windows
└── README.md            # File này
```

## Sử dụng

### Giao diện

- **Bên trái:** Làn Xe RA
  - Camera trước (trên)
  - Camera sau/biển số (dưới)
  
- **Bên phải:** Làn Xe VÀO
  - Camera trước (trên)
  - Camera sau/biển số (dưới)

### Chức năng

1. **Xem video realtime:** 4 camera hiển thị đồng thời
2. **Chụp ảnh:** 
   - Click vào khung hình camera, hoặc
   - Bấm nút "Chụp ảnh"
   - Ảnh sẽ được lưu tự động với format: `[LAN]_[yyyyMMdd_HHmmss]_front.jpg` và `[LAN]_[yyyyMMdd_HHmmss]_rear.jpg`
3. **Dừng xe/Kiểm tra:** Bấm nút "Dừng xe / Kiểm tra" để đánh dấu xe đang được kiểm tra

### Cấu trúc file ảnh lưu

```
D:\DuLieuBaiXe\
├── RA_20240101\
│   ├── RA_20240101_143022_front.jpg
│   ├── RA_20240101_143022_rear.jpg
│   └── ...
└── VAO_20240101\
    ├── VAO_20240101_143022_front.jpg
    ├── VAO_20240101_143022_rear.jpg
    └── ...
```

## Xử lý sự cố

### Camera không kết nối được

1. Kiểm tra kết nối mạng đến DVR (192.168.1.108)
2. Kiểm tra RTSP URLs trong `config.json`
3. Xem log file để biết chi tiết lỗi

### Không lưu được file ảnh

1. Đảm bảo chạy với quyền Administrator
2. Kiểm tra quyền ghi vào thư mục `D:\DuLieuBaiXe`
3. Kiểm tra dung lượng ổ cứng

### Ứng dụng bị đơ

1. Kiểm tra log file để xem lỗi
2. Đảm bảo DVR đang hoạt động
3. Khởi động lại ứng dụng

## Logging

File log được lưu tại: `D:\DuLieuBaiXe\app.log`

Format log: `[YYYY-MM-DD HH:MM:SS] [LEVEL] [LAN] Message`

## Phát triển

### Thêm tính năng mới

- Chỉnh sửa các module tương ứng
- Cập nhật `config.json` nếu cần thêm cấu hình
- Test kỹ trước khi build .exe

### Debug

Chạy từ source code với Python để xem log chi tiết trên console.

## License

Dự án nội bộ - Parking Control System

