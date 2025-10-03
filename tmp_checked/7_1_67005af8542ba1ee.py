# server.py
import socket
import threading
import sys
from server_utils import get_ctf_answer

# client_handler.py
from typing import Tuple
import socket

def handle_client(conn: socket.socket, addr: Tuple[str, int], expected_answer: str) -> None:
    """
    Xử lý 1 client:
    - Gửi challenge
    - Nhận response
    - Nếu đúng gửi expected_answer, nếu sai gửi "Wrong answer!"
    - Đóng kết nối
    """
    try:
        conn.sendall(b"3 + 5 = ?\n")

        response = conn.recv(1024).decode(errors='ignore').strip()

        if response == "8":
            conn.sendall(expected_answer.encode())
        else:
            conn.sendall(b"Wrong answer!")

    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def start_server(host: str = '0.0.0.0', port: int = 0) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))  # bind đến port tự động nếu port=0
    port = sock.getsockname()[1]

    # In port ra dòng đầu (yêu cầu hệ thống)
    print(port)
    sys.stdout.flush()

    sock.listen(5)

    # Lấy expected_answer cho port hiện tại
    ctf_answer = get_ctf_answer(port)

    try:
        while True:
            conn, addr = sock.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(conn, addr, ctf_answer)
            )
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("Server shutting down.")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    start_server()
