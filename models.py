# models.py
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB = "exam.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    );
    """)

    # exams
    cur.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        duration_minutes INTEGER NOT NULL,
        max_questions INTEGER NOT NULL DEFAULT 50
    );
    """)

    # questions (MCQ)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,
        q_index INTEGER NOT NULL,
        question TEXT NOT NULL,
        option_a TEXT, option_b TEXT, option_c TEXT, option_d TEXT,
        correct TEXT,
        FOREIGN KEY(exam_id) REFERENCES exams(id)
    );
    """)

    # attempts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        exam_id INTEGER NOT NULL,
        start_time TEXT,
        allowed_until TEXT,
        end_time TEXT,
        score INTEGER,
        submitted INTEGER DEFAULT 0,
        time_exceeded INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(exam_id) REFERENCES exams(id)
    );
    """)

    # answers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        selected TEXT,
        FOREIGN KEY(attempt_id) REFERENCES attempts(id),
        FOREIGN KEY(question_id) REFERENCES questions(id)
    );
    """)

    # proctor images
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proctor_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER,
        filename TEXT,
        timestamp TEXT,
        FOREIGN KEY(attempt_id) REFERENCES attempts(id)
    );
    """)

    # proctor audio
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proctor_audio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER,
        filename TEXT,
        timestamp TEXT,
        FOREIGN KEY(attempt_id) REFERENCES attempts(id)
    );
    """)

    # proctor events (tab switch, focus, etc.)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proctor_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER,
        event_type TEXT,
        detail TEXT,
        timestamp TEXT,
        FOREIGN KEY(attempt_id) REFERENCES attempts(id)
    );
    """)

    conn.commit()
    conn.close()

def create_user(username, password, is_admin=0):
    conn = get_conn()
    cur = conn.cursor()
    pwd_hash = generate_password_hash(password)
    cur.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (?,?,?)",
                (username, pwd_hash, is_admin))
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    if row and check_password_hash(row["password_hash"], password):
        return dict(row)
    return None

def is_admin(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM users WHERE id=?", (user_id,))
    r = cur.fetchone()
    conn.close()
    return bool(r and r["is_admin"] == 1)
