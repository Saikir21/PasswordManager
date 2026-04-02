import secrets
import string
import pyperclip
import threading
from core import VaultManager
import config
from utils import generate_password, evaluate_strength

def clear_clipboard():
    pyperclip.copy("")
    print('\n[СИСТЕМА] Буфер обмена очищен для безопасности.')

def main():
    print("=== ВХОД В СИСТЕМУ ===")
    master_pass = input("Введите/Создайте ваш мастер-пароль: ")

    try:
        vault = VaultManager(master_pass)
        if vault.is_new_vault: # <-- Проверяем флаг здесь
            print("\n[СИСТЕМА] Создание нового защищенного хранилища...")
    except ValueError as e:
        print(f"❌ Ошибка: {e}")
        return

    with vault:
        print("✅ Доступ разрешен!\n")

        while True:
            print("\n=== МЕНЕДЖЕР ПАРОЛЕЙ (SQL) ===")
            print("1. Найти пароль")
            print("2. Добавить или изменить пароль")
            print("3. Показать все сервисы")
            print("4. Сгенерировать надежный пароль")
            print("5. Удалить пароль")
            print("6. Экспорт списка сервисов") 
            print("7. Выход")

            choice = input("\nВыберите действие (1-7): ")

            match choice:
                case '1':
                    service = input("Введите название сервиса: ").lower()
                    entry = vault.load_entry(service)
                    if entry:
                        # Точное совпадение — берём сразу, без лишних вопросов.
                        pyperclip.copy(entry.password)
                        print(f"✅ [{entry.service.upper()}] Данные найдены! Логин: {entry.login}")
                        print(f"👉 Пароль скопирован в буфер обмена на {config.CLIPBOARD_TIMEOUT} секунд.")
                        timer = threading.Timer(config.CLIPBOARD_TIMEOUT, clear_clipboard)
                        timer.daemon = True 
                        timer.start()
                    else:
                        # Fallback: ищем похожие сервисы по подстроке.
                        matches = vault.search_entries(service)
                        if matches:
                            print(f"❌ Точного совпадения нет. Похожие сервисы:")
                            for i, s in enumerate(matches, 1):
                                print(f"   {i}. {s}")
                            pick = input("Введите номер нужного (или Enter для отмены): ").strip()
                            if pick.isdigit() and 1 <= int(pick) <= len(matches):
                                chosen = matches[int(pick) - 1]
                                entry = vault.load_entry(chosen)
                                pyperclip.copy(entry.password)
                                print(f"✅ [{entry.service.upper()}] Данные найдены! Логин: {entry.login}")
                                print(f"👉 Пароль скопирован в буфер обмена на {config.CLIPBOARD_TIMEOUT} секунд.")
                                timer = threading.Timer(config.CLIPBOARD_TIMEOUT, clear_clipboard)
                                timer.daemon = True 
                                timer.start()
                            else:
                                print("Отменено.")
                        else:
                            print("❌ Такого сервиса нет в базе даже приблизительно.")
                
                case '2':
                    service = input("Название сервиса: ").lower()
                    if vault.has_entry(service):
                        confirm = input(f"⚠️ Сервис '{service}' уже есть. Перезаписать? (y/n): ").lower()
                        if confirm != 'y':
                            print("Отменено.")
                            continue

                    login = input("Введите логин: ")
                    use_gen = input("Сгенерировать пароль автоматически? (y/n): ").lower()

                    if use_gen == 'y':
                        password = generate_password()
                        pyperclip.copy(password)
                        print(f"✅ Сгенерирован пароль: {password}")
                        print(f"👉 Он скопирован в буфер обмена на {config.CLIPBOARD_TIMEOUT} секунд!")
                        timer = threading.Timer(config.CLIPBOARD_TIMEOUT, clear_clipboard)
                        timer.daemon = True 
                        timer.start()
                    else:
                        while True:
                            password = input("Введите пароль вручную: ")
                            is_ok, message = evaluate_strength(password)
                            if is_ok:
                                print(message)
                                break 
                            else:
                                print(message)
                                print("Попробуйте еще раз.")

                    vault.add_entry(service, login, password)
                    print(f"✅ Данные для {service} успешно сохранены!")
                    
                case '3':
                    services = vault.get_services_list()  # уже отсортированы в SQL (ORDER BY)
                    if services:
                        # Выводим пронумерованным столбцом — читаемо даже при 50+ паролях.
                        # ljust выравнивает строки по ширине самого длинного сервиса.
                        col_width = max(len(s) for s in services) + 2
                        print(f"\n📋 Сервисов в базе: {len(services)}")
                        print("-" * (col_width + 6))
                        for i, s in enumerate(services, 1):
                            print(f"  {i:>2}. {s}")
                        print("-" * (col_width + 6))
                    else:
                        print("База пуста.")

                case '4':
                    length_input = input(f"Введите длину (по умолчанию {config.DEFAULT_PASS_LENGTH}): ")
                    length = int(length_input) if length_input.isdigit() else config.DEFAULT_PASS_LENGTH
                    new_pass = generate_password(length)
                    
                    pyperclip.copy(new_pass)
                    print(f"✅ Ваш новый пароль: {new_pass}")
                    print(f"👉 Пароль скопирован в буфер обмена. Очистка через {config.CLIPBOARD_TIMEOUT} секунд.")
                    timer = threading.Timer(config.CLIPBOARD_TIMEOUT, clear_clipboard)
                    timer.daemon = True 
                    timer.start()

                case '5':
                    service = input('Напишите сервис для удаления: ')
                    if vault.delete_pass(service):
                        print(f'✅ Сервис {service} удалён.')
                    else:
                        print('❌ Такого сервиса нет.')

                case '6':
                    success, message = vault.export_services_to_file()
                    if success:
                        print(f"✅ {message}")
                    else:
                        print(f"❌ {message}")
                case "7":
                    print ("До свидания!")
                    break
                    
                case _:
                    print("❌ Ошибка: выберите пункт от 1 до 7.")

                
                

if __name__ == "__main__":
    main()