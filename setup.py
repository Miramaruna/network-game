import os
import subprocess
import sys
import platform

# Настройки
VENV_PATH = ".venv"
REQUIRED_PACKAGES = ["pygame", "requests"]

def get_venv_python():
    """Определяет путь к python в зависимости от операционной системы"""
    if platform.system() == "Windows":
        return os.path.join(VENV_PATH, "Scripts", "python.exe")
    else:
        # Для macOS и Linux
        return os.path.join(VENV_PATH, "bin", "python")

def setup_environment():
    # 1. Создаем виртуальное окружение
    if not os.path.exists(VENV_PATH):
        print(f"--- Создание виртуального окружения ({platform.system()})...")
        subprocess.check_call([sys.executable, "-m", "venv", VENV_PATH])
    
    venv_python = get_venv_python()

    # 2. Обновляем pip
    print("--- Обновление pip...")
    subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])

    # 3. Устанавливаем библиотеки
    print(f"--- Установка библиотек: {', '.join(REQUIRED_PACKAGES)}...")
    subprocess.check_call([venv_python, "-m", "pip", "install"] + REQUIRED_PACKAGES)

def run_game():
    venv_python = get_venv_python()
    # Путь к главной функции твоей игры
    game_script = os.path.join("game", "main.py") 
    
    if os.path.exists(game_script):
        print(f"--- Запуск игры: {game_script}")
        # Запускаем игру через python из виртуальной среды
        subprocess.run([venv_python, game_script])
    else:
        print(f"Ошибка: Файл {game_script} не найден!")

if __name__ == "__main__":
    try:
        setup_environment()
        print("\n[Окружение готово]\n")
        run_game()
    except Exception as e:
        print(f"Произошла ошибка: {e}")