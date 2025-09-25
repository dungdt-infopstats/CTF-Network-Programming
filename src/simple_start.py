#!/usr/bin/env python3
"""
Simple startup script - no external dependencies
"""

import os
import sys

def main():
    print("🌟 CTF Platform - Simple Setup")
    print("=" * 40)

    # Initialize database
    print("📊 Initializing database...")
    from database import init_database
    init_database()

    # Ask if user wants demo data
    while True:
        choice = input("Do you want to create demo data? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            print("📋 Creating demo data...")
            from demo_data import create_demo_data
            create_demo_data()
            break
        elif choice in ['n', 'no']:
            print("📋 Skipping demo data creation")
            break
        else:
            print("Please enter 'y' or 'n'")

    print("🚀 Starting CTF Platform...")
    print("📍 URL: http://localhost:5000")
    print("=" * 40)

    # Start Flask app
    from app import app
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()