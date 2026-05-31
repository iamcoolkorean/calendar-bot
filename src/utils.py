from cryptography.fernet import Fernet
import os

def get_fernet():
    key = os.getenv("ENCRYPTION_KEY")
    return Fernet(key)

def encrypt(plain_text: str) -> str:
    f = get_fernet()
    return f.encrypt(plain_text.encode()).decode()

def decrypt(encrypted_text: str) -> str:
    f = get_fernet()
    return f.decrypt(encrypted_text.encode()).decode()
