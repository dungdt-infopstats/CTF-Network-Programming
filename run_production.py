#!/usr/bin/env python3
"""
Production startup script for the CTF platform
This script runs without auto-reload to prevent restart when tmp files change
"""

import os
import sys

def main():
    print("=== CTF Platform Production Mode ===\n")

    # Set environment for production
    os.environ['FLASK_ENV'] = 'production'

    # Ensure directories exist
    temp_dir = os.path.join(os.getcwd(), 'tmp')
    checked_dir = os.path.join(os.getcwd(), 'tmp_checked')
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(checked_dir, exist_ok=True)

    print("Admin interface: http://localhost:5000/admin")
    print("Student interface: http://localhost:5000")
    print("Ranking page: http://localhost:5000/ranking")
    print("Demo accounts: alice/password123, bob/password456, charlie/password789")
    print("\nPress Ctrl+C to stop the server\n")

    # Start the Flask application without auto-reload
    try:
        from app import app, init_db
        init_db()

        # Run in production mode without auto-reload
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()