#!/usr/bin/env python3
"""
Web Server cho hệ thống Online Judge Network Programming
Sử dụng Flask để cung cấp giao diện web cho sinh viên và giảng viên
"""

from flask import Flask, render_template, request, session, redirect, url_for, flash
import os
import uuid
import hmac
import hashlib
import json
import time
from datetime import datetime

# --- Cấu hình ứng dụng ---
app = Flask(__name__)
app.secret_key = 'network-programming-oj-secret-key-2025'  # Key để mã hóa session

# --- Cấu hình ---
TOKEN_FILE = "/tmp/judge_tokens.json"  # File để giao tiếp với Judge Server

# --- Giả lập cơ sở dữ liệu ---
# Trong thực tế, đây sẽ là các bảng trong CSDL
USERS = {
    "student1": {"password": "pass1", "full_name": "Nguyễn Văn A"},
    "student2": {"password": "pass2", "full_name": "Trần Thị B"},
    "admin": {"password": "admin123", "full_name": "Giảng viên"}
}

PROBLEMS = [
    {
        "id": 1,
        "title": "Bài 1: Tải và Phân tích File Log",
        "description": "Viết một chương trình client kết nối đến server, tải file log được gửi về, tìm ra 'SECRET_CODE' bên trong file và gửi lại kết quả cho server để nhận mã nộp bài.",
        "port": 10005,
        "base_flag": "flask-is-awesome-2025",  # Phải khớp với Judge Server
        "difficulty": "Cơ bản",
        "points": 100
    }
]

# CSDL giả lập cho token và bài đã giải
# Cấu trúc: { "username": { "problem_id": {"token": "xxx", "created_at": timestamp} } }
USER_SESSIONS = {} 
# Cấu trúc: { "username": [problem_id_1, problem_id_2] }
SOLVED_PROBLEMS = {}

# --- Hàm trợ giúp ---
def generate_submission_code(session_token, base_flag):
    """Tái tạo mã nộp bài để xác thực."""
    return hmac.new(base_flag.encode(), session_token.encode(), hashlib.sha256).hexdigest()

def save_token_to_file(token, username, problem_id):
    """Lưu token vào file để Judge Server có thể đọc"""
    try:
        # Đọc dữ liệu hiện tại
        tokens = {}
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                tokens = json.load(f)
        
        # Thêm token mới
        tokens[token] = {
            "username": username,
            "problem_id": problem_id,
            "created_at": time.time()
        }
        
        # Ghi lại file
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)
            
        print(f"[WEB] Đã lưu token '{token}' cho user '{username}' vào file.")
        return True
    except Exception as e:
        print(f"[WEB] Lỗi khi lưu token: {e}")
        return False

def remove_token_from_file(token):
    """Xóa token khỏi file sau khi đã sử dụng"""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                tokens = json.load(f)
            
            if token in tokens:
                del tokens[token]
                
                with open(TOKEN_FILE, 'w') as f:
                    json.dump(tokens, f, indent=2)
                    
                print(f"[WEB] Đã xóa token '{token}' khỏi file.")
        return True
    except Exception as e:
        print(f"[WEB] Lỗi khi xóa token: {e}")
        return False

# --- Các Route của Web ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Trang đăng nhập"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form.get('password', '')
        
        # Kiểm tra thông tin đăng nhập
        if username in USERS:
            # Để đơn giản demo, chỉ cần username đúng
            session['username'] = username
            session['full_name'] = USERS[username]['full_name']
            
            # Khởi tạo session cho user nếu chưa có
            if username not in USER_SESSIONS:
                USER_SESSIONS[username] = {}
            if username not in SOLVED_PROBLEMS:
                SOLVED_PROBLEMS[username] = []
                
            flash(f"Chào mừng {USERS[username]['full_name']}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Tên đăng nhập không tồn tại.", "error")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Đăng xuất"""
    username = session.get('username', 'Unknown')
    session.clear()
    flash(f"Đã đăng xuất thành công. Hẹn gặp lại!", "success")
    return redirect(url_for('login'))

@app.route('/')
def index():
    """Trang chủ - danh sách bài tập"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    solved_list = SOLVED_PROBLEMS.get(username, [])
    
    # Thống kê
    total_problems = len(PROBLEMS)
    solved_count = len(solved_list)
    total_points = sum(p['points'] for p in PROBLEMS if p['id'] in solved_list)
    
    return render_template('index.html', 
                         problems=PROBLEMS, 
                         solved_problems=solved_list,
                         stats={
                             'total_problems': total_problems,
                             'solved_count': solved_count,
                             'total_points': total_points
                         })

@app.route('/problem/<int:problem_id>', methods=['GET', 'POST'])
def problem_detail(problem_id):
    """Trang chi tiết bài tập"""
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    problem = next((p for p in PROBLEMS if p['id'] == problem_id), None)
    
    if not problem:
        flash("Bài tập không tồn tại.", "error")
        return redirect(url_for('index'))

    # Tạo hoặc lấy Session Token cho user và bài tập này
    if problem_id not in USER_SESSIONS[username]:
        # Tạo token mới
        token = str(uuid.uuid4())
        USER_SESSIONS[username][problem_id] = {
            "token": token,
            "created_at": time.time()
        }
        
        # Lưu token vào file để Judge Server có thể đọc
        save_token_to_file(token, username, problem_id)
        
        print(f"[WEB] Đã cấp token mới '{token}' cho user '{username}', problem {problem_id}")
    
    session_token = USER_SESSIONS[username][problem_id]["token"]

    # Xử lý nộp bài
    if request.method == 'POST':
        submitted_code = request.form['submission_code'].strip()
        
        if not submitted_code:
            flash("Vui lòng nhập mã nộp bài.", "error")
            return render_template('problem.html', problem=problem, session_token=session_token)
        
        # Tạo lại mã mong đợi để so sánh
        expected_code = generate_submission_code(session_token, problem['base_flag'])

        if submitted_code == expected_code:
            # Nộp bài thành công
            flash("🎉 Chính xác! Bạn đã giải thành công bài toán.", "success")
            
            # Ghi nhận bài đã giải
            if problem_id not in SOLVED_PROBLEMS[username]:
                SOLVED_PROBLEMS[username].append(problem_id)
                print(f"[WEB] User '{username}' đã giải thành công problem {problem_id}")
            
            # Xóa token sau khi đã sử dụng để không thể nộp lại
            if problem_id in USER_SESSIONS[username]:
                old_token = USER_SESSIONS[username][problem_id]["token"]
                del USER_SESSIONS[username][problem_id]
                remove_token_from_file(old_token)
            
            return redirect(url_for('index'))
        else:
            flash("❌ Mã nộp bài không chính xác. Hãy kiểm tra lại chương trình của bạn.", "error")
            print(f"[WEB] User '{username}' nộp sai mã. Expected: {expected_code}, Got: {submitted_code}")

    return render_template('problem.html', problem=problem, session_token=session_token)

@app.route('/leaderboard')
def leaderboard():
    """Bảng xếp hạng"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Tính điểm cho từng user
    rankings = []
    for username in USERS:
        if username in SOLVED_PROBLEMS:
            solved_list = SOLVED_PROBLEMS[username]
            total_points = sum(p['points'] for p in PROBLEMS if p['id'] in solved_list)
            solved_count = len(solved_list)
        else:
            total_points = 0
            solved_count = 0
            
        rankings.append({
            'username': username,
            'full_name': USERS[username]['full_name'],
            'solved_count': solved_count,
            'total_points': total_points
        })
    
    # Sắp xếp theo điểm giảm dần
    rankings.sort(key=lambda x: (x['total_points'], x['solved_count']), reverse=True)
    
    return render_template('leaderboard.html', rankings=rankings)

@app.route('/status')
def status():
    """Trang trạng thái hệ thống"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Kiểm tra Judge Server có hoạt động không
    judge_status = "Unknown"
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 10005))
        sock.close()
        judge_status = "Online" if result == 0 else "Offline"
    except:
        judge_status = "Offline"
    
    # Thống kê token
    active_tokens = 0
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                tokens = json.load(f)
                active_tokens = len(tokens)
    except:
        pass
    
    system_info = {
        'judge_server_status': judge_status,
        'active_tokens': active_tokens,
        'total_users': len(USERS),
        'total_problems': len(PROBLEMS),
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return render_template('status.html', system_info=system_info)

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🌐 NETWORK PROGRAMMING ONLINE JUDGE - WEB SERVER")
    print("=" * 60)
    print(f"🔗 URL: http://127.0.0.1:5000")
    print(f"👥 Demo accounts: student1, student2, admin")
    print(f"📁 Token file: {TOKEN_FILE}")
    print("=" * 60)
    
    # Tạo thư mục tmp nếu chưa có
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    
    # Khởi động Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

