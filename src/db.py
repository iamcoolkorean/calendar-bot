import sqlite3
from utils import encrypt

conn = sqlite3.connect("users.db")  # 파일로 저장됨
cursor = conn.cursor()

def init_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            encrypted_naver_id TEXT,
            encrypted_app_pw TEXT
        )
    """)
    conn.commit()

def save_naver_credentials(user_id, naver_id, app_pw):
    enc_id = encrypt(naver_id)
    enc_pw = encrypt(app_pw)
    cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, encrypted_naver_id, encrypted_app_pw)
        VALUES (?, ?, ?)
    """, (user_id, enc_id, enc_pw))
    conn.commit()

def get_user_credentials(user_id):
    cursor.execute("""
        SELECT encrypted_naver_id, encrypted_app_pw
        FROM users WHERE user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    if row:
        return row  # 암호문 그대로 반환 (복호화는 호출한 곳에서)
    return None, None
