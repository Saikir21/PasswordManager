import secrets 
import string 
import config
def generate_password(length=config.DEFAULT_PASS_LENGTH):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
def evaluate_strength(password: str) -> tuple[bool, str]:
    """
    Оценивает надежность пароля и возвращает статус + визуальную шкалу.
    """
    if len(password) < 8:
        return False, "❌ Ошибка: Минимум 8 символов. [░░░░░]"
    
    score = 0
    if any(c.islower() for c in password): score += 1
    if any(c.isupper() for c in password): score += 1
    if any(c.isdigit() for c in password): score += 1
    if any(c in "!@#$%^&*"    if len(password) >= 12: score += 1

    # Рисуем шкалу прогресса
    bars = "█" * score + "░" * (5 - score)
    
    if score < 3:
        return False, f"⚠️ Слабый пароль [{bars}] (Добавьте спецсимволы или цифры)"
    elif score == 5:
        return True, f"✅ Супер-надежно [{bars}]"
    else:
        return True, f"✅ Нормальный пароль [{bars}]"