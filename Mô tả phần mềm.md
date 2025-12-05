HỆ THỐNG QUẢN LÝ BÃI XE (PARKING CONTROL SYSTEM)

Bản mô tả dành cho lập trình & triển khai phần mềm

1. Hạ tầng hệ thống & kết nối mạng
1.1. Máy chủ (Server)

Hệ điều hành: Windows Server.

Địa chỉ IP: 192.168.1.150 (IP tĩnh).

Chức năng:

Chạy phần mềm Parking Control (file .exe dạng portable).

Lưu trữ hình ảnh chụp từ camera (ổ D: hoặc thư mục cấu hình).

1.2. Đầu ghi hình (DVR Dahua)

Địa chỉ IP: 192.168.1.108

Tài khoản đăng nhập DVR:

Username: admin2

Password: 123321abc

Cổng RTSP: 554 (đã xác nhận mở bằng Nmap).

Yêu cầu đồng bộ thời gian:

Thời gian trên đầu ghi hiện đang lệch khoảng -1 giờ so với thực tế.

Kỹ thuật viên phải chỉnh lại giờ trong giao diện web DVR:

Truy cập: http://192.168.1.108

Đăng nhập bằng admin2 / 123321abc

Đặt đúng múi giờ: GMT+7

Lý do: đảm bảo timestamp trong dữ liệu ghi hình khớp với thời gian thực, đồng bộ với log và file ảnh trên Server.

2. Đặc tả phần mềm & triển khai
2.1. Định dạng & triển khai phần mềm

Phần mềm dạng Portable:

Chỉ cần chạy file .exe, không có bước cài đặt phức tạp.

Cho phép copy/triển khai nhanh qua USB.

Khuyến nghị vị trí lưu trữ:

Thư mục: D:\PhanMemBaiXe\

Hoặc tạo shortcut từ đây ra Desktop.

Mục đích: tránh mất dữ liệu khi cài lại hệ điều hành (ổ C).

Khi chạy phần mềm:

Yêu cầu chạy với quyền Run as Administrator

Để có quyền ghi file ảnh chụp và log xuống ổ cứng.

2.2. Yêu cầu chung cho phần mềm

Không phụ thuộc cài đặt phức tạp (registry tối thiểu).

Lưu được cấu hình (RTSP, thư mục lưu ảnh, âm thanh cảnh báo) vào:

File config riêng (.json, .ini, …) hoặc registry (tùy thiết kế).

Có cơ chế log:

Lỗi kết nối RTSP.

Lỗi lưu file.

Sự kiện chụp ảnh (thời gian, làn xe, camera, đường dẫn file).

3. Cấu hình & xử lý camera (RTSP)
3.1. Cấu trúc chuỗi RTSP

Mỗi camera kết nối qua RTSP theo cấu trúc:

rtsp://admin2:123321abc@192.168.1.108:554/cam/realmonitor?channel=[KENH]&subtype=[SUBTYPE]


channel: số kênh trên đầu ghi (1–4).

subtype:

1: luồng phụ (sub stream) – độ phân giải thấp, nhẹ, giảm tải CPU/RAM.

0: luồng chính (main stream) – độ nét cao, phù hợp khi cần nhận diện biển số rõ hơn.

3.2. Mapping RTSP cho từng camera

Hệ thống sử dụng 4 kênh camera tương ứng:

Khu vực	Vị trí camera	Channel	Đường dẫn RTSP mẫu
Làn Xe RA (trái)	Camera Trước	1	rtsp://admin2:123321abc@192.168.1.108:554/cam/realmonitor?channel=1&subtype=1
Làn Xe RA (trái)	Camera Sau (biển số)	2	rtsp://admin2:123321abc@192.168.1.108:554/cam/realmonitor?channel=2&subtype=1
Làn Xe VÀO (phải)	Camera Trước	3	rtsp://admin2:123321abc@192.168.1.108:554/cam/realmonitor?channel=3&subtype=1
Làn Xe VÀO (phải)	Camera Sau (biển số)	4	rtsp://admin2:123321abc@192.168.1.108:554/cam/realmonitor?channel=4&subtype=1

Yêu cầu phần mềm:

Cho phép cấu hình/sửa các chuỗi RTSP (có thể qua file cấu hình hoặc màn hình “Cài đặt”).

Tự động thử kết nối lại nếu luồng RTSP bị mất.

Hiển thị trạng thái kết nối từng camera (OK / Connecting… / Error).

4. Thiết kế giao diện vận hành (UI/UX)

Giao diện chính của phần mềm chia làm 2 khối chính, tương ứng 2 làn xe:

4.1. Khu vực Làn Xe RA (bên trái)

2 khung hình camera:

Khung trên: hình từ camera trước (mặt xe/người lái).

Khung dưới: hình từ camera sau (biển số phía sau).

Nút chức năng chính:

Nút “Dừng xe / Kiểm tra” (hoặc text tương đương).

Nút chụp (nếu tách riêng) hoặc cho phép click trực tiếp lên khung hình.

4.2. Khu vực Làn Xe VÀO (bên phải)

Cấu trúc tương tự Làn Xe RA:

Khung trên: camera trước.

Khung dưới: camera sau.

Nút “Dừng xe / Kiểm tra”.

Nút chụp hoặc thao tác click trên khu vực hình.

4.3. Yêu cầu về trải nghiệm người dùng

Màn hình hiển thị realtime 4 camera đồng thời, độ trễ thấp.

Vị trí nút bấm rõ ràng, dễ thao tác bằng chuột.

Có hiển thị tên làn (RA / VÀO) và thông tin cơ bản:

Trạng thái kết nối camera.

Trạng thái lần chụp gần nhất (thời gian, thành công/thất bại).

5. Luồng nghiệp vụ chính (Business Flow)
5.1. Sự kiện “Xe tới vị trí kiểm soát”

Nhân viên vận hành quan sát:

Xe đã nằm gọn trong khung hình của camera trước và camera sau.

Có thể hiển thị “vùng tham chiếu” trên UI (option).

(Đoạn này chủ yếu là nghiệp vụ, phần mềm chỉ cần hiển thị video mượt.)

5.2. Sự kiện “Dừng xe / Xét xe”

Nhân viên vận hành bấm nút tương ứng làn:

Bên trái: áp dụng cho Làn RA.

Bên phải: áp dụng cho Làn VÀO.

Mục đích:

Đánh dấu trạng thái xe đang trong quá trình kiểm tra/chụp.

Có thể dùng để log sự kiện hoặc kích hoạt overlay (tuỳ thiết kế phần mềm).

5.3. Sự kiện “Chụp hình & Lưu dữ liệu”

Trigger chụp:

Một trong các thao tác:

Click chuột trong vùng hình ảnh của làn tương ứng.

Hoặc bấm nút “Chụp” riêng nằm ở nửa dưới giao diện.

Hành vi phần mềm khi chụp:

Phát âm thanh “PÍP”:

Thể hiện trạng thái đã chụp thành công.

Đồng thời lấy snapshot từ 2 camera của làn đó:

1 ảnh từ camera trước.

1 ảnh từ camera sau.

Lưu file ảnh xuống thư mục dữ liệu:

Thư mục gốc: cấu hình được, ví dụ: D:\DuLieuBaiXe\.

Cấu trúc thư mục/filename đề xuất (tuỳ bạn triển khai, ví dụ):

D:\DuLieuBaiXe\[LAN]_[yyyyMMdd]\[LAN]_[yyyyMMdd_HHmmss]_front.jpg

D:\DuLieuBaiXe\[LAN]_[yyyyMMdd]\[LAN]_[yyyyMMdd_HHmmss]_rear.jpg

Trong đó:

LAN: RA hoặc VAO.

timestamp: dùng giờ hệ thống Server (đã đồng bộ với DVR).

(Tuỳ chọn) Ghi log:

Thời gian chụp.

Làn xe.

Kết quả chụp (OK/FAIL).

Đường dẫn 2 file ảnh.

Sau khi chụp xong:

Có thể hiển thị nhanh hình vừa chụp (preview) hoặc chỉ log lại, tuỳ yêu cầu UI.