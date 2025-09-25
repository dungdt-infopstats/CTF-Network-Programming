# 🏁 CTF Network Programming Platform

A simple and complete CTF platform for network programming challenges with both **Web UI** and **API**.

## ✨ Features

- 🌐 **Web Frontend** - Easy-to-use web interface
- 🔗 **REST API** - Full API for programmatic access
- 👥 **User Management** - Students and admin accounts
- 🎯 **Challenge System** - Create and solve network programming challenges
- 📁 **File Upload** - Students upload their server code
- ⚡ **Auto Port Management** - Dynamic port allocation
- 🔐 **Secure CTF Answers** - Encrypted student ID verification
- 📊 **Progress Tracking** - Real-time challenge status

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd src
pip install -r requirements.txt
```

### 2. Start Platform
```bash
python simple_start.py
```

Choose **'y'** for demo data when asked.

### 3. Access Web Interface
Open browser: **http://localhost:5000**

### 4. Login with Demo Accounts
- **Admin**: admin / admin123
- **Students**: student1, student2 / student123
- **Special**: 22025501 / password123
- **Others**: alice, bob, charlie / [name]123

## 🌐 Web Interface

### For Students:
1. **Login** → Dashboard with your progress
2. **View Challenges** → See all available challenges
3. **Start Challenge** → Upload code, get connection details
4. **Submit Answer** → Paste CTF answer to complete

### For Admins:
1. **Admin Panel** → Create challenges and students
2. **Manage Users** → View all students and their progress
3. **Create Challenges** → Add new network programming tasks

## 🔧 API Usage

### Authentication
```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name": "student1", "password": "student123"}'
```

### Student Operations
```bash
# Get challenges
curl -X GET http://localhost:5000/api/challenges \
  -H "Authorization: Bearer <token>"

# Upload file
curl -X POST http://localhost:5000/api/challenges/1/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@my_server.py"

# Start challenge
curl -X GET http://localhost:5000/api/challenges/1/start \
  -H "Authorization: Bearer <token>"

# Submit answer
curl -X POST http://localhost:5000/api/challenges/1/submit \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"ctf_answer": "your_ctf_answer_here"}'
```

## 🧪 Testing

### Test with Demo Client
```bash
# Test any student
python test_client.py [challenge_id]

# Test specific student 22025501
python test_student_22025501.py [challenge_id]
```

### Manual Testing
1. **Upload server code** via web interface
2. **Start challenge** to get port
3. **Connect with client** to the given host:port
4. **Get CTF answer** from your server
5. **Submit answer** on web interface

## 📝 Creating Server Code

Your server code must import the CTF helper:

```python
#!/usr/bin/env python3
import socket
import sys
from ctf_helper import get_ctf_answer_for_current_server

def handle_client(client_socket):
    # Your challenge logic here
    client_socket.send(b"Welcome to my server!\n")

    while True:
        data = client_socket.recv(1024).decode().strip()

        if data == "GET_FLAG":
            # Get and send CTF answer
            ctf_answer = get_ctf_answer_for_current_server()
            if ctf_answer:
                client_socket.send(f"CTF_ANSWER:{ctf_answer}\n".encode())
                break
        else:
            # Handle other commands
            client_socket.send(f"Echo: {data}\n".encode())

def start_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()
        handle_client(client_socket)

if __name__ == '__main__':
    port = int(sys.argv[1])  # Port provided by platform
    start_server(port)
```

## 🗂️ File Structure

```
src/
├── app.py                     # Main Flask application
├── simple_start.py           # Easy startup script
├── database.py               # Database operations
├── demo_data.py              # Demo data creation
├── auth.py                   # JWT authentication
├── crypto_utils.py           # Encryption utilities
├── simple_port_manager.py    # Port management
├── ctf_helper.py            # Helper for server codes
├── web_routes.py            # Web frontend routes
├── test_client.py           # General test client
├── test_student_22025501.py # Specific test client
├── requirements.txt         # Dependencies
├── templates/               # HTML templates
│   ├── base.html           # Base template
│   ├── login.html          # Login page
│   ├── dashboard.html      # Student dashboard
│   ├── challenges.html     # Challenge list
│   ├── challenge_detail.html # Challenge page
│   └── admin.html          # Admin panel
├── server_code/             # Pre-built challenge servers
├── tmp/                     # Uploaded student files
└── ctf_platform.db         # SQLite database
```

## 🎯 How It Works

### Challenge Flow:
1. **Student uploads** server code → Saved to `tmp/`
2. **Student starts** challenge:
   - Platform generates CTF answer = `encrypt(student_id, challenge_secret)`
   - Finds free port, stores mapping in memory
   - Executes student's server on that port
   - Returns connection details
3. **Student connects** to their server → Gets CTF answer
4. **Student submits** answer → Platform verifies by decryption

### Security:
- **JWT tokens** for authentication
- **Encrypted CTF answers** tied to student ID
- **Port isolation** - each student gets unique port
- **Automatic cleanup** - ports expire after 1 hour

## 🐛 Troubleshooting

### Database Issues:
- Ensure you're running from `src/` directory
- Check file permissions for `ctf_platform.db`

### Port Issues:
- Default ports: 8000-9000
- Check if ports are already in use
- Platform will find free ports automatically

### Connection Issues:
- Ensure your server code accepts connections on `('localhost', port)`
- Use `python simple_start.py` not `app.py` directly

## 📊 Database Schema

```sql
-- Challenges table
CREATE TABLE challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    secret TEXT NOT NULL
);

-- Students table
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    hashed_pw TEXT NOT NULL
);

-- Progress tracking
CREATE TABLE student_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL,
    solved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, challenge_id)
);
```

## 🎓 Educational Use

Perfect for:
- **Network Programming Courses**
- **CTF Competitions**
- **Socket Programming Practice**
- **Client-Server Architecture Learning**

Students learn by implementing real network servers that handle actual client connections!

---

**🌟 Ready to start?** Run `python simple_start.py` and visit http://localhost:5000