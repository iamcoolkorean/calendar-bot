import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

def get_fernet():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY not set in .env")
    return Fernet(key)

def encrypt(plain_text: str) -> str:
    f = get_fernet()
    return f.encrypt(plain_text.encode()).decode()

def decrypt(encrypted_text: str) -> str:
    f = get_fernet()
    return f.decrypt(encrypted_text.encode()).decode()
