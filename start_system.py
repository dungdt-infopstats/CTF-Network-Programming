#!/usr/bin/env python3
"""
Startup script for the CTF platform
This script checks dependencies and starts the system
"""

import os
import sys
import subprocess
import time

def check_redis():
    """Check if Redis is running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✓ Redis is running")
        return True
    except Exception as e:
        print("✗ Redis is not running or not accessible")
        print("  Please start Redis server first:")
        print("  - On Windows: Download and run redis-server.exe")
        print("  - On Linux/Mac: redis-server")
        return False

def check_dependencies():
    """Check if all Python dependencies are installed"""
    required = ['flask', 'redis', 'cryptography']
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} is missing")

    if missing:
        print(f"\nInstall missing packages with:")
        print(f"pip install {' '.join(missing)}")
        return False
    return True

def initialize_database():
    """Initialize the database with sample data"""
    try:
        from init_data import init_sample_data
        init_sample_data()
        print("✓ Database initialized with sample data")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        return False

def main():
    print("=== CTF Platform Startup ===\n")

    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)

    # Check Redis
    print("\nChecking Redis...")
    if not check_redis():
        sys.exit(1)

    # Initialize database
    print("\nInitializing database...")
    initialize_database()

    print("\n=== Starting CTF Platform ===")
    print("Admin interface: http://localhost:5000")
    print("Student interface: http://localhost:5000/student")
    print("Demo accounts: alice/password123, bob/password456, charlie/password789")
    print("\nPress Ctrl+C to stop the server\n")

    # Start the Flask application
    try:
        from app import app
        import os

        # Configure Flask to exclude tmp directories from auto-reload
        app.config['EXCLUDE_PATTERNS'] = [
            os.path.join(os.getcwd(), 'tmp', '*'),
            os.path.join(os.getcwd(), 'tmp_checked', '*'),
            os.path.join(os.getcwd(), '__pycache__', '*')
        ]

        # For development - you can disable debug mode or run with use_reloader=False
        # to prevent auto-restart when tmp files change
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()