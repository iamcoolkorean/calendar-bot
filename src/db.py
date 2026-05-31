import sqlite3
from src.utils import encrypt, decrypt

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            encrypted_naver_id TEXT,
            encrypted_app_pw TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_naver_credentials(user_id: int, naver_id: str, app_pw: str):
    enc_id = encrypt(naver_id)
    enc_pw = encrypt(app_pw)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO users (user_id, encrypted_naver_id, encrypted_app_pw)
        VALUES (?, ?, ?)
    """, (user_id, enc_id, enc_pw))
    conn.commit()
    conn.close()

def get_user_credentials(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT encrypted_naver_id, encrypted_app_pw FROM users WHERE user_id = ?
    """, (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return row  # (enc_id, enc_pw)
    return None, None

def user_has_naver_creds(user_id: int) -> bool:
    creds = get_user_credentials(user_id)
    return creds[0] is not None and creds[1] is not None
