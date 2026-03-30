import secrets
import string
import pyperclip
import threading
from core import VaultManager
import config

def is_password_strong(password):
    if len(password) < 8:
        return False, "❌ Ошибка: В пароле должно быть не меньше 8 символов."
    has_upper = any(char.isupper() for char in password)
    has_digit = any(char.isdigit() for char in password)
    if not has_upper:
        return False, "❌ Ошибка: Добавьте хотя бы одну заглавную букву."
    if not has_digit:
        return False, "❌ Ошибка: Добавьте хотя бы одну цифру."
    return True, "✅ Пароль прошел проверку!"

def generate_password(length=config.DEFAULT_PASS_LENGTH):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def clear_clipboard():
    pyperclip.copy("")
    print('\n[СИСТЕМА] Буфер обмена очищен для безопасности.')

def main():
    print("=== ВХОД В СИСТЕМУ ===")
    master_pass = input("Введите/Создайте ваш мастер-пароль: ")

    try:
        vault = VaultManager(master_pass)
        print("✅ Доступ разрешен!\n")
    except ValueError as e:
        print(f"❌ Ошибка: {e}")
        return

    while True:
        print("\n=== МЕНЕДЖЕР ПАРОЛЕЙ (SQL) ===")
        print("1. Найти пароль")
        print("2. Добавить или изменить пароль")
        print("3. Показать все сервисы")
        print("4. Сгенерировать надежный пароль")
        print("5. Удалить пароль")
        print("6. Выход")
        
        choice = input("\nВыберите действие (1-6): ")

        match choice:
            case '1':
                service = input("Введите название сервиса: ").lower()
                entry = vault.load_entry(service)
                if entry:
                    # Использование атрибутов датакласса вместо словаря
                    pyperclip.copy(entry.password)
                    print(f"✅ [{entry.service.upper()}] Данные найдены! Логин: {entry.login}")
                    print(f"👉 Пароль скопирован в буфер обмена на {config.CLIPBOARD_TIMEOUT} секунд.")
                    threading.Timer(config.CLIPBOARD_TIMEOUT, clear_clipboard).start()
                else:
                    print("❌ Такого сервиса нет в базе.")
            
            case '2':
                service = input("Название сервиса: ").lower()
                login = input("Введите логин: ")
                use_gen = input("Сгенерировать пароль автоматически? (y/n): ").lower()

                if use_gen == 'y':
                    password = generate_password()
                    pyperclip.copy(password)
                    print(f"✅ Сгенерирован пароль: {password}")
                    print(f"👉 Он скопирован в буфер обмена на {config.CLIPBOARD_TIMEOUT} секунд!")
                    threading.Timer(config.CLIPBOARD_TIMEOUT, clear_clipboard).start()
                else:
                    while True:
                        password = input("Введите пароль вручную: ")
                        is_ok, message = is_password_strong(password)
                        if is_ok:
                            print(message)
                            break 
                        else:
                            print(message)
                            print("Попробуйте еще раз.")

                vault.add_entry(service, login, password)
                print(f"✅ Данные для {service} успешно сохранены!")
                
            case '3':
                services = vault.get_services_list()
                if services:
                    print("Ваши сервисы:", ", ".join(services))
                else:
                    print("База пуста.")

            case '4':
                length_input = input(f"Введите длину (по умолчанию {config.DEFAULT_PASS_LENGTH}): ")
                length = int(length_input) if length_input.isdigit() else config.DEFAULT_PASS_LENGTH
                new_pass = generate_password(length)
                
                pyperclip.copy(new_pass)
                print(f"✅ Ваш новый пароль: {new_pass}")
                print(f"👉 Пароль скопирован в буфер обмена. Очистка через {config.CLIPBOARD_TIMEOUT} секунд.")
                threading.Timer(config.CLIPBOARD_TIMEOUT, clear_clipboard).start()

            case '5':
                service = input('Напишите сервис для удаления: ')
                if vault.delete_pass(service):
                    print(f'✅ Сервис {service} удалён.')
                else:
                    print('❌ Такого сервиса нет.')

            case '6':
                print("Сейф закрыт. До свидания!")
                break
                
            case _:
                print("❌ Ошибка: выберите пункт от 1 до 6.")

if __name__ == "__main__":
    main()