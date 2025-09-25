#!/usr/bin/env python3
"""
Common helper function for server codes to get CTF answers
This file should be imported by all challenge server codes
"""

import os
import socket
from redis_manager import get_ctf_answer

def get_current_port():
    """Get the port that the current server is running on"""
    try:
        # Method 1: Try to get from environment variable (set by main app)
        port = os.environ.get('CTF_PORT')
        if port:
            return int(port)

        # Method 2: Try to get from command line argument
        import sys
        if len(sys.argv) > 1:
            return int(sys.argv[1])

        # Method 3: Try to discover by checking socket (fallback)
        # This is more complex and may not always work
        return None

    except Exception as e:
        print(f"Error getting current port: {e}")
        return None

def get_ctf_answer_for_current_server():
    """
    Main function that server codes should call to get their CTF answer
    This checks the current port and returns the corresponding CTF answer from Redis
    """
    try:
        port = get_current_port()
        if not port:
            return None

        # Get CTF answer from Redis using the port
        ctf_answer = get_ctf_answer(port)
        return ctf_answer

    except Exception as e:
        print(f"Error getting CTF answer: {e}")
        return None

def send_ctf_answer_to_client(client_socket):
    """
    Helper function to send CTF answer to client
    Server codes can use this for consistency
    """
    try:
        ctf_answer = get_ctf_answer_for_current_server()
        if ctf_answer:
            client_socket.send(f"CTF_ANSWER:{ctf_answer}\n".encode())
            return True
        else:
            client_socket.send(b"ERROR:No CTF answer found\n")
            return False
    except Exception as e:
        print(f"Error sending CTF answer: {e}")
        return False

# Example usage for server codes:
"""
import socket
from ctf_helper import send_ctf_answer_to_client, get_ctf_answer_for_current_server

def handle_client(client_socket):
    # Your challenge logic here...

    # When ready to send CTF answer:
    send_ctf_answer_to_client(client_socket)

    # Or get it manually:
    ctf_answer = get_ctf_answer_for_current_server()
    if ctf_answer:
        client_socket.send(f"Your answer: {ctf_answer}\n".encode())
"""