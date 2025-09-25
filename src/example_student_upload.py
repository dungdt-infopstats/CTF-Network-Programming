#!/usr/bin/env python3
"""
Example server code that a student might upload for testing
This demonstrates the challenge server format
"""

import socket
import sys
import threading
import os

# Import the CTF helper (this is the key requirement)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ctf_helper import get_ctf_answer_for_current_server, send_ctf_answer_to_client

def handle_client(client_socket, client_address):
    """Handle client connections for student's server"""
    print(f"Student server: New connection from {client_address}")

    try:
        # Send custom welcome message
        client_socket.send(b"Welcome to Student's Custom Server!\n")
        client_socket.send(b"This is a server uploaded by a student.\n")
        client_socket.send(b"Commands: 'hello', 'info', 'flag'\n")

        while True:
            data = client_socket.recv(1024).decode().strip()
            if not data:
                break

            print(f"Student server received: {data}")

            if data.lower() == "hello":
                client_socket.send(b"Hello from student server!\n")
            elif data.lower() == "info":
                client_socket.send(b"This server was created by a student for the CTF challenge.\n")
            elif data.lower() == "flag":
                # Use the common CTF helper function
                if send_ctf_answer_to_client(client_socket):
                    print(f"Sent CTF answer to {client_address}")
                    break
                else:
                    print(f"Failed to send CTF answer to {client_address}")
            else:
                client_socket.send(f"Unknown command: {data}\n".encode())

    except Exception as e:
        print(f"Student server error: {e}")
    finally:
        client_socket.close()
        print(f"Student server: Connection closed with {client_address}")

def start_student_server(port):
    """Start the student's custom server"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind(('localhost', port))
        server.listen(3)
        print(f"Student server listening on localhost:{port}")

        while True:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            client_thread.daemon = True
            client_thread.start()

    except KeyboardInterrupt:
        print("\nStudent server shutting down...")
    except Exception as e:
        print(f"Student server error: {e}")
    finally:
        server.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python example_student_upload.py <port>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        start_student_server(port)
    except ValueError:
        print("Invalid port number")
        sys.exit(1)