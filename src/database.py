#!/usr/bin/env python3
"""
Database initialization and management for CTF Platform
"""

import sqlite3
import os
from datetime import datetime
import bcrypt

DATABASE_FILE = 'ctf_platform.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access
    return conn

def init_database():
    """Initialize database with required tables"""
    conn = get_db_connection()

    try:
        # Create tables
        conn.executescript('''
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

        # Create admin user if not exists
        admin_password = 'admin123'
        hashed_admin_pw = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn.execute('''
        INSERT OR IGNORE INTO students (name, hashed_pw) VALUES ('admin', ?)
        ''', (hashed_admin_pw,))

        # Create sample student accounts
        student_password = 'student123'
        hashed_student_pw = bcrypt.hashpw(student_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn.execute('''
        INSERT OR IGNORE INTO students (name, hashed_pw) VALUES ('student1', ?)
        ''', (hashed_student_pw,))

        conn.execute('''
        INSERT OR IGNORE INTO students (name, hashed_pw) VALUES ('student2', ?)
        ''', (hashed_student_pw,))

        # Create sample challenge
        conn.execute('''
        INSERT OR IGNORE INTO challenges (name, description, secret) VALUES
        ('Network Echo Challenge', 'Create a client that connects to server and echoes messages', 'secret_key_123')
        ''')

        conn.commit()
        print("Database initialized successfully!")

    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_student(name, password):
    """Add a new student"""
    conn = get_db_connection()
    try:
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn.execute('INSERT INTO students (name, hashed_pw) VALUES (?, ?)', (name, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def add_challenge(name, description, secret):
    """Add a new challenge"""
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO challenges (name, description, secret) VALUES (?, ?, ?)',
                    (name, description, secret))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding challenge: {e}")
        return False
    finally:
        conn.close()

def get_all_challenges():
    """Get all challenges"""
    conn = get_db_connection()
    try:
        challenges = conn.execute('SELECT * FROM challenges').fetchall()
        return [dict(challenge) for challenge in challenges]
    finally:
        conn.close()

def get_challenge_by_id(challenge_id):
    """Get challenge by ID"""
    conn = get_db_connection()
    try:
        challenge = conn.execute('SELECT * FROM challenges WHERE id = ?', (challenge_id,)).fetchone()
        return dict(challenge) if challenge else None
    finally:
        conn.close()

def get_all_students():
    """Get all students"""
    conn = get_db_connection()
    try:
        students = conn.execute('SELECT id, name FROM students').fetchall()
        return [dict(student) for student in students]
    finally:
        conn.close()

def verify_student(name, password):
    """Verify student credentials"""
    conn = get_db_connection()
    try:
        student = conn.execute('SELECT * FROM students WHERE name = ?', (name,)).fetchone()
        if student and bcrypt.checkpw(password.encode('utf-8'), student['hashed_pw'].encode('utf-8')):
            return dict(student)
        return None
    finally:
        conn.close()

def mark_challenge_solved(student_id, challenge_id):
    """Mark challenge as solved by student"""
    conn = get_db_connection()
    try:
        conn.execute('''
        INSERT OR IGNORE INTO student_challenges (student_id, challenge_id)
        VALUES (?, ?)
        ''', (student_id, challenge_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error marking challenge solved: {e}")
        return False
    finally:
        conn.close()

def is_challenge_solved(student_id, challenge_id):
    """Check if student has solved challenge"""
    conn = get_db_connection()
    try:
        result = conn.execute('''
        SELECT 1 FROM student_challenges
        WHERE student_id = ? AND challenge_id = ?
        ''', (student_id, challenge_id)).fetchone()
        return result is not None
    finally:
        conn.close()

if __name__ == '__main__':
    init_database()
    print("Sample accounts:")
    print("Admin: admin / admin123")
    print("Students: student1, student2 / student123")