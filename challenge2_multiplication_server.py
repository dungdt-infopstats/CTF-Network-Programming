#!/usr/bin/env python3
"""
Challenge 2: Multiplication Server
Server sends 2 numbers, client must calculate the product, 1 correct answer means pass
"""

import socket
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from server_utils import get_ctf_answer

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 0))  # Bind to any available port
    port = server_socket.getsockname()[1]

    # Print port for the main process to read
    print(port)
    sys.stdout.flush()

    server_socket.listen(1)

    while True:
        try:
            client_socket, address = server_socket.accept()
            print(f"Connection from {address}")

            # Generate two random numbers
            num1 = random.randint(1, 20)
            num2 = random.randint(1, 20)
            expected_product = num1 * num2

            # Send the challenge
            message = f"Calculate the product: {num1} * {num2} = ?\n"
            client_socket.send(message.encode())

            # Receive the answer
            try:
                response = client_socket.recv(1024).decode().strip()

                if response == str(expected_product):
                    # Correct answer - send CTF flag
                    ctf_answer = get_ctf_answer()
                    if ctf_answer:
                        client_socket.send(f"Correct! Here's your flag: {ctf_answer}\n".encode())
                    else:
                        client_socket.send("Correct! But couldn't retrieve flag.\n".encode())
                else:
                    client_socket.send(f"Wrong! The correct answer was {expected_product}\n".encode())

            except Exception as e:
                client_socket.send(f"Error processing answer: {e}\n".encode())

            client_socket.close()

        except Exception as e:
            print(f"Server error: {e}")
            continue

if __name__ == "__main__":
    start_server()