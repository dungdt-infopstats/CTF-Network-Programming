from app import get_db, init_db
import hashlib
import secrets

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_sample_data():
    init_db()
    db = get_db()

    # Create sample challenges
    challenges = [
        ('Addition Challenge', 'Server sends 2 numbers, client must calculate the sum', 'secret1'),
        ('Multiplication Challenge', 'Server sends 2 numbers, client must calculate the product', 'secret2')
    ]

    for name, desc, secret in challenges:
        # Check if challenge with this name already exists
        existing = db.execute('SELECT id FROM challenges WHERE name = ?', (name,)).fetchone()
        if not existing:
            db.execute('INSERT INTO challenges (name, description, secret) VALUES (?, ?, ?)',
                      (name, desc, secret))

    # Create sample students
    students = [
        ('alice', 'password123'),
        ('bob', 'password456'),
        ('charlie', 'password789')
    ]

    for username, password in students:
        hashed = hash_password(password)
        try:
            db.execute('INSERT INTO students (name, hashed_pw) VALUES (?, ?)', (username, hashed))
        except:
            pass  # Student already exists

    db.commit()
    db.close()
    print("Sample data initialized successfully!")

if __name__ == '__main__':
    init_sample_data()