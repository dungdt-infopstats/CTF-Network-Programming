#!/usr/bin/env python3
"""
Redis manager for port-answer mapping in CTF Platform
"""

import redis
import socket
import random

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def test_redis_connection():
    """Test Redis connection"""
    try:
        redis_client.ping()
        return True
    except redis.ConnectionError:
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
        redis_client.setex(f"port:{port}", expiry_seconds, ctf_answer)
        return True
    except Exception as e:
        print(f"Error storing CTF answer: {e}")
        return False

def get_ctf_answer(port):
    """Get CTF answer for a specific port"""
    try:
        answer = redis_client.get(f"port:{port}")
        return answer
    except Exception as e:
        print(f"Error getting CTF answer: {e}")
        return None

def remove_ctf_answer(port):
    """Remove CTF answer for a specific port"""
    try:
        redis_client.delete(f"port:{port}")
        return True
    except Exception as e:
        print(f"Error removing CTF answer: {e}")
        return False

def store_run_info(run_id, student_id, challenge_id, port, status='running'):
    """Store information about a running challenge"""
    try:
        run_info = {
            'student_id': student_id,
            'challenge_id': challenge_id,
            'port': port,
            'status': status
        }

        redis_client.hmset(f"run:{run_id}", run_info)
        redis_client.expire(f"run:{run_id}", 3600)  # 1 hour expiry
        return True
    except Exception as e:
        print(f"Error storing run info: {e}")
        return False

def get_run_info(run_id):
    """Get information about a running challenge"""
    try:
        run_info = redis_client.hgetall(f"run:{run_id}")
        return run_info if run_info else None
    except Exception as e:
        print(f"Error getting run info: {e}")
        return None

def update_run_status(run_id, status):
    """Update status of a running challenge"""
    try:
        redis_client.hset(f"run:{run_id}", 'status', status)
        return True
    except Exception as e:
        print(f"Error updating run status: {e}")
        return False

def cleanup_expired_ports():
    """Clean up expired port mappings (run periodically)"""
    try:
        # Get all port keys
        port_keys = redis_client.keys("port:*")

        # Check which ones are expired and clean up
        for key in port_keys:
            if redis_client.ttl(key) == -1:  # No expiry set, clean up
                redis_client.delete(key)

        return True
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return False