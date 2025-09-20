#!/usr/bin/env python3
"""
Client Demo cho hệ thống Online Judge Network Programming
Đây là chương trình mẫu mà sinh viên có thể tham khảo để giải bài toán
"""

import socket
import os
import sys

# --- Cấu hình kết nối ---
JUDGE_HOST = '127.0.0.1'  # Địa chỉ Judge Server
JUDGE_PORT = 10005        # Port của bài tập
BUFFER_SIZE = 4096        # Kích thước buffer để nhận dữ liệu

# --- Tên file sẽ được lưu ở máy client ---
LOCAL_FILENAME = "received_log.txt"

def print_banner():
    """In banner chào mừng"""
    print("=" * 60)
    print("🌐 NETWORK PROGRAMMING CLIENT DEMO")
    print("=" * 60)
    print("Chương trình này sẽ kết nối đến Judge Server và giải bài toán:")
    print("'Tải và Phân tích File Log'")
    print("=" * 60)

def get_session_token():
    """Lấy Session Token từ người dùng"""
    print("\n📋 BƯỚC 1: NHẬP SESSION TOKEN")
    print("-" * 30)
    print("Hãy truy cập trang web Online Judge và:")
    print("1. Đăng nhập với tài khoản của bạn")
    print("2. Chọn bài 'Tải và Phân tích File Log'")
    print("3. Sao chép Session Token được hiển thị")
    print()
    
    while True:
        token = input("Nhập Session Token của bạn: ").strip()
        if token:
            return token
        print("❌ Token không được để trống. Vui lòng thử lại.")

def connect_to_server(host, port):
    """Tạo kết nối đến Judge Server"""
    print(f"\n🔗 BƯỚC 2: KẾT NỐI ĐẾN SERVER")
    print("-" * 30)
    print(f"Đang kết nối đến {host}:{port}...")
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(30)  # Timeout 30 giây
        client_socket.connect((host, port))
        print("✅ Kết nối thành công!")
        return client_socket
    except Exception as e:
        print(f"❌ Không thể kết nối: {e}")
        print("💡 Hãy đảm bảo Judge Server đang chạy.")
        return None

def authenticate(client_socket, session_token):
    """Xác thực với Judge Server"""
    print(f"\n🔐 BƯỚC 3: XÁC THỰC")
    print("-" * 30)
    
    try:
        # Nhận yêu cầu từ server
        server_prompt = client_socket.recv(1024).decode().strip()
        print(f"Server: {server_prompt}")
        
        if server_prompt == "SEND_TOKEN":
            print("Đang gửi Session Token...")
            client_socket.sendall((session_token + '\n').encode())
            print("✅ Đã gửi token thành công!")
            return True
        else:
            print(f"❌ Giao thức không mong muốn từ server: {server_prompt}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi trong quá trình xác thực: {e}")
        return False

def receive_file(client_socket):
    """Nhận file từ Judge Server"""
    print(f"\n📥 BƯỚC 4: NHẬN FILE LOG")
    print("-" * 30)
    
    try:
        # Nhận header thông tin file
        file_header = client_socket.recv(1024).decode().strip()
        print(f"Server: {file_header}")
        
        if not file_header.startswith("SENDING_FILE:"):
            print(f"❌ Không nhận được header gửi file: {file_header}")
            return False
            
        # Phân tích header để lấy tên file và kích thước
        # Format: "SENDING_FILE:filename:filesize"
        parts = file_header.split(':')
        if len(parts) != 3:
            print("❌ Header file không đúng định dạng")
            return False
            
        filename = parts[1]
        filesize = int(parts[2])
        print(f"📄 File: {filename}")
        print(f"📊 Kích thước: {filesize} bytes")
        
        # Nhận và lưu file
        print(f"Đang tải file...")
        bytes_received = 0
        
        with open(LOCAL_FILENAME, 'wb') as f:
            while bytes_received < filesize:
                chunk = client_socket.recv(min(BUFFER_SIZE, filesize - bytes_received))
                if not chunk:
                    print("❌ Kết nối bị ngắt đột ngột")
                    return False
                f.write(chunk)
                bytes_received += len(chunk)
                
                # Hiển thị tiến độ
                progress = (bytes_received / filesize) * 100
                print(f"\rTiến độ: {progress:.1f}% ({bytes_received}/{filesize} bytes)", end='')
        
        print(f"\n✅ Đã tải xong file và lưu tại '{LOCAL_FILENAME}'")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi nhận file: {e}")
        return False

def analyze_log_file():
    """Phân tích file log để tìm SECRET_CODE"""
    print(f"\n🔍 BƯỚC 5: PHÂN TÍCH FILE LOG")
    print("-" * 30)
    
    try:
        print(f"Đang đọc file '{LOCAL_FILENAME}'...")
        
        # Hiển thị nội dung file
        print("\n📄 Nội dung file log:")
        print("-" * 40)
        
        secret_code = None
        line_count = 0
        
        with open(LOCAL_FILENAME, 'r', encoding='utf-8') as f:
            for line in f:
                line_count += 1
                line = line.strip()
                print(f"{line_count:2d}: {line}")
                
                # Tìm SECRET_CODE
                if line.startswith("SECRET_CODE:"):
                    secret_code = line.split(':', 1)[1].strip()
                    print(f"\n🎯 Tìm thấy SECRET_CODE tại dòng {line_count}: '{secret_code}'")
        
        print("-" * 40)
        
        # Xóa file tạm sau khi đã phân tích
        os.remove(LOCAL_FILENAME)
        print(f"🗑️  Đã xóa file tạm '{LOCAL_FILENAME}'")
        
        if secret_code:
            return secret_code
        else:
            print("❌ Không tìm thấy SECRET_CODE trong file log")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi khi phân tích file: {e}")
        return None

def send_result(client_socket, secret_code):
    """Gửi kết quả phân tích lại cho server"""
    print(f"\n📤 BƯỚC 6: GỬI KẾT QUẢ")
    print("-" * 30)
    
    try:
        result_message = f"RESULT: {secret_code}\n"
        print(f"Đang gửi: {result_message.strip()}")
        
        client_socket.sendall(result_message.encode())
        print("✅ Đã gửi kết quả thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi gửi kết quả: {e}")
        return False

def receive_submission_code(client_socket):
    """Nhận Mã nộp bài từ server"""
    print(f"\n🏆 BƯỚC 7: NHẬN MÃ NỘP BÀI")
    print("-" * 30)
    
    try:
        submission_code = client_socket.recv(1024).decode().strip()
        
        if submission_code.startswith("INCORRECT"):
            print("❌ Server báo kết quả không chính xác!")
            print(f"Phản hồi: {submission_code}")
            return None
        elif len(submission_code) == 64:  # HMAC-SHA256 có độ dài 64 ký tự hex
            print("🎉 THÀNH CÔNG! Bạn đã giải đúng bài toán!")
            print("=" * 60)
            print("🏆 MÃ NỘP BÀI CỦA BẠN:")
            print(f"   {submission_code}")
            print("=" * 60)
            print("📋 HƯỚNG DẪN TIẾP THEO:")
            print("1. Sao chép mã nộp bài ở trên")
            print("2. Quay lại trang web Online Judge")
            print("3. Dán mã vào ô 'Submission Code'")
            print("4. Nhấn 'Nộp bài' để hoàn thành")
            print("=" * 60)
            return submission_code
        else:
            print(f"❌ Phản hồi không mong muốn từ server: {submission_code}")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi khi nhận mã nộp bài: {e}")
        return None

def main():
    """Hàm chính"""
    print_banner()
    
    # Bước 1: Lấy Session Token
    session_token = get_session_token()
    
    # Bước 2: Kết nối đến server
    client_socket = connect_to_server(JUDGE_HOST, JUDGE_PORT)
    if not client_socket:
        return
    
    try:
        # Bước 3: Xác thực
        if not authenticate(client_socket, session_token):
            return
        
        # Bước 4: Nhận file
        if not receive_file(client_socket):
            return
        
        # Bước 5: Phân tích file
        secret_code = analyze_log_file()
        if not secret_code:
            return
        
        # Bước 6: Gửi kết quả
        if not send_result(client_socket, secret_code):
            return
        
        # Bước 7: Nhận mã nộp bài
        submission_code = receive_submission_code(client_socket)
        
        if submission_code:
            print("\n🎊 CHÚC MỪNG! Bạn đã hoàn thành thành công bài tập!")
        else:
            print("\n😞 Có lỗi xảy ra. Hãy thử lại.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Chương trình bị dừng bởi người dùng.")
    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn: {e}")
    finally:
        client_socket.close()
        print("\n🔌 Đã đóng kết nối.")

if __name__ == '__main__':
    main()

