#!/usr/bin/env python3
"""
Example Challenge Server - Echo Server
This server will be executed automatically when a student starts challenge 1
"""

import socket
import sys
import threading
import os

# Add the parent directory to sys.path to import ctf_helper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ctf_helper import get_ctf_answer_for_current_server

def handle_client(client_socket, client_address):
    """Handle individual client connections"""
    print(f"New connection from {client_address}")

    try:
        # Send welcome message
        client_socket.send(b"Welcome to Echo Challenge!\n")
        client_socket.send(b"Send me any message and I'll echo it back.\n")
        client_socket.send(b"Send 'GET_FLAG' to get your CTF answer.\n")

        while True:
            # Receive message from client
            data = client_socket.recv(1024).decode().strip()
            if not data:
                break

            print(f"Received from {client_address}: {data}")

            if data.upper() == "GET_FLAG":
                # Client wants the CTF answer
                ctf_answer = get_ctf_answer_for_current_server()
                if ctf_answer:
                    response = f"CTF_ANSWER:{ctf_answer}\n"
                    client_socket.send(response.encode())
                    print(f"Sent CTF answer to {client_address}")
                    break  # End session after giving flag
                else:
                    client_socket.send(b"ERROR: No CTF answer found\n")
            else:
                # Echo the message back
                echo_response = f"ECHO: {data}\n"
                client_socket.send(echo_response.encode())

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"Connection closed with {client_address}")

def start_echo_server(port):
    """Start the echo server on specified port"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind(('localhost', port))
        server.listen(5)
        print(f"Echo server listening on localhost:{port}")

        while True:
            client_socket, client_address = server.accept()

            # Handle each client in a separate thread
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            client_thread.daemon = True
            client_thread.start()

    except KeyboardInterrupt:
        print("\nServer shutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python challenge_1.py <port>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        start_echo_server(port)
    except ValueError:
        print("Invalid port number")
        sys.exit(1)