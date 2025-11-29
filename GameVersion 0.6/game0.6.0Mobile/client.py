import pygame
import random
import math
import json
import os
from network import Network
from player import Player, Wall, ShieldAbility, WallAbility 
import pygame.freetype 

pygame.init()
pygame.freetype.init()

# --- SETTINGS ---
WIDTH = 900
HEIGHT = 700
MAP_WIDTH = 2000
MAP_HEIGHT = 2000

win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Shooter: Mobile Controls Update")

# --- SKINS LOADING ---
SKINS_DATA = {}

def load_skins():
    global SKINS_DATA
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "Config", "skins.json")
        with open(config_path, "r", encoding='utf-8') as f:
            SKINS_DATA = json.load(f)
        print("Скины загружены:", list(SKINS_DATA.keys()))
    except Exception as e:
        print(f"Ошибка загрузки скинов: {e}")
        SKINS_DATA = {
            "DEFAULT": {"body_color": [0, 255, 255], "trail_color": [0, 200, 200], "outline_color": [255, 255, 255]}
        }

load_skins()

# --- PALETTE & FONTS ---
C_BG = (10, 10, 20)
C_GRID_DIM = (30, 30, 50)
C_GRID_BRIGHT = (60, 60, 100)
C_ACCENT = (0, 255, 255)
C_DANGER = (255, 50, 50)
C_TEXT_MAIN = (240, 240, 240)
C_UI_BG = (0, 0, 0, 150)
C_BG_DEEP = (5, 5, 12)  
C_NEON_CYAN = (0, 255, 255)
C_NEON_PINK = (255, 0, 150)
C_TEXT = (220, 240, 255)

FONT_CHOICES = ["arial", "dejavusans", "verdana"] 
try:
    FONT_UI = pygame.freetype.Font("arial", 16)
    FONT_HUD = pygame.freetype.Font("arial", 20)
    FONT_TITLE = pygame.freetype.Font("arial", 70)
    FONT_DEBUG = pygame.freetype.SysFont("consolas", 14) 
except:
    FONT_UI = pygame.freetype.SysFont(FONT_CHOICES, 16)
    FONT_HUD = pygame.freetype.SysFont(FONT_CHOICES, 20, bold=True)
    FONT_TITLE = pygame.freetype.SysFont(FONT_CHOICES, 70, bold=True)
    FONT_DEBUG = pygame.freetype.SysFont("courier", 14)

# --- GLOBAL EFFECTS ---
shoot_flash_timer = 0
flash_pos = (0, 0)
vignette_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for x in range(WIDTH):
    for y in range(HEIGHT):
        dx = x - WIDTH // 2
        dy = y - HEIGHT // 2
        dist = math.sqrt(dx**2 + dy**2)
        alpha = min(255, int(dist / (WIDTH * 0.65) * 255))
        if alpha > 40:
            vignette_surf.set_at((x, y), (0, 0, 0, alpha))

def draw_text_freetype(font_obj, text, color, x, y, center=False):
    if isinstance(font_obj, pygame.font.Font):
        # Fallback for old font system if freetype fails
        text_surf = font_obj.render(text, True, color)
        text_rect = text_surf.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        win.blit(text_surf, text_rect)
        return
        
    shadow_color = (0, 0, 0)
    shadow_surf, shadow_rect = font_obj.render(text, shadow_color)
    main_surf, main_rect = font_obj.render(text, color)
    if center:
        main_rect.center = (x, y)
        shadow_rect.center = (x + 2, y + 2)
    else:
        main_rect.topleft = (x, y)
        shadow_rect.topleft = (x + 2, y + 2)
    win.blit(shadow_surf, shadow_rect)
    win.blit(main_surf, main_rect)

# --- DEBUG INTERFACE CLASS (Оставлено без изменений) ---
class DebugInterface:
    def __init__(self):
        self.active = False
        self.bg_surf = pygame.Surface((300, 220), pygame.SRCALPHA)
        self.bg_surf.fill((0, 0, 0, 200)) # Полупрозрачный черный фон

    def toggle(self):
        self.active = not self.active
        return self.active

    def draw(self, win, player, network, fps, scroll, last_packet_info):
        if not self.active: return

        x, y = 10, 10
        win.blit(self.bg_surf, (x, y))
        pygame.draw.rect(win, (0, 255, 0), (x, y, 300, 220), 1)

        # Сбор данных
        net_stats = network.traffic_stats
        sent_kb = net_stats['sent_total'] / 1024
        recv_kb = net_stats['recv_total'] / 1024
        
        info_lines = [
            f"--- DEBUG MODE ---",
            f"FPS: {fps}",
            f"Position: ({int(player.x)}, {int(player.y)})",
            f"Scroll: ({int(scroll[0])}, {int(scroll[1])})",
            f"Entities: Bullets: {len(player.bullets)}",
            f"--- NETWORK ---",
            f"Sent Total: {sent_kb:.2f} KB",
            f"Recv Total: {recv_kb:.2f} KB",
            f"Packet Size: {net_stats['last_packet_size']} bytes",
            f"Packets Sent: {net_stats['packets_sent']}",
            f"Last Action: {last_packet_info}"
        ]

        # Отрисовка текста
        line_height = 18
        curr_y = y + 10
        for line in info_lines:
            FONT_DEBUG.render_to(win, (x + 10, curr_y), line, (0, 255, 0))
            curr_y += line_height

# --- HELPERS (Без изменений) ---
def draw_modern_grid(win, scroll):
    win.fill(C_BG)
    border_rect = pygame.Rect(-scroll[0], -scroll[1], MAP_WIDTH, MAP_HEIGHT)
    pygame.draw.rect(win, C_DANGER, border_rect, 3)
    grid_size = 100
    start_x = -int(scroll[0]) % grid_size
    start_y = -int(scroll[1]) % grid_size
    for i in range(start_x, WIDTH, grid_size):
        real_world_x = i + scroll[0]
        color = C_GRID_BRIGHT if abs(real_world_x) % (grid_size*5) < grid_size else C_GRID_DIM
        pygame.draw.line(win, color, (i, 0), (i, HEIGHT))
    for i in range(start_y, HEIGHT, grid_size):
        real_world_y = i + scroll[1]
        color = C_GRID_BRIGHT if abs(real_world_y) % (grid_size*5) < grid_size else C_GRID_DIM
        pygame.draw.line(win, color, (0, i), (WIDTH, i))

def draw_custom_cursor(mx, my):
    # Оставляем курсор для PC/Debug
    pygame.draw.circle(win, C_ACCENT, (mx, my), 8, 1)
    pygame.draw.line(win, C_ACCENT, (mx - 12, my), (mx + 12, my), 1)
    pygame.draw.line(win, C_ACCENT, (mx, my - 12), (mx, my + 12), 1)

# --- НОВЫЕ ФУНКЦИИ ДЛЯ МОБИЛЬНОГО УПРАВЛЕНИЯ ---

# Глобальная переменная для джойстика
joystick_active = False 
# ИЗМЕНЕНИЕ 1: Скорректированная позиция джойстика
joystick_center = (WIDTH // 4, HEIGHT - 170) 
joystick_radius = 80
joystick_stick_pos = joystick_center

# Функция отрисовки управления: Добавлена кнопка чата
def draw_mobile_controls(player):
    global joystick_active, joystick_center, joystick_radius, joystick_stick_pos
    
    # --- 1. Виртуальный джойстик (Левая сторона) ---
    pygame.draw.circle(win, (50, 50, 100, 150), joystick_center, joystick_radius + 10, 0)
    pygame.draw.circle(win, (100, 100, 200, 200), joystick_center, joystick_radius, 3)
    
    # Стик джойстика
    stick_color = C_ACCENT if joystick_active else (150, 150, 150)
    pygame.draw.circle(win, stick_color, joystick_stick_pos, 25, 0)
    pygame.draw.circle(win, (0, 0, 0), joystick_stick_pos, 25, 2)
    
    # --- 2. Кнопка чата (Левая сторона, под HUD) ---
    chat_button_rect = pygame.Rect(10, 10, 100, 35)
    
    # Фон кнопки
    pygame.draw.rect(win, (0, 0, 0, 180), chat_button_rect, border_radius=5)
    # Рамка кнопки
    pygame.draw.rect(win, C_NEON_PINK, chat_button_rect, 2, border_radius=5)
    draw_text_freetype(FONT_HUD, "ЧАТ", C_TEXT_MAIN, chat_button_rect.centerx, chat_button_rect.centery, center=True)
    
    # --- 3. Кнопки способностей (Правая сторона) ---
    
    ability_keys = ["shield", "wall"]
    ability_names = {"shield": "SHIELD", "wall": "WALL"}
    
    ab_y_start = HEIGHT - 180 
    ab_center_x = WIDTH - 100
    
    ability_rects = {}
    
    for i, key in enumerate(ability_keys):
        ability = player.abilities[key]
        cooldown_s = ability.cooldown / 60
        cooldown_max_s = ability.cooldown_max / 60
        
        box_w, box_h = 100, 35
        box_x = ab_center_x - box_w // 2
        box_y = ab_y_start - i * (box_h + 10) 
        
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        ability_rects[key] = box_rect
        
        # Фон кнопки
        pygame.draw.rect(win, (0, 0, 0, 180), box_rect, border_radius=5)
        
        if cooldown_s > 0:
            fill_pct = cooldown_s / cooldown_max_s
            fill_h = int(box_h * fill_pct)
            
            # Затемнение/заполнение кулдауна
            cooldown_fill = pygame.Surface((box_w, fill_h), pygame.SRCALPHA)
            cooldown_fill.fill((10, 10, 50, 200)) 
            win.blit(cooldown_fill, (box_x, box_y + box_h - fill_h))
            
            # Текст кулдауна
            draw_text_freetype(FONT_UI, f"{cooldown_s:.1f}s", C_DANGER, box_rect.centerx, box_rect.centery - 5, center=True)
            pygame.draw.rect(win, (50, 50, 50), box_rect, 1, border_radius=5)
        else:
            # Готово
            draw_text_freetype(FONT_UI, ability_names[key], C_NEON_CYAN, box_rect.centerx, box_rect.centery - 5, center=True)
            pygame.draw.rect(win, C_NEON_CYAN, box_rect, 2, border_radius=5)
            
    # Добавляем rect чата в список, чтобы его можно было обработать
    ability_rects["chat_button"] = chat_button_rect
            
    return ability_rects

# Функция обработки ввода: Обновлена логика для точного определения джойстика и чата
def handle_mobile_input(event, player, scroll, ui_rects, typing_mode):
    global joystick_active, joystick_stick_pos, joystick_center, joystick_radius, shoot_flash_timer, flash_pos
    
    mx, my = event.pos
    ability_to_cast = None
    
    joystick_touch_radius = joystick_radius + 30 
    
    # --- 1. Обработка нажатия (MOUSEBUTTONDOWN) ---
    if event.type == pygame.MOUSEBUTTONDOWN:
        
        # c) Нажатие на кнопки способностей или чата (Проверяем первым)
        for key, rect in ui_rects.items():
            if rect.collidepoint(mx, my):
                if key == "chat_button":
                    return {"action": "TOGGLE_CHAT"}
                
                # Только способности
                if player.cast_ability(key):
                    ability_to_cast = {"key": key}
                return ability_to_cast 
        
        # a) Нажатие на джойстик (Точная проверка по радиусу)
        dx_joy = mx - joystick_center[0]
        dy_joy = my - joystick_center[1]
        dist_joy = math.sqrt(dx_joy**2 + dy_joy**2)
        
        if dist_joy < joystick_touch_radius:
            joystick_active = True
            
        # b) Клик-чтобы-стрелять (Если не попали ни в кнопку, ни в зону джойстика)
        # Игрок не должен стрелять, если он в режиме ввода текста (typing_mode)
        elif not typing_mode: 
            # Преобразование экранных координат в мировые
            world_target_x = mx + scroll[0]
            world_target_y = my + scroll[1]
            
            player.shoot(world_target_x, world_target_y)
            
            # Эффект вспышки
            shoot_flash_timer = 5
            flash_pos = (mx, my) # Вспышка в месте клика

    # --- 2. Обработка движения (MOUSEMOTION) ---
    elif event.type == pygame.MOUSEMOTION:
        if joystick_active:
            # Вектор от центра к курсору
            dx = mx - joystick_center[0]
            dy = my - joystick_center[1]
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > joystick_radius:
                # Ограничиваем стик радиусом
                angle = math.atan2(dy, dx)
                new_x = joystick_center[0] + math.cos(angle) * joystick_radius
                new_y = joystick_center[1] + math.sin(angle) * joystick_radius
                joystick_stick_pos = (new_x, new_y)
            else:
                joystick_stick_pos = (mx, my)

    # --- 3. Обработка отпускания (MOUSEBUTTONUP) ---
    elif event.type == pygame.MOUSEBUTTONUP:
        if joystick_active:
            # Сбрасываем стик и статус
            joystick_active = False
            joystick_stick_pos = joystick_center
            
    return ability_to_cast

def get_movement_vector(player_vel):
    """Рассчитывает вектор движения на основе положения стика джойстика"""
    global joystick_active, joystick_stick_pos, joystick_center, joystick_radius
    
    if not joystick_active:
        return 0, 0, (0, 0) # dx, dy, last_move (для трейла)
    
    dx_raw = joystick_stick_pos[0] - joystick_center[0]
    dy_raw = joystick_stick_pos[1] - joystick_center[1]
    dist = math.sqrt(dx_raw**2 + dy_raw**2)
    
    if dist < 10: # Мертвая зона
        return 0, 0, (0, 0)
        
    angle = math.atan2(dy_raw, dx_raw)
    
    # Нормализуем скорость по радиусу стика (чем дальше стик, тем быстрее)
    speed_factor = min(1.0, dist / joystick_radius)
    
    vel_x = math.cos(angle) * player_vel * speed_factor
    vel_y = math.sin(angle) * player_vel * speed_factor
    
    # Для trail_particles (Player._generate_trail_particles) нам нужны дискретные -1/0/1
    last_move_x = 1 if vel_x > 0.5 else (-1 if vel_x < -0.5 else 0)
    last_move_y = 1 if vel_y > 0.5 else (-1 if vel_y < -0.5 else 0)
    
    return vel_x, vel_y, (last_move_x, last_move_y)

# --- HUD (Изменено для поддержки мобильных кнопок) ---
def draw_hud(player, fps):
    # HUD отрисовка (сокращена для экономии места, логика та же)
    bar_w, bar_h = 200, 20
    bar_x = WIDTH // 2 - bar_w // 2
    bar_y = HEIGHT - 40
    pygame.draw.rect(win, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
    hp_pct = max(0, player.hp / 100)
    fill_w = int(bar_w * hp_pct)
    color = C_ACCENT if hp_pct > 0.3 else C_DANGER
    pygame.draw.rect(win, color, (bar_x, bar_y, fill_w, bar_h), border_radius=5)
    pygame.draw.rect(win, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=5)
    draw_text_freetype(FONT_HUD, f"HP: {player.hp}%", C_TEXT_MAIN, bar_x + bar_w//2, bar_y + 1, center=True)
    draw_text_freetype(FONT_UI, f"FPS: {fps}", C_DANGER, WIDTH - 180, 35)

# --- MENUS (Без изменений) ---
def main_menu():
    clock = pygame.time.Clock()
    user_ip = "192.168.0.110" 
    user_nick = ""
    active_field = "NICK"
    skins = ["DEFAULT", "RED_CYBORG", "GOLD_ELITE", "TOXIC_GREEN", "VOID_WALKER"]
    skin_idx = 0
    pygame.mouse.set_visible(True) 

    # Определяем Rect-объекты для кликов
    NICK_BOX_RECT = pygame.Rect(WIDTH//2 - 150, 280, 300, 40)
    IP_BOX_RECT = pygame.Rect(WIDTH//2 - 150, 380, 300, 40)
    
    SKIN_Y = 480
    LEFT_ARROW_RECT = pygame.Rect(WIDTH//2 - 120, SKIN_Y - 20, 50, 40)
    RIGHT_ARROW_RECT = pygame.Rect(WIDTH//2 + 70, SKIN_Y - 20, 50, 40)
    START_BUTTON_RECT = pygame.Rect(WIDTH//2 - 100, 540, 200, 50) # Новая кнопка START

    while True:
        clock.tick(60)
        win.fill(C_BG_DEEP)
        t = pygame.time.get_ticks() / 1000
        grid_off = (t * 20) % 50
        for x in range(0, WIDTH, 50): pygame.draw.line(win, (20, 20, 40), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 50): pygame.draw.line(win, (20, 20, 40), (0, y + grid_off), (WIDTH, y + grid_off))

        draw_text_freetype(FONT_TITLE, "NEON STRIKE", C_NEON_CYAN, WIDTH//2, 100, center=True)
        draw_text_freetype(FONT_HUD, "MULTIPLAYER BATTLE ARENA", C_NEON_PINK, WIDTH//2, 160, center=True)

        # Отрисовка полей ввода
        inputs = [("NICKNAME", user_nick, NICK_BOX_RECT, active_field == "NICK"), 
                  ("SERVER IP", user_ip, IP_BOX_RECT, active_field == "IP")]
                  
        for label, val, box_rect, is_active in inputs:
            draw_text_freetype(FONT_UI, label, (150, 150, 150), WIDTH//2, box_rect.y - 25 + 20, center=True)
            col = C_NEON_CYAN if is_active else (50, 50, 100)
            pygame.draw.rect(win, (10, 10, 20), box_rect)
            pygame.draw.rect(win, col, box_rect, 2)
            txt_display = val + ("|" if is_active and (pygame.time.get_ticks()//500)%2 else "")
            draw_text_freetype(FONT_HUD, txt_display, C_TEXT, box_rect.x + 10, box_rect.y + 10)

        # Отрисовка селектора скинов с кнопками
        draw_text_freetype(FONT_UI, "SELECT CLASS", (150, 150, 150), WIDTH//2, 450, center=True)
        skin_name = skins[skin_idx]
        
        # Левая стрелка
        pygame.draw.rect(win, (10, 10, 20), LEFT_ARROW_RECT)
        pygame.draw.rect(win, C_NEON_PINK, LEFT_ARROW_RECT, 2)
        draw_text_freetype(FONT_HUD, "<", C_NEON_PINK, LEFT_ARROW_RECT.centerx, LEFT_ARROW_RECT.centery, center=True)
        
        # Имя скина
        draw_text_freetype(FONT_HUD, skin_name, C_NEON_PINK, WIDTH//2, SKIN_Y, center=True)
        
        # Правая стрелка
        pygame.draw.rect(win, (10, 10, 20), RIGHT_ARROW_RECT)
        pygame.draw.rect(win, C_NEON_PINK, RIGHT_ARROW_RECT, 2)
        draw_text_freetype(FONT_HUD, ">", C_NEON_PINK, RIGHT_ARROW_RECT.centerx, RIGHT_ARROW_RECT.centery, center=True)
        
        # Кнопка START
        pygame.draw.rect(win, C_NEON_CYAN, START_BUTTON_RECT, border_radius=5)
        draw_text_freetype(FONT_TITLE, "START", (0, 0, 0), START_BUTTON_RECT.centerx, START_BUTTON_RECT.centery, center=True)

        draw_text_freetype(FONT_UI, "[ENTER] Start  [ESC] Exit", (100, 100, 150), WIDTH//2, 650, center=True)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Клик по полю ввода
                if NICK_BOX_RECT.collidepoint(mx, my):
                    active_field = "NICK"
                elif IP_BOX_RECT.collidepoint(mx, my):
                    active_field = "IP"
                # Клик по стрелкам скинов
                elif LEFT_ARROW_RECT.collidepoint(mx, my):
                    skin_idx = (skin_idx - 1) % len(skins)
                elif RIGHT_ARROW_RECT.collidepoint(mx, my):
                    skin_idx = (skin_idx + 1) % len(skins)
                # Клик по кнопке START
                elif START_BUTTON_RECT.collidepoint(mx, my):
                    final_nick = user_nick if user_nick else f"User{random.randint(100,999)}"
                    return (user_ip, final_nick, skin_name)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return "QUIT"
                # Удален K_TAB
                if event.key == pygame.K_RETURN:
                    final_nick = user_nick if user_nick else f"User{random.randint(100,999)}"
                    return (user_ip, final_nick, skin_name)
                # Удалены K_LEFT/K_RIGHT для скинов
                if event.key == pygame.K_BACKSPACE:
                    if active_field == "NICK": user_nick = user_nick[:-1]
                    else: user_ip = user_ip[:-1]
                elif event.unicode.isprintable():
                    if active_field == "NICK" and len(user_nick) < 12: user_nick += event.unicode
                    if active_field == "IP" and len(user_ip) < 15: user_ip += event.unicode

# --- GAME LOOP (Измененная логика ввода) ---
def game_loop(server_ip, nickname, selected_skin):
    global shoot_flash_timer, flash_pos
    
    try:
        n = Network(server_ip)
        p = n.getP()
    except:
        print("Ошибка подключения к серверу")
        return

    if not p: return 
    
    p.nickname = nickname
    p.skin_id = selected_skin 
    
    init_packet = {
        "type": "INIT",
        "skin": selected_skin,
        "nick": nickname
    }
    n.send(init_packet)
    print(f"Отправлен пакет инициализации: {selected_skin}")
    
    clock = pygame.time.Clock()
    run = True
    typing_mode = False
    current_message = ""
    
    scroll_x = p.x - WIDTH // 2 + p.width // 2
    scroll_y = p.y - HEIGHT // 2 + p.height // 2
    pygame.mouse.set_visible(False)
    
    last_walls = {}
    debug_ui = DebugInterface()
    
    # Переменные для мобильного управления
    ui_rects = {} # Теперь включает кнопки способностей и кнопку чата

    while run:
        clock.tick(60)
        msg_to_send = None 
        ability_to_cast = None
        
        target_x = p.x - WIDTH // 2 + p.width // 2
        target_y = p.y - HEIGHT // 2 + p.height // 2
        scroll_x += (target_x - scroll_x) * 0.2 
        scroll_y += (target_y - scroll_y) * 0.2
        scroll = (scroll_x, scroll_y)

        if shoot_flash_timer > 0: shoot_flash_timer -= 1
        
        # --- Мобильное движение (Применяем вектор от джойстика) ---
        vel_x, vel_y, p.last_move = get_movement_vector(p.vel)
        if p.hp > 0:
            p.x += vel_x
            p.y += vel_y
            
            p.x = max(0, min(p.x, MAP_WIDTH - p.width))
            p.y = max(0, min(p.y, MAP_HEIGHT - p.height))
            p.update(MAP_WIDTH, MAP_HEIGHT)
        elif p.hp <= 0:
            p.last_move = (0, 0)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False; pygame.mouse.set_visible(True); return "QUIT"
            
            # --- Мобильный ввод (Обработка мыши/тача) ---
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                # В handle_mobile_input теперь передаются все rects UI
                result = handle_mobile_input(event, p, scroll, ui_rects, typing_mode)
                
                # Обработка клика по кнопке чата
                if result and result.get("action") == "TOGGLE_CHAT":
                    typing_mode = not typing_mode
                    if not typing_mode:
                        if current_message.strip():
                            msg_to_send = current_message
                        current_message = ""
                # Обработка способностей
                elif result and result.get("key"):
                    ability_to_cast = result
            
            # --- Ввод с клавиатуры (Для чата и дебага) ---
            if event.type == pygame.KEYDOWN:
                # Чат / Дебаг
                if event.key == pygame.K_ESCAPE:
                    if typing_mode: typing_mode = False
                    else: n.disconnect(); run = False; pygame.mouse.set_visible(True)
                elif event.key == pygame.K_RETURN:
                    if typing_mode:
                        if len(current_message) > 0: 
                            if current_message.strip() == "/debug":
                                is_active = debug_ui.toggle()
                                status = "ON" if is_active else "OFF"
                                print(f"Debug mode {status}")
                                msg_to_send = None 
                            else:
                                msg_to_send = current_message
                            
                            current_message = ""
                        typing_mode = False
                    else: typing_mode = True; current_message = ""
                elif typing_mode:
                    if event.key == pygame.K_BACKSPACE: current_message = current_message[:-1]
                    else: 
                        if len(current_message) < 40: current_message += event.unicode
        
        # --- КОНЕЦ ОБРАБОТКИ ВВОДА ---


        hit_data = [] 
        current_bullets = list(p.bullets) 
        for bullet in current_bullets:
            bullet_rect = pygame.Rect(bullet[0] - 5, bullet[1] - 5, 10, 10) 
            wall_hit = False
            for wall in last_walls.values():
                if bullet_rect.colliderect(wall.rect):
                    p.deleteBullet(bullet); wall_hit = True; break
            if wall_hit: continue

            for other_id, other_p in all_players.items():
                # Проверка: не сам, жив, нет щита
                if other_id != p.id and other_p.hp > 0 and other_p.abilities["shield"].duration <= 0:
                    if bullet_rect.colliderect(other_p.rect):
                        p.deleteBullet(bullet)
                        hit_data.append({"target_id": other_id, "damage": 10})
                        break
        
        # --- СБОР ДАННЫХ ДЛЯ ДЕБАГА ---
        last_packet_info = "None"
        if ability_to_cast: last_packet_info = f"Cast {ability_to_cast['key']}"
        elif msg_to_send: last_packet_info = "Chat Message"
        elif hit_data: last_packet_info = f"Hit {len(hit_data)} targets"
        elif vel_x != 0 or vel_y != 0: last_packet_info = "Move"
        else: last_packet_info = "Idle"

        packet = {"player": p, "msg": msg_to_send, "hits": hit_data, "ability_cast": ability_to_cast} 
        server_data = n.send(packet)
        
        if server_data == "NETWORK_FAILURE": 
            n.disconnect(); run = False; break
            
        all_players = server_data.get("players", {})
        chat_messages = server_data.get("chat", [])
        last_walls = server_data.get("walls", {})
        
        if p.id in all_players:
            server_p = all_players[p.id]
            p.hp = server_p.hp     
            p.setPose(server_p.x, server_p.y)
            # Синхронизация способностей
            for key, ability in server_p.abilities.items():
                if key in p.abilities:
                    p.abilities[key].cooldown = ability.cooldown
                    p.abilities[key].duration = ability.duration
                else: 
                    p.abilities[key] = ability

        # --- DRAWING ---
        draw_modern_grid(win, scroll)
        
        for wall in last_walls.values():
            wall.draw(win, scroll)

        for p_id, player in all_players.items():
            skin_props = SKINS_DATA.get(player.skin_id, SKINS_DATA["DEFAULT"])
            player.color = skin_props.get("body_color", (255, 255, 255))
            player.trail_color = skin_props.get("trail_color", player.color)
            player.outline_color = skin_props.get("outline_color", (255, 255, 255))
            
            player.draw(win, scroll)
            
            screen_px = player.x - scroll[0] + player.width // 2
            screen_py = player.y - (scroll[1] + 20)
            
            if 0 < screen_px < WIDTH and 0 < screen_py < HEIGHT:
                display_name = getattr(player, 'nickname', f"Игрок {p_id}")
                draw_text_freetype(FONT_UI, display_name, (200, 200, 200), screen_px, screen_py - 20, center=True)

        if shoot_flash_timer > 0:
            flash_radius = 20 + shoot_flash_timer * 3
            flash_alpha = int(255 * (shoot_flash_timer / 5))
            flash_surf = pygame.Surface((flash_radius*2, flash_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 255, 0, flash_alpha), (flash_radius, flash_radius), flash_radius)
            win.blit(flash_surf, (flash_pos[0] - flash_radius, flash_pos[1] - flash_radius))

        win.blit(vignette_surf, (0, 0))

        # --- Мобильное управление (Отрисовка) ---
        ui_rects = draw_mobile_controls(p)

        # HUD / Chat
        chat_bg_height = 220
        chat_x, chat_y = 10, HEIGHT - chat_bg_height - 60
        chat_surf = pygame.Surface((360, chat_bg_height), pygame.SRCALPHA)
        chat_surf.fill((0, 0, 0, 150))
        win.blit(chat_surf, (chat_x, chat_y))
        pygame.draw.rect(win, C_ACCENT, (chat_x, chat_y, 360, chat_bg_height), 1)
        
        for i, msg in enumerate(chat_messages[-8:]):
            color = C_TEXT_MAIN
            if "[💀]" in msg or "[KILL]" in msg: color = C_DANGER
            if "[SERVER]" in msg: color = C_ACCENT
            draw_text_freetype(FONT_UI, msg, color, chat_x + 10, chat_y + 10 + i * 25)

        input_y = HEIGHT - 50
        input_w = 350
        if typing_mode:
            pygame.draw.rect(win, (20, 20, 20), (10, input_y, input_w, 30))
            pygame.draw.rect(win, C_DANGER, (10, input_y, input_w, 30), 2)
            draw_text_freetype(FONT_UI, current_message + "_", C_DANGER, 15, input_y + 5)
        # Удалили надпись "Нажми ENTER для чата"
        # else:
        #     draw_text_freetype(FONT_UI, "Нажми ENTER для чата", (120, 120, 120), 10, input_y + 5)

        draw_hud(p, int(clock.get_fps()))
        
        # --- DRAW DEBUG OVERLAY ---
        debug_ui.draw(win, p, n, int(clock.get_fps()), scroll, last_packet_info)

        mx, my = pygame.mouse.get_pos()
        draw_custom_cursor(mx, my)

        pygame.display.update()

def main_app():
    app_running = True
    while app_running:
        result = main_menu()
        if result == "QUIT": 
            app_running = False
        elif isinstance(result, tuple):
            server_ip, nickname, selected_skin = result 
            game_loop(server_ip, nickname, selected_skin) 
    pygame.quit()
    
def display_error_message(message):
    temp_surf = win.copy()
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) 
    temp_surf.blit(overlay, (0, 0))
    FONT_TITLE.render_to(temp_surf, (WIDTH//2 - 200, HEIGHT//2 - 50), "ERROR", C_DANGER)
    FONT_HUD.render_to(temp_surf, (WIDTH//2 - 200, HEIGHT//2 + 50), message, C_TEXT_MAIN)
    win.blit(temp_surf, (0, 0))
    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN or event.type == pygame.QUIT: waiting = False

if __name__ == "__main__":
    main_app()