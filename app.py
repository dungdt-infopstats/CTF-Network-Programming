from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3
import redis
import hashlib
import secrets
import subprocess
import sys
import os
import time
from datetime import datetime
from functools import wraps
from cryptography.fernet import Fernet
import base64

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['DATABASE'] = 'ctf.db'
app.config['REDIS_HOST'] = 'localhost'
app.config['REDIS_PORT'] = 6379
app.config['REDIS_DB'] = 0

redis_client = redis.Redis(host=app.config['REDIS_HOST'],
                          port=app.config['REDIS_PORT'],
                          db=app.config['REDIS_DB'],
                          decode_responses=True)

def get_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                secret TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                hashed_pw TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS student_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                challenge_id INTEGER NOT NULL,
                solved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, challenge_id),
                FOREIGN KEY(student_id) REFERENCES students(id),
                FOREIGN KEY(challenge_id) REFERENCES challenges(id)
            );
        ''')
        db.commit()
        db.close()

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def encrypt_answer(student_id, secret):
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    f = Fernet(key)
    return f.encrypt(str(student_id).encode()).decode()

def decrypt_answer(encrypted_answer, secret):
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    f = Fernet(key)
    return int(f.decrypt(encrypted_answer.encode()).decode())

# Student API Routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    db = get_db()
    student = db.execute('SELECT * FROM students WHERE name = ?', (username,)).fetchone()

    if student and student['hashed_pw'] == hashlib.sha256(password.encode()).hexdigest():
        session['student_id'] = student['id']
        session['student_name'] = student['name']
        return jsonify({'message': 'Login successful', 'student_id': student['id']})

    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/challenges')
@require_auth
def get_challenges():
    db = get_db()
    challenges = db.execute('SELECT id, name, description FROM challenges').fetchall()
    return jsonify([dict(c) for c in challenges])

@app.route('/api/challenges/<int:challenge_id>')
@require_auth
def get_challenge(challenge_id):
    db = get_db()
    challenge = db.execute('SELECT id, name, description FROM challenges WHERE id = ?',
                          (challenge_id,)).fetchone()
    if not challenge:
        return jsonify({'error': 'Challenge not found'}), 404
    return jsonify(dict(challenge))

@app.route('/api/challenges/<int:challenge_id>/upload', methods=['POST'])
@require_auth
def upload_server_code(challenge_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    student_id = session['student_id']
    random_suffix = secrets.token_hex(8)
    filename = f"{challenge_id}_{student_id}_{random_suffix}.py"
    temp_dir = os.path.join(os.getcwd(), 'tmp')
    os.makedirs(temp_dir, exist_ok=True)
    filepath = os.path.join(temp_dir, filename)

    try:
        file.save(filepath)
        return jsonify({'message': 'File uploaded successfully', 'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/challenges/<int:challenge_id>/start')
@require_auth
def start_challenge(challenge_id):
    student_id = session['student_id']

    db = get_db()
    challenge = db.execute('SELECT * FROM challenges WHERE id = ?', (challenge_id,)).fetchone()
    if not challenge:
        return jsonify({'error': 'Challenge not found'}), 404

    # Create CTF answer by encrypting student_id with challenge secret
    ctf_answer = encrypt_answer(student_id, challenge['secret'])

    # Find available port (simple implementation)
    import socket
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()

    # Store in Redis
    redis_client.set(f"{student_id}-{challenge_id}", port)
    redis_client.set(str(port), ctf_answer)

    # Try to find and execute the checked server code
    checked_dir = os.path.join(os.getcwd(), 'tmp_checked')
    server_files = []
    if os.path.exists(checked_dir):
        for filename in os.listdir(checked_dir):
            # First try to find student-specific code
            if filename.startswith(f"{challenge_id}_{student_id}_") and filename.endswith('.py'):
                server_files.append(filename)

        # If no student-specific code found, look for any approved code for this challenge
        if not server_files:
            for filename in os.listdir(checked_dir):
                if filename.startswith(f"{challenge_id}_") and filename.endswith('.py'):
                    server_files.append(filename)

    if not server_files:
        return jsonify({'error': 'No verified server code available for this challenge. Please wait for admin approval.'}), 400

    # Use the most recent checked upload (by modification time)
    server_files_with_time = [(f, os.path.getmtime(os.path.join(checked_dir, f))) for f in server_files]
    server_file = max(server_files_with_time, key=lambda x: x[1])[0]
    server_path = os.path.join(checked_dir, server_file)

    try:
        # Start the server process with correct working directory and Python path
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd()  # Add current directory to Python path

        proc = subprocess.Popen([sys.executable, server_path],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              text=True,
                              cwd=os.getcwd(),
                              env=env)

        # Read the port from stdout (server should print it first)
        actual_port = proc.stdout.readline().strip()
        if not actual_port.isdigit():
            proc.terminate()
            # Debug: show stderr output
            stderr_output = proc.stderr.read()
            return jsonify({'error': f'Server failed to start properly. Output: {actual_port}, Error: {stderr_output}'}), 500

        port = int(actual_port)

        # Update Redis with actual port
        redis_client.set(f"{student_id}-{challenge_id}", port)
        redis_client.set(str(port), ctf_answer)

        return jsonify({
            'message': 'Challenge started successfully',
            'port': port,
            'ip': '0.0.0.0'
        })

    except Exception as e:
        return jsonify({'error': f'Failed to start server: {str(e)}'}), 500

@app.route('/api/challenges/<int:challenge_id>/submit', methods=['POST'])
@require_auth
def submit_answer(challenge_id):
    data = request.get_json()
    submitted_answer = data.get('answer')

    if not submitted_answer:
        return jsonify({'error': 'Answer required'}), 400

    student_id = session['student_id']

    db = get_db()
    challenge = db.execute('SELECT * FROM challenges WHERE id = ?', (challenge_id,)).fetchone()
    if not challenge:
        return jsonify({'error': 'Challenge not found'}), 404

    try:
        # Decrypt the submitted answer
        decrypted_student_id = decrypt_answer(submitted_answer, challenge['secret'])

        if decrypted_student_id == student_id:
            # Mark as solved
            db.execute('''INSERT OR IGNORE INTO student_challenges
                         (student_id, challenge_id) VALUES (?, ?)''',
                      (student_id, challenge_id))
            db.commit()
            return jsonify({'message': 'Correct! Challenge solved!'})
        else:
            return jsonify({'error': 'Incorrect answer'}), 400

    except Exception as e:
        return jsonify({'error': 'Invalid answer format'}), 400

@app.route('/api/challenges/<int:challenge_id>/status')
@require_auth
def get_challenge_status(challenge_id):
    student_id = session['student_id']

    db = get_db()
    # Check if already solved
    solved = db.execute('''SELECT * FROM student_challenges
                          WHERE student_id = ? AND challenge_id = ?''',
                       (student_id, challenge_id)).fetchone()

    if solved:
        return jsonify({'status': 'solved', 'solved_at': solved['solved_at']})

    # Check if there's an active session in Redis
    port = redis_client.get(f"{student_id}-{challenge_id}")
    if port:
        return jsonify({'status': 'active', 'port': int(port)})

    return jsonify({'status': 'not_started'})

# Admin Web Interface Routes
@app.route('/admin')
def admin_home():
    return render_template('admin/index.html')

@app.route('/admin/challenges')
def admin_challenges():
    db = get_db()
    challenges = db.execute('SELECT * FROM challenges ORDER BY id').fetchall()
    return render_template('admin/challenges.html', challenges=challenges)

@app.route('/admin/challenges/create', methods=['GET', 'POST'])
def admin_create_challenge():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        secret = request.form['secret'] or secrets.token_urlsafe(32)

        db = get_db()
        db.execute('INSERT INTO challenges (name, description, secret) VALUES (?, ?, ?)',
                  (name, description, secret))
        db.commit()
        return redirect(url_for('admin_challenges'))

    return render_template('admin/create_challenge.html')

@app.route('/admin/challenges/<int:challenge_id>/edit', methods=['GET', 'POST'])
def admin_edit_challenge(challenge_id):
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        secret = request.form['secret']

        db.execute('UPDATE challenges SET name = ?, description = ?, secret = ? WHERE id = ?',
                  (name, description, secret, challenge_id))
        db.commit()
        return redirect(url_for('admin_challenges'))

    challenge = db.execute('SELECT * FROM challenges WHERE id = ?', (challenge_id,)).fetchone()
    return render_template('admin/edit_challenge.html', challenge=challenge)

@app.route('/admin/challenges/<int:challenge_id>/delete', methods=['POST'])
def admin_delete_challenge(challenge_id):
    db = get_db()
    db.execute('DELETE FROM challenges WHERE id = ?', (challenge_id,))
    db.commit()
    return redirect(url_for('admin_challenges'))

@app.route('/admin/students')
def admin_students():
    db = get_db()
    students = db.execute('SELECT * FROM students ORDER BY id').fetchall()
    return render_template('admin/students.html', students=students)

@app.route('/admin/students/create', methods=['GET', 'POST'])
def admin_create_student():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        db = get_db()
        try:
            db.execute('INSERT INTO students (name, hashed_pw) VALUES (?, ?)', (name, hashed_pw))
            db.commit()
        except sqlite3.IntegrityError:
            return render_template('admin/create_student.html', error='Student name already exists')
        return redirect(url_for('admin_students'))

    return render_template('admin/create_student.html')

@app.route('/admin/students/import', methods=['POST'])
def admin_import_students():
    if 'file' not in request.files:
        return redirect(url_for('admin_students'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('admin_students'))

    content = file.read().decode('utf-8')
    lines = content.strip().split('\n')

    db = get_db()
    imported = 0
    for line in lines:
        if ',' in line:
            name, password = line.strip().split(',', 1)
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            try:
                db.execute('INSERT INTO students (name, hashed_pw) VALUES (?, ?)', (name, hashed_pw))
                imported += 1
            except sqlite3.IntegrityError:
                continue  # Skip duplicates

    db.commit()
    return redirect(url_for('admin_students'))

@app.route('/admin/students/bulk_delete', methods=['POST'])
def admin_bulk_delete_students():
    student_ids = request.form.getlist('student_ids')
    if student_ids:
        db = get_db()
        placeholders = ','.join(['?'] * len(student_ids))
        db.execute(f'DELETE FROM students WHERE id IN ({placeholders})', student_ids)
        db.commit()
    return redirect(url_for('admin_students'))

@app.route('/admin/server_codes')
def admin_server_codes():
    """Admin interface to manage server codes"""
    tmp_dir = os.path.join(os.getcwd(), 'tmp')
    checked_dir = os.path.join(os.getcwd(), 'tmp_checked')

    # Get files from tmp directory (pending approval)
    pending_files = []
    if os.path.exists(tmp_dir):
        for filename in os.listdir(tmp_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(tmp_dir, filename)
                file_stat = os.stat(filepath)
                pending_files.append({
                    'filename': filename,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })

    # Get files from tmp_checked directory (approved)
    approved_files = []
    if os.path.exists(checked_dir):
        for filename in os.listdir(checked_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(checked_dir, filename)
                file_stat = os.stat(filepath)
                approved_files.append({
                    'filename': filename,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })

    return render_template('admin/server_codes.html',
                         pending_files=pending_files,
                         approved_files=approved_files)

@app.route('/admin/server_codes/approve/<filename>', methods=['POST'])
def admin_approve_server_code(filename):
    """Move a server code from tmp to tmp_checked (approve it)"""
    tmp_path = os.path.join(os.getcwd(), 'tmp', filename)
    checked_path = os.path.join(os.getcwd(), 'tmp_checked', filename)

    if not os.path.exists(tmp_path):
        return jsonify({'error': 'File not found'}), 404

    try:
        # Copy file to checked directory
        import shutil
        shutil.copy2(tmp_path, checked_path)
        # Remove from tmp directory
        os.remove(tmp_path)
        return jsonify({'message': 'Server code approved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/server_codes/reject/<filename>', methods=['POST'])
def admin_reject_server_code(filename):
    """Remove a server code from tmp (reject it)"""
    tmp_path = os.path.join(os.getcwd(), 'tmp', filename)

    if not os.path.exists(tmp_path):
        return jsonify({'error': 'File not found'}), 404

    try:
        os.remove(tmp_path)
        return jsonify({'message': 'Server code rejected successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/server_codes/view/<path:filename>')
def admin_view_server_code(filename):
    """View the contents of a server code file"""
    # Check both directories
    tmp_path = os.path.join(os.getcwd(), 'tmp', filename)
    checked_path = os.path.join(os.getcwd(), 'tmp_checked', filename)

    file_path = None
    file_status = None

    if os.path.exists(tmp_path):
        file_path = tmp_path
        file_status = 'pending'
    elif os.path.exists(checked_path):
        file_path = checked_path
        file_status = 'approved'

    if not file_path:
        return jsonify({'error': 'File not found'}), 404

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({
            'filename': filename,
            'content': content,
            'status': file_status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Student Web Interface Routes
@app.route('/', methods=['GET', 'POST'])
def student_home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        student = db.execute('SELECT * FROM students WHERE name = ?', (username,)).fetchone()

        if student and student['hashed_pw'] == hashlib.sha256(password.encode()).hexdigest():
            session['student_id'] = student['id']
            session['student_name'] = student['name']
            return redirect(url_for('student_dashboard'))

        return render_template('student/login.html', error='Invalid credentials')

    if 'student_id' not in session:
        return render_template('student/login.html')
    return render_template('student/dashboard.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        student = db.execute('SELECT * FROM students WHERE name = ?', (username,)).fetchone()

        if student and student['hashed_pw'] == hashlib.sha256(password.encode()).hexdigest():
            session['student_id'] = student['id']
            session['student_name'] = student['name']
            return redirect(url_for('student_dashboard'))

        return render_template('student/login.html', error='Invalid credentials')

    return render_template('student/login.html')

@app.route('/student/dashboard')
@require_auth
def student_dashboard():
    db = get_db()
    challenges = db.execute('SELECT * FROM challenges ORDER BY id').fetchall()

    # Get solved challenges for this student
    solved_challenges = db.execute('''
        SELECT challenge_id FROM student_challenges WHERE student_id = ?
    ''', (session['student_id'],)).fetchall()

    solved_ids = [c['challenge_id'] for c in solved_challenges]

    return render_template('student/dashboard.html',
                         challenges=challenges,
                         solved_ids=solved_ids)

@app.route('/student/challenge/<int:challenge_id>')
@require_auth
def student_challenge(challenge_id):
    db = get_db()
    challenge = db.execute('SELECT * FROM challenges WHERE id = ?', (challenge_id,)).fetchone()

    if not challenge:
        return render_template('error.html', message='Challenge not found'), 404

    # Check if already solved
    solved = db.execute('''
        SELECT * FROM student_challenges WHERE student_id = ? AND challenge_id = ?
    ''', (session['student_id'], challenge_id)).fetchone()

    # Check if there's an active session
    port = redis_client.get(f"{session['student_id']}-{challenge_id}")

    return render_template('student/challenge.html',
                         challenge=challenge,
                         solved=solved,
                         active_port=port)

@app.route('/student/logout')
def student_logout():
    session.clear()
    return redirect(url_for('student_login'))

@app.route('/ranking')
def public_ranking():
    """Public ranking page showing student progress"""
    db = get_db()

    # Get ranking data - students with their solved challenge counts
    ranking_data = db.execute('''
        SELECT
            s.name,
            COUNT(sc.challenge_id) as solved_count,
            MAX(sc.solved_at) as last_solved
        FROM students s
        LEFT JOIN student_challenges sc ON s.id = sc.student_id
        GROUP BY s.id, s.name
        ORDER BY solved_count DESC, last_solved ASC
    ''').fetchall()

    # Get total number of challenges
    total_challenges = db.execute('SELECT COUNT(*) as count FROM challenges').fetchone()['count']

    return render_template('ranking.html',
                         ranking_data=ranking_data,
                         total_challenges=total_challenges)

if __name__ == '__main__':
    temp_dir = os.path.join(os.getcwd(), 'tmp')
    os.makedirs(temp_dir, exist_ok=True)
    # Create tmp_checked directory for verified server codes
    tmp_checked_dir = os.path.join(os.getcwd(), 'tmp_checked')
    os.makedirs(tmp_checked_dir, exist_ok=True)
    init_db()

    # Configure Flask to exclude tmp directory from auto-reload
    import sys
    from werkzeug.serving import WSGIRequestHandler
    WSGIRequestHandler.protocol_version = "HTTP/1.1"

    # Set up reloader to exclude tmp directory
    app.config['EXCLUDE_PATTERNS'] = [
        os.path.join(os.getcwd(), 'tmp', '*'),
        os.path.join(os.getcwd(), '__pycache__', '*')
    ]

    # For development - you can disable debug mode or run with use_reloader=False
    # to prevent auto-restart when tmp files change
    app.run(debug=False, host='0.0.0.0', port=5000)