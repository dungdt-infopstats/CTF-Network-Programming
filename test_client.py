#!/usr/bin/env python3
"""
Robust test client for small arithmetic CTF challenges.
Can parse expressions like:
  "3 + 5 = ?"
  "Calculate the sum: 5 + 3 = ?"
  "product: 4 * 6 = ?"
Supports: + - * / and variants (x, ×). Sends a newline after the answer.
"""

import socket
import sys
import re

def solve_from_text(text):
    text = text.strip()
    # Try to find a direct "num op num" pattern first
    m = re.search(r'([-+]?\d+)\s*([+\-*/x×])\s*([-+]?\d+)', text)
    if m:
        a = int(m.group(1))
        op = m.group(2)
        b = int(m.group(3))
    else:
        # Fallback: extract numbers and infer operation from words/symbols
        nums = re.findall(r'[-+]?\d+', text)
        if len(nums) < 2:
            return None
        a = int(nums[0])
        b = int(nums[1])
        lower = text.lower()
        if 'product' in lower or 'multiply' in lower or ('*' in text) or ('x' in text):
            op = '*'
        elif 'sum' in lower or 'add' in lower or ('+' in text):
            op = '+'
        elif 'subtract' in lower or '-' in text:
            op = '-'
        elif 'divide' in lower or '/' in text:
            op = '/'
        else:
            op = '+'

    # Compute result
    if op == '+' :
        return a + b
    if op == '-':
        return a - b
    if op in ('*', 'x', '×'):
        return a * b
    if op == '/':
        if b == 0:
            return None
        # If divisible, return integer; else return float
        if a % b == 0:
            return a // b
        return a / b
    return None

def test_server(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', port))

        # Receive challenge
        data = s.recv(4096).decode(errors='ignore')
        print("Server:", data.strip())

        ans = solve_from_text(data)
        if ans is None:
            print("Couldn't parse expression. Sending default answer '42'.")
            payload = "42\n"
        else:
            # Format answer: avoid accidental trailing .0 formatting issues
            if isinstance(ans, float):
                # strip trailing zeros if any
                payload = (str(ans).rstrip('0').rstrip('.') if '.' in str(ans) else str(ans)) + "\n"
            else:
                payload = f"{ans}\n"
            print("Calculated answer:", payload.strip())

        s.sendall(payload.encode())

        # Read response
        response = s.recv(4096).decode(errors='ignore')
        print("Response:", response.strip())
        s.close()
        return True

    except Exception as e:
        print(f"Error connecting to server on port {port}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 test_client.py <port>")
        sys.exit(1)
    port = int(sys.argv[1])
    test_server(port)
