import pygame
import random
import math
from network import Network
from player import Player # Убедитесь, что Player теперь импортирует random

pygame.init()

# --- НАСТРОЙКИ ЭКРАНА И КАРТЫ ---
WIDTH = 900
HEIGHT = 700
MAP_WIDTH = 2000
MAP_HEIGHT = 2000

win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Shooter: Redux")

# --- ЦВЕТОВАЯ ПАЛИТРА (NEON STYLE) ---
C_BG = (10, 10, 20)           # Глубокий темный фон
C_GRID_DIM = (30, 30, 50)     # Тусклая сетка
C_GRID_BRIGHT = (60, 60, 100) # Яркие линии сетки
C_ACCENT = (0, 255, 255)      # Неоновый циан
C_DANGER = (255, 50, 50)      # Неоновый красный
C_TEXT_MAIN = (240, 240, 240)
C_UI_BG = (0, 0, 0, 150)      # Полупрозрачный фон для интерфейса

# --- ШРИФТЫ ---
FONT_CHOICES = ["arial", "dejavusans", "verdana", "comicsansms"] 
font_ui = pygame.font.SysFont(FONT_CHOICES, 16)
font_hud = pygame.font.SysFont(FONT_CHOICES, 20, bold=True)
font_title = pygame.font.SysFont(FONT_CHOICES, 70, bold=True)

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ЭФФЕКТОВ ---
shoot_flash_timer = 0
flash_pos = (0, 0)

# --- ЭФФЕКТ ВИНЬЕТКИ (ЗАТЕМНЕНИЕ УГЛОВ) ---
# Создаем один раз, чтобы не нагружать процессор каждый кадр
vignette_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for x in range(WIDTH):
    for y in range(HEIGHT):
        dx = x - WIDTH // 2
        dy = y - HEIGHT // 2
        dist = math.sqrt(dx**2 + dy**2)
        # Формула затемнения краев
        alpha = min(255, int(dist / (WIDTH * 0.65) * 255))
        if alpha > 40:
            vignette_surf.set_at((x, y), (0, 0, 0, alpha))

# --- КЛАСС ЧАСТИЦ (ДЛЯ МЕНЮ) ---
class Particle:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = random.randint(2, 4)
        self.speed_y = random.uniform(-1.5, -0.5)
        self.alpha = random.randint(50, 150)
        self.color = C_ACCENT

    def move(self):
        self.y += self.speed_y
        self.alpha -= 0.5
        if self.y < 0 or self.alpha <= 0:
            self.y = HEIGHT
            self.x = random.randint(0, WIDTH)
            self.alpha = 150

    def draw(self, surf):
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        s.fill((*self.color, int(self.alpha)))
        surf.blit(s, (self.x, self.y))

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ОТРИСОВКИ ---

def draw_text_shadow(text, font, color, x, y, center=False):
    """Рисует текст с черной тенью для лучшей читаемости"""
    shadow = font.render(text, True, (0, 0, 0))
    main_txt = font.render(text, True, color)
    
    if center:
        rect = main_txt.get_rect(center=(x, y))
        shadow_rect = shadow.get_rect(center=(x+2, y+2))
        win.blit(shadow, shadow_rect)
        win.blit(main_txt, rect)
    else:
        win.blit(shadow, (x+2, y+2))
        win.blit(main_txt, (x, y))

def draw_modern_grid(win, scroll):
    """Красивая неоновая сетка"""
    win.fill(C_BG) # Очистка фона
    
    # Границы мира
    border_rect = pygame.Rect(-scroll[0], -scroll[1], MAP_WIDTH, MAP_HEIGHT)
    pygame.draw.rect(win, C_DANGER, border_rect, 3)
    
    grid_size = 100
    start_x = -int(scroll[0]) % grid_size
    start_y = -int(scroll[1]) % grid_size
    
    # Вертикальные линии
    for i in range(start_x, WIDTH, grid_size):
        real_world_x = i + scroll[0]
        color = C_GRID_BRIGHT if abs(real_world_x) % (grid_size*5) < grid_size else C_GRID_DIM
        pygame.draw.line(win, color, (i, 0), (i, HEIGHT))
        
    # Горизонтальные линии
    for i in range(start_y, HEIGHT, grid_size):
        real_world_y = i + scroll[1]
        color = C_GRID_BRIGHT if abs(real_world_y) % (grid_size*5) < grid_size else C_GRID_DIM
        pygame.draw.line(win, color, (0, i), (WIDTH, i))

def draw_custom_cursor(mx, my):
    """Рисуем прицел вместо мышки"""
    pygame.draw.circle(win, C_ACCENT, (mx, my), 8, 1)
    pygame.draw.line(win, C_ACCENT, (mx - 12, my), (mx + 12, my), 1)
    pygame.draw.line(win, C_ACCENT, (mx, my - 12), (mx, my + 12), 1)
    # Точка в центре
    pygame.draw.circle(win, (255, 255, 255), (mx, my), 2)

def draw_hud(player, fps):
    """Интерфейс игрока (HP, FPS, Координаты)"""
    # 1. Полоска здоровья
    bar_w, bar_h = 200, 20
    bar_x = WIDTH // 2 - bar_w // 2
    bar_y = HEIGHT - 40
    
    # Подложка
    pygame.draw.rect(win, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
    
    # Жизнь
    hp_pct = max(0, player.hp / 100)
    fill_w = int(bar_w * hp_pct)
    color = C_ACCENT if hp_pct > 0.3 else C_DANGER
    pygame.draw.rect(win, color, (bar_x, bar_y, fill_w, bar_h), border_radius=5)
    
    # Рамка
    pygame.draw.rect(win, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=5)
    
    # Текст HP
    draw_text_shadow(f"HP: {player.hp}%", font_hud, C_TEXT_MAIN, bar_x + bar_w//2, bar_y + 1, center=True)
    
    # 2. FPS и Координаты (в углу)
    info_bg = pygame.Surface((180, 80), pygame.SRCALPHA)
    info_bg.fill((0,0,0, 150)) # Полупрозрачный фон
    win.blit(info_bg, (WIDTH - 190, 10))
    
    draw_text_shadow(f"PLAYER ID: {player.id}", font_ui, C_ACCENT, WIDTH - 180, 15)
    draw_text_shadow(f"FPS: {fps}", font_ui, C_DANGER, WIDTH - 180, 35)
    draw_text_shadow(f"XY: {int(player.x)}, {int(player.y)}", font_ui, C_TEXT_MAIN, WIDTH - 180, 55)


# --- ОСНОВНЫЕ ФУНКЦИИ ---

def main_menu():
    # ... (код меню остается без изменений) ...
    user_ip = ""
    clock = pygame.time.Clock()
    active = True
    
    # Генерируем частицы
    particles = [Particle() for _ in range(35)]
    
    while active:
        clock.tick(60)
        win.fill(C_BG)
        
        # Анимация фона
        for p in particles:
            p.move()
            p.draw(win)

        # Текст
        draw_text_shadow("NEON SHOOTER", font_title, C_ACCENT, WIDTH//2, 150, center=True)
        draw_text_shadow("IP СЕРВЕРА:", font_hud, (180, 180, 180), WIDTH//2, 280, center=True)
        
        # Поле ввода
        input_box = pygame.Rect(WIDTH//2 - 180, 320, 360, 40)
        pygame.draw.rect(win, (20, 20, 30), input_box, border_radius=5)
        pygame.draw.rect(win, C_ACCENT, input_box, 2, border_radius=5)
        
        # Мигающий курсор
        txt_surf = font_hud.render(user_ip + ("|" if (pygame.time.get_ticks()//500)%2==0 else ""), True, C_TEXT_MAIN)
        win.blit(txt_surf, (input_box.x + 10, input_box.y + 10))
        
        draw_text_shadow("ENTER - Играть | ESC - Выход", font_ui, (120, 120, 120), WIDTH//2, 450, center=True)
        if user_ip == "":
             draw_text_shadow("(Пусто = localhost)", font_ui, (80, 80, 80), WIDTH//2, 380, center=True)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return "QUIT"
                if event.key == pygame.K_RETURN: return user_ip if user_ip else "127.0.0.1"
                if event.key == pygame.K_BACKSPACE: user_ip = user_ip[:-1]
                else: 
                    if len(user_ip) < 15: user_ip += event.unicode
# ... (конец кода меню) ...


def game_loop(server_ip):
    global shoot_flash_timer, flash_pos
    
    try:
        n = Network(server_ip)
        p = n.getP()
    except:
        print("Ошибка подключения к серверу")
        return

    if not p:
        return 

    clock = pygame.time.Clock()
    run = True
    
    chat_messages = []
    typing_mode = False
    current_message = ""
    
    # Инициализация плавной камеры (ставим её сразу на игрока)
    scroll_x = p.x - WIDTH // 2 + p.width // 2
    scroll_y = p.y - HEIGHT // 2 + p.height // 2
    
    # Скрываем стандартный курсор
    pygame.mouse.set_visible(False)

    while run:
        clock.tick(60)
        msg_to_send = None 
        
        # --- ПЛАВНАЯ КАМЕРА (LERP) ---
        target_x = p.x - WIDTH // 2 + p.width // 2
        target_y = p.y - HEIGHT // 2 + p.height // 2
        
        # Коэффициент плавности (0.2 = более отзывчиво)
        scroll_x += (target_x - scroll_x) * 0.2 
        scroll_y += (target_y - scroll_y) * 0.2
        
        scroll = (scroll_x, scroll_y)

        # Уменьшаем таймер вспышки
        if shoot_flash_timer > 0:
            shoot_flash_timer -= 1

        # События
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.mouse.set_visible(True)
                return "QUIT"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if typing_mode: typing_mode = False
                    else: 
                        n.disconnect()
                        run = False
                        pygame.mouse.set_visible(True)

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
                    p.shoot(mx, my, scroll)
                    
                    # --- ГЕЙМПЛЕЙ/АНИМАЦИЯ: Вспышка выстрела ---
                    shoot_flash_timer = 5 # Длительность вспышки (в кадрах)
                    flash_pos = (mx, my)

        if not typing_mode:
            p.move(MAP_WIDTH, MAP_HEIGHT)

        # --- ОБРАБОТКА ПОПАДАНИЙ (ВАША ЛОГИКА) ---
        # ... (логика без изменений) ...
        killer_id = None 
        my_rect = pygame.Rect(p.x, p.y, p.width, p.height)
        
        # Получаем список врагов (безопасно)
        enemies = all_players.items() if 'all_players' in locals() else {}.items()

        for p_id, enemy in enemies:
            if p_id != p.id:
                # В player.py пули теперь удаляются после попадания.
                # Поэтому итерация по копии списка пуль
                for bullet in list(enemy.bullets):
                    # Используем координаты пули до изменения, чтобы проверить коллизию
                    b_rect = pygame.Rect(bullet[0]-6, bullet[1]-6, 12, 12)
                    if my_rect.colliderect(b_rect):
                        p.hp -= 5 
                        # Помечаем пулю как "удаленную" для отправки на сервер, 
                        # чтобы избежать повторных попаданий за один кадр.
                        # В оригинальном коде была логика сдвига пули за карту, 
                        # но в Player.py ее теперь нужно удалить явно. 
                        # В рамках клиента мы просто сдвинем её, а на сервере 
                        # (в реальной ММО) должна быть отдельная логика. 
                        # Для этого проекта используем метод, как в оригинале.
                        bullet[0] = -5000 
                        bullet[1] = -5000
                        killer_id = p_id 

        if p.hp <= 0:
            if killer_id is not None:
                # Отправляем килл-сообщение с ID убийцы
                msg_to_send = f"[KILL] {killer_id} >> {p.id}"
            else:
                msg_to_send = f"[DEATH] Игрок {p.id} погиб."
            
            p.hp = 100
            p.x = random.randint(100, MAP_WIDTH - 100)
            p.y = random.randint(100, MAP_HEIGHT - 100)
        # --- КОНЕЦ ОБРАБОТКИ ПОПАДАНИЙ ---

        # --- СЕТЬ ---
        packet = {"player": p, "msg": msg_to_send}
        server_data = n.send(packet)
        
        if not server_data:
            run = False
            break
            
        all_players = server_data.get("players", {})
        chat_messages = server_data.get("chat", [])

        # --- ОТРИСОВКА ---
        draw_modern_grid(win, scroll)

        # Игроки
        for p_id, player in all_players.items():
            player.draw(win, scroll)
            
            # Инфо над головой врага
            screen_px = player.x - scroll[0] + player.width // 2
            screen_py = player.y - (scroll[1] + 20)
            
            # Ник (отцентрован)
            draw_text_shadow(f"ID: {p_id}", font_ui, (200, 200, 200), screen_px, screen_py - 20, center=True)
            
            # HP бар врага (обновлен, теперь рисуется в player.draw)
            # Удалена дублирующая логика HP бара

        # --- АНИМАЦИЯ: ВСПЫШКА ВЫСТРЕЛА ---
        if shoot_flash_timer > 0:
            # Чем меньше таймер, тем меньше и прозрачнее вспышка
            flash_radius = 20 + shoot_flash_timer * 3
            flash_alpha = int(255 * (shoot_flash_timer / 5))
            flash_color = (255, 255, 0, flash_alpha) 
            
            flash_surf = pygame.Surface((flash_radius*2, flash_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, flash_color, (flash_radius, flash_radius), flash_radius)
            
            # Рисуем поверх мира, но под HUD
            win.blit(flash_surf, (flash_pos[0] - flash_radius, flash_pos[1] - flash_radius))


        # Виньетка (атмосфера) - рисуем поверх игрового мира, но под HUD
        win.blit(vignette_surf, (0, 0))

        # --- HUD / ИНТЕРФЕЙС ---
        
        # Окно Чата
        chat_bg_height = 220
        chat_x, chat_y = 10, HEIGHT - chat_bg_height - 60
        chat_surf = pygame.Surface((360, chat_bg_height), pygame.SRCALPHA)
        chat_surf.fill((0, 0, 0, 150))
        win.blit(chat_surf, (chat_x, chat_y))
        pygame.draw.rect(win, C_ACCENT, (chat_x, chat_y, 360, chat_bg_height), 1)
        
        # Сообщения чата
        for i, msg in enumerate(chat_messages[-8:]):
            color = C_TEXT_MAIN
            if "[💀]" in msg: color = C_DANGER # Обновлено на [💀] из server.py
            if "[SERVER]" in msg: color = C_ACCENT
            
            draw_text_shadow(msg, font_ui, color, chat_x + 10, chat_y + 10 + i * 25)

        # Поле ввода чата
        input_y = HEIGHT - 50
        input_w = 350
        if typing_mode:
            pygame.draw.rect(win, (20, 20, 20), (10, input_y, input_w, 30))
            pygame.draw.rect(win, C_DANGER, (10, input_y, input_w, 30), 2)
            draw_text_shadow(current_message + "_", font_ui, C_DANGER, 15, input_y + 5)
        else:
            draw_text_shadow("Нажми ENTER для чата", font_ui, (120, 120, 120), 10, input_y + 5)

        # Данные игрока (HP, FPS)
        draw_hud(p, int(clock.get_fps()))

        # Кастомный курсор
        mx, my = pygame.mouse.get_pos()
        draw_custom_cursor(mx, my)

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