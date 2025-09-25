#!/usr/bin/env python3
"""
Simple in-memory port manager - no Redis needed
"""

import socket
import threading
import time
from datetime import datetime, timedelta

# Simple in-memory storage
port_mappings = {}  # {port: {'ctf_answer': str, 'expires_at': datetime}}
run_info_storage = {}  # {run_id: {'student_id': int, 'challenge_id': int, 'port': int, 'status': str}}

# Thread lock for thread-safe operations
storage_lock = threading.Lock()

def test_redis_connection():
    """Always return False since we don't use Redis"""
    return False

def find_free_port(start_port=8000, end_port=9000):
    """Find a free port in the given range"""
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            if result != 0:  # Port is free
                return port
    return None

def store_ctf_answer(port, ctf_answer, expiry_seconds=3600):
    """Store CTF answer for a specific port with expiry"""
    try:
        with storage_lock:
            expires_at = datetime.now() + timedelta(seconds=expiry_seconds)
            port_mappings[port] = {
                'ctf_answer': ctf_answer,
                'expires_at': expires_at
            }
        return True
    except Exception as e:
        print(f"Error storing CTF answer: {e}")
        return False

def get_ctf_answer(port):
    """Get CTF answer for a specific port"""
    try:
        with storage_lock:
            cleanup_expired_ports()  # Clean up first

            if port in port_mappings:
                mapping = port_mappings[port]
                if mapping['expires_at'] > datetime.now():
                    return mapping['ctf_answer']
                else:
                    del port_mappings[port]  # Remove expired

            return None
    except Exception as e:
        print(f"Error getting CTF answer: {e}")
        return None

def remove_ctf_answer(port):
    """Remove CTF answer for a specific port"""
    try:
        with storage_lock:
            if port in port_mappings:
                del port_mappings[port]
        return True
    except Exception as e:
        print(f"Error removing CTF answer: {e}")
        return False

def store_run_info(run_id, student_id, challenge_id, port, status='running'):
    """Store information about a running challenge"""
    try:
        with storage_lock:
            run_info_storage[run_id] = {
                'student_id': str(student_id),
                'challenge_id': str(challenge_id),
                'port': str(port),
                'status': status
            }
        return True
    except Exception as e:
        print(f"Error storing run info: {e}")
        return False

def get_run_info(run_id):
    """Get information about a running challenge"""
    try:
        with storage_lock:
            return run_info_storage.get(run_id)
    except Exception as e:
        print(f"Error getting run info: {e}")
        return None

def update_run_status(run_id, status):
    """Update status of a running challenge"""
    try:
        with storage_lock:
            if run_id in run_info_storage:
                run_info_storage[run_id]['status'] = status
        return True
    except Exception as e:
        print(f"Error updating run status: {e}")
        return False

def cleanup_expired_ports():
    """Clean up expired port mappings (called automatically)"""
    try:
        now = datetime.now()
        expired_ports = []

        for port, mapping in port_mappings.items():
            if mapping['expires_at'] <= now:
                expired_ports.append(port)

        for port in expired_ports:
            del port_mappings[port]

        return True
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return False