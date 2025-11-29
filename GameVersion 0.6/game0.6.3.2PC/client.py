import pygame
import random
import math
import json
import os
import time
import threading 
from network import Network, LANScanner 
import server # Импортируем модуль сервера
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
pygame.display.set_caption("Neon Shooter: Ultimate Edition")

# --- SKINS LOADING (Как было) ---
SKINS_DATA = {}
def load_skins():
    global SKINS_DATA
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "Config", "skins.json")
        with open(config_path, "r", encoding='utf-8') as f:
            SKINS_DATA = json.load(f)
    except Exception:
        SKINS_DATA = {"DEFAULT": {"body_color": [0, 255, 255], "trail_color": [0, 200, 200], "outline_color": [255, 255, 255]}}
load_skins()

# --- PALETTE & FONTS ---
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

FONT_CHOICES = ["arial", "consolas"] 
FONT_UI = pygame.freetype.SysFont(FONT_CHOICES, 16)
FONT_HUD = pygame.freetype.SysFont(FONT_CHOICES, 20, bold=True)
FONT_TITLE = pygame.freetype.SysFont(FONT_CHOICES, 60, bold=True)
FONT_DEBUG = pygame.freetype.SysFont("consolas", 14)

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

# --- UI HELPERS ---
def draw_text_freetype(font_obj, text, color, x, y, center=False):
    shadow_surf, shadow_rect = font_obj.render(text, (0,0,0))
    main_surf, main_rect = font_obj.render(text, color)
    if center:
        main_rect.center = (x, y)
        shadow_rect.center = (x + 2, y + 2)
    else:
        main_rect.topleft = (x, y)
        shadow_rect.topleft = (x + 2, y + 2)
    win.blit(shadow_surf, shadow_rect)
    win.blit(main_surf, main_rect)
    return main_rect # Возвращаем rect для кликов

class DebugInterface:
    def __init__(self):
        self.active = False
        self.bg_surf = pygame.Surface((300, 220), pygame.SRCALPHA)
        self.bg_surf.fill((0, 0, 0, 200)) 

    def toggle(self):
        self.active = not self.active
        return self.active

    def draw(self, win, player, network, fps, scroll, last_packet_info):
        if not self.active: return
        x, y = 10, 10
        win.blit(self.bg_surf, (x, y))
        pygame.draw.rect(win, (0, 255, 0), (x, y, 300, 220), 1)
        net_stats = network.traffic_stats
        info_lines = [
            f"--- DEBUG MODE ---",
            f"FPS: {fps}",
            f"Pos: {int(player.x)}, {int(player.y)}",
            f"Sent: {net_stats['sent_total']/1024:.1f} KB",
            f"Recv: {net_stats['recv_total']/1024:.1f} KB",
            f"Last Act: {last_packet_info}"
        ]
        curr_y = y + 10
        for line in info_lines:
            FONT_DEBUG.render_to(win, (x + 10, curr_y), line, (0, 255, 0))
            curr_y += 18

# --- GAME FUNCTIONS ---
def draw_modern_grid(win, scroll):
    win.fill(C_BG)
    border_rect = pygame.Rect(-scroll[0], -scroll[1], MAP_WIDTH, MAP_HEIGHT)
    pygame.draw.rect(win, C_DANGER, border_rect, 3)
    grid_size = 100
    start_x = -int(scroll[0]) % grid_size
    start_y = -int(scroll[1]) % grid_size
    for i in range(start_x, WIDTH, grid_size):
        color = C_GRID_BRIGHT if abs(i + scroll[0]) % (grid_size*5) < grid_size else C_GRID_DIM
        pygame.draw.line(win, color, (i, 0), (i, HEIGHT))
    for i in range(start_y, HEIGHT, grid_size):
        color = C_GRID_BRIGHT if abs(i + scroll[1]) % (grid_size*5) < grid_size else C_GRID_DIM
        pygame.draw.line(win, color, (0, i), (WIDTH, i))

def draw_hud(player, fps):
    # Упрощенный HUD
    bar_w, bar_h = 200, 20
    bar_x = WIDTH // 2 - bar_w // 2
    bar_y = HEIGHT - 40
    hp_pct = max(0, player.hp / 100)
    pygame.draw.rect(win, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
    pygame.draw.rect(win, C_ACCENT if hp_pct > 0.3 else C_DANGER, (bar_x, bar_y, int(bar_w * hp_pct), bar_h), border_radius=5)
    draw_text_freetype(FONT_HUD, f"HP: {player.hp}%", C_TEXT_MAIN, bar_x + bar_w//2, bar_y + 1, center=True)
    draw_text_freetype(FONT_UI, f"FPS: {fps}", C_DANGER, WIDTH - 60, 10)
    
    # Кулдауны
    ab_y = HEIGHT - 100
    for i, key in enumerate(["shield", "wall"]):
        ability = player.abilities[key]
        cd_pct = ability.cooldown / ability.cooldown_max
        bx = WIDTH//2 - 120 + i*140
        pygame.draw.rect(win, (0,0,0), (bx, ab_y, 100, 10), 1)
        if cd_pct > 0:
            pygame.draw.rect(win, C_DANGER, (bx, ab_y, int(100*cd_pct), 10))
        draw_text_freetype(FONT_UI, key.upper(), C_TEXT_MAIN, bx+50, ab_y-15, center=True)

# --- MENUS ---
def main_menu():
    clock = pygame.time.Clock()
    user_ip = "127.0.0.1"
    user_nick = f"Player{random.randint(10,99)}"
    active_field = "NICK"
    skins = list(SKINS_DATA.keys())
    skin_idx = 0
    
    # Состояния меню: MAIN, SERVERS
    menu_state = "MAIN" 
    found_servers = []
    scan_msg = ""

    while True:
        clock.tick(60)
        win.fill(C_BG_DEEP)
        
        # Grid BG Animation
        t = pygame.time.get_ticks() / 1000
        for x in range(0, WIDTH, 50): pygame.draw.line(win, (20, 20, 40), (x, 0), (x, HEIGHT))
        
        mx, my = pygame.mouse.get_pos()
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: click = True
            if event.type == pygame.KEYDOWN:
                if menu_state == "MAIN":
                    if event.key == pygame.K_ESCAPE: return "QUIT"
                    if event.key == pygame.K_TAB: active_field = "IP" if active_field == "NICK" else "NICK"
                    if event.key == pygame.K_LEFT: skin_idx = (skin_idx - 1) % len(skins)
                    if event.key == pygame.K_RIGHT: skin_idx = (skin_idx + 1) % len(skins)
                    if event.unicode.isprintable() and event.key != pygame.K_TAB:
                        if active_field == "NICK" and len(user_nick) < 12: user_nick += event.unicode
                        if active_field == "IP" and len(user_ip) < 15: user_ip += event.unicode
                    if event.key == pygame.K_BACKSPACE:
                         if active_field == "NICK": user_nick = user_nick[:-1]
                         else: user_ip = user_ip[:-1]
                elif menu_state == "SERVERS":
                    if event.key == pygame.K_ESCAPE: menu_state = "MAIN"

        # --- DRAW HEADER ---
        draw_text_freetype(FONT_TITLE, "NEON STRIKE", C_NEON_CYAN, WIDTH//2, 80, center=True)

        if menu_state == "MAIN":
            # Inputs
            inputs = [("NICKNAME", user_nick, 200, active_field == "NICK"), ("DIRECT IP", user_ip, 280, active_field == "IP")]
            for label, val, y, is_active in inputs:
                col = C_NEON_CYAN if is_active else (50, 50, 100)
                box_rect = pygame.Rect(WIDTH//2 - 150, y, 300, 40)
                pygame.draw.rect(win, (10, 10, 20), box_rect)
                pygame.draw.rect(win, col, box_rect, 2)
                draw_text_freetype(FONT_UI, label, (150, 150, 150), WIDTH//2, y - 20, center=True)
                draw_text_freetype(FONT_HUD, val + ("|" if is_active and (pygame.time.get_ticks()//500)%2 else ""), C_TEXT, box_rect.x + 10, box_rect.y + 10)
                
                if click and box_rect.collidepoint(mx, my):
                    active_field = "NICK" if label == "NICKNAME" else "IP"

            # Skin Selector
            skin_name = skins[skin_idx]
            draw_text_freetype(FONT_UI, "CLASS / SKIN", (150, 150, 150), WIDTH//2, 360, center=True)
            s_rect = draw_text_freetype(FONT_HUD, f"<  {skin_name}  >", C_NEON_PINK, WIDTH//2, 390, center=True)
            if click and s_rect.collidepoint(mx, my):
                 skin_idx = (skin_idx + 1) % len(skins)

            # Buttons
            btn_y = 480
            
            # 1. Connect Button
            conn_rect = pygame.Rect(WIDTH//2 - 200, btn_y, 190, 50)
            pygame.draw.rect(win, (0, 100, 0), conn_rect)
            draw_text_freetype(FONT_HUD, "CONNECT (IP)", C_TEXT_MAIN, conn_rect.centerx, conn_rect.centery - 10, center=True)
            
            # 2. LAN Scan Button
            scan_rect = pygame.Rect(WIDTH//2 + 10, btn_y, 190, 50)
            pygame.draw.rect(win, (0, 0, 100), scan_rect)
            draw_text_freetype(FONT_HUD, "SCAN LAN", C_TEXT_MAIN, scan_rect.centerx, scan_rect.centery - 10, center=True)
            
            # 3. Offline Mode Button
            off_rect = pygame.Rect(WIDTH//2 - 100, btn_y + 70, 200, 50)
            pygame.draw.rect(win, (100, 50, 0), off_rect)
            draw_text_freetype(FONT_HUD, "OFFLINE MODE", C_TEXT_MAIN, off_rect.centerx, off_rect.centery - 10, center=True)

            if click:
                if conn_rect.collidepoint(mx, my):
                    return (user_ip, user_nick, skin_name, False) # False = Not Local Host
                if scan_rect.collidepoint(mx, my):
                    menu_state = "SERVERS"
                    scan_msg = "Scanning..."
                    found_servers = []
                    # Запускаем сканирование (в этом кадре, блокирует на 0.5с)
                    found_servers = LANScanner.scan(timeout=0.5)
                    scan_msg = f"Found {len(found_servers)} servers"
                if off_rect.collidepoint(mx, my):
                    return ("127.0.0.1", user_nick, skin_name, True) # True = Start Local Server

        elif menu_state == "SERVERS":
            draw_text_freetype(FONT_HUD, "SERVER BROWSER", C_TEXT_MAIN, WIDTH//2, 160, center=True)
            draw_text_freetype(FONT_UI, scan_msg, C_ACCENT, WIDTH//2, 200, center=True)
            
            # Refresh Button
            ref_rect = pygame.Rect(WIDTH - 150, HEIGHT - 80, 120, 40)
            pygame.draw.rect(win, (50, 50, 100), ref_rect)
            draw_text_freetype(FONT_UI, "REFRESH", C_TEXT, ref_rect.centerx, ref_rect.centery-8, center=True)
            if click and ref_rect.collidepoint(mx, my):
                 scan_msg = "Scanning..."
                 pygame.display.flip()
                 found_servers = LANScanner.scan(timeout=0.5)
                 scan_msg = f"Found {len(found_servers)} servers"

            # Back Button
            back_rect = pygame.Rect(30, HEIGHT - 80, 120, 40)
            pygame.draw.rect(win, (100, 50, 50), back_rect)
            draw_text_freetype(FONT_UI, "BACK", C_TEXT, back_rect.centerx, back_rect.centery-8, center=True)
            if click and back_rect.collidepoint(mx, my): menu_state = "MAIN"

            # Server List
            list_y = 240
            for srv in found_servers:
                row_rect = pygame.Rect(WIDTH//2 - 200, list_y, 400, 40)
                color = (30, 80, 30) if row_rect.collidepoint(mx, my) else (20, 20, 40)
                pygame.draw.rect(win, color, row_rect)
                pygame.draw.rect(win, C_ACCENT, row_rect, 1)
                
                txt = f"{srv['name']} | IP: {srv['ip']} | Pl: {srv['players']}"
                draw_text_freetype(FONT_UI, txt, C_TEXT, row_rect.x + 10, row_rect.y + 10)
                
                if click and row_rect.collidepoint(mx, my):
                    return (srv['ip'], user_nick, skin_name, False)
                
                list_y += 50

        pygame.display.flip()

def game_loop(server_ip, nickname, selected_skin, is_local_host):
    global shoot_flash_timer, flash_pos
    
    server_thread = None
    if is_local_host:
        # Запускаем сервер в отдельном потоке
        print("Запуск локального сервера...")
        server_thread = threading.Thread(target=server.start_server_instance, args=("127.0.0.1",))
        server_thread.daemon = True # Чтобы закрылся при выходе
        server_thread.start()
        time.sleep(1) # Даем серверу время запуститься

    try:
        n = Network(server_ip)
        p = n.getP()
    except:
        print("Ошибка подключения")
        return

    if not p: 
        if is_local_host: server.server_running = False
        return 
    
    # Init packet
    p.nickname = nickname
    p.skin_id = selected_skin 
    n.send({"type": "INIT", "skin": selected_skin, "nick": nickname})
    
    clock = pygame.time.Clock()
    run = True
    typing_mode = False
    current_message = ""
    
    scroll_x = p.x - WIDTH // 2 + p.width // 2
    scroll_y = p.y - HEIGHT // 2 + p.height // 2
    
    debug_ui = DebugInterface()
    last_walls = {}
    all_players = {}
    chat_messages = []
    
    pygame.mouse.set_visible(False)

    while run:
        clock.tick(60)
        
        # --- GAMEPLAY LOGIC (Copy from original but optimized) ---
        target_x = p.x - WIDTH // 2 + p.width // 2
        target_y = p.y - HEIGHT // 2 + p.height // 2
        scroll_x += (target_x - scroll_x) * 0.2
        scroll_y += (target_y - scroll_y) * 0.2
        scroll = (scroll_x, scroll_y)
        
        if shoot_flash_timer > 0: shoot_flash_timer -= 1
        
        msg_to_send = None
        ability_to_cast = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if typing_mode: typing_mode = False
                    else: run = False
                elif event.key == pygame.K_RETURN:
                    if typing_mode:
                        if current_message:
                            if current_message.strip() == "/debug": debug_ui.toggle()
                            else: msg_to_send = current_message
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
                    p.shoot(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], scroll)
                    shoot_flash_timer = 5; flash_pos = pygame.mouse.get_pos()

        if not typing_mode and p.hp > 0: p.move(MAP_WIDTH, MAP_HEIGHT)

        # Hit detection client prediction
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

        # Networking
        last_info = "Idle"
        if ability_to_cast: last_info = "Ability"
        elif msg_to_send: last_info = "Chat"
        
        packet = {"player": p, "msg": msg_to_send, "hits": hit_data, "ability_cast": ability_to_cast}
        server_data = n.send(packet)
        
        if server_data == "NETWORK_FAILURE": run = False; break
        
        all_players = server_data.get("players", {})
        chat_messages = server_data.get("chat", [])
        last_walls = server_data.get("walls", {})
        
        if p.id in all_players:
            srv_p = all_players[p.id]
            p.hp = srv_p.hp
            p.setPose(srv_p.x, srv_p.y)
            for k, ab in srv_p.abilities.items():
                if k in p.abilities:
                    p.abilities[k].cooldown = ab.cooldown
                    p.abilities[k].duration = ab.duration

        # --- DRAWING ---
        draw_modern_grid(win, scroll)
        
        for w in last_walls.values(): w.draw(win, scroll)
        
        for pid, pl in all_players.items():
            s_data = SKINS_DATA.get(pl.skin_id, SKINS_DATA["DEFAULT"])
            pl.color = s_data["body_color"]
            pl.trail_color = s_data["trail_color"]
            pl.outline_color = s_data["outline_color"]
            pl.draw(win, scroll)
            
            spx, spy = pl.x - scroll[0] + pl.width//2, pl.y - scroll[1] - 20
            if 0 < spx < WIDTH and 0 < spy < HEIGHT:
                draw_text_freetype(FONT_UI, pl.nickname, (200,200,200), spx, spy, center=True)

        if shoot_flash_timer > 0:
             s = pygame.Surface((100, 100), pygame.SRCALPHA)
             pygame.draw.circle(s, (255, 255, 0, 100), (50, 50), 20 + shoot_flash_timer*5)
             win.blit(s, (flash_pos[0]-50, flash_pos[1]-50))
             
        win.blit(vignette_surf, (0,0))
        
        # Chat Draw
        cx, cy = 10, HEIGHT - 240
        s_chat = pygame.Surface((300, 200), pygame.SRCALPHA)
        s_chat.fill((0,0,0,150))
        win.blit(s_chat, (cx, cy))
        for i, m in enumerate(chat_messages[-7:]):
            col = C_DANGER if "KILL" in m else C_TEXT_MAIN
            draw_text_freetype(FONT_UI, m, col, cx+5, cy+5+i*20)
            
        # Input box
        if typing_mode:
            pygame.draw.rect(win, C_DANGER, (10, HEIGHT-35, 300, 30), 2)
            draw_text_freetype(FONT_UI, current_message + "_", C_TEXT, 15, HEIGHT-30)
        else:
            draw_text_freetype(FONT_UI, "Press ENTER to chat", (100,100,100), 10, HEIGHT-30)

        draw_hud(p, int(clock.get_fps()))
        debug_ui.draw(win, p, n, int(clock.get_fps()), scroll, last_info)
        
        # Cursor
        mx, my = pygame.mouse.get_pos()
        pygame.draw.circle(win, C_ACCENT, (mx, my), 8, 1)
        pygame.display.update()

    n.disconnect()
    pygame.mouse.set_visible(True)
    if is_local_host:
        print("Остановка локального сервера...")
        server.server_running = False

def main_app():
    running = True
    while running:
        res = main_menu()
        if res == "QUIT": running = False
        elif isinstance(res, tuple):
            # ip, nick, skin, is_local
            game_loop(res[0], res[1], res[2], res[3])
    pygame.quit()

if __name__ == "__main__":
    main_app()