import sqlite3
import secrets
import base64
import hashlib
import hmac
import time
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional

import config
from models import AccountEntry

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(config.DB_PATH)
        self.cursor = self.conn.cursor()
        self.create_tables()
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  

    def close(self):
        self.conn.close()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth (
                id INTEGER PRIMARY KEY CHECK (id = 1), 
                salt BLOB NOT NULL,
                password_hash BLOB NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                service TEXT UNIQUE NOT NULL,
                login TEXT NOT NULL,
                password BLOB NOT NULL
            )
        ''')
        self.conn.commit()

    def get_auth(self):
        self.cursor.execute("SELECT salt, password_hash FROM auth WHERE id = 1")
        return self.cursor.fetchone()

    def set_auth(self, salt, password_hash):
        self.cursor.execute("INSERT INTO auth (id, salt, password_hash) VALUES (1, ?, ?)", (salt, password_hash))
        self.conn.commit()

    def add_account(self, service, login, encrypted_pass):
        self.cursor.execute("INSERT OR REPLACE INTO accounts (service, login, password) VALUES (?, ?, ?)", 
                            (service, login, encrypted_pass))
        self.conn.commit()

    def get_account(self, service):
        self.cursor.execute("SELECT login, password FROM accounts WHERE service = ?", (service,))
        return self.cursor.fetchone()

    def get_all_services(self):
        self.cursor.execute("SELECT service FROM accounts ORDER BY service")
        return [row[0] for row in self.cursor.fetchall()]

    def search_services(self, pattern: str) -> list[str]:
        # SQL LIKE с wildcards '%pattern%' — ищем вхождение подстроки.
        # Фильтруем на уровне БД, а не тащим все записи в Python.
        self.cursor.execute(
            "SELECT service FROM accounts WHERE service LIKE ? ORDER BY service",
            (f"%{pattern.lower()}%",)
        )
        return [row[0] for row in self.cursor.fetchall()]


    def has_account(self, service) -> bool:
        self.cursor.execute("SELECT 1 FROM accounts WHERE service = ?", (service,))
        return self.cursor.fetchone() is not None

    def delete_account(self, service):
        self.cursor.execute("DELETE FROM accounts WHERE service = ?", (service,))
        self.conn.commit()
        return self.cursor.rowcount > 0 

class Security:
    def __init__(self) -> None:
        self.cipher: Optional[Fernet] = None

    def generate_salt(self):
        return secrets.token_bytes(16)

    def encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())

    def decrypt(self, encrypted_data: bytes) -> str:
        return self.cipher.decrypt(encrypted_data).decode()

    def _get_combined_payload(self, password, salt):
        if not config.PEPPER:
            raise ValueError("SECRET_PEPPER не найден! Проверь файл .env")
        return password.encode() + salt + config.PEPPER.encode()

    def hash_password(self, password, salt):
        payload = self._get_combined_payload(password, salt)
        return hashlib.sha512(payload).digest()

    def setup_cipher(self, password, salt):
        payload = self._get_combined_payload(password, salt)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=salt,
            iterations=config.KDF_ITERATIONS,
        )
        key = base64.urlsafe_b64encode(kdf.derive(payload))
        self.cipher = Fernet(key)

class VaultManager:
    def __init__(self, master_password):
        self.db = Database()
        self.security = Security()
        self.authenticate(master_password)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
        return False

    def authenticate(self, master_password):
        auth_data = self.db.get_auth()
        if auth_data is None:
            print("[СИСТЕМА] Создание нового защищенного хранилища...")
            salt = self.security.generate_salt()
            pass_hash = self.security.hash_password(master_password, salt)
            self.db.set_auth(salt, pass_hash)
            self.security.setup_cipher(master_password, salt)
        else:
            salt, stored_hash = auth_data
            current_hash = self.security.hash_password(master_password, salt)
            if not hmac.compare_digest(current_hash, stored_hash):
                time.sleep(2)
                raise ValueError("Неверный мастер-пароль!")
            self.security.setup_cipher(master_password, salt)

    def add_entry(self, service, login, password):
        encrypted_pass = self.security.encrypt(password)
        self.db.add_account(service.lower(), login, encrypted_pass)

    def load_entry(self, service) -> Optional[AccountEntry]:
        record = self.db.get_account(service.lower())
        if record:
            login, enc_pass = record
            decrypted_pass = self.security.decrypt(enc_pass)
            # Возвращаем объект датакласса
            return AccountEntry(service=service.lower(), login=login, password=decrypted_pass)
        return None 

    def get_services_list(self):
        return self.db.get_all_services()

    def search_entries(self, pattern: str) -> list[str]:
        # Делегируем поиск напрямую в Database — VaultManager не знает SQL,
        # он просто передаёт запрос ниже по слоям.
        return self.db.search_services(pattern)

    def has_entry(self, service) -> bool:
        return self.db.has_account(service.lower())

    def delete_pass(self, service):
        return self.db.delete_account(service.lower())