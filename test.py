

import socket
import hmac
import hashlib
import os
import time

JUDGE_SERVER_HOST = '127.0.0.1'
JUDGE_SERVER_PORT = 10005

def solve_problem(session_token):
    print(f"[CLIENT] Bắt đầu giải bài với Session Token: {session_token}")
    
    try:
        # 1. Kết nối đến Judge Server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((JUDGE_SERVER_HOST, JUDGE_SERVER_PORT))
            print(f"[CLIENT] Đã kết nối đến Judge Server tại {JUDGE_SERVER_HOST}:{JUDGE_SERVER_PORT}")

            # 2. Gửi Session Token
            sock.sendall(session_token.encode() + b'\n')
            print(f"[CLIENT] Đã gửi Session Token.")

            # 3. Nhận File Log
            log_data = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                log_data += chunk
            
            log_content = log_data.decode().strip()
            print(f"[CLIENT] Đã nhận file log có độ dài {len(log_content)} bytes.")
            print(log_content)  # In nội dung file log để kiểm tra

            # 4. Phân tích File Log để tìm SECRET_CODE
            secret_code = None
            for line in log_content.splitlines():
                if "SECRET_CODE:" in line:
                    secret_code = line.split("SECRET_CODE:")[1].strip()
                    break
            
            if not secret_code:
                print("[CLIENT] Không tìm thấy SECRET_CODE trong file log.")
                return None
            
            print(f"[CLIENT] Đã tìm thấy SECRET_CODE: {secret_code}")

            # 5. Gửi SECRET_CODE trở lại Judge Server
            sock.sendall(secret_code.encode() + b'\n')
            print(f"[CLIENT] Đã gửi SECRET_CODE.")

            # 6. Nhận Base Flag từ Judge Server
            base_flag = sock.recv(1024).decode().strip()
            if not base_flag:
                print("[CLIENT] Không nhận được Base Flag từ Judge Server.")
                return None
            
            print(f"[CLIENT] Đã nhận Base Flag: {base_flag}")

            # 7. Tạo Submission Code
            submission_code = hmac.new(base_flag.encode(), session_token.encode(), hashlib.sha256).hexdigest()
            print(f"[CLIENT] Submission Code được tạo: {submission_code}")
            
            return submission_code

    except ConnectionRefusedError:
        print(f"[CLIENT ERROR] Kết nối bị từ chối. Đảm bảo Judge Server đang chạy trên {JUDGE_SERVER_HOST}:{JUDGE_SERVER_PORT}")
    except Exception as e:
        print(f"[CLIENT ERROR] Đã xảy ra lỗi: {e}")
    
    return None

if __name__ == '__main__':
    print("=" * 60)
    print("💻 CLIENT DEMO - GIẢI BÀI TẬP NETWORK PROGRAMMING")
    print("=" * 60)
    print("Hướng dẫn:")
    print("1. Đăng nhập vào Web Server (URL đã được cung cấp).")
    print("2. Truy cập trang chi tiết bài tập 'Tải và Phân tích File Log'.")
    print("3. Lấy 'Session Token' hiển thị trên trang đó.")
    print("4. Dán 'Session Token' vào đây khi được yêu cầu.")
    print("=" * 60)

    # Lấy Session Token từ người dùng
    session_token_input = input("Vui lòng nhập Session Token của bạn: ").strip()

    if not session_token_input:
        print("[CLIENT] Session Token không được để trống. Thoát.")
    else:
        final_submission_code = solve_problem(session_token_input)
        if final_submission_code:
            print("=" * 60)
            print("✅ Đã tạo thành công Submission Code!")
            print(f"Mã nộp bài của bạn là: {final_submission_code}")
            print("Vui lòng dán mã này vào ô nộp bài trên Web Server để hoàn thành.")
            print("=" * 60)
        else:
            print("=" * 60)
            print("❌ Không thể tạo Submission Code. Vui lòng kiểm tra lại log lỗi.")
            print("Đảm bảo Judge Server đang chạy và Session Token hợp lệ.")
            print("=" * 60)

