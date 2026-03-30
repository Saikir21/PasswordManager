from dataclasses import dataclass

@dataclass
class AccountEntry:
    service: str
    login: str
    password: str  # Здесь будет уже расшифрованный пароль для удобства UI