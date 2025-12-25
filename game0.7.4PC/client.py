import pygame
import random

# import math
import json
import os
import time
import threading 
from network import Network, LANScanner 
import server
# import pygame.freetype 
from UI import *

# --- Инициализация ---
pygame.init()
pygame.freetype.init()

# --- КОНФИГУРАЦИЯ И НАСТРОЙКИ ---
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "width": 1280,
    "height": 720,
    "fullscreen": False,
    "nick": f"Player_{random.randint(10,99)}",
    "ip": "127.0.0.1",
    "skin_idx": 0
}

# Глобальные переменные экрана (будут обновляться)
WIDTH = 1280
HEIGHT = 720
win = None
MAP_WIDTH = 2000
MAP_HEIGHT = 2000

RESOLUTIONS = [
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080)
]

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            # Merge with defaults in case of missing keys
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data: data[k] = v
            return data
    except:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

def init_display(settings):
    global win, WIDTH, HEIGHT
    WIDTH = settings["width"]
    HEIGHT = settings["height"]
    
    flags = pygame.DOUBLEBUF | pygame.HWSURFACE
    if settings["fullscreen"]:
        flags |= pygame.FULLSCREEN
    else:
        flags |= pygame.RESIZABLE
        
    try:
        win = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    except:
        # Если разрешение не поддерживается, сброс на безопасное
        print("Ошибка установки разрешения, сброс на 800x600")
        WIDTH, HEIGHT = 800, 600
        win = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    
    pygame.display.set_caption("Sahur Shooter: Ultimate UI")
    return win

# --- ГРАФИЧЕСКИЕ ЭФФЕКТЫ ---
class ParticleSystem:
    def __init__(self, count=50):
        self.particles = []
        self.count = count
        self.reinit()

    def reinit(self):
        self.particles = []
        for _ in range(self.count):
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
            
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p['color'], int(p['alpha'])), (p['size'], p['size']), p['size'])
            surface.blit(s, (p['x'], p['y']))

# --- ЗАГРУЗКА СКИНОВ ---
SKINS_DATA = {}
def load_skins():
    global SKINS_DATA
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "Config", "skins.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding='utf-8') as f:
                SKINS_DATA = json.load(f)
        else: raise Exception("No file")
    except:
        SKINS_DATA = {
            "DEFAULT": {"body_color": [0, 255, 255], "trail_color": [0, 200, 200], "outline_color": [255, 255, 255]}
        }
load_skins()

# --- МЕНЮ НАСТРОЕК ---
def settings_menu(current_settings):
    clock = pygame.time.Clock()
    
    # Локальные переменные для редактирования
    temp_w = current_settings["width"]
    temp_h = current_settings["height"]
    temp_full = current_settings["fullscreen"]
    
    # Поиск текущего индекса разрешения
    res_idx = 0
    if (temp_w, temp_h) in RESOLUTIONS:
        res_idx = RESOLUTIONS.index((temp_w, temp_h))
    
    while True:
        dt = clock.tick(60)
        WIDTH, HEIGHT = win.get_size() # Обновляем для отрисовки
        cx, cy = WIDTH // 2, HEIGHT // 2
        
        mx, my = pygame.mouse.get_pos()
        
        win.fill(C_BG_DEEP)
        
        # Заголовок
        title_surf, title_rect = FONT_BIG.render("SETTINGS", C_NEON_CYAN)
        title_rect.center = (cx, 100)
        win.blit(title_surf, title_rect)
        
        # 1. Разрешение
        res_text = f"{RESOLUTIONS[res_idx][0]} x {RESOLUTIONS[res_idx][1]}"
        FONT_MED.render_to(win, (cx - 150, cy - 50), "RESOLUTION:", C_TEXT_DIM)
        
        # Стрелки выбора
        btn_left = pygame.Rect(cx + 20, cy - 55, 30, 30)
        btn_right = pygame.Rect(cx + 180, cy - 55, 30, 30)
        
        pygame.draw.rect(win, C_BG_LIGHT, btn_left, border_radius=5)
        pygame.draw.rect(win, C_BG_LIGHT, btn_right, border_radius=5)
        FONT_MED.render_to(win, (btn_left.x + 8, btn_left.y + 2), "<", C_NEON_PINK if btn_left.collidepoint(mx,my) else C_TEXT_MAIN)
        FONT_MED.render_to(win, (btn_right.x + 8, btn_right.y + 2), ">", C_NEON_PINK if btn_right.collidepoint(mx,my) else C_TEXT_MAIN)
        
        FONT_MED.render_to(win, (cx + 60, cy - 50), res_text, C_NEON_CYAN)
        
        # 2. Полноэкранный режим
        FONT_MED.render_to(win, (cx - 150, cy + 20), "FULLSCREEN:", C_TEXT_DIM)
        check_rect = pygame.Rect(cx + 60, cy + 20, 30, 30)
        pygame.draw.rect(win, C_BG_LIGHT, check_rect, border_radius=5)
        pygame.draw.rect(win, C_NEON_CYAN, check_rect, 2, border_radius=5)
        if temp_full:
            pygame.draw.rect(win, C_NEON_GREEN, (check_rect.x+5, check_rect.y+5, 20, 20), border_radius=3)
        
        # Кнопки действия
        btn_apply = NeonButton("APPLY & SAVE", cx - 130, cy + 100, 260, 50, C_NEON_GREEN)
        btn_cancel = NeonButton("BACK", cx - 130, cy + 160, 260, 50, C_DANGER)
        
        btn_apply.update(mx, my)
        btn_cancel.update(mx, my)
        btn_apply.draw(win)
        btn_cancel.draw(win)
        
        draw_custom_cursor(win, mx, my)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Resolution Arrows
                    if btn_left.collidepoint(mx, my):
                        res_idx = (res_idx - 1) % len(RESOLUTIONS)
                    if btn_right.collidepoint(mx, my):
                        res_idx = (res_idx + 1) % len(RESOLUTIONS)
                    
                    # Fullscreen Toggle
                    if check_rect.collidepoint(mx, my):
                        temp_full = not temp_full
                        
                    # Apply
                    if btn_apply.rect.collidepoint(mx, my):
                        new_w, new_h = RESOLUTIONS[res_idx]
                        current_settings["width"] = new_w
                        current_settings["height"] = new_h
                        current_settings["fullscreen"] = temp_full
                        save_settings(current_settings)
                        # Re-init display
                        init_display(current_settings)
                        return "APPLY" # Возвращаемся в меню
                        
                    # Cancel
                    if btn_cancel.rect.collidepoint(mx, my):
                        return "BACK"

# --- ГЛАВНОЕ МЕНЮ ---

def main_menu():
    global WIDTH, HEIGHT
    settings = load_settings()
    init_display(settings)
    
    clock = pygame.time.Clock()
    
    # Данные из настроек
    user_ip = settings.get("ip", "127.0.0.1")
    user_nick = settings.get("nick", f"Sahur_{random.randint(10,99)}")
    skin_idx = settings.get("skin_idx", 0)
    
    skin_list = ["DEFAULT", "RED_CYBORG", "GOLD_ELITE", "TOXIC_GREEN", "VOID_WALKER"]
    
    # Состояние
    active_input = None 
    menu_state = "MAIN" # MAIN, SERVERS
    
    particles = ParticleSystem(60)
    
    # UI Элементы (создаем один раз, координаты обновляем в цикле)
    btn_connect = NeonButton("CONNECT DIRECT", 0,0, 260, 50, C_NEON_CYAN)
    btn_search  = NeonButton("SCAN SERVERS", 0,0, 260, 50, C_NEON_GREEN)
    btn_offline = NeonButton("OFFLINE / HOST", 0,0, 260, 50, C_NEON_PINK)
    btn_settings = NeonButton("SETTINGS", 0,0, 260, 50, (100, 100, 255))
    
    input_nick = NeonInput("CODENAME", user_nick, 0,0)
    input_ip   = NeonInput("TARGET IP", user_ip, 0,0)
    
    found_servers = []
    scan_status = ""

    while True:
        dt = clock.tick(60)
        ticks = pygame.time.get_ticks()
        WIDTH, HEIGHT = win.get_size() # Всегда берем актуальный размер
        cx, cy = WIDTH // 2, HEIGHT // 2
        
        mx, my = pygame.mouse.get_pos()
        
        # Обновление позиций элементов (для ресайза)
        btn_connect.rect.topleft = (cx - 130, cy + 60)
        btn_search.rect.topleft  = (cx - 130, cy + 120)
        btn_offline.rect.topleft = (cx - 130, cy + 180)
        btn_settings.rect.topleft = (WIDTH - 280, HEIGHT - 70) # В углу
        
        input_nick.rect.topleft = (cx - 150, cy - 100)
        input_ip.rect.topleft   = (cx - 150, cy - 20)
        
        # --- 1. ОТРИСОВКА ФОНА ---
        win.fill(C_BG_DEEP)
        
        # Сетка
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
        shadow_surf, _ = FONT_BIG.render("Sahur STRIKE", (C_NEON_PINK))
        win.blit(shadow_surf, (cx - title_rect.width//2 + 4, 84))
        win.blit(title_surf, (cx - title_rect.width//2, 80))
        
        if menu_state == "MAIN":
            input_nick.value = user_nick
            input_ip.value = user_ip
            input_nick.active = (active_input == "NICK")
            input_ip.active = (active_input == "IP")
            
            input_nick.update(mx, my)
            input_ip.update(mx, my)
            input_nick.draw(win, ticks)
            input_ip.draw(win, ticks)
            
            skin_txt = f"< SKIN: {skin_list[skin_idx]} >"
            skin_surf, skin_rect = FONT_MED.render(skin_txt, C_NEON_PINK)
            skin_rect.center = (cx, cy + 40)
            if skin_rect.collidepoint(mx, my):
                pygame.draw.rect(win, (255, 255, 255, 20), skin_rect.inflate(20, 10), border_radius=5)
            win.blit(skin_surf, skin_rect)

            btn_connect.update(mx, my)
            btn_search.update(mx, my)
            btn_offline.update(mx, my)
            btn_settings.update(mx, my)
            
            btn_connect.draw(win)
            btn_search.draw(win)
            btn_offline.draw(win)
            btn_settings.draw(win)
            
        elif menu_state == "SERVERS":
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
                if is_hover: pygame.draw.rect(win, C_NEON_GREEN, row_rect, 1, border_radius=10)
                
                txt = f"{srv['name']}  |  {srv['ip']}  |  Players: {srv['players']}"
                FONT_SMALL.render_to(win, (row_rect.x + 20, row_rect.y + 18), txt, C_TEXT_MAIN)
                y_off += 60
            
            btn_back = NeonButton("BACK", cx - 100, panel_rect.bottom - 70, 200, 40, C_DANGER)
            btn_refresh = NeonButton("REFRESH", cx - 100, panel_rect.bottom - 120, 200, 40, C_NEON_CYAN)
            
            btn_back.update(mx, my)
            btn_refresh.update(mx, my)
            btn_back.draw(win)
            btn_refresh.draw(win)

        draw_custom_cursor(win, mx, my)
        pygame.display.flip()

        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            
            # Сохранение данных при выходе или смене
            settings["nick"] = user_nick
            settings["ip"] = user_ip
            settings["skin_idx"] = skin_idx
            save_settings(settings)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_state == "MAIN":
                    if input_nick.rect.collidepoint(mx, my): active_input = "NICK"
                    elif input_ip.rect.collidepoint(mx, my): active_input = "IP"
                    else: active_input = None
                    
                    if skin_rect.collidepoint(mx, my):
                         skin_idx = (skin_idx + 1) % len(skin_list)
                    
                    if btn_settings.rect.collidepoint(mx, my):
                        res = settings_menu(settings)
                        if res == "QUIT": return "QUIT"
                        # Переинициализация частиц при смене разрешения
                        particles.reinit()
                        
                    if btn_connect.rect.collidepoint(mx, my):
                        return (user_ip, user_nick, skin_list[skin_idx], False)
                    if btn_offline.rect.collidepoint(mx, my):
                        return ("127.0.0.1", user_nick, skin_list[skin_idx], True)
                    if btn_search.rect.collidepoint(mx, my):
                        menu_state = "SERVERS"
                        scan_status = "Scanning..."
                        pygame.display.flip()
                        found_servers = LANScanner.scan(0.5)
                        scan_status = f"Found {len(found_servers)}"

                elif menu_state == "SERVERS":
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


def game_loop(server_ip, nickname, selected_skin, is_local_host):
    global WIDTH, HEIGHT
    # Запуск сервера
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
        return 
    
    if not p: return 
    
    p.nickname = nickname
    p.skin_id = selected_skin 
    n.send({"type": "INIT", "skin": selected_skin, "nick": nickname, "player": p})
    
    clock = pygame.time.Clock()
    run = True
    
    # Камера
    scroll_x = p.x - WIDTH // 2 + p.width // 2
    scroll_y = p.y - HEIGHT // 2 + p.height // 2
    
    last_walls = {}
    all_players = {}
    chat_messages = []
    
    typing_mode = False
    current_message = ""
    shoot_flash = 0
    flash_pos = (0,0)
    displayed_hp = p.hp
    debug_ui = DebugInterface()
    
    pygame.mouse.set_visible(False) 

    while run:
        dt = clock.tick(60)
        WIDTH, HEIGHT = win.get_size() # Актуализируем размеры для отрисовки
        
        # Камера (обновляем центрирование)
        target_x = p.x - WIDTH // 2 + p.width // 2
        target_y = p.y - HEIGHT // 2 + p.height // 2
        scroll_x += (target_x - scroll_x) * 0.1 
        scroll_y += (target_y - scroll_y) * 0.1
        scroll = (scroll_x, scroll_y)
        
        # HP Animation
        if p.hp > 0:
            if displayed_hp > p.hp: displayed_hp -= (displayed_hp - p.hp) * 0.1 
            elif displayed_hp < p.hp: displayed_hp += 1 
            displayed_hp = max(p.hp, displayed_hp)

        msg_to_send = None
        ability_to_cast = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT: run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if typing_mode: typing_mode = False
                    else: run = False
                elif event.key == pygame.K_RETURN:
                    if typing_mode:
                        if len(current_message) > 0: 
                            if current_message.strip() == "/debug":
                                debug_ui.toggle()
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

        # if not typing_mode and p.hp > 0: p.move(MAP_WIDTH, MAP_HEIGHT)
        if p.hp > 0:
            if not typing_mode:
                # Если не печатаем -> слушаем WASD и обновляем пули
                p.move(MAP_WIDTH, MAP_HEIGHT)
            else:
                # Если печатаем -> ТОЛЬКО обновляем пули (инерцию)
                p.update(MAP_WIDTH, MAP_HEIGHT)
        
        # Сеть
        hit_data = []
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
        
        packet = {"type": "UPDATE", "player": p}
        if hit_data: packet["hits"] = hit_data
        if msg_to_send: packet["msg"] = msg_to_send
        if ability_to_cast: packet["ability_cast"] = ability_to_cast

        server_data = n.send(packet)
        if server_data == "NETWORK_FAILURE": n.disconnect(); run = False; break
            
        all_players = server_data.get("players", {})
        last_walls = server_data.get("walls", {})
        if "chat" in server_data:
            chat_messages.extend(server_data["chat"])
            if len(chat_messages) > 20: chat_messages = chat_messages[-20:]
        
        if p.id in all_players:
            srv_p = all_players[p.id]
            p.hp = srv_p.hp
            p.setPose(srv_p.x, srv_p.y)
            for k, ab in srv_p.abilities.items():
                if k in p.abilities:
                    p.abilities[k].cooldown = ab.cooldown
                    p.abilities[k].duration = ab.duration

        # --- ОТРИСОВКА ---
        win.fill(C_BG_DEEP)
        draw_modern_grid(win, scroll)
            
        for w in last_walls.values():
            screen_x = w.x - scroll[0]
            screen_y = w.y - scroll[1]
            # Glow
            s = pygame.Surface((w.width+20, w.height+20), pygame.SRCALPHA)
            pygame.draw.rect(s, (100, 100, 255, 50), (10,10,w.width,w.height), border_radius=5)
            pygame.draw.rect(s, (150, 150, 255), (10,10,w.width,w.height), 2, border_radius=5)
            win.blit(s, (screen_x-10, screen_y-10))

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
                draw_text_freetype(FONT_UI, display_name, (200, 200, 200), screen_px, screen_py - 20, center=True, win=win)

        if shoot_flash > 0:
            shoot_flash -= 1
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 100, 100), (30,30), 20 + shoot_flash*2)
            win.blit(s, (flash_pos[0]-30, flash_pos[1]-30))

        # --- HUD ---
        bar_w = 300
        bar_h = 35
        bar_x = WIDTH // 2 - bar_w // 2
        bar_y = HEIGHT - 60
        
        draw_cyber_health(win, bar_x, bar_y, bar_w, bar_h, p.hp, 100, displayed_hp)
        
        # Abilities
        sh_cd = p.abilities["shield"].cooldown / p.abilities["shield"].cooldown_max
        sh_col = (50, 50, 50) if sh_cd > 0 else C_NEON_CYAN
        pygame.draw.circle(win, sh_col, (bar_x - 40, bar_y + 10), 25)
        pygame.draw.circle(win, (255,255,255), (bar_x - 40, bar_y + 10), 25, 2)
        FONT_HUD.render_to(win, (bar_x - 50, bar_y), "1", (255,255,255))
        if sh_cd > 0:
            h = int(50 * sh_cd)
            pygame.draw.rect(win, (0,0,0,150), (bar_x - 65, bar_y + 35 - h, 50, h))

        w_cd = p.abilities["wall"].cooldown / p.abilities["wall"].cooldown_max
        w_col = (50, 50, 50) if w_cd > 0 else C_NEON_PINK
        pygame.draw.circle(win, w_col, (bar_x + bar_w + 40, bar_y + 10), 25)
        pygame.draw.circle(win, (255,255,255), (bar_x + bar_w + 40, bar_y + 10), 25, 2)
        FONT_HUD.render_to(win, (bar_x + bar_w + 32, bar_y), "2", (255,255,255))

        # Chat
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
        
        mx, my = pygame.mouse.get_pos()
        draw_custom_cursor(win, mx, my)
        pygame.display.flip()

    try:
        n.disconnect()  
    except Exception as e:
        print("Error during disconnect:", e)
        
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