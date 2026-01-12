import os
import subprocess
import sys
import platform
import shutil
import zipfile
import io
import argparse

# --- Настройки ---
VENV_PATH = "venv"
REQUIRED_PACKAGES = ["pygame", "requests"]
REPO_OWNER = "Miramaruna"
REPO_NAME = "network-game"
FOLDER_TO_EXTRACT = "game"
TEMP_ZIP_DIR = "temp_extacting"

def print_colored(message, color="white"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{message}{colors['reset']}")

def check_admin_windows():
    if platform.system() == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    return True

def get_venv_python_path():
    if platform.system() == "Windows":
        return os.path.join(VENV_PATH, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_PATH, "bin", "python")

def create_virtual_environment(force_reinstall=False):
    print_colored("\n--- Создание/проверка виртуального окружения ---", "blue")
    venv_python = get_venv_python_path()

    if force_reinstall and os.path.exists(VENV_PATH):
        print_colored("Удаление существующего виртуального окружения...", "yellow")
        try:
            shutil.rmtree(VENV_PATH)
            print_colored("Существующее виртуальное окружение удалено.", "green")
        except Exception as e:
            print_colored(f"Ошибка при удалении виртуального окружения: {e}", "red")
            print_colored("Пожалуйста, удалите папку .venv вручную и попробуйте снова.", "yellow")
            sys.exit(1)

    if not os.path.exists(VENV_PATH):
        print_colored(f"Создание виртуального окружения в {VENV_PATH}...", "cyan")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", VENV_PATH])
            print_colored("Виртуальное окружение успешно создано.", "green")
        except Exception as e:
            print_colored(f"Ошибка при создании виртуального окружения: {e}", "red")
            print_colored("Убедитесь, что Python установлен корректно и добавлен в PATH.", "yellow")
            sys.exit(1)
    else:
        print_colored("Виртуальное окружение уже существует.", "green")

    # Проверка, что Python из venv существует
    if not os.path.exists(venv_python):
        print_colored(f"Ошибка: Исполняемый файл Python не найден в {venv_python}", "red")
        print_colored("Возможно, виртуальное окружение повреждено. Попробуйте удалить папку .venv и запустить скрипт снова.", "yellow")
        sys.exit(1)
    return venv_python

def install_dependencies(venv_python):
    print_colored("\n--- Установка/обновление зависимостей ---", "blue")
    try:
        print_colored("Обновление pip...", "cyan")
        subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
        print_colored("pip обновлен.", "green")

        print_colored(f"Установка библиотек: {', '.join(REQUIRED_PACKAGES)}...", "cyan")
        subprocess.check_call([venv_python, "-m", "pip", "install"] + REQUIRED_PACKAGES)
        print_colored("Зависимости успешно установлены.", "green")
    except subprocess.CalledProcessError as e:
        print_colored(f"Ошибка при установке зависимостей: {e}", "red")
        print_colored(f"Команда: {' '.join(e.cmd)} вернула код ошибки {e.returncode}", "red")
        print_colored("Убедитесь в наличии стабильного интернет-соединения.", "yellow")
        sys.exit(1)
    except FileNotFoundError:
        print_colored(f"Ошибка: Исполняемый файл Python не найден по пути {venv_python}", "red")
        print_colored("Убедитесь, что виртуальное окружение создано корректно и Python.exe существует.", "yellow")
        sys.exit(1)
    except Exception as e:
        print_colored(f"Произошла непредвиденная ошибка при установке зависимостей: {e}", "red")
        sys.exit(1)

def update_game_files():
    import requests # Moved import here
    print_colored("\n--- Загрузка и обновление игровых файлов ---", "blue")
    url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/main.zip"
    
    try:
        print_colored(f"Скачивание файлов игры с {url}...", "cyan")
        r = requests.get(url, stream=True)
        r.raise_for_status() # Вызовет исключение для ошибок HTTP
        
        with zipfile.ZipFile(io.BytesIO(r.content)) as zip_ref:
            top_folder = zip_ref.namelist()[0].split('/')[0]
            target_path_in_zip = f"{top_folder}/{FOLDER_TO_EXTRACT}/"
            
            print_colored(f"Извлечение папки '{FOLDER_TO_EXTRACT}'...", "cyan")
            
            if os.path.exists(FOLDER_TO_EXTRACT):
                print_colored(f"Удаление старой версии игры в {FOLDER_TO_EXTRACT}...", "yellow")
                shutil.rmtree(FOLDER_TO_EXTRACT)
            
            os.makedirs(TEMP_ZIP_DIR, exist_ok=True) # Создаем временную папку
            for file in zip_ref.namelist():
                if file.startswith(target_path_in_zip):
                    zip_ref.extract(file, TEMP_ZIP_DIR)
            
            source_path = os.path.join(TEMP_ZIP_DIR, target_path_in_zip)
            if os.path.exists(source_path):
                shutil.move(source_path, FOLDER_TO_EXTRACT)
                print_colored("Игровые файлы успешно обновлены.", "green")
            else:
                print_colored(f"Ошибка: Папка {FOLDER_TO_EXTRACT} не найдена в архиве.", "red")
                sys.exit(1)

        # Чистим временные файлы
        if os.path.exists(TEMP_ZIP_DIR):
            shutil.rmtree(TEMP_ZIP_DIR)

    except requests.exceptions.RequestException as e:
        print_colored(f"Ошибка сети при скачивании игры: {e}", "red")
        print_colored("Проверьте ваше интернет-соединение.", "yellow")
        sys.exit(1)
    except zipfile.BadZipFile:
        print_colored("Ошибка: Скачанный файл не является корректным ZIP-архивом.", "red")
        sys.exit(1)
    except FileNotFoundError as e:
        print_colored(f"Ошибка файловой системы: {e}", "red")
        print_colored("Возможно, проблема с путями или правами доступа.", "yellow")
        sys.exit(1)
    except PermissionError as e:
        print_colored(f"Ошибка доступа: {e}", "red")
        print_colored("Попробуйте запустить скрипт с правами администратора.", "yellow")
        sys.exit(1)
    except Exception as e:
        print_colored(f"Произошла непредвиденная ошибка при обновлении игры: {e}", "red")
        sys.exit(1)

def run_game(venv_python):
    print_colored("\n--- Запуск игры ---", "blue")
    game_script = os.path.join(FOLDER_TO_EXTRACT, "main.py")
    
    if not os.path.exists(game_script):
        print_colored(f"Ошибка: Основной файл игры '{game_script}' не найден.", "red")
        print_colored("Убедитесь, что игра была успешно загружена и распакована.", "yellow")
        sys.exit(1)
    
    try:
        print_colored(f"Запуск игры '{game_script}'...", "green")
        subprocess.run([venv_python, game_script])
    except FileNotFoundError:
        print_colored(f"Ошибка: Python из виртуального окружения не найден по пути {venv_python}", "red")
        print_colored("Убедитесь, что виртуальное окружение создано корректно.", "yellow")
        sys.exit(1)
    except Exception as e:
        print_colored(f"Произошла ошибка при запуске игры: {e}", "red")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Установщик и запускатор сетевой игры.")
    parser.add_argument("--force-reinstall", action="store_true", help="Принудительно пересоздать виртуальное окружение и переустановить зависимости.")
    args = parser.parse_args()

    print_colored("=== Запуск установщика игры ===", "magenta")
    print_colored(f"Операционная система: {platform.system()} {platform.release()}", "white")
    print_colored(f"Версия Python: {sys.version.split(' ')[0]}", "white")

    if platform.system() == "Windows" and not check_admin_windows():
        print_colored("\nВнимание: На Windows для некоторых операций могут потребоваться права администратора.", "yellow")
        print_colored("Рекомендуется запустить скрипт от имени администратора.", "yellow")
        # sys.exit(1) # Можно сделать выход, но пока просто предупреждение

    venv_python = create_virtual_environment(args.force_reinstall)
    install_dependencies(venv_python)

    if sys.executable != venv_python and not os.environ.get("RUNNING_IN_VENV"):
        print_colored("\n--- Перезапуск скрипта в виртуальном окружении ---", "blue")
        os.environ["RUNNING_IN_VENV"] = "1"
        try:
            subprocess.check_call([venv_python, sys.argv[0]] + sys.argv[1:])
            print_colored("Скрипт успешно перезапущен в виртуальном окружении.", "green")
            sys.exit(0) # Exit the current process
        except Exception as e:
            print_colored(f"Ошибка при перезапуске скрипта в виртуальном окружении: {e}", "red")
            sys.exit(1)
    
    # These functions will now run in the virtual environment
    update_game_files()
    run_game(venv_python)
    
    print_colored("\n=== Установка завершена успешно! ===\n", "green")

if __name__ == "__main__":
    main()
