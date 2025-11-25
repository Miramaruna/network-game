import pygame
import random
import math
from network import Network
from player import Player 

pygame.init()

# --- НАСТРОЙКИ ЭКРАНА И КАРТЫ (Мобильный ландшафт) ---
WIDTH = 800  # Мобильное разрешение (ландшафт)
HEIGHT = 450
MAP_WIDTH = 2000
MAP_HEIGHT = 2000

win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Shooter: Mobile")

# --- ЦВЕТОВАЯ ПАЛИТРА (NEON STYLE) ---
C_BG = (10, 10, 20)           
C_GRID_DIM = (30, 30, 50)     
C_GRID_BRIGHT = (60, 60, 100) 
C_ACCENT = (0, 255, 255)      # Неоновый циан
C_DANGER = (255, 50, 50)      # Неоновый красный
C_TEXT_MAIN = (240, 240, 240)
C_UI_BG = (0, 0, 0, 150)      

# --- ШРИФТЫ ---
FONT_CHOICES = ["arial", "dejavusans", "verdana", "comicsansms"] 
font_ui = pygame.font.SysFont(FONT_CHOICES, 16)
font_hud = pygame.font.SysFont(FONT_CHOICES, 20, bold=True)
font_title = pygame.font.SysFont(FONT_CHOICES, 70, bold=True)

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ЭФФЕКТОВ ---
shoot_flash_timer = 0
flash_pos = (0, 0)

# --- ЭФФЕКТ ВИНЬЕТКИ (ЗАТЕМНЕНИЕ УГЛОВ) ---
vignette_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for x in range(WIDTH):
    for y in range(HEIGHT):
        dx = x - WIDTH // 2
        dy = y - HEIGHT // 2
        dist = math.sqrt(dx**2 + dy**2)
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

# --- НОВЫЙ КЛАСС: ВИРТУАЛЬНЫЙ ДЖОЙСТИК ---
class Joystick:
    def __init__(self, x, y, radius):
        self.center_x = x
        self.center_y = y
        self.radius = radius
        self.knob_radius = radius * 0.4
        self.knob_pos = (x, y)
        self.is_dragging = False
        self.move_vector = (0, 0) # (dx, dy) normalized
        self.touch_id = -1 # Для отслеживания мультитача (если используется)

    def draw(self, win):
        # Внешний круг (фон джойстика - полупрозрачный)
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        # Полупрозрачный фон
        pygame.draw.circle(s, (255, 255, 255, 60), (self.radius, self.radius), self.radius, 0)
        win.blit(s, (self.center_x - self.radius, self.center_y - self.radius))
        
        # Обводка
        pygame.draw.circle(win, C_ACCENT, (self.center_x, self.center_y), self.radius, 2)
        
        # Внутренний круг (рукоятка)
        pygame.draw.circle(win, C_DANGER, self.knob_pos, int(self.knob_radius * 1.2), 0)
        pygame.draw.circle(win, (255, 255, 255), self.knob_pos, self.knob_radius, 2)

    def handle_event(self, event):
        pos = pygame.mouse.get_pos()
        mouse_x, mouse_y = pos
        
        # Обработка начала касания
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            dist = math.hypot(mouse_x - self.center_x, mouse_y - self.center_y)
            if dist < self.radius * 2 and not self.is_dragging: # Проверка, что касание в зоне джойстика
                self.is_dragging = True
                self.touch_id = 1 # В Pygame только одно "касание"
                return True # Обработан джойстиком
                
        # Обработка отпускания касания
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging:
                self.is_dragging = False
                self.knob_pos = (self.center_x, self.center_y)
                self.move_vector = (0, 0)
                self.touch_id = -1
                return True # Отпущено в зоне джойстика
        
        return False # Не обработан джойстиком

    def update(self):
        if self.is_dragging:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = mouse_x - self.center_x
            dy = mouse_y - self.center_y
            distance = math.hypot(dx, dy)

            # Ограничиваем рукоятку радиусом
            if distance > self.radius:
                dx *= self.radius / distance
                dy *= self.radius / distance
                distance = self.radius

            self.knob_pos = (self.center_x + int(dx), self.center_y + int(dy))

            # Нормализуем вектор движения
            if distance > self.knob_radius / 4: # Небольшая мертвая зона
                self.move_vector = (dx / distance, dy / distance)
            else:
                self.move_vector = (0, 0)
        
        return self.move_vector


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ОТРИСОВКИ ---

def draw_text_shadow(text, font, color, x, y, center=False):
    """Рисует текст с черной тенью для лучшей читаемости"""
    shadow = font.render(text, True, (0, 0, 0))
    main_txt = font.render(text, True, color)
    
    if center:
        rect = main_txt.get_rect(center=(x, y))
        shadow_rect = shadow.get_rect(center=(x+1, y+1))
        win.blit(shadow, shadow_rect)
        win.blit(main_txt, rect)
    else:
        win.blit(shadow, (x+1, y+1))
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
    """Рисуем прицел/точку касания"""
    # Рисуем только прицел, если это последнее место стрельбы
    pygame.draw.circle(win, C_ACCENT, (mx, my), 15, 2)
    pygame.draw.circle(win, (255, 255, 255), (mx, my), 4)

def draw_hud(player, fps):
    """Интерфейс игрока (HP, FPS, Ник) - адаптирован под 800x450"""
    # 1. Полоска здоровья (сверху по центру)
    bar_w, bar_h = 200, 20
    bar_x = WIDTH // 2 - bar_w // 2
    bar_y = 10 
    
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
    
    # 2. Информация (в правом верхнем углу)
    info_bg = pygame.Surface((200, 60), pygame.SRCALPHA)
    info_bg.fill((0,0,0, 150)) 
    win.blit(info_bg, (WIDTH - 200, 45))
    
    draw_text_shadow(f"NICK: {player.nickname[:10]}", font_ui, C_ACCENT, WIDTH - 190, 50)
    draw_text_shadow(f"FPS: {fps}", font_ui, C_DANGER, WIDTH - 190, 70)


# --- ОСНОВНЫЕ ФУНКЦИИ ---

def main_menu():
    user_ip = ""
    user_nick = ""
    clock = pygame.time.Clock()
    active_field = "NICK" # Начинаем с ника
    active = True
    
    particles = [Particle() for _ in range(35)]
    
    # Пересчет позиций для 800x450
    title_y = 80
    nick_y = 180
    ip_y = 280
    
    while active:
        clock.tick(60)
        win.fill(C_BG)
        
        for p in particles:
            p.move()
            p.draw(win)

        # Текст
        draw_text_shadow("NEON SHOOTER", font_title, C_ACCENT, WIDTH//2, title_y, center=True)
        
        # --- ПОЛЕ: НИКНЕЙМ ---
        draw_text_shadow("НИКНЕЙМ:", font_hud, (180, 180, 180), WIDTH//2, nick_y, center=True)
        nick_box = pygame.Rect(WIDTH//2 - 150, nick_y + 30, 300, 35)
        
        nick_border_color = C_DANGER if active_field == "NICK" else C_ACCENT
        
        pygame.draw.rect(win, (20, 20, 30), nick_box, border_radius=5)
        pygame.draw.rect(win, nick_border_color, nick_box, 2, border_radius=5)
        
        nick_text = user_nick
        if active_field == "NICK" and (pygame.time.get_ticks()//500)%2==0:
             nick_text += "|"
        
        txt_surf_nick = font_hud.render(nick_text, True, C_TEXT_MAIN)
        win.blit(txt_surf_nick, (nick_box.x + 10, nick_box.y + 7))

        # --- ПОЛЕ: IP АДРЕС ---
        draw_text_shadow("IP СЕРВЕРА:", font_hud, (180, 180, 180), WIDTH//2, ip_y, center=True)
        ip_box = pygame.Rect(WIDTH//2 - 150, ip_y + 30, 300, 35)
        
        ip_border_color = C_DANGER if active_field == "IP" else C_ACCENT
        
        pygame.draw.rect(win, (20, 20, 30), ip_box, border_radius=5)
        pygame.draw.rect(win, ip_border_color, ip_box, 2, border_radius=5)
        
        ip_text = user_ip
        if active_field == "IP" and (pygame.time.get_ticks()//500)%2==0:
            ip_text += "|"

        txt_surf_ip = font_hud.render(ip_text, True, C_TEXT_MAIN)
        win.blit(txt_surf_ip, (ip_box.x + 10, ip_box.y + 7))
        
        # Подсказка
        draw_text_shadow("TAB/Нажми - сменить поле | ENTER - Играть", font_ui, (120, 120, 120), WIDTH//2, HEIGHT - 50, center=True)
        if user_ip == "":
             draw_text_shadow("(Пусто = localhost)", font_ui, (80, 80, 80), WIDTH//2, ip_y + 70, center=True)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_TAB:
                    active_field = "IP" if active_field == "NICK" else "NICK"
                    
                if event.key == pygame.K_ESCAPE: return "QUIT"
                
                if event.key == pygame.K_RETURN: 
                    final_ip = user_ip if user_ip else "127.0.0.1"
                    final_nick = user_nick if user_nick else f"Игрок_{random.randint(100, 999)}"
                    return (final_ip, final_nick)

                if event.key == pygame.K_BACKSPACE:
                    if active_field == "IP": user_ip = user_ip[:-1]
                    elif active_field == "NICK": user_nick = user_nick[:-1]
                else: 
                    if active_field == "IP" and len(user_ip) < 15: user_ip += event.unicode
                    elif active_field == "NICK" and len(user_nick) < 12: user_nick += event.unicode

            # Обработка клика/тача для смены активного поля
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if nick_box.collidepoint(mouse_x, mouse_y):
                    active_field = "NICK"
                elif ip_box.collidepoint(mouse_x, mouse_y):
                    active_field = "IP"
    return "QUIT"


def game_loop(server_ip, nickname):
    global shoot_flash_timer, flash_pos
    
    try:
        n = Network(server_ip)
        p = n.getP()
    except:
        print("Ошибка подключения к серверу")
        return

    if not p: return 
        
    p.nickname = nickname 

    clock = pygame.time.Clock()
    run = True
    
    chat_messages = []
    typing_mode = False
    current_message = ""
    
    # Инициализация джойстика
    joystick_radius = 60
    joystick = Joystick(joystick_radius + 20, HEIGHT - joystick_radius - 20, joystick_radius)
    
    # Скрываем стандартный курсор (для эмуляции тач-интерфейса)
    pygame.mouse.set_visible(False) 
    
    # Хранение позиции последнего касания для стрельбы
    last_touch_pos = None 
    
    # Инициализация плавной камеры
    scroll_x = p.x - WIDTH // 2 + p.width // 2
    scroll_y = p.y - HEIGHT // 2 + p.height // 2

    while run:
        clock.tick(60)
        msg_to_send = None 
        
        # --- ПЛАВНАЯ КАМЕРА ---
        target_x = p.x - WIDTH // 2 + p.width // 2
        target_y = p.y - HEIGHT // 2 + p.height // 2
        
        scroll_x += (target_x - scroll_x) * 0.2 
        scroll_y += (target_y - scroll_y) * 0.2
        
        scroll = (scroll_x, scroll_y)

        if shoot_flash_timer > 0: shoot_flash_timer -= 1

        # События
        mouse_x, mouse_y = pygame.mouse.get_pos()
        joystick_processed = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.mouse.set_visible(True)
                return "QUIT"
            
            # 1. Обработка джойстика
            if not typing_mode:
                if joystick.handle_event(event):
                    joystick_processed = True
            
            # 2. Обработка чата (оставляем клавиатуру для ввода, если эмулируется)
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

            
            # 3. Стрельба (Тап/Клик вне джойстика)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # Проверяем, было ли касание использовано джойстиком
                if not joystick_processed:
                    last_touch_pos = (mouse_x, mouse_y)
                    
                    if not typing_mode:
                        p.shoot(mouse_x, mouse_y, scroll)
                        shoot_flash_timer = 5 
                        flash_pos = (mouse_x, mouse_y)
            
        # --- ДВИЖЕНИЕ (ИСПОЛЬЗУЕМ ВЕКТОР ДЖОЙСТИКА) ---
        move_vector = joystick.update()
        if not typing_mode:
            p.move_mobile(MAP_WIDTH, MAP_HEIGHT, move_vector) 
        
        # --- ОБРАБОТКА ПОПАДАНИЙ (ЛОКАЛЬНО) ---
        all_players = n.send({"player": p, "msg": msg_to_send}).get("players", {})
        
        # 1. Попадание вражеских пуль в локального игрока (урон)
        killer_id = None 
        my_rect = pygame.Rect(p.x, p.y, p.width, p.height)
        enemies = all_players.items()
        
        for p_id, enemy in enemies:
            if p_id != p.id:
                for bullet in list(enemy.bullets):
                    b_rect = pygame.Rect(bullet[0]-6, bullet[1]-6, 12, 12)
                    if my_rect.colliderect(b_rect):
                        p.hp -= 5 
                        bullet[0] = -5000 
                        bullet[1] = -5000
                        killer_id = p_id 

        # 2. Попадание локальных пуль во врагов (исчезновение пули)
        bullets_to_remove = []
        for bullet in list(p.bullets): 
            b_rect = pygame.Rect(bullet[0]-6, bullet[1]-6, 12, 12)
            for enemy_id, enemy in all_players.items():
                if enemy_id != p.id:
                    enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                    if b_rect.colliderect(enemy_rect):
                        bullets_to_remove.append(bullet)
                        break 
        
        for bullet in bullets_to_remove:
            if bullet in p.bullets:
                p.bullets.remove(bullet)
        
        # --- СМЕРТЬ ---
        if p.hp <= 0:
            if killer_id is not None:
                msg_to_send = f"[KILL] {all_players[killer_id].nickname} >> {p.nickname}"
            else:
                msg_to_send = f"[DEATH] {p.nickname} погиб."
            
            p.hp = 100
            p.x = random.randint(100, MAP_WIDTH - 100)
            p.y = random.randint(100, MAP_HEIGHT - 100)

        # --- СЕТЬ (Окончательная отправка) ---
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
            
            # Инфо над головой
            screen_px = player.x - scroll[0] + player.width // 2
            screen_py = player.y - (scroll[1] + 20)
            
            display_name = getattr(player, 'nickname', f"Игрок {p_id}")
            draw_text_shadow(display_name, font_ui, (200, 200, 200), screen_px, screen_py - 20, center=True)

        # Вспышка выстрела
        if shoot_flash_timer > 0:
            flash_radius = 20 + shoot_flash_timer * 3
            flash_alpha = int(255 * (shoot_flash_timer / 5))
            flash_color = (255, 255, 0, flash_alpha) 
            flash_surf = pygame.Surface((flash_radius*2, flash_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, flash_color, (flash_radius, flash_radius), flash_radius)
            win.blit(flash_surf, (flash_pos[0] - flash_radius, flash_pos[1] - flash_radius))

        # Виньетка 
        win.blit(vignette_surf, (0, 0))

        # --- HUD / ИНТЕРФЕЙС ---
        draw_hud(p, int(clock.get_fps()))
        
        # Рисуем джойстик
        joystick.draw(win) 

        # Окно Чата (справа внизу)
        chat_bg_height = 150 
        chat_x, chat_y = WIDTH - 360 - 10, HEIGHT - chat_bg_height - 10 
        chat_surf = pygame.Surface((360, chat_bg_height), pygame.SRCALPHA)
        chat_surf.fill((0, 0, 0, 150))
        win.blit(chat_surf, (chat_x, chat_y))
        pygame.draw.rect(win, C_ACCENT, (chat_x, chat_y, 360, chat_bg_height), 1)
        
        # Сообщения чата
        for i, msg in enumerate(chat_messages[-6:]):
            color = C_TEXT_MAIN
            if "[💀]" in msg: color = C_DANGER
            if "[SERVER]" in msg: color = C_ACCENT
            
            draw_text_shadow(msg, font_ui, color, chat_x + 10, chat_y + 10 + i * 25)

        # Поле ввода чата
        chat_input_x = chat_x
        chat_input_y = chat_y - 40 
        input_w = 360
        
        if typing_mode:
            pygame.draw.rect(win, (20, 20, 20), (chat_input_x, chat_input_y, input_w, 30))
            pygame.draw.rect(win, C_DANGER, (chat_input_x, chat_input_y, input_w, 30), 2)
            draw_text_shadow(current_message + "_", font_ui, C_DANGER, chat_input_x + 5, chat_input_y + 5)
        else:
            draw_text_shadow("Нажми ENTER для чата", font_ui, (120, 120, 120), chat_input_x + 5, chat_input_y + 5)

        # Прицел (последнее место касания для стрельбы)
        if last_touch_pos and not joystick.is_dragging:
            draw_custom_cursor(*last_touch_pos)

        pygame.display.update()


def main_app():
    app_running = True
    while app_running:
        result = main_menu()
        
        if result == "QUIT": 
            app_running = False
        elif isinstance(result, tuple):
            server_ip, nickname = result 
            game_loop(server_ip, nickname) 
    pygame.quit()

if __name__ == "__main__":
    main_app()