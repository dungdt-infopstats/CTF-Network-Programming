# CTF Network Programming Platform

A complete CTF platform for network programming challenges built with Flask, SQLite, and Redis.

## Features

- **Student Authentication**: JWT-based authentication system
- **Challenge Management**: CRUD operations for challenges and students
- **File Upload**: Students can upload server code for testing
- **Dynamic Port Allocation**: Automatic port management with Redis
- **CTF Answer System**: Encrypted student ID as challenge answers
- **Real-time Status**: Track challenge progress and completion

## Tech Stack

- **Flask** - Web framework
- **SQLite** - Database
- **Redis** - Port-answer mapping
- **PyJWT** - Authentication
- **bcrypt** - Password hashing
- **cryptography** - Encryption/decryption

## Installation

1. Install dependencies:
```bash
cd src
pip install -r requirements.txt
```

2. Start Redis server:
```bash
redis-server
```

3. Initialize database:
```bash
python database.py
```

4. Start the application:
```bash
python app.py
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Student login

### Student Endpoints
- `GET /api/challenges` - Get all challenges
- `GET /api/challenges/{id}` - Get specific challenge
- `POST /api/challenges/{id}/upload` - Upload server code
- `GET /api/challenges/{id}/start` - Start challenge (get port)
- `POST /api/challenges/{id}/submit` - Submit CTF answer
- `GET /api/runs/{run_id}/status` - Check run status

### Admin Endpoints
- `POST /api/admin/challenges` - Create challenge
- `POST /api/admin/students` - Create student
- `GET /api/admin/students` - List students

## Usage

### For Students

1. **Login**:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name": "student1", "password": "student123"}'
```

2. **Get Challenges**:
```bash
curl -X GET http://localhost:5000/api/challenges \
  -H "Authorization: Bearer <your_token>"
```

3. **Start Challenge**:
```bash
curl -X GET http://localhost:5000/api/challenges/1/start \
  -H "Authorization: Bearer <your_token>"
```

4. **Connect to Server** (use returned host:port)

5. **Submit Answer**:
```bash
curl -X POST http://localhost:5000/api/challenges/1/submit \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"ctf_answer": "your_encrypted_answer"}'
```

### For Testing

Run the test client:
```bash
python test_client.py [challenge_id]
```

## File Structure

```
src/
├── app.py                    # Main Flask application
├── database.py              # Database operations
├── auth.py                  # JWT authentication
├── crypto_utils.py          # Encryption utilities
├── redis_manager.py         # Redis operations
├── ctf_helper.py           # Common functions for server codes
├── test_client.py          # Test client
├── example_student_upload.py # Example student server
├── requirements.txt        # Dependencies
├── server_code/            # Challenge server codes
│   └── challenge_1.py     # Example challenge server
└── tmp/                   # Uploaded student files
```

## How It Works

### Challenge Flow

1. **Student uploads server code** → Saved to `/tmp/<chal_id>_<student_id>_<random>.py`

2. **Student starts challenge**:
   - System generates CTF answer: `encrypt(student_id, challenge_secret)`
   - Finds free port and stores in Redis: `{port: ctf_answer}`
   - Executes challenge server on that port
   - Returns connection info to student

3. **Student connects to server**:
   - Server uses `ctf_helper.get_ctf_answer_for_current_server()` to get answer
   - Server sends CTF answer to student client

4. **Student submits answer**:
   - System decrypts answer with challenge secret
   - Verifies student ID matches JWT token
   - Marks challenge as solved

### Server Code Requirements

All server codes (both challenge and student-uploaded) must:

1. **Import CTF helper**:
```python
from ctf_helper import get_ctf_answer_for_current_server
```

2. **Get CTF answer**:
```python
ctf_answer = get_ctf_answer_for_current_server()
```

3. **Send to client**:
```python
client_socket.send(f"CTF_ANSWER:{ctf_answer}\n".encode())
```

## Sample Accounts

- **Admin**: admin / admin123
- **Students**: student1, student2 / student123

## Database Schema

### challenges
- id (INTEGER PRIMARY KEY)
- name (TEXT NOT NULL)
- description (TEXT)
- secret (TEXT NOT NULL)

### students
- id (INTEGER PRIMARY KEY)
- name (TEXT NOT NULL UNIQUE)
- hashed_pw (TEXT NOT NULL)

### student_challenges
- id (INTEGER PRIMARY KEY)
- student_id (INTEGER)
- challenge_id (INTEGER)
- solved_at (DATETIME)

## Redis Keys

- `port:{port}` → CTF answer (with TTL)
- `run:{run_id}` → Run information hash

## Health Check

```bash
curl http://localhost:5000/health
```

Returns system status including Redis connection.