import os
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_db():
    """Get PostgreSQL database connection"""
    try:
        # For local development with SQLite
        if os.environ.get('RENDER') is None and 'DATABASE_URL' not in os.environ:
            import sqlite3
            conn = sqlite3.connect('voting_system.db')
            conn.row_factory = sqlite3.Row
            return conn
        else:
            # For Render (PostgreSQL)
            DATABASE_URL = os.environ.get('DATABASE_URL')
            if DATABASE_URL.startswith('postgres://'):
                DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialize database with PostgreSQL schema"""
    with get_db() as db:
        cursor = db.cursor()
        
        # Create constituencies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS constituencies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                state VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create voters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voters (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                constituency VARCHAR(255) NOT NULL,
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create admins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create candidates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                party VARCHAR(255) NOT NULL,
                constituency VARCHAR(255) NOT NULL,
                photo_path TEXT,
                symbol_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create elections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS elections (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                constituency VARCHAR(255) NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                status VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create votes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id SERIAL PRIMARY KEY,
                voter_id INTEGER NOT NULL,
                election_id INTEGER NOT NULL,
                candidate_id INTEGER NOT NULL,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(voter_id, election_id),
                FOREIGN KEY (voter_id) REFERENCES voters (id),
                FOREIGN KEY (election_id) REFERENCES elections (id),
                FOREIGN KEY (candidate_id) REFERENCES candidates (id)
            )
        ''')
        
        # Create audit_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                action VARCHAR(255) NOT NULL,
                user_type VARCHAR(50) NOT NULL,
                user_id INTEGER NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert Andhra Pradesh constituencies
        ap_constituencies = [
            'Araku', 'Srikakulam', 'Vizianagaram', 'Visakhapatnam', 
            'Anakapalli', 'Kakinada', 'Amalapuram', 'Rajahmundry', 
            'Narasapuram', 'Eluru', 'Machilipatnam', 'Vijayawada', 
            'Guntur', 'Narasaraopet', 'Bapatla', 'Ongole', 
            'Nandyal', 'Kurnool', 'Anantapur', 'Hindupur', 
            'Kadapa', 'Nellore', 'Tirupati', 'Rajampet', 
            'Chittoor'
        ]
        
        for constituency in ap_constituencies:
            cursor.execute(
                'INSERT INTO constituencies (name, state) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING',
                (constituency, 'Andhra Pradesh')
            )
        
        # Insert default admin
        cursor.execute(
            'SELECT * FROM admins WHERE username = %s',
            ('admin',)
        )
        existing_admin = cursor.fetchone()
        
        if not existing_admin:
            cursor.execute(
                'INSERT INTO admins (username, password) VALUES (%s, %s)',
                ('admin', hash_password('admin123'))
            )
            print("Default admin created: username='admin', password='admin123'")
        
        db.commit()

def get_constituencies():
    """Get all constituencies for dropdowns"""
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('SELECT name FROM constituencies ORDER BY name')
        constituencies = cursor.fetchall()
        return [constituency['name'] for constituency in constituencies]