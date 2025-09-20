# 🌐 Network Programming Online Judge

Hệ thống Online Judge cho môn Lập trình mạng, cho phép sinh viên thực hành lập trình socket thông qua các bài tập tương tác thực tế.

## 🎯 Tính năng chính

- **Web Interface**: Giao diện web thân thiện cho sinh viên và giảng viên
- **Judge Server**: Máy chủ chấm bài tự động với các bài toán mạng thực tế
- **Session Token**: Hệ thống token duy nhất cho mỗi sinh viên, chống gian lận
- **HMAC Verification**: Xác thực bài nộp bằng mã hóa HMAC-SHA256
- **Real-time Interaction**: Tương tác thời gian thực giữa client và server

## 📁 Cấu trúc dự án

```
online-judge-demo/
├── web_server.py          # Flask Web Server
├── judge_server.py        # Judge Server (xử lý bài toán mạng)
├── client_demo.py         # Chương trình client demo
├── server_log.txt         # File dữ liệu mẫu cho bài tập
├── README.md              # File hướng dẫn này
├── templates/             # Template HTML
│   ├── login.html
│   ├── index.html
│   └── problem.html
└── static/
    └── style.css          # CSS styling
```

## 🚀 Cách chạy hệ thống

### Bước 1: Cài đặt dependencies

```bash
pip install Flask
```

### Bước 2: Khởi động Judge Server

Mở terminal đầu tiên và chạy:

```bash
cd online-judge-demo
python judge_server.py
```

Bạn sẽ thấy output:
```
🌐 NETWORK PROGRAMMING ONLINE JUDGE - JUDGE SERVER
================================================================
[*] Judge Server đang lắng nghe trên 0.0.0.0:10005
[*] Sẵn sàng nhận kết nối từ client...
```

### Bước 3: Khởi động Web Server

Mở terminal thứ hai và chạy:

```bash
cd online-judge-demo
python web_server.py
```

Bạn sẽ thấy output:
```
🌐 NETWORK PROGRAMMING ONLINE JUDGE - WEB SERVER
================================================================
🔗 URL: http://127.0.0.1:5000
👥 Demo accounts: student1, student2, admin
================================================================
```

### Bước 4: Truy cập giao diện web

Mở trình duyệt và truy cập: `http://127.0.0.1:5000`

**Tài khoản demo:**
- Username: `student1` hoặc `student2`
- Password: không cần (chỉ cần username đúng)

## 📝 Hướng dẫn sử dụng

### Cho sinh viên:

1. **Đăng nhập** vào hệ thống web
2. **Chọn bài tập** từ danh sách
3. **Lấy thông tin kết nối**:
   - Host: `127.0.0.1`
   - Port: `10005`
   - Session Token: (được tạo tự động cho mỗi sinh viên)
4. **Viết chương trình client** để giải bài toán
5. **Chạy chương trình** và lấy "Mã nộp bài"
6. **Nộp mã** trên trang web để hoàn thành

### Chương trình client mẫu:

Bạn có thể sử dụng `client_demo.py` làm tham khảo:

```bash
python client_demo.py
```

Hoặc viết chương trình riêng theo cấu trúc:

```python
import socket

# Kết nối đến Judge Server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 10005))

# Gửi Session Token khi server yêu cầu
# Nhận và xử lý file log
# Tìm SECRET_CODE và gửi lại
# Nhận submission code

sock.close()
```

## 🎮 Bài tập hiện có

### Bài 1: Tải và Phân tích File Log

**Mục tiêu**: Học cách nhận file qua socket và xử lý dữ liệu

**Kỹ năng**:
- Lập trình socket TCP
- Nhận dữ liệu nhị phân
- Xử lý file text
- Phân tích và trích xuất thông tin

**Luồng thực hiện**:
1. Kết nối đến Judge Server
2. Xác thực bằng Session Token
3. Nhận file log từ server
4. Tìm `SECRET_CODE` trong file
5. Gửi kết quả lại server
6. Nhận "Mã nộp bài" để nộp trên web

## 🔧 Kiến trúc hệ thống

### Web Server (Flask)
- Quản lý người dùng và phiên làm việc
- Tạo Session Token duy nhất cho mỗi sinh viên
- Xác thực "Mã nộp bài" bằng HMAC-SHA256
- Giao diện web responsive

### Judge Server (Python Socket)
- Lắng nghe kết nối từ client sinh viên
- Xác thực Session Token
- Thực hiện kịch bản bài toán
- Tạo "Mã nộp bài" động cho mỗi sinh viên

### Cơ chế bảo mật
- **Session Token**: Mỗi sinh viên có token riêng, không thể chia sẻ
- **HMAC-SHA256**: Mã nộp bài được tạo từ flag gốc + session token
- **One-time use**: Token bị xóa sau khi nộp bài thành công

## 🛠️ Mở rộng hệ thống

### Thêm bài tập mới:

1. **Cập nhật `PROBLEMS` trong `web_server.py`**:
```python
{
    "id": 2,
    "title": "Bài 2: Tên bài mới",
    "description": "Mô tả bài toán...",
    "port": 10006,
    "base_flag": "flag-moi-cho-bai-2"
}
```

2. **Thêm logic xử lý trong `judge_server.py`**:
```python
# Thêm port mới và logic tương ứng
if port == 10006:
    handle_new_problem(conn, addr)
```

### Tích hợp cơ sở dữ liệu:

Thay thế các biến toàn cục bằng PostgreSQL/MySQL:
- Bảng `users`: Thông tin người dùng
- Bảng `problems`: Danh sách bài tập
- Bảng `sessions`: Session tokens
- Bảng `submissions`: Lịch sử nộp bài

## 🐛 Troubleshooting

### Judge Server không khởi động được:
- Kiểm tra port 10005 có bị chiếm không: `netstat -an | grep 10005`
- Đảm bảo file `server_log.txt` tồn tại

### Web Server lỗi:
- Kiểm tra Flask đã được cài đặt: `pip install Flask`
- Đảm bảo thư mục `templates/` và `static/` tồn tại

### Client không kết nối được:
- Kiểm tra Judge Server đang chạy
- Thử kết nối thủ công: `telnet 127.0.0.1 10005`

## 📚 Tài liệu tham khảo

- [Python Socket Programming](https://docs.python.org/3/library/socket.html)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [HMAC Authentication](https://docs.python.org/3/library/hmac.html)

## 👥 Đóng góp

Hệ thống này được thiết kế để dễ dàng mở rộng. Bạn có thể:
- Thêm bài tập mới
- Cải thiện giao diện
- Tích hợp cơ sở dữ liệu
- Thêm tính năng bảo mật

## 📄 License

MIT License - Tự do sử dụng cho mục đích giáo dục và nghiên cứu.

