import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv("SECRET_PEPPER.env")

# Пути
BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = str(BASE_DIR / "passwords.db")

# Криптография
PEPPER = os.getenv("SECRET_PEPPER")
KDF_ITERATIONS = 600000

# Настройки интерфейса
CLIPBOARD_TIMEOUT = 20.0
DEFAULT_PASS_LENGTH = 15