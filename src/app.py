#!/usr/bin/env python3
"""
Main Flask application for CTF Platform
"""

from flask import Flask, request, jsonify
import os
import uuid
import subprocess
import threading
import time
from datetime import datetime

# Local imports
from database import *
from auth import *
from crypto_utils import *
from redis_manager import *

app = Flask(__name__)
app.secret_key = 'ctf-platform-secret-key-2025'

# Create required directories
os.makedirs('tmp', exist_ok=True)
os.makedirs('server_code', exist_ok=True)

# ============= AUTH ENDPOINTS =============

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Student login endpoint"""
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'password' not in data:
            return jsonify({'error': 'Name and password required'}), 400

        student = verify_student(data['name'], data['password'])
        if not student:
            return jsonify({'error': 'Invalid credentials'}), 401

        # Generate JWT token
        token = generate_jwt_token(student['id'], student['name'])

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'student': {
                'id': student['id'],
                'name': student['name']
            }
        })

    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

# ============= STUDENT ENDPOINTS =============

@app.route('/api/challenges', methods=['GET'])
@require_auth
def get_challenges():
    """Get all challenges"""
    try:
        challenges = get_all_challenges()

        # Add solved status for current student
        for challenge in challenges:
            challenge['solved'] = is_challenge_solved(request.student_id, challenge['id'])

        return jsonify({'challenges': challenges})

    except Exception as e:
        return jsonify({'error': f'Failed to get challenges: {str(e)}'}), 500

@app.route('/api/challenges/<int:challenge_id>', methods=['GET'])
@require_auth
def get_challenge_detail(challenge_id):
    """Get specific challenge details"""
    try:
        challenge = get_challenge_by_id(challenge_id)
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404

        challenge['solved'] = is_challenge_solved(request.student_id, challenge_id)

        return jsonify({'challenge': challenge})

    except Exception as e:
        return jsonify({'error': f'Failed to get challenge: {str(e)}'}), 500

@app.route('/api/challenges/<int:challenge_id>/upload', methods=['POST'])
@require_auth
def upload_server_code(challenge_id):
    """Upload server code for a challenge"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.py'):
            return jsonify({'error': 'Only Python files allowed'}), 400

        # Generate unique filename
        random_str = str(uuid.uuid4())[:8]
        filename = f"{challenge_id}_{request.student_id}_{random_str}.py"
        filepath = os.path.join('tmp', filename)

        # Save file
        file.save(filepath)

        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'filepath': filepath
        })

    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/challenges/<int:challenge_id>/start', methods=['GET'])
@require_auth
def start_challenge(challenge_id):
    """Start a challenge - allocate port and create CTF answer"""
    try:
        # Get challenge details
        challenge = get_challenge_by_id(challenge_id)
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404

        # Generate CTF answer
        ctf_answer = encrypt_student_id(request.student_id, challenge['secret'])

        # Find free port
        port = find_free_port()
        if not port:
            return jsonify({'error': 'No available ports'}), 500

        # Store CTF answer in Redis
        if not store_ctf_answer(port, ctf_answer):
            return jsonify({'error': 'Failed to store CTF answer'}), 500

        # Generate run ID
        run_id = str(uuid.uuid4())

        # Store run information
        store_run_info(run_id, request.student_id, challenge_id, port)

        # Start server code (if exists)
        server_code_path = os.path.join('server_code', f'challenge_{challenge_id}.py')
        if os.path.exists(server_code_path):
            # Start server in background
            threading.Thread(
                target=start_server_process,
                args=(server_code_path, port, run_id),
                daemon=True
            ).start()

        return jsonify({
            'message': 'Challenge started',
            'run_id': run_id,
            'connection': {
                'host': '127.0.0.1',
                'port': port
            }
        })

    except Exception as e:
        return jsonify({'error': f'Failed to start challenge: {str(e)}'}), 500

@app.route('/api/challenges/<int:challenge_id>/submit', methods=['POST'])
@require_auth
def submit_challenge(challenge_id):
    """Submit CTF answer for verification"""
    try:
        data = request.get_json()
        if not data or 'ctf_answer' not in data:
            return jsonify({'error': 'CTF answer required'}), 400

        # Get challenge details
        challenge = get_challenge_by_id(challenge_id)
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404

        # Decrypt CTF answer
        decrypted_student_id = decrypt_ctf_answer(data['ctf_answer'], challenge['secret'])

        if decrypted_student_id != request.student_id:
            return jsonify({'error': 'Invalid CTF answer'}), 400

        # Mark challenge as solved
        if mark_challenge_solved(request.student_id, challenge_id):
            return jsonify({'message': 'Challenge solved successfully!'})
        else:
            return jsonify({'error': 'Failed to mark challenge as solved'}), 500

    except Exception as e:
        return jsonify({'error': f'Submit failed: {str(e)}'}), 500

@app.route('/api/runs/<run_id>/status', methods=['GET'])
@require_auth
def get_run_status(run_id):
    """Get status of a running challenge"""
    try:
        # Check if already solved in database
        run_info = get_run_info(run_id)
        if not run_info:
            return jsonify({'error': 'Run not found'}), 404

        challenge_id = int(run_info['challenge_id'])
        if is_challenge_solved(request.student_id, challenge_id):
            return jsonify({'status': 'accepted'})

        # Check if port still has CTF answer (challenge still running)
        port = int(run_info['port'])
        ctf_answer = get_ctf_answer(port)

        if ctf_answer:
            return jsonify({'status': 'running'})
        else:
            return jsonify({'status': 'finished'})

    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500

# ============= HELPER FUNCTIONS =============

def start_server_process(server_code_path, port, run_id):
    """Start server process on specified port"""
    try:
        print(f"Starting server process: {server_code_path} on port {port}")

        # Set environment variable for the server to know its port
        env = os.environ.copy()
        env['CTF_PORT'] = str(port)
        env['CTF_RUN_ID'] = run_id

        # Start the server process
        process = subprocess.Popen([
            'python', server_code_path, str(port)
        ], env=env, cwd=os.path.dirname(server_code_path) or '.')

        # Wait for process to complete or timeout after 1 hour
        try:
            process.wait(timeout=3600)
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"Server process timeout for port {port}")

        # Cleanup
        remove_ctf_answer(port)
        update_run_status(run_id, 'finished')

    except Exception as e:
        print(f"Error starting server process: {e}")

# ============= ADMIN ENDPOINTS =============

@app.route('/api/admin/challenges', methods=['POST'])
@require_auth
def create_challenge():
    """Create new challenge (admin only)"""
    try:
        if request.student_name != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json()
        if not data or not all(k in data for k in ['name', 'description', 'secret']):
            return jsonify({'error': 'Name, description, and secret required'}), 400

        if add_challenge(data['name'], data['description'], data['secret']):
            return jsonify({'message': 'Challenge created successfully'})
        else:
            return jsonify({'error': 'Failed to create challenge'}), 500

    except Exception as e:
        return jsonify({'error': f'Create challenge failed: {str(e)}'}), 500

@app.route('/api/admin/students', methods=['POST'])
@require_auth
def create_student():
    """Create new student (admin only)"""
    try:
        if request.student_name != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json()
        if not data or not all(k in data for k in ['name', 'password']):
            return jsonify({'error': 'Name and password required'}), 400

        if add_student(data['name'], data['password']):
            return jsonify({'message': 'Student created successfully'})
        else:
            return jsonify({'error': 'Student already exists or creation failed'}), 400

    except Exception as e:
        return jsonify({'error': f'Create student failed: {str(e)}'}), 500

@app.route('/api/admin/students', methods=['GET'])
@require_auth
def list_students():
    """List all students (admin only)"""
    try:
        if request.student_name != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        students = get_all_students()
        return jsonify({'students': students})

    except Exception as e:
        return jsonify({'error': f'Failed to list students: {str(e)}'}), 500

# ============= HEALTH CHECK =============

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'redis_connected': test_redis_connection(),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("Initializing CTF Platform...")

    # Initialize database
    init_database()

    # Test Redis connection
    if not test_redis_connection():
        print("Warning: Redis not connected. Some features may not work.")

    print("CTF Platform is ready!")
    print("API Base URL: http://localhost:5000")
    print("Sample accounts: admin/admin123, student1/student123, student2/student123")

    app.run(host='0.0.0.0', port=5000, debug=True)