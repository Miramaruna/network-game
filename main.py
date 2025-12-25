import requests
import zipfile
import io
import os
import shutil

# Настройки
REPO_OWNER = "Miramaruna"
REPO_NAME = "network-game"
FOLDER_TO_EXTRACT = "game"
TEMP_ZIP_DIR = "temp_extacting"

def update_game():
    # 1. Получаем ссылку на архив последней версии из ветки main
    url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/main.zip"
    
    print("Скачивание обновления...")
    r = requests.get(url)
    
    if r.status_code == 200:
        # 2. Распаковываем архив в памяти
        with zipfile.ZipFile(io.BytesIO(r.content)) as zip_ref:
            # GitHub добавляет префикс 'название_репо-main/' к папкам в архиве
            top_folder = zip_ref.namelist()[0].split('/')[0]
            target_path_in_zip = f"{top_folder}/{FOLDER_TO_EXTRACT}/"
            
            # 3. Извлекаем только нужную папку
            for file in zip_ref.namelist():
                if file.startswith(target_path_in_zip):
                    zip_ref.extract(file, TEMP_ZIP_DIR)
            
            # 4. Переносим папку game в текущую директорию
            source = os.path.join(TEMP_ZIP_DIR, target_path_in_zip)
            if os.path.exists(FOLDER_TO_EXTRACT):
                shutil.rmtree(FOLDER_TO_EXTRACT) # Удаляем старую версию
            
            shutil.move(source, FOLDER_TO_EXTRACT)
            
            # Чистим временные файлы
            shutil.rmtree(TEMP_ZIP_DIR)
            print("Обновление завершено успешно!")
    else:
        print("Ошибка при скачивании:", r.status_code)

if __name__ == "__main__":
    update_game()