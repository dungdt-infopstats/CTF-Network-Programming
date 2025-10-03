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
