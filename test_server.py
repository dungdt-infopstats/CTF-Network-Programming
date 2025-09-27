import socket
import threading
import sys
from server_utils import get_ctf_answer

def handle_client(conn, addr, expected_answer):
    try:
        # Send challenge
        conn.send(b"3 + 5 = ?\n")

        # Receive answer
        response = conn.recv(1024).decode().strip()

        if response == "8":
            # Correct answer - send CTF flag
            conn.send(expected_answer.encode())
        else:
            conn.send(b"Wrong answer!")

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()

def start_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 0))  # Bind to any available port
    port = sock.getsockname()[1]

    # Print port as first line (required by system)
    print(port)
    sys.stdout.flush()

    sock.listen(5)

    # Get CTF answer for this port
    ctf_answer = get_ctf_answer(port)

    while True:
        try:
            conn, addr = sock.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(conn, addr, ctf_answer)
            )
            client_thread.daemon = True
            client_thread.start()
        except Exception as e:
            print(f"Server error: {e}")
            break

if __name__ == "__main__":
    start_server()