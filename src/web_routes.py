#!/usr/bin/env python3
"""
Web frontend routes for CTF Platform
"""

from flask import render_template, request, redirect, url_for, session, flash, jsonify
import requests
import json

def register_web_routes(app):
    """Register web frontend routes"""

    API_BASE = "http://localhost:5000"

    @app.route('/web')
    def web_index():
        """Redirect to dashboard"""
        return redirect(url_for('web_dashboard'))

    @app.route('/web/login', methods=['GET', 'POST'])
    def web_login():
        """Web login page"""
        if request.method == 'POST':
            username = request.form.get('name')
            password = request.form.get('password')

            try:
                # Call API login
                response = requests.post(f"{API_BASE}/api/auth/login", json={
                    'name': username,
                    'password': password
                })

                if response.status_code == 200:
                    data = response.json()
                    session['token'] = data['token']
                    session['student_id'] = data['student']['id']
                    session['student_name'] = data['student']['name']
                    return redirect(url_for('web_dashboard'))
                else:
                    error_data = response.json()
                    return render_template('login.html', error=error_data.get('error', 'Login failed'))

            except Exception as e:
                return render_template('login.html', error=f"Connection error: {str(e)}")

        return render_template('login.html')

    @app.route('/web/logout')
    def web_logout():
        """Web logout"""
        session.clear()
        return redirect(url_for('web_login'))

    def require_web_auth(f):
        """Decorator for web routes that require authentication"""
        def wrapper(*args, **kwargs):
            if 'token' not in session:
                return redirect(url_for('web_login'))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper

    @app.route('/web/dashboard')
    @require_web_auth
    def web_dashboard():
        """Web dashboard"""
        try:
            # Get challenges
            response = requests.get(f"{API_BASE}/api/challenges", headers={
                'Authorization': f"Bearer {session['token']}"
            })

            if response.status_code == 200:
                challenges = response.json()['challenges']
                solved_count = sum(1 for c in challenges if c.get('solved', False))
                total_challenges = len(challenges)

                return render_template('dashboard.html',
                                     challenges=challenges,
                                     solved_count=solved_count,
                                     total_challenges=total_challenges)
            else:
                flash("Failed to load challenges", "error")
                return render_template('dashboard.html', challenges=[])

        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            return render_template('dashboard.html', challenges=[])

    @app.route('/web/challenges')
    @require_web_auth
    def web_challenges():
        """Web challenges list"""
        try:
            response = requests.get(f"{API_BASE}/api/challenges", headers={
                'Authorization': f"Bearer {session['token']}"
            })

            if response.status_code == 200:
                challenges = response.json()['challenges']
                return render_template('challenges.html', challenges=challenges)
            else:
                flash("Failed to load challenges", "error")
                return render_template('challenges.html', challenges=[])

        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            return render_template('challenges.html', challenges=[])

    @app.route('/web/challenges/<int:challenge_id>')
    @require_web_auth
    def web_challenge_detail(challenge_id):
        """Web challenge detail page"""
        try:
            response = requests.get(f"{API_BASE}/api/challenges/{challenge_id}", headers={
                'Authorization': f"Bearer {session['token']}"
            })

            if response.status_code == 200:
                challenge = response.json()['challenge']
                return render_template('challenge_detail.html', challenge=challenge)
            else:
                flash("Challenge not found", "error")
                return redirect(url_for('web_challenges'))

        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for('web_challenges'))

    @app.route('/web/challenges/<int:challenge_id>/submit', methods=['POST'])
    @require_web_auth
    def web_submit_challenge(challenge_id):
        """Web challenge submission"""
        ctf_answer = request.form.get('ctf_answer')

        try:
            response = requests.post(f"{API_BASE}/api/challenges/{challenge_id}/submit",
                                   json={'ctf_answer': ctf_answer},
                                   headers={'Authorization': f"Bearer {session['token']}"})

            if response.status_code == 200:
                flash("Challenge solved successfully! 🎉", "success")
            else:
                error_data = response.json()
                flash(f"Submit failed: {error_data.get('error', 'Unknown error')}", "error")

        except Exception as e:
            flash(f"Error: {str(e)}", "error")

        return redirect(url_for('web_challenge_detail', challenge_id=challenge_id))

    @app.route('/web/admin')
    @require_web_auth
    def web_admin():
        """Web admin panel"""
        if session.get('student_name') != 'admin':
            flash("Admin access required", "error")
            return redirect(url_for('web_dashboard'))

        return render_template('admin.html')

    # Default route - redirect to web
    @app.route('/')
    def index():
        """Default route"""
        return redirect(url_for('web_login'))