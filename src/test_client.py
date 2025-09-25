#!/usr/bin/env python3
"""
Test client for CTF Platform
This client demonstrates how to interact with the challenge servers
"""

import socket
import json
import requests
import sys

# Configuration
API_BASE_URL = "http://localhost:5000"
USERNAME = "student1"
PASSWORD = "student123"

def login():
    """Login and get JWT token"""
    login_data = {
        "name": USERNAME,
        "password": PASSWORD
    }

    response = requests.post(f"{API_BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful! Welcome {data['student']['name']}")
        return data['token']
    else:
        print(f"❌ Login failed: {response.json()}")
        return None

def get_challenges(token):
    """Get list of available challenges"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{API_BASE_URL}/api/challenges", headers=headers)
    if response.status_code == 200:
        challenges = response.json()['challenges']
        print(f"\n📋 Available challenges:")
        for challenge in challenges:
            status = "✅ Solved" if challenge['solved'] else "⏳ Not solved"
            print(f"  {challenge['id']}. {challenge['name']} - {status}")
        return challenges
    else:
        print(f"❌ Failed to get challenges: {response.json()}")
        return []

def start_challenge(token, challenge_id):
    """Start a challenge and get connection info"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{API_BASE_URL}/api/challenges/{challenge_id}/start", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Challenge started!")
        print(f"Connection: {data['connection']['host']}:{data['connection']['port']}")
        print(f"Run ID: {data['run_id']}")
        return data
    else:
        print(f"❌ Failed to start challenge: {response.json()}")
        return None

def connect_to_challenge_server(host, port):
    """Connect to challenge server and interact"""
    print(f"\n🔗 Connecting to challenge server at {host}:{port}")

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(30)
        client_socket.connect((host, port))

        print("✅ Connected to challenge server!")

        # Receive welcome messages
        welcome_msg = client_socket.recv(1024).decode()
        print(f"Server: {welcome_msg.strip()}")

        instructions = client_socket.recv(1024).decode()
        print(f"Server: {instructions.strip()}")

        flag_instructions = client_socket.recv(1024).decode()
        print(f"Server: {flag_instructions.strip()}")

        # Interactive session
        print("\n💬 Interactive session started. Type 'GET_FLAG' to get your CTF answer, or any message to echo.")
        print("Type 'quit' to exit.")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() == 'quit':
                break

            # Send message to server
            client_socket.send((user_input + '\n').encode())

            # Receive response
            response = client_socket.recv(1024).decode().strip()
            print(f"Server: {response}")

            # Check if we received a CTF answer
            if response.startswith("CTF_ANSWER:"):
                ctf_answer = response.split(":", 1)[1]
                print(f"\n🎉 Got CTF answer: {ctf_answer}")
                return ctf_answer

        client_socket.close()
        return None

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def submit_answer(token, challenge_id, ctf_answer):
    """Submit CTF answer"""
    headers = {"Authorization": f"Bearer {token}"}
    submit_data = {"ctf_answer": ctf_answer}

    response = requests.post(f"{API_BASE_URL}/api/challenges/{challenge_id}/submit", json=submit_data, headers=headers)
    if response.status_code == 200:
        print(f"✅ {response.json()['message']}")
        return True
    else:
        print(f"❌ Submit failed: {response.json()}")
        return False

def main():
    """Main test flow"""
    print("🌟 CTF Platform Test Client")
    print("=" * 40)

    # Step 1: Login
    token = login()
    if not token:
        return

    # Step 2: Get challenges
    challenges = get_challenges(token)
    if not challenges:
        return

    # Step 3: Choose challenge
    if len(sys.argv) > 1:
        challenge_id = int(sys.argv[1])
    else:
        challenge_id = 1  # Default to challenge 1

    # Step 4: Start challenge
    start_result = start_challenge(token, challenge_id)
    if not start_result:
        return

    connection = start_result['connection']

    # Step 5: Connect to challenge server
    ctf_answer = connect_to_challenge_server(connection['host'], connection['port'])
    if not ctf_answer:
        print("❌ Failed to get CTF answer from server")
        return

    # Step 6: Submit answer
    if submit_answer(token, challenge_id, ctf_answer):
        print("\n🎊 Challenge completed successfully!")
    else:
        print("\n😞 Failed to submit answer")

if __name__ == '__main__':
    main()