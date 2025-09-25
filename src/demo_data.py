#!/usr/bin/env python3
"""
Demo data setup for CTF Platform
Creates sample challenges and students including student ID 22025501
"""

import bcrypt
from database import get_db_connection

def create_demo_data():
    """Create demo challenges and students"""
    conn = get_db_connection()

    try:
        # Clear existing data (except admin)
        print("Clearing existing demo data...")
        conn.execute("DELETE FROM student_challenges")
        conn.execute("DELETE FROM students WHERE name != 'admin'")
        conn.execute("DELETE FROM challenges")

        # Create demo students
        print("Creating demo students...")
        students_data = [
            ("student1", "student123"),
            ("student2", "student123"),
            ("22025501", "password123"),  # Your requested student ID
            ("alice", "alice123"),
            ("bob", "bob123"),
            ("charlie", "charlie123")
        ]

        for name, password in students_data:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            conn.execute('INSERT INTO students (name, hashed_pw) VALUES (?, ?)', (name, hashed_pw))
            print(f"  ✅ Created student: {name}")

        # Create demo challenges
        print("Creating demo challenges...")
        challenges_data = [
            (
                "Echo Server Challenge",
                "Create a TCP server that echoes back any message sent by clients. The server should handle multiple clients and send the CTF answer when client sends 'GET_FLAG'.",
                "echo_secret_2025"
            ),
            (
                "Chat Server Challenge",
                "Build a multi-client chat server where clients can send messages to all connected users. Implement commands like /users, /help, and /flag.",
                "chat_secret_2025"
            ),
            (
                "File Transfer Challenge",
                "Implement a file transfer protocol where clients can upload and download files from the server. Server should validate file types and sizes.",
                "file_secret_2025"
            ),
            (
                "Calculator Server Challenge",
                "Create a network calculator that accepts mathematical expressions and returns results. Support operations: +, -, *, /, and parentheses.",
                "calc_secret_2025"
            ),
            (
                "Game Server Challenge",
                "Build a simple guessing game server where clients try to guess a random number. Provide hints like 'higher' or 'lower'.",
                "game_secret_2025"
            )
        ]

        for name, description, secret in challenges_data:
            conn.execute('INSERT INTO challenges (name, description, secret) VALUES (?, ?, ?)',
                        (name, description, secret))
            print(f"  ✅ Created challenge: {name}")

        # Create some solved challenges for demo
        print("Creating demo solved challenges...")

        # Get student and challenge IDs
        students = {row[1]: row[0] for row in conn.execute('SELECT id, name FROM students').fetchall()}
        challenges = {row[1]: row[0] for row in conn.execute('SELECT id, name FROM challenges').fetchall()}

        # Mark some challenges as solved by different students
        solved_records = [
            ("student1", "Echo Server Challenge"),
            ("student1", "Calculator Server Challenge"),
            ("22025501", "Echo Server Challenge"),
            ("alice", "Echo Server Challenge"),
            ("alice", "Chat Server Challenge"),
            ("bob", "Game Server Challenge")
        ]

        for student_name, challenge_name in solved_records:
            if student_name in students and challenge_name in challenges:
                student_id = students[student_name]
                challenge_id = challenges[challenge_name]
                conn.execute('''
                INSERT OR IGNORE INTO student_challenges (student_id, challenge_id)
                VALUES (?, ?)
                ''', (student_id, challenge_id))
                print(f"  ✅ {student_name} solved {challenge_name}")

        conn.commit()
        print("\n🎉 Demo data created successfully!")

        # Print summary
        print("\n" + "="*50)
        print("📊 DEMO DATABASE SUMMARY")
        print("="*50)

        print("\n👥 STUDENTS:")
        students_list = conn.execute('SELECT id, name FROM students ORDER BY id').fetchall()
        for student_id, name in students_list:
            solved_count = conn.execute('''
            SELECT COUNT(*) FROM student_challenges WHERE student_id = ?
            ''', (student_id,)).fetchone()[0]
            print(f"  {student_id:2d}. {name:<12} (Solved: {solved_count} challenges)")

        print(f"\n🎯 CHALLENGES:")
        challenges_list = conn.execute('SELECT id, name FROM challenges ORDER BY id').fetchall()
        for challenge_id, name in challenges_list:
            solved_count = conn.execute('''
            SELECT COUNT(*) FROM student_challenges WHERE challenge_id = ?
            ''', (challenge_id,)).fetchone()[0]
            print(f"  {challenge_id}. {name:<25} (Solved by: {solved_count} students)")

        print(f"\n🏆 LEADERBOARD:")
        leaderboard = conn.execute('''
        SELECT s.name, COUNT(sc.challenge_id) as solved_count
        FROM students s
        LEFT JOIN student_challenges sc ON s.id = sc.student_id
        WHERE s.name != 'admin'
        GROUP BY s.id, s.name
        ORDER BY solved_count DESC, s.name
        ''').fetchall()

        for i, (name, solved_count) in enumerate(leaderboard, 1):
            print(f"  {i:2d}. {name:<12} - {solved_count} challenges solved")

        print("\n" + "="*50)
        print("🔑 LOGIN CREDENTIALS:")
        print("="*50)
        print("Admin:     admin / admin123")
        print("Students:  student1, student2 / student123")
        print("Special:   22025501 / password123")
        print("Others:    alice, bob, charlie / [name]123")
        print("="*50)

    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    create_demo_data()