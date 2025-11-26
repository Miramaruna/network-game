import pygame
import random
import math
from network import Network
from player import Player

pygame.init()

# --- SETTINGS ---
WIDTH = 900
HEIGHT = 700
MAP_WIDTH = 2000
MAP_HEIGHT = 2000

win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Shooter: Redux (Optimized)")

# --- PALETTE ---
C_BG = (10, 10, 20)
C_GRID_DIM = (30, 30, 50)
C_GRID_BRIGHT = (60, 60, 100)
C_ACCENT = (0, 255, 255)
C_DANGER = (255, 50, 50)
C_TEXT_MAIN = (240, 240, 240)
C_UI_BG = (0, 0, 0, 150)

# --- FONTS ---
FONT_CHOICES = ["arial", "dejavusans", "verdana", "comicsansms"] 
font_ui = pygame.font.SysFont(FONT_CHOICES, 16)
font_hud = pygame.font.SysFont(FONT_CHOICES, 20, bold=True)
font_title = pygame.font.SysFont(FONT_CHOICES, 70, bold=True)

# --- GLOBAL EFFECTS ---
shoot_flash_timer = 0
flash_pos = (0, 0)

# --- VIGNETTE (Pre-calculated) ---
vignette_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
# Optimization: Using a radial gradient blit or simpler math could be even faster, 
# but pre-calculating once at startup is perfectly fine.
for x in range(WIDTH):
    for y in range(HEIGHT):
        dx = x - WIDTH // 2
        dy = y - HEIGHT // 2
        dist = math.sqrt(dx**2 + dy**2)
        alpha = min(255, int(dist / (WIDTH * 0.65) * 255))
        if alpha > 40:
            vignette_surf.set_at((x, y), (0, 0, 0, alpha))

# --- TEXT CACHING (MEMORY OPTIMIZATION) ---
# Cache format: {(text, font_obj, color): surface}
TEXT_CACHE = {}

def draw_text_shadow(text, font, color, x, y, center=False):
    """Draws cached text with shadow"""
    # Create unique keys for cache lookups
    key_main = (text, font, color)
    key_shadow = (text, font, (0, 0, 0))
    
    if key_main not in TEXT_CACHE:
        TEXT_CACHE[key_main] = font.render(text, True, color)
    if key_shadow not in TEXT_CACHE:
        TEXT_CACHE[key_shadow] = font.render(text, True, (0, 0, 0))
        
    main_txt = TEXT_CACHE[key_main]
    shadow = TEXT_CACHE[key_shadow]
    
    if center:
        rect = main_txt.get_rect(center=(x, y))
        shadow_rect = shadow.get_rect(center=(x+2, y+2))
        win.blit(shadow, shadow_rect)
        win.blit(main_txt, rect)
    else:
        win.blit(shadow, (x+2, y+2))
        win.blit(main_txt, (x, y))

# --- PARTICLE CLASS ---
class Particle:
    __slots__ = ('x', 'y', 'size', 'speed_y', 'alpha', 'color', 'surf')

    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = random.randint(2, 4)
        self.speed_y = random.uniform(-1.5, -0.5)
        self.alpha = random.randint(50, 150)
        self.color = C_ACCENT
        # Pre-render surface
        self.surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.surf.fill((*self.color, 150)) # Fixed alpha for menu particles for simplicity

    def move(self):
        self.y += self.speed_y
        self.alpha -= 0.5
        if self.y < 0 or self.alpha <= 0:
            self.y = HEIGHT
            self.x = random.randint(0, WIDTH)
            self.alpha = 150

    def draw(self, surf):
        # Only changing alpha via set_alpha is faster than recreating surface
        self.surf.set_alpha(int(self.alpha))
        surf.blit(self.surf, (self.x, self.y))

# --- RENDERING HELPER ---
def draw_modern_grid(win, scroll):
    win.fill(C_BG)
    
    # World Borders
    border_rect = pygame.Rect(-scroll[0], -scroll[1], MAP_WIDTH, MAP_HEIGHT)
    pygame.draw.rect(win, C_DANGER, border_rect, 3)
    
    grid_size = 100
    
    # Optimization: Only calculate lines that are actually visible
    start_x = -int(scroll[0]) % grid_size
    start_y = -int(scroll[1]) % grid_size
    
    # Draw Vertical Lines
    # We loop from start_x to WIDTH, which limits drawing to screen size
    for i in range(start_x, WIDTH, grid_size):
        real_world_x = i + scroll[0]
        # Determine color
        color = C_GRID_BRIGHT if abs(real_world_x) % (grid_size*5) < grid_size else C_GRID_DIM
        pygame.draw.line(win, color, (i, 0), (i, HEIGHT))
        
    # Draw Horizontal Lines
    for i in range(start_y, HEIGHT, grid_size):
        real_world_y = i + scroll[1]
        color = C_GRID_BRIGHT if abs(real_world_y) % (grid_size*5) < grid_size else C_GRID_DIM
        pygame.draw.line(win, color, (0, i), (WIDTH, i))

def draw_custom_cursor(mx, my):
    pygame.draw.circle(win, C_ACCENT, (mx, my), 8, 1)
    pygame.draw.line(win, C_ACCENT, (mx - 12, my), (mx + 12, my), 1)
    pygame.draw.line(win, C_ACCENT, (mx, my - 12), (mx, my + 12), 1)
    pygame.draw.circle(win, (255, 255, 255), (mx, my), 2)

def draw_hud(player, fps):
    # HP Bar
    bar_w, bar_h = 200, 20
    bar_x = WIDTH // 2 - bar_w // 2
    bar_y = HEIGHT - 40
    
    pygame.draw.rect(win, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
    hp_pct = max(0, player.hp / 100)
    fill_w = int(bar_w * hp_pct)
    color = C_ACCENT if hp_pct > 0.3 else C_DANGER
    pygame.draw.rect(win, color, (bar_x, bar_y, fill_w, bar_h), border_radius=5)
    pygame.draw.rect(win, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=5)
    
    draw_text_shadow(f"HP: {player.hp}%", font_hud, C_TEXT_MAIN, bar_x + bar_w//2, bar_y + 1, center=True)
    
    # Info Box
    info_bg = pygame.Surface((180, 80), pygame.SRCALPHA)
    info_bg.fill((0,0,0, 150))
    win.blit(info_bg, (WIDTH - 190, 10))
    
    draw_text_shadow(f"PLAYER ID: {player.id}", font_ui, C_ACCENT, WIDTH - 180, 15)
    draw_text_shadow(f"FPS: {fps}", font_ui, C_DANGER, WIDTH - 180, 35)
    draw_text_shadow(f"XY: {int(player.x)}, {int(player.y)}", font_ui, C_TEXT_MAIN, WIDTH - 180, 55)

# --- MENUS ---
def main_menu():
    user_ip = ""
    user_nick = "" 
    clock = pygame.time.Clock()
    active_field = "IP"
    active = True
    particles = [Particle() for _ in range(35)]
    
    while active:
        clock.tick(60)
        win.fill(C_BG)
        
        for p in particles:
            p.move()
            p.draw(win)

        draw_text_shadow("NEON SHOOTER", font_title, C_ACCENT, WIDTH//2, 120, center=True)
        
        # Nickname Field
        draw_text_shadow("НИКНЕЙМ:", font_hud, (180, 180, 180), WIDTH//2, 250, center=True)
        nick_box = pygame.Rect(WIDTH//2 - 180, 280, 360, 40)
        nick_border_color = C_DANGER if active_field == "NICK" else C_ACCENT
        pygame.draw.rect(win, (20, 20, 30), nick_box, border_radius=5)
        pygame.draw.rect(win, nick_border_color, nick_box, 2, border_radius=5)
        
        nick_text = user_nick
        if active_field == "NICK" and (pygame.time.get_ticks()//500)%2==0:
            nick_text += "|"
        
        txt_surf_nick = font_hud.render(nick_text, True, C_TEXT_MAIN)
        win.blit(txt_surf_nick, (nick_box.x + 10, nick_box.y + 10))

        # IP Field
        draw_text_shadow("IP СЕРВЕРА:", font_hud, (180, 180, 180), WIDTH//2, 360, center=True)
        ip_box = pygame.Rect(WIDTH//2 - 180, 390, 360, 40)
        ip_border_color = C_DANGER if active_field == "IP" else C_ACCENT
        pygame.draw.rect(win, (20, 20, 30), ip_box, border_radius=5)
        pygame.draw.rect(win, ip_border_color, ip_box, 2, border_radius=5)
        
        ip_text = user_ip
        if active_field == "IP" and (pygame.time.get_ticks()//500)%2==0:
            ip_text += "|"

        txt_surf_ip = font_hud.render(ip_text, True, C_TEXT_MAIN)
        win.blit(txt_surf_ip, (ip_box.x + 10, ip_box.y + 10))
        
        draw_text_shadow("TAB - сменить поле | ENTER - Играть | ESC - Выход", font_ui, (120, 120, 120), WIDTH//2, 500, center=True)
        if user_ip == "":
            draw_text_shadow("(Пусто = localhost)", font_ui, (80, 80, 80), WIDTH//2, 440, center=True)

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
                    if active_field == "IP" and len(user_ip) < 15:
                        user_ip += event.unicode
                    elif active_field == "NICK" and len(user_nick) < 12:
                        user_nick += event.unicode
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
    typing_mode = False
    current_message = ""
    
    scroll_x = p.x - WIDTH // 2 + p.width // 2
    scroll_y = p.y - HEIGHT // 2 + p.height // 2
    pygame.mouse.set_visible(False)

    while run:
        clock.tick(60)
        msg_to_send = None 
        
        # Camera LERP
        target_x = p.x - WIDTH // 2 + p.width // 2
        target_y = p.y - HEIGHT // 2 + p.height // 2
        scroll_x += (target_x - scroll_x) * 0.2 
        scroll_y += (target_y - scroll_y) * 0.2
        scroll = (scroll_x, scroll_y)

        if shoot_flash_timer > 0: shoot_flash_timer -= 1

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
                    shoot_flash_timer = 5 
                    flash_pos = (mx, my)
        
        if not typing_mode and p.hp > 0:
            p.move(MAP_WIDTH, MAP_HEIGHT) 
        elif p.hp <= 0:
            p.last_move = (0, 0)

        # --- COLLISION LOGIC (OPTIMIZED) ---
        hit_data = [] 
        current_bullets = list(p.bullets) 

        # Create bullet rects only once per frame if possible, 
        # but here we do it per bullet. We reuse other players' existing rects.
        for bullet in current_bullets:
            # We must create a new rect for the bullet as it is just a list [x, y, dx, dy]
            bullet_rect = pygame.Rect(bullet[0] - 5, bullet[1] - 5, 10, 10) 

            for other_id, other_p in all_players.items():
                if other_id != p.id and other_p.hp > 0:
                    # OPTIMIZATION: Use the pre-calculated rect of the other player
                    # other_p.rect is already updated via its own methods or server sync
                    
                    if bullet_rect.colliderect(other_p.rect):
                        p.deleteBullet(bullet)
                        hit_data.append({"target_id": other_id, "damage": 10})
                        break

        # --- NETWORK ---
        packet = {"player": p, "msg": msg_to_send, "hits": hit_data} 
        server_data = n.send(packet)
        
        if not server_data:
            run = False
            break
            
        all_players = server_data.get("players", {})
        chat_messages = server_data.get("chat", [])
        
        if p.id in all_players:
            server_p = all_players[p.id]
            p.hp = server_p.hp     
            # print(p.x, p.y, "|", server_p.x, server_p.y)
            p.setPose(server_p.x, server_p.y)

        # --- DRAWING ---
        draw_modern_grid(win, scroll)

        for p_id, player in all_players.items():
            player.draw(win, scroll)
            
            # Draw names
            screen_px = player.x - scroll[0] + player.width // 2
            screen_py = player.y - (scroll[1] + 20)
            
            # Simple visibility check for text
            if 0 < screen_px < WIDTH and 0 < screen_py < HEIGHT:
                display_name = getattr(player, 'nickname', f"Игрок {p_id}")
                draw_text_shadow(display_name, font_ui, (200, 200, 200), screen_px, screen_py - 20, center=True)

        if shoot_flash_timer > 0:
            flash_radius = 20 + shoot_flash_timer * 3
            flash_alpha = int(255 * (shoot_flash_timer / 5))
            flash_surf = pygame.Surface((flash_radius*2, flash_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 255, 0, flash_alpha), (flash_radius, flash_radius), flash_radius)
            win.blit(flash_surf, (flash_pos[0] - flash_radius, flash_pos[1] - flash_radius))

        win.blit(vignette_surf, (0, 0))

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
            draw_text_shadow(msg, font_ui, color, chat_x + 10, chat_y + 10 + i * 25)

        input_y = HEIGHT - 50
        input_w = 350
        if typing_mode:
            pygame.draw.rect(win, (20, 20, 20), (10, input_y, input_w, 30))
            pygame.draw.rect(win, C_DANGER, (10, input_y, input_w, 30), 2)
            draw_text_shadow(current_message + "_", font_ui, C_DANGER, 15, input_y + 5)
        else:
            draw_text_shadow("Нажми ENTER для чата", font_ui, (120, 120, 120), 10, input_y + 5)

        draw_hud(p, int(clock.get_fps()))
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
            server_ip, nickname = result 
            game_loop(server_ip, nickname) 
    pygame.quit()

if __name__ == "__main__":
    main_app()