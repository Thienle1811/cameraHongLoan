# Hướng dẫn cấu hình âm thanh

## Cách thêm file âm thanh

### Tùy chọn 1: Thêm file WAV vào thư mục `sounds/`

1. Tạo thư mục `sounds` trong thư mục dự án (nếu chưa có)
2. Đặt file WAV vào thư mục `sounds/` với một trong các tên sau:
   - `beep.wav`
   - `pip.wav`
   - `capture.wav`
   - `sound.wav`

3. Ứng dụng sẽ tự động tìm và sử dụng file này

### Tùy chọn 2: Chỉ định đường dẫn trong config.json

Thêm vào `config.json`:

```json
{
  "sound_file": "C:\\path\\to\\your\\sound.wav"
}
```

## Lưu ý

- **WAV files**: Được hỗ trợ đầy đủ (khuyến nghị)
- **MP3 files**: Không được hỗ trợ trực tiếp. Cần chuyển đổi sang WAV hoặc dùng system sound
- **System sound**: Nếu không có file, ứng dụng sẽ tự động dùng system beep

## Kiểm tra âm thanh

1. Chạy ứng dụng
2. Click nút "XÁC NHẬN XE RA" hoặc "XÁC NHẬN XE VÀO"
3. Bạn sẽ nghe thấy âm thanh "Píp"

Nếu không nghe thấy:
- Kiểm tra volume hệ thống
- Kiểm tra file âm thanh có tồn tại không
- Kiểm tra quyền truy cập file

