import pygame
import random
from network import Network
from player import Player

pygame.init()

# Размер ОКНА (то, что мы видим)
WIDTH = 900
HEIGHT = 700

# Размер ВСЕГО МИРА (карты)
MAP_WIDTH = 2000
MAP_HEIGHT = 2000

win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Сетевой Шутер: Большая Карта")

# --- ИЗМЕНЕНИЕ ДЛЯ ПОДДЕРЖКИ РУССКОГО ЯЗЫКА ---
# Используем список шрифтов, где "arial" или "dejavusans" 
# гарантированно поддерживают кириллицу на большинстве систем.
FONT_CHOICES = ["arial", "dejavusans", "verdana", "comicsansms"] 

font_main = pygame.font.SysFont(FONT_CHOICES, 24)
font_small = pygame.font.SysFont(FONT_CHOICES, 18)
font_title = pygame.font.SysFont(FONT_CHOICES, 70)

COLOR_BG = (30, 35, 45)
COLOR_ACCENT = (52, 152, 219)

def draw_text(text, font, color, x, y, center=False):
    img = font.render(text, True, color)
    if center:
        rect = img.get_rect(center=(x, y))
        win.blit(img, rect)
    else:
        win.blit(img, (x, y))

# Функция отрисовки фона (сетки) с учетом камеры
def draw_grid(win, scroll):
    # Рисуем темно-серый фон для всей карты
    win.fill((40, 40, 40))
    
    # Рисуем границы карты (красная рамка)
    border_rect = pygame.Rect(-scroll[0], -scroll[1], MAP_WIDTH, MAP_HEIGHT)
    pygame.draw.rect(win, (255, 50, 50), border_rect, 5)
    
    # Сетка
    grid_size = 100
    # Вычисляем смещение сетки, чтобы она "ездила"
    start_x = -scroll[0] % grid_size
    start_y = -scroll[1] % grid_size
    
    for i in range(start_x, WIDTH, grid_size):
        pygame.draw.line(win, (60, 60, 60), (i, 0), (i, HEIGHT))
    for i in range(start_y, HEIGHT, grid_size):
        pygame.draw.line(win, (60, 60, 60), (0, i), (WIDTH, i))

def main_menu():
    user_ip = ""
    clock = pygame.time.Clock()
    active = True

    while active:
        clock.tick(60)
        win.fill(COLOR_BG)
        draw_text("BIG MAP SHOOTER", font_title, COLOR_ACCENT, WIDTH//2, 150, center=True)
        draw_text("Введите IP сервера:", font_main, (180, 180, 180), WIDTH//2, 280, center=True)
        
        input_box = pygame.Rect(WIDTH//2 - 200, 320, 400, 50)
        pygame.draw.rect(win, (255, 255, 255), input_box, border_radius=5)
        pygame.draw.rect(win, COLOR_ACCENT, input_box, 3, border_radius=5)
        
        text_surf = font_main.render(user_ip, True, (0, 0, 0))
        win.blit(text_surf, (input_box.x + 10, input_box.y + 10))
        
        draw_text("ENTER - Старт | ESC - Выход", font_small, (100, 100, 100), WIDTH//2, 450, center=True)
        if user_ip == "":
            draw_text("(Пусто = локальная игра)", font_small, (80, 80, 80), WIDTH//2, 380, center=True)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return "QUIT"
                if event.key == pygame.K_RETURN: return user_ip if user_ip else "127.0.0.1"
                if event.key == pygame.K_BACKSPACE: user_ip = user_ip[:-1]
                else: 
                    if len(user_ip) < 15: user_ip += event.unicode

def game_loop(server_ip):
    n = Network(server_ip)
    p = n.getP()

    if not p:
        return # Ошибка подключения

    clock = pygame.time.Clock()
    run = True
    
    chat_messages = []
    typing_mode = False
    current_message = ""

    while run:
        clock.tick(60)
        msg_to_send = None 
        
        # --- КАМЕРА ---
        # Мы хотим, чтобы игрок был в центре экрана
        # scroll_x = (Координата игрока) - (Половина ширины экрана)
        scroll_x = p.x - WIDTH // 2 + p.width // 2
        scroll_y = p.y - HEIGHT // 2 + p.height // 2

        # Ограничиваем камеру, чтобы не видеть пустоту за пределами карты (опционально)
        # Если хотите видеть черную пустоту, закомментируйте следующие 4 строки
        # scroll_x = max(0, min(scroll_x, MAP_WIDTH - WIDTH))
        # scroll_y = max(0, min(scroll_y, MAP_HEIGHT - HEIGHT))
        
        scroll = (scroll_x, scroll_y)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                return "QUIT"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if typing_mode: typing_mode = False
                    else: 
                        n.disconnect()
                        run = False

                elif event.key == pygame.K_RETURN:
                    if typing_mode:
                        if len(current_message) > 0:
                            msg_to_send = current_message
                            current_message = ""
                        typing_mode = False
                    else:
                        typing_mode = True
                        current_message = ""
                
                elif typing_mode:
                    if event.key == pygame.K_BACKSPACE: current_message = current_message[:-1]
                    else: 
                        if len(current_message) < 40: current_message += event.unicode
            
            if event.type == pygame.MOUSEBUTTONDOWN and not typing_mode:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    # Передаем scroll в функцию стрельбы
                    p.shoot(mx, my, scroll)

        if not typing_mode:
            # Передаем размеры карты для ограничения движения
            p.move(MAP_WIDTH, MAP_HEIGHT)

        # --- ОБРАБОТКА ПОПАДАНИЙ ---
        # Мы проверяем коллизии локально. Если нас убили, МЫ сообщаем об этом серверу.
        killer_id = None # Кто нас убил?
        
        my_rect = pygame.Rect(p.x, p.y, p.width, p.height)
        for p_id, enemy in all_players.items() if 'all_players' in locals() else {}.items():
            if p_id != p.id:
                for bullet in enemy.bullets:
                    # bullet: [x, y, vx, vy]
                    b_rect = pygame.Rect(bullet[0]-6, bullet[1]-6, 12, 12)
                    if my_rect.colliderect(b_rect):
                        p.hp -= 2
                        bullet[0] = -5000 # Убираем пулю далеко
                        bullet[1] = -5000
                        killer_id = p_id # Запоминаем, чья это была пуля

        # Если умерли
        if p.hp <= 0:
            if killer_id is not None:
                # Отправляем специальное сообщение об убийстве
                msg_to_send = f"[KILL] Игрок {killer_id} уничтожил Игрока {p.id}!"
            else:
                msg_to_send = f"[KILL] Игрок {p.id} погиб по неизвестной причине."
            
            # Респаун
            p.hp = 100
            p.x = random.randint(100, MAP_WIDTH - 100)
            p.y = random.randint(100, MAP_HEIGHT - 100)


        # --- ОТПРАВКА ДАННЫХ ---
        packet = {"player": p, "msg": msg_to_send}
        server_data = n.send(packet)
        
        if not server_data:
            run = False
            break
            
        all_players = server_data.get("players", {})
        chat_messages = server_data.get("chat", [])

        # --- ОТРИСОВКА ---
        draw_grid(win, scroll) # Рисуем фон со смещением

        for p_id, player in all_players.items():
            player.draw(win, scroll) # Рисуем игроков со смещением
            
            # Никнейм над головой (с учетом камеры)
            screen_px = player.x - scroll[0]
            screen_py = player.y - (scroll[1] + 20)
            draw_text(f"ID: {p_id}", font_small, (200, 200, 200), screen_px, screen_py - 25)

        # --- ИНТЕРФЕЙС (НЕ ЗАВИСИТ ОТ КАМЕРЫ) ---
        # Чат
        # chat_bg = pygame.Surface((400, 250))
        # chat_bg.set_alpha(100)
        # chat_bg.fill((0,0,0))
        # win.blit(chat_bg, (10, HEIGHT - 260))
        
        # for i, msg in enumerate(chat_messages[-10:]):
        #     color = (255, 255, 255)
        #     if "[💀]" in msg: color = (255, 100, 100) # Красный цвет для смертей
        #     if "[SERVER]" in msg: color = (100, 255, 100) # Зеленый для сервера
        #     draw_text(msg, font_small, color, 20, HEIGHT - 250 + i * 20)
        
        chat_bg_height = 250
        chat_bg = pygame.Surface((360, chat_bg_height))
        chat_bg.set_alpha(150) # Прозрачность
        chat_bg.fill((0, 0, 0))
        win.blit(chat_bg, (10, HEIGHT - chat_bg_height - 10))
        
        # Отрисовка сообщений
        start_y = HEIGHT - chat_bg_height
        for i, msg in enumerate(chat_messages[-8:]): # Показываем последние 8
            color = (255, 255, 255)
            if "[💀]" in msg: color = (255, 100, 100) # Красный цвет для смертей
            if "[SERVER]" in msg: color = (100, 255, 100) # Зеленый для сервера
            draw_text(msg, font_small, color, 20, HEIGHT - 250 + i * 20)

        # Поле ввода
        # if typing_mode:
        #     pygame.draw.rect(win, (255, 255, 255), (10, HEIGHT - 40, 400, 30))
        #     draw_text(current_message, font_small, (0, 0, 0), 15, HEIGHT - 35)
        # else:
        #     draw_text("ENTER для чата", font_small, (150, 150, 150), 10, HEIGHT - 30)
        
        if typing_mode:
            pygame.draw.rect(win, (255, 255, 255), (10, HEIGHT - 40, 350, 30))
            pygame.draw.rect(win, COLOR_ACCENT, (10, HEIGHT - 40, 350, 30), 2)
            draw_text(current_message, font_small, (0, 0, 0), 15, HEIGHT - 35)
            draw_text("Typing...", font_small, COLOR_ACCENT, 370, HEIGHT - 35)
        else:
            draw_text("Нажми ENTER для чата", font_small, (100, 100, 100), 10, HEIGHT - 30)

        # Мини-карта / Координаты
        draw_text(f"Pos: {p.x}, {p.y}", font_small, (255, 255, 0), WIDTH - 150, 10)
        draw_text(f"FPS: {int(clock.get_fps())}", font_main, (255, 0, 0), WIDTH - 120, 40)

        pygame.display.update()

def main_app():
    app_running = True
    while app_running:
        result = main_menu()
        if result == "QUIT": app_running = False
        elif result:
            game_loop(result)
    pygame.quit()

if __name__ == "__main__":
    main_app()