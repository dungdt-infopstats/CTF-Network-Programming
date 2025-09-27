# CTF Web Platform

A Flask-based CTF (Capture The Flag) platform where students can upload server code and participate in challenges.

## Features

### Admin Interface
- **Challenge Management**: Create, edit, and delete challenges
- **Student Management**: Add students manually or import from CSV, bulk delete
- **No authentication required**: Direct access to admin features

### Student Interface
- **Authentication**: Login system for students
- **Challenge Participation**: View challenges, upload server code, start servers, submit answers
- **Real-time Feedback**: AJAX-based interactions for smooth user experience

## Architecture

### Database (SQLite)
- `challenges`: Challenge information with secret keys
- `students`: Student accounts with hashed passwords
- `student_challenges`: Tracks solved challenges per student

### Redis Integration
- Stores active port mappings: `{student_id-chal_id: port}`
- Stores CTF answers: `{port: encrypted_answer}`

### Server Code Execution
- Students upload Python server code to `/tmp`
- System executes server code in isolated processes
- Servers bind to available ports and print port numbers
- Common utility function retrieves correct CTF answers from Redis

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Redis Server**
   ```bash
   redis-server
   ```

3. **Initialize Database and Sample Data**
   ```bash
   python init_data.py
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

## Usage

### Admin Access
- Navigate to `http://localhost:5000` for admin dashboard
- Manage challenges at `/admin/challenges`
- Manage students at `/admin/students`

### Student Access
- Navigate to `http://localhost:5000/student` for student login
- **Demo accounts**: alice/password123, bob/password456, charlie/password789

### Challenge Workflow
1. **Student logs in** and selects a challenge
2. **Uploads server code** (Python file implementing the challenge)
3. **Starts the server** (system runs the uploaded code)
4. **Connects as client** to test the server (using provided example code)
5. **Submits the CTF flag** received from successful server interaction

## Sample Challenges

### Challenge 1: Addition Server
- Server sends two random numbers
- Client must calculate and return the sum
- Correct answer returns the encrypted student ID as CTF flag

### Challenge 2: Multiplication Server
- Server sends two random numbers
- Client must calculate and return the product
- Correct answer returns the encrypted student ID as CTF flag

## Files Structure

```
├── app.py                           # Main Flask application
├── init_data.py                     # Database initialization with sample data
├── server_utils.py                  # Utilities for server code
├── requirements.txt                 # Python dependencies
├── challenge1_addition_server.py    # Sample addition challenge server
├── challenge2_multiplication_server.py # Sample multiplication challenge server
├── templates/
│   ├── admin/                       # Admin interface templates
│   └── student/                     # Student interface templates
├── static/                          # Static files (CSS, JS)
└── tmp/                            # Uploaded server code storage
```

## Security Notes

- Passwords are hashed with SHA-256
- CTF answers are encrypted using Fernet (symmetric encryption)
- Server code execution is isolated but runs with system privileges
- Redis stores temporary session data

## API Endpoints

### Student API
- `POST /api/auth/login` - Student authentication
- `GET /api/challenges` - List all challenges
- `GET /api/challenges/{id}` - Get specific challenge
- `POST /api/challenges/{id}/upload` - Upload server code
- `GET /api/challenges/{id}/start` - Start challenge server
- `POST /api/challenges/{id}/submit` - Submit CTF answer
- `GET /api/challenges/{id}/status` - Check challenge status

## Development Notes

- The system uses port 5000 for the main Flask application
- Challenge servers bind to random available ports
- Redis runs on standard port 6379
- Server code must print its port number as the first line of output
- The `get_ctf_answer()` function in server_utils.py should be called by all server implementations