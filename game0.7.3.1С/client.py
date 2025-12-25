import pygame
import random
import math
import json
import os
import time
import threading 
from network import Network, LANScanner 
import server
import pygame.freetype 
# from UI import DebugInterface, NeonButton, NeonInput, draw_modern_grid, draw_custom_cursor, draw_cyber_health, draw_text_freetype
from UI import *

# --- Инициализация ---
pygame.init()
pygame.freetype.init()

# --- КОНФИГУРАЦИЯ ---
WIDTH = 900
HEIGHT = 700
MAP_WIDTH = 2000
MAP_HEIGHT = 2000

# Включаем сглаживание и аппаратное ускорение, если возможно
win = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("Sahur Shooter: Ultimate UI")

# --- ЦВЕТОВАЯ ПАЛИТРА (CYBERPUNK) ---
C_BG_DEEP     = (5, 5, 10)       # Почти черный
C_BG_LIGHT    = (20, 20, 35)     # Светлее для полей
C_NEON_CYAN   = (0, 255, 240)    # Основной акцент
C_NEON_PINK   = (255, 0, 110)    # Вторичный акцент (враги/выход)
C_NEON_GREEN  = (57, 255, 20)    # Успех
C_TEXT_MAIN   = (240, 245, 255)  # Белый с оттенком
C_TEXT_DIM    = (100, 110, 130)  # Серый текст
C_OVERLAY     = (0, 0, 0, 120)   # Затемнение

# --- ШРИФТЫ ---
# Пытаемся загрузить красивые системные шрифты, иначе дефолт
def get_font(name, size, bold=False):
    try:
        return pygame.freetype.SysFont(name, size, bold=bold)
    except:
        return pygame.freetype.SysFont("arial", size, bold=bold)

# FONT_BIG   = get_font("impact, verendana, arial black", 70)
# FONT_MED   = get_font("segoe ui, roboto, arial", 24)
# FONT_SMALL = get_font("consolas, menlo", 14)
# FONT_CHOICES = ["arial", "consolas"]
FONT_CHOICES = ["arial", "dejavusans", "verdana"] 
try:
    FONT_UI = pygame.freetype.Font("arial", 16)
    FONT_HUD = pygame.freetype.Font("arial", 20)
    FONT_TITLE = pygame.freetype.Font("arial", 70)
    FONT_DEBUG = pygame.freetype.SysFont("consolas", 14) # Моноширинный шрифт для дебага
    FONT_BIG = pygame.freetype.Font("arial", 70)
    FONT_MED = pygame.freetype.Font("arial", 24)
    FONT_SMALL = pygame.freetype.Font("arial", 14)
except:
    FONT_UI = pygame.freetype.SysFont(FONT_CHOICES, 16)
    FONT_HUD = pygame.freetype.SysFont(FONT_CHOICES, 20, bold=True)
    FONT_TITLE = pygame.freetype.SysFont(FONT_CHOICES, 70, bold=True)
    FONT_DEBUG = pygame.freetype.SysFont("courier", 14)
    FONT_BIG = pygame.freetype.SysFont(FONT_CHOICES, 70, bold=True)
    FONT_MED = pygame.freetype.SysFont(FONT_CHOICES, 24, bold=True)
    FONT_SMALL = pygame.freetype.SysFont(FONT_CHOICES, 14)

C_BG_DEEP = (5, 5, 12)  
C_NEON_CYAN = (0, 255, 255)
C_NEON_PINK = (255, 0, 150)
C_TEXT = (220, 240, 255)
C_TEXT_MAIN = (240, 240, 240)
C_ACCENT = (0, 255, 255)
C_DANGER = (255, 50, 50)
C_BG = (10, 10, 20)
C_GRID_DIM = (30, 30, 50)
C_GRID_BRIGHT = (60, 60, 100)

# --- ГРАФИЧЕСКИЕ ЭФФЕКТЫ (ENGINE) ---

class ParticleSystem:
    """Создает красивые летающие частицы на фоне"""
    def __init__(self, count=50):
        self.particles = []
        for _ in range(count):
            self.particles.append(self._create_particle())

    def _create_particle(self):
        return {
            'x': random.randint(0, WIDTH),
            'y': random.randint(0, HEIGHT),
            'size': random.randint(1, 3),
            'speed': random.uniform(0.2, 1.0),
            'alpha': random.randint(50, 200),
            'color': random.choice([C_NEON_CYAN, C_NEON_PINK, (255,255,255)])
        }

    def update_and_draw(self, surface):
        for p in self.particles:
            p['y'] -= p['speed']
            p['alpha'] -= 0.5
            if p['y'] < 0 or p['alpha'] <= 0:
                new_p = self._create_particle()
                p.update(new_p)
                p['y'] = HEIGHT # Спавн снизу
            
            # Рисуем с прозрачностью
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p['color'], int(p['alpha'])), (p['size'], p['size']), p['size'])
            surface.blit(s, (p['x'], p['y']))

# --- ИГРОВЫЕ КЛАССЫ (SKINS и т.д.) ---
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

# --- ИГРОВОЙ ЦИКЛ (CLIENT) ---

def main_menu():
    clock = pygame.time.Clock()
    
    # Данные
    user_ip = "127.0.0.1"
    user_nick = f"Sahur_{random.randint(10,99)}"
    skin_list = ["DEFAULT", "RED_CYBORG", "GOLD_ELITE", "TOXIC_GREEN", "VOID_WALKER"]
    skin_idx = 0
    
    # Состояние
    active_input = None # "NICK" or "IP"
    menu_state = "MAIN" # MAIN, SERVERS
    
    # UI Элементы
    particles = ParticleSystem(60)
    
    # Создаем кнопки (размещаем их по центру с отступами)
    cx = WIDTH // 2
    cy = HEIGHT // 2
    
    btn_connect = NeonButton("CONNECT DIRECT", cx - 130, cy + 80, 260, 50, C_NEON_CYAN)
    btn_search  = NeonButton("SCAN SERVERS", cx - 130, cy + 140, 260, 50, C_NEON_GREEN)
    btn_offline = NeonButton("OFFLINE / HOST", cx - 130, cy + 200, 260, 50, C_NEON_PINK)
    
    input_nick = NeonInput("CODENAME", user_nick, cx - 150, cy - 100)
    input_ip   = NeonInput("TARGET IP", user_ip, cx - 150, cy - 20)
    
    found_servers = []
    scan_status = ""

    while True:
        dt = clock.tick(60)
        ticks = pygame.time.get_ticks()
        mx, my = pygame.mouse.get_pos()
        
        # --- 1. ОТРИСОВКА ФОНА ---
        win.fill(C_BG_DEEP)
        
        # Сетка в перспективе (простая анимация)
        grid_offset = (ticks * 0.05) % 50
        for x in range(0, WIDTH, 50):
            pygame.draw.line(win, (30, 30, 50), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 50):
            alpha_y = int(y + grid_offset) % HEIGHT
            pygame.draw.line(win, (30, 30, 50), (0, alpha_y), (WIDTH, alpha_y))
            
        particles.update_and_draw(win)
        
        # --- 2. ОТРИСОВКА МЕНЮ ---
        
        # Заголовок
        title_surf, title_rect = FONT_BIG.render("Sahur STRIKE", C_NEON_CYAN)
        # Эффект тени заголовка
        shadow_surf, _ = FONT_BIG.render("Sahur STRIKE", (C_NEON_PINK))
        win.blit(shadow_surf, (WIDTH//2 - title_rect.width//2 + 4, 84))
        win.blit(title_surf, (WIDTH//2 - title_rect.width//2, 80))
        
        if menu_state == "MAIN":
            # Inputs
            input_nick.value = user_nick
            input_ip.value = user_ip
            input_nick.active = (active_input == "NICK")
            input_ip.active = (active_input == "IP")
            
            input_nick.update(mx, my)
            input_ip.update(mx, my)
            
            input_nick.draw(win, ticks)
            input_ip.draw(win, ticks)
            
            # Skin Selector (Simple Text Switcher)
            skin_txt = f"< SKIN: {skin_list[skin_idx]} >"
            skin_col = C_NEON_PINK
            skin_surf, skin_rect = FONT_MED.render(skin_txt, skin_col)
            skin_rect.center = (WIDTH//2, cy + 40)
            
            # Hover effect on skin text
            if skin_rect.collidepoint(mx, my):
                pygame.draw.rect(win, (255, 255, 255, 20), skin_rect.inflate(20, 10), border_radius=5)
            win.blit(skin_surf, skin_rect)

            # Buttons
            btn_connect.update(mx, my)
            btn_search.update(mx, my)
            btn_offline.update(mx, my)
            
            btn_connect.draw(win)
            btn_search.draw(win)
            btn_offline.draw(win)
            
        elif menu_state == "SERVERS":
            # Окно списка серверов
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,150))
            win.blit(overlay, (0,0))
            
            panel_rect = pygame.Rect(100, 100, WIDTH-200, HEIGHT-200)
            pygame.draw.rect(win, C_BG_LIGHT, panel_rect, border_radius=20)
            pygame.draw.rect(win, C_NEON_CYAN, panel_rect, 2, border_radius=20)
            
            FONT_MED.render_to(win, (panel_rect.x + 20, panel_rect.y + 20), "FOUND SERVERS:", C_NEON_CYAN)
            FONT_SMALL.render_to(win, (panel_rect.x + 240, panel_rect.y + 25), scan_status, C_TEXT_DIM)
            
            y_off = 80
            for srv in found_servers:
                row_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + y_off, panel_rect.w - 40, 50)
                is_hover = row_rect.collidepoint(mx, my)
                col = (40, 60, 80) if is_hover else (30, 30, 40)
                
                pygame.draw.rect(win, col, row_rect, border_radius=10)
                if is_hover:
                    pygame.draw.rect(win, C_NEON_GREEN, row_rect, 1, border_radius=10)
                
                txt = f"{srv['name']}  |  {srv['ip']}  |  Players: {srv['players']}"
                FONT_SMALL.render_to(win, (row_rect.x + 20, row_rect.y + 18), txt, C_TEXT_MAIN)
                y_off += 60
            
            # Back Button
            btn_back = NeonButton("BACK", WIDTH//2 - 100, panel_rect.bottom - 70, 200, 40, C_DANGER)
            btn_refresh = NeonButton("REFRESH", WIDTH//2 - 100, panel_rect.bottom - 120, 200, 40, C_NEON_CYAN)
            
            btn_back.update(mx, my)
            btn_refresh.update(mx, my)
            btn_back.draw(win)
            btn_refresh.draw(win)

        # Scanlines overlay
        # draw_scanlines(win)

        pygame.display.flip()

        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_state == "MAIN":
                    if input_nick.rect.collidepoint(mx, my): active_input = "NICK"
                    elif input_ip.rect.collidepoint(mx, my): active_input = "IP"
                    else: active_input = None
                    
                    if skin_rect.collidepoint(mx, my):
                         skin_idx = (skin_idx + 1) % len(skin_list)
                    
                    if btn_connect.rect.collidepoint(mx, my):
                        return (user_ip, user_nick, skin_list[skin_idx], False)
                    if btn_offline.rect.collidepoint(mx, my):
                        return ("127.0.0.1", user_nick, skin_list[skin_idx], True)
                    if btn_search.rect.collidepoint(mx, my):
                        menu_state = "SERVERS"
                        scan_status = "Scanning..."
                        # Отрисуем один кадр перед зависанием скана
                        pygame.display.flip()
                        found_servers = LANScanner.scan(0.5)
                        scan_status = f"Found {len(found_servers)}"

                elif menu_state == "SERVERS":
                    # Проверка клика по серверу
                    y_off_check = 80
                    for srv in found_servers:
                        r = pygame.Rect(panel_rect.x + 20, panel_rect.y + y_off_check, panel_rect.w - 40, 50)
                        if r.collidepoint(mx, my):
                            return (srv['ip'], user_nick, skin_list[skin_idx], False)
                        y_off_check += 60
                    
                    if btn_back.rect.collidepoint(mx, my): menu_state = "MAIN"
                    if btn_refresh.rect.collidepoint(mx, my):
                        scan_status = "Scanning..."
                        pygame.display.flip()
                        found_servers = LANScanner.scan(0.5)
                        scan_status = f"Found {len(found_servers)}"

            if event.type == pygame.KEYDOWN:
                if active_input:
                    if event.key == pygame.K_BACKSPACE:
                        if active_input == "NICK": user_nick = user_nick[:-1]
                        else: user_ip = user_ip[:-1]
                    elif event.key == pygame.K_TAB:
                        active_input = "IP" if active_input == "NICK" else "NICK"
                    elif event.unicode.isprintable():
                        if active_input == "NICK" and len(user_nick) < 12: user_nick += event.unicode
                        if active_input == "IP" and len(user_ip) < 15: user_ip += event.unicode

# --- ИГРОВОЙ ПРОЦЕСС (GAME LOOP) ---
# Остается почти таким же, но с красивым UI

def game_loop(server_ip, nickname, selected_skin, is_local_host):
    # Запуск сервера если нужно
    server_thread = None
    if is_local_host:
        server_thread = threading.Thread(target=server.start_server_instance, args=("127.0.0.1",))
        server_thread.daemon = True
        server_thread.start()
        time.sleep(1)

    try:
        n = Network(server_ip)
        p = n.getP()
    except:
        return # Вернуться в меню, если ошибка

    if not p: return 
    
    # Init Setup
    p.nickname = nickname
    p.skin_id = selected_skin 
    n.send({"type": "INIT", "skin": selected_skin, "nick": nickname, "player": p})
    
    clock = pygame.time.Clock()
    run = True
    
    # Камера
    scroll_x = p.x - WIDTH // 2 + p.width // 2
    scroll_y = p.y - HEIGHT // 2 + p.height // 2
    
    # Переменные
    last_walls = {}
    all_players = {}
    chat_messages = []
    
    typing_mode = False
    current_message = ""
    shoot_flash = 0
    flash_pos = (0,0)
    
    displayed_hp = p.hp
    
    # --- DEBUG INIT ---
    debug_ui = DebugInterface()
    
    pygame.mouse.set_visible(False) # Скрываем обычный курсор

    while run:
        dt = clock.tick(60)
        
        # --- ЛОГИКА КАМЕРЫ ---
        target_x = p.x - WIDTH // 2 + p.width // 2
        target_y = p.y - HEIGHT // 2 + p.height // 2
        scroll_x += (target_x - scroll_x) * 0.1 # Плавнее
        scroll_y += (target_y - scroll_y) * 0.1
        scroll = (scroll_x, scroll_y)
        
        # --- СОБЫТИЯ ---
        msg_to_send = None
        ability_to_cast = None
        
        if p.hp > 0:
            if displayed_hp > p.hp:
                # Плавное "утекание" здоровья (эффект задержки)
                displayed_hp -= (displayed_hp - p.hp) * 0.1 
            elif displayed_hp < p.hp:
                # Быстрое восстановление (если здоровье восстановилось)
                displayed_hp += 1 
            # Ограничение
            displayed_hp = max(p.hp, displayed_hp)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if typing_mode: typing_mode = False
                    else: run = False
                elif event.key == pygame.K_RETURN:
                    if typing_mode:
                        if current_message: msg_to_send = current_message
                        if len(current_message) > 0: 
                            # --- ПЕРЕХВАТ КОМАНДЫ ДЕБАГА ---
                            if current_message.strip() == "/debug":
                                is_active = debug_ui.toggle()
                                status = "ON" if is_active else "OFF"
                                # Локальное сообщение в чат (опционально, но здесь не добавляем в лог сервера)
                                print(f"Debug mode {status}")
                                msg_to_send = None # Не отправляем на сервер
                            else:
                                msg_to_send = current_message
                        current_message = ""; typing_mode = False
                    else: typing_mode = True
                elif typing_mode:
                    if event.key == pygame.K_BACKSPACE: current_message = current_message[:-1]
                    elif len(current_message) < 40: current_message += event.unicode
                elif not typing_mode:
                    if event.key == pygame.K_1 and p.cast_ability("shield"): ability_to_cast = {"key": "shield"}
                    if event.key == pygame.K_2 and p.cast_ability("wall"): ability_to_cast = {"key": "wall"}

            if event.type == pygame.MOUSEBUTTONDOWN and not typing_mode:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    p.shoot(mx, my, scroll)
                    shoot_flash = 5; flash_pos = (mx, my)

        # --- ДВИЖЕНИЕ И СЕТЬ ---
        if not typing_mode and p.hp > 0: p.move(MAP_WIDTH, MAP_HEIGHT)
        
        # Предсказание попаданий
        hit_data = []
        # (Код коллизий сокращен для краткости, он тот же что и раньше)
        for bullet in list(p.bullets):
            br = pygame.Rect(bullet[0]-5, bullet[1]-5, 10, 10)
            hit = False
            for w in last_walls.values(): 
                if br.colliderect(w.rect): hit = True; break
            if hit: p.deleteBullet(bullet); continue
            for pid, op in all_players.items():
                if pid != p.id and op.hp > 0 and op.abilities["shield"].duration <= 0:
                    if br.colliderect(op.rect):
                        p.deleteBullet(bullet); hit_data.append({"target_id": pid, "damage": 10})
                        break

        # last_packet_info = "None"
        # if ability_to_cast: last_packet_info = f"Cast {ability_to_cast['key']}"
        # elif msg_to_send: last_packet_info = "Chat Message"
        # elif hit_data: last_packet_info = f"Hit {len(hit_data)} targets"
        # else: last_packet_info = "Move/Idle"
        
        # Отправка пакета
        # packet = {"player": p, "msg": msg_to_send, "hits": hit_data, "ability_cast": ability_to_cast} 
        # packet = {"msg": msg_to_send, "hits": hit_data, "ability_cast": ability_to_cast} 
        # print(packet)
        
        # print(hit_data)
        packet = {
            "type": "UPDATE",  # Используем единый тип пакета, например, "UPDATE"
            "player": p, 
        }

        # 2. Динамически добавляем дополнительные поля, если они содержат данные
        # Проверка hits:
        if hit_data: # hit_data - это список, если он не пуст ([]), то True
            packet["hits"] = hit_data

        # Проверка msg_to_send:
        if msg_to_send: # msg_to_send - это строка, если она не пуста ("") или не None, то True
            packet["msg"] = msg_to_send
            
        # Проверка ability_to_cast:
        if ability_to_cast is not None: # ability_to_cast - объект или None
            packet["ability_cast"] = ability_to_cast

        # 3. Отправляем динамически сформированный пакет
        # print(f"Sending packet with keys: {list(packet.keys())}")
        server_data = n.send(packet)
        
        if server_data == "NETWORK_FAILURE": 
            n.disconnect(); run = False; break
            
        all_players = server_data.get("players", {})
        # chat_messages = server_data.get("chat", [])
        last_walls = server_data.get("walls", {})
        
        if "chat" in server_data:
            new_chat_messages = server_data["chat"]
            # Используем extend, чтобы добавить НОВЫЕ сообщения к существующему списку
            chat_messages.extend(new_chat_messages)
            # Ограничиваем размер списка чата (на всякий случай)
            if len(chat_messages) > 20: 
                chat_messages = chat_messages[-20:]
        
        # Синхронизация себя
        if p.id in all_players:
            srv_p = all_players[p.id]
            p.hp = srv_p.hp
            p.setPose(srv_p.x, srv_p.y)
            # Синхронизация абилок
            for k, ab in srv_p.abilities.items():
                if k in p.abilities:
                    p.abilities[k].cooldown = ab.cooldown
                    p.abilities[k].duration = ab.duration

        # --- ОТРИСОВКА ИГРЫ (КРАСИВАЯ) ---
        win.fill(C_BG_DEEP)
        
        draw_modern_grid(win, scroll)
            
        # Стены (Неоновые)
        for w in last_walls.values():
            screen_x = w.x - scroll[0]
            screen_y = w.y - scroll[1]
            # Glow
            s = pygame.Surface((w.width+20, w.height+20), pygame.SRCALPHA)
            pygame.draw.rect(s, (100, 100, 255, 50), (10,10,w.width,w.height), border_radius=5)
            pygame.draw.rect(s, (150, 150, 255), (10,10,w.width,w.height), 2, border_radius=5)
            win.blit(s, (screen_x-10, screen_y-10))

        # Игроки
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

        # Эффект выстрела (вспышка)
        if shoot_flash > 0:
            shoot_flash -= 1
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 100, 100), (30,30), 20 + shoot_flash*2)
            win.blit(s, (flash_pos[0]-30, flash_pos[1]-30))

        # --- HUD (КРАСИВЫЙ) ---
        
        # 1. HP Bar (снизу по центру, большой)
        # bar_w = 400
        # bar_x = WIDTH//2 - bar_w//2
        # bar_y = HEIGHT - 50
        
        # # Подложка
        # pygame.draw.rect(win, (20, 20, 20), (bar_x, bar_y, bar_w, 20), border_radius=10)
        # # HP
        # hp_pct = max(0, p.hp / 100)
        # hp_col = C_NEON_GREEN if hp_pct > 0.4 else C_DANGER
        # pygame.draw.rect(win, hp_col, (bar_x, bar_y, int(bar_w*hp_pct), 20), border_radius=10)
        # # Рамка
        # pygame.draw.rect(win, (255, 255, 255), (bar_x, bar_y, bar_w, 20), 2, border_radius=10)
        # FONT_SMALL.render_to(win, (bar_x + bar_w//2 - 20, bar_y + 2), f"{p.hp}%", (0,0,0))
        
        bar_w = 300
        bar_h = 35
        bar_x = WIDTH // 2 - bar_w // 2
        bar_y = HEIGHT - 60
        
        draw_cyber_health(win, bar_x, bar_y, bar_w, bar_h, p.hp, 100, displayed_hp)
        
        # 2. Abilities (Слева и справа от HP)
        # Shield (Key 1)
        sh_cd = p.abilities["shield"].cooldown / p.abilities["shield"].cooldown_max
        sh_col = (50, 50, 50) if sh_cd > 0 else C_NEON_CYAN
        pygame.draw.circle(win, sh_col, (bar_x - 40, bar_y + 10), 25)
        pygame.draw.circle(win, (255,255,255), (bar_x - 40, bar_y + 10), 25, 2)
        FONT_HUD.render_to(win, (bar_x - 50, bar_y), "1", (255,255,255))
        if sh_cd > 0: # Сектор кулдауна (упрощенно квадрат)
            h = int(50 * sh_cd)
            pygame.draw.rect(win, (0,0,0,150), (bar_x - 65, bar_y + 35 - h, 50, h))

        # Wall (Key 2)
        w_cd = p.abilities["wall"].cooldown / p.abilities["wall"].cooldown_max
        w_col = (50, 50, 50) if w_cd > 0 else C_NEON_PINK
        pygame.draw.circle(win, w_col, (bar_x + bar_w + 40, bar_y + 10), 25)
        pygame.draw.circle(win, (255,255,255), (bar_x + bar_w + 40, bar_y + 10), 25, 2)
        FONT_HUD.render_to(win, (bar_x + bar_w + 32, bar_y), "2", (255,255,255))

        # 3. Chat
        chat_x = 20
        chat_y = HEIGHT - 200
        for i, msg in enumerate(chat_messages[-6:]):
            col = C_DANGER if "KILL" in msg else C_TEXT_MAIN
            FONT_SMALL.render_to(win, (chat_x, chat_y + i*20), msg, col)
            
        if typing_mode:
            pygame.draw.rect(win, (0,0,0,200), (10, HEIGHT-80, 300, 30))
            pygame.draw.rect(win, C_NEON_CYAN, (10, HEIGHT-80, 300, 30), 2)
            FONT_SMALL.render_to(win, (15, HEIGHT-75), current_message + "_", C_NEON_CYAN)
            
        debug_ui.draw(win, p, all_players, int(clock.get_fps()), n)

        # Кастомный курсор
        mx, my = pygame.mouse.get_pos()
        draw_custom_cursor(mx, my)
        
        # draw_scanlines(win)
        pygame.display.flip()

    n.disconnect()
    pygame.mouse.set_visible(True)
    if is_local_host:
        server.server_running = False

def main_app():
    while True:
        res = main_menu()
        if res == "QUIT": break
        elif isinstance(res, tuple):
            game_loop(res[0], res[1], res[2], res[3])
    pygame.quit()

if __name__ == "__main__":
    main_app()