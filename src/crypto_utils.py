#!/usr/bin/env python3
"""
Cryptographic utilities for CTF Platform
"""

from cryptography.fernet import Fernet
import base64
import hashlib

def generate_key_from_secret(secret):
    """Generate Fernet key from challenge secret"""
    # Create a 32-byte key from the secret
    key = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(key)

def encrypt_student_id(student_id, challenge_secret):
    """Encrypt student ID with challenge secret to create CTF answer"""
    key = generate_key_from_secret(challenge_secret)
    fernet = Fernet(key)

    # Convert student_id to string and encrypt
    plaintext = str(student_id).encode()
    encrypted = fernet.encrypt(plaintext)

    # Return as base64 string for easy storage/transmission
    return base64.urlsafe_b64encode(encrypted).decode()

def decrypt_ctf_answer(ctf_answer, challenge_secret):
    """Decrypt CTF answer to get original student ID"""
    try:
        key = generate_key_from_secret(challenge_secret)
        fernet = Fernet(key)

        # Decode from base64 and decrypt
        encrypted_data = base64.urlsafe_b64decode(ctf_answer.encode())
        decrypted = fernet.decrypt(encrypted_data)

        # Return as integer
        return int(decrypted.decode())
    except Exception as e:
        print(f"Decryption error: {e}")
        return None