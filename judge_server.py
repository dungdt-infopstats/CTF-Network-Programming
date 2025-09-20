#!/usr/bin/env python3
"""
Judge Server cho hệ thống Online Judge Network Programming
Xử lý các kết nối từ client của sinh viên và tương tác theo kịch bản bài toán
"""

import socket
import threading
import os
import hmac
import hashlib
import time
import json

# Cấu hình server
HOST = '0.0.0.0'  # Lắng nghe trên tất cả interface
PROBLEM_PORT = 10005
BASE_FLAG = "flask-is-awesome-2025"  # Flag gốc, phải khớp với web server

# Giả lập CSDL Session Token (trong thực tế sẽ truy vấn DB)
# Web server sẽ thêm token vào đây, Judge server chỉ đọc
# Cấu trúc: { "token": {"username": "student1", "problem_id": 1, "created_at": timestamp} }
VALID_TOKENS = {}

# File log để giao tiếp với Web Server (đơn giản hóa cho demo)
TOKEN_FILE = "/tmp/judge_tokens.json"

def load_tokens():
    """Đọc danh sách token hợp lệ từ file"""
    global VALID_TOKENS
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                VALID_TOKENS = json.load(f)
    except Exception as e:
        print(f"[JUDGE] Lỗi khi đọc token file: {e}")
        VALID_TOKENS = {}

def generate_submission_code(session_token, base_flag):
    """Tạo mã nộp bài bằng HMAC-SHA256."""
    return hmac.new(base_flag.encode(), session_token.encode(), hashlib.sha256).hexdigest()

def handle_client(conn, addr):
    """Xử lý một client kết nối"""
    print(f"[JUDGE] Kết nối mới từ {addr}")
    
    try:
        # 1. Yêu cầu và xác thực Session Token
        conn.sendall(b"SEND_TOKEN\n")
        
        # Đợi client gửi token (timeout 30 giây)
        conn.settimeout(30.0)
        token_data = conn.recv(1024).decode().strip()
        
        if not token_data:
            print(f"[JUDGE] Không nhận được token từ {addr}")
            conn.sendall(b"NO_TOKEN_RECEIVED\n")
            return

        # Reload tokens từ file để có dữ liệu mới nhất
        load_tokens()
        
        if token_data not in VALID_TOKENS:
            print(f"[JUDGE] Token không hợp lệ: {token_data}. Đóng kết nối.")
            conn.sendall(b"INVALID_TOKEN\n")
            return

        token_info = VALID_TOKENS[token_data]
        username = token_info.get('username', 'unknown')
        print(f"[JUDGE] Token hợp lệ cho user '{username}'.")

        # 2. Gửi file log
        filepath = "server_log.txt"
        if not os.path.exists(filepath):
            print(f"[JUDGE] File log không tồn tại: {filepath}")
            conn.sendall(b"FILE_NOT_FOUND\n")
            return
            
        filesize = os.path.getsize(filepath)
        
        # Gửi header thông tin file
        header = f"SENDING_FILE:{os.path.basename(filepath)}:{filesize}\n"
        conn.sendall(header.encode())
        
        # Gửi nội dung file
        with open(filepath, 'rb') as f:
            data = f.read()
            conn.sendall(data)
        
        print(f"[JUDGE] Đã gửi file '{filepath}' ({filesize} bytes) cho {username}.")

        # 3. Chờ kết quả phân tích từ client
        print(f"[JUDGE] Đang chờ kết quả phân tích từ {username}...")
        client_response = conn.recv(1024).decode().strip()
        
        if not client_response.startswith("RESULT:"):
            print(f"[JUDGE] Phản hồi không đúng định dạng từ {username}: {client_response}")
            conn.sendall(b"INVALID_FORMAT\n")
            return
            
        secret_code = client_response.split(':', 1)[1].strip()
        
        # Lấy secret code thật từ file log để so sánh
        real_secret = ""
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith("SECRET_CODE:"):
                    real_secret = line.split(':', 1)[1].strip()
                    print(real_secret)
                    break
        
        if secret_code == real_secret:
            print(f"[JUDGE] {username} gửi đúng secret code: {secret_code}")
            
            # 4. Tạo và gửi mã nộp bài
            submission_code = generate_submission_code(token_data, BASE_FLAG)
            conn.sendall(submission_code.encode())
            print(f"[JUDGE] Đã gửi submission code cho {username}: {submission_code}")
            
        else:
            print(f"[JUDGE] {username} gửi sai secret code. Mong đợi: '{real_secret}', nhận được: '{secret_code}'")
            conn.sendall(b"INCORRECT_SECRET_CODE\n")

    except socket.timeout:
        print(f"[JUDGE] Timeout khi chờ dữ liệu từ {addr}")
        try:
            conn.sendall(b"TIMEOUT\n")
        except:
            pass
    except Exception as e:
        print(f"[JUDGE] Lỗi trong quá trình xử lý client {addr}: {e}")
        try:
            conn.sendall(b"SERVER_ERROR\n")
        except:
            pass
    finally:
        try:
            conn.close()
        except:
            pass
        print(f"[JUDGE] Đóng kết nối với {addr}")

def start_judge_server():
    """Khởi động Judge Server"""
    # Tạo file token nếu chưa có
    if not os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'w') as f:
            json.dump({}, f)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PROBLEM_PORT))
        server.listen(5)
        print(f"[*] Judge Server đang lắng nghe trên {HOST}:{PROBLEM_PORT}")
        print(f"[*] File log: {os.path.abspath('server_log.txt')}")
        print(f"[*] Token file: {TOKEN_FILE}")
        print(f"[*] Sẵn sàng nhận kết nối từ client...")
        
        while True:
            try:
                conn, addr = server.accept()
                # Xử lý mỗi client trong một thread riêng
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                thread.daemon = True
                thread.start()
            except KeyboardInterrupt:
                print("\n[*] Đang tắt Judge Server...")
                break
            except Exception as e:
                print(f"[JUDGE] Lỗi khi accept connection: {e}")
                
    except Exception as e:
        print(f"[JUDGE] Lỗi khi khởi động server: {e}")
    finally:
        server.close()
        print("[*] Judge Server đã tắt.")

if __name__ == '__main__':
    print("=" * 60)
    print("🌐 NETWORK PROGRAMMING ONLINE JUDGE - JUDGE SERVER")
    print("=" * 60)
    
    # Kiểm tra file log có tồn tại không
    if not os.path.exists("server_log.txt"):
        print("[!] Cảnh báo: File 'server_log.txt' không tồn tại!")
        print("[!] Hãy đảm bảo file này có trong thư mục hiện tại.")
        exit(1)
    
    try:
        start_judge_server()
    except KeyboardInterrupt:
        print("\n[*] Judge Server đã được tắt bởi người dùng.")
    except Exception as e:
        print(f"[!] Lỗi nghiêm trọng: {e}")

