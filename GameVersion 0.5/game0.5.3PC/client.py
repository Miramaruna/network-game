import pygame
import random
import math
from network import Network
from player import Player, Wall, ShieldAbility, WallAbility 
import pygame.freetype # NEW: For anti-aliasing

pygame.init()
pygame.freetype.init() # Initialize freetype

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

C_BG_DEEP = (5, 5, 12)        # Very dark blue
C_GRID = (25, 25, 50)         # Subtle grid
C_GRID_GLOW = (50, 50, 100)
C_NEON_CYAN = (0, 255, 255)
C_NEON_PINK = (255, 0, 150)
C_DANGER = (255, 50, 50)
C_TEXT = (220, 240, 255)

# --- FONTS ---
FONT_CHOICES = ["arial", "dejavusans", "verdana", "comicsansms"] 
# FONT_UI = pygame.font.SysFont(FONT_CHOICES, 16)
# FONT_HUD = pygame.font.SysFont(FONT_CHOICES, 20, bold=True)
# FONT_TITLE = pygame.font.SysFont(FONT_CHOICES, 70, bold=True)

try:
    FONT_UI = pygame.freetype.Font("arial", 16) # Replace "arial" with a .ttf path if desired
    FONT_HUD = pygame.freetype.Font("arial", 20)
    FONT_TITLE = pygame.freetype.Font("arial", 70)
except:
    # Fallback if TTF fails
    FONT_UI = pygame.freetype.SysFont(FONT_CHOICES, 16)
    FONT_HUD = pygame.freetype.SysFont(FONT_CHOICES, 20, bold=True)
    FONT_TITLE = pygame.freetype.SysFont(FONT_CHOICES, 70, bold=True)

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

def draw_text_freetype(font_obj, text, color, x, y, center=False):
    """Draws text using freetype with a simple shadow."""
    if isinstance(font_obj, pygame.font.Font): # Fallback check for SysFont
        font_obj.render(text, True, color) # Use existing SysFont if Freetype failed initialization
        return 
        
    shadow_color = (0, 0, 0)
    shadow_offset = (2, 2)
    
    # Render shadow and main text
    # Freetype returns a (surface, rect) tuple
    shadow_surf, shadow_rect = font_obj.render(text, shadow_color)
    main_surf, main_rect = font_obj.render(text, color)
    
    if center:
        main_rect.center = (x, y)
        shadow_rect.center = (x + shadow_offset[0], y + shadow_offset[1])
    else:
        main_rect.topleft = (x, y)
        shadow_rect.topleft = (x + shadow_offset[0], y + shadow_offset[1])
        
    win.blit(shadow_surf, shadow_rect)
    win.blit(main_surf, main_rect)

# def draw_text_freetype(text, font, color, x, y, center=False):
#     """Draws cached text with shadow"""
#     # Create unique keys for cache lookups
#     key_main = (text, font, color)
#     key_shadow = (text, font, (0, 0, 0))
    
#     if key_main not in TEXT_CACHE:
#         TEXT_CACHE[key_main] = font.render(text, True, color)
#     if key_shadow not in TEXT_CACHE:
#         TEXT_CACHE[key_shadow] = font.render(text, True, (0, 0, 0))
        
#     main_txt = TEXT_CACHE[key_main]
#     shadow = TEXT_CACHE[key_shadow]
    
#     if center:
#         rect = main_txt.get_rect(center=(x, y))
#         shadow_rect = shadow.get_rect(center=(x+2, y+2))
#         win.blit(shadow, shadow_rect)
#         win.blit(main_txt, rect)
#     else:
#         win.blit(shadow, (x+2, y+2))
#         win.blit(main_txt, (x, y))

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
    
    # draw_text_freetype(f"HP: {player.hp}%", FONT_HUD, C_TEXT_MAIN, bar_x + bar_w//2, bar_y + 1, center=True)
    
    draw_text_freetype(FONT_HUD, f"HP: {player.hp}%", C_TEXT_MAIN, bar_x + bar_w//2, bar_y + 1, center=True)
    
    # Info Box
    # info_bg = pygame.Surface((180, 80), pygame.SRCALPHA)
    # info_bg.fill((0,0,0, 150))
    # win.blit(info_bg, (WIDTH - 190, 10))
    
    # draw_text_freetype(f"PLAYER ID: {player.id}", FONT_UI, C_ACCENT, WIDTH - 180, 15)
    # draw_text_freetype(f"FPS: {fps}", FONT_UI, C_DANGER, WIDTH - 180, 35)
    # draw_text_freetype(f"XY: {int(player.x)}, {int(player.y)}", FONT_UI, C_TEXT_MAIN, WIDTH - 180, 55)
    
    draw_text_freetype(FONT_UI, f"PLAYER ID: {player.id}", C_ACCENT, WIDTH - 180, 15)
    draw_text_freetype(FONT_UI, f"FPS: {fps}", C_DANGER, WIDTH - 180, 35)
    draw_text_freetype(FONT_UI, f"XY: {int(player.x)}, {int(player.y)}", C_TEXT_MAIN, WIDTH - 180, 55)

    # NEW: Ability Cooldowns
    ability_keys = ["shield", "wall"]
    ability_names = {"shield": "SHIELD (1)", "wall": "WALL (2)"}
    ab_y = HEIGHT - 120
    
    for i, key in enumerate(ability_keys):
        ability = player.abilities[key]
        cooldown_s = ability.cooldown / 60
        cooldown_max_s = ability.cooldown_max / 60
        
        box_x = WIDTH // 2 - 120 + i * 140
        box_w, box_h = 100, 20
        
        # Cooldown box background (alpha transparency)
        cooldown_bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        cooldown_bg.fill((0, 0, 0, 120))
        win.blit(cooldown_bg, (box_x, ab_y))

        if cooldown_s > 0:
            # Cooldown fill bar
            fill_pct = cooldown_s / cooldown_max_s
            fill_h = int(box_h * fill_pct)
            
            # Draw overlay to show cooldown
            cooldown_fill = pygame.Surface((box_w, fill_h), pygame.SRCALPHA)
            cooldown_fill.fill((10, 10, 50, 200)) # Dark blue/black overlay
            win.blit(cooldown_fill, (box_x, ab_y + box_h - fill_h))
            
            # Display time remaining
            time_text = f"{cooldown_s:.1f}s"
            draw_text_freetype(FONT_UI, time_text, C_DANGER, box_x + box_w//2, ab_y + 5, center=True)
            
        else:
            draw_text_freetype(FONT_UI, "READY", C_ACCENT, box_x + box_w//2, ab_y + 5, center=True)

        draw_text_freetype(FONT_UI, ability_names[key], C_TEXT_MAIN, box_x + box_w//2, ab_y - 20, center=True)
        pygame.draw.rect(win, C_TEXT_MAIN, (box_x, ab_y, box_w, box_h), 1)

# --- MENUS ---
def main_menu():
    clock = pygame.time.Clock()
    user_ip = "127.0.0.1"
    user_nick = ""
    active_field = "NICK"
    
    skins = ["CYAN_NEON", "RED_CYBORG", "GOLD_ELITE"]
    skin_idx = 0

    while True:
        clock.tick(60)
        win.fill(C_BG_DEEP)
        
        # Grid Animation for menu
        t = pygame.time.get_ticks() / 1000
        grid_off = (t * 20) % 50
        for x in range(0, WIDTH, 50):
            pygame.draw.line(win, (20, 20, 40), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(win, (20, 20, 40), (0, y + grid_off), (WIDTH, y + grid_off))

        # Title
        draw_text_freetype(FONT_TITLE, "NEON STRIKE", C_NEON_CYAN, WIDTH//2, 100, center=True)
        draw_text_freetype(FONT_HUD, "MULTIPLAYER BATTLE ARENA", C_NEON_PINK, WIDTH//2, 160, center=True)

        # Input Boxes
        inputs = [
            ("NICKNAME", user_nick, 250, active_field == "NICK"),
            ("SERVER IP", user_ip, 350, active_field == "IP")
        ]

        for label, val, y, is_active in inputs:
            draw_text_freetype(FONT_UI, label, (150, 150, 150), WIDTH//2, y - 25, center=True)
            box_rect = pygame.Rect(WIDTH//2 - 150, y, 300, 40)
            
            col = C_NEON_CYAN if is_active else (50, 50, 100)
            pygame.draw.rect(win, (10, 10, 20), box_rect)
            pygame.draw.rect(win, col, box_rect, 2)
            
            txt_display = val + ("|" if is_active and (pygame.time.get_ticks()//500)%2 else "")
            draw_text_freetype(FONT_HUD, txt_display, C_TEXT, box_rect.x + 10, box_rect.y + 10)

        # Skin Selector
        draw_text_freetype(FONT_UI, "SELECT CLASS", (150, 150, 150), WIDTH//2, 450, center=True)
        skin_name = skins[skin_idx]
        draw_text_freetype(FONT_HUD, f"<  {skin_name}  >", C_NEON_PINK, WIDTH//2, 480, center=True)
        
        # Instructions
        draw_text_freetype(FONT_UI, "[TAB] Switch Field  [ENTER] Start  [ESC] Exit", (100, 100, 150), WIDTH//2, 600, center=True)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return "QUIT"
                if event.key == pygame.K_TAB:
                    active_field = "IP" if active_field == "NICK" else "NICK"
                if event.key == pygame.K_RETURN:
                    final_nick = user_nick if user_nick else f"User{random.randint(100,999)}"
                    return (user_ip, final_nick, skin_name)
                
                # Skin swap
                if event.key == pygame.K_LEFT: skin_idx = (skin_idx - 1) % len(skins)
                if event.key == pygame.K_RIGHT: skin_idx = (skin_idx + 1) % len(skins)

                # Typing
                if event.key == pygame.K_BACKSPACE:
                    if active_field == "NICK": user_nick = user_nick[:-1]
                    else: user_ip = user_ip[:-1]
                elif event.unicode.isprintable():
                    if active_field == "NICK" and len(user_nick) < 12: user_nick += event.unicode
                    if active_field == "IP" and len(user_ip) < 15: user_ip += event.unicode


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
    p.skin_id = selected_skin # Set the selected skin
    clock = pygame.time.Clock()
    run = True
    typing_mode = False
    current_message = ""
    
    scroll_x = p.x - WIDTH // 2 + p.width // 2
    scroll_y = p.y - HEIGHT // 2 + p.height // 2
    pygame.mouse.set_visible(False)
    
    last_walls = {}

    while run:
        # clock.tick(60)
        clock.tick(120)
        msg_to_send = None 
        ability_to_cast = None
        
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
                        
                elif not typing_mode:
                    if event.key == pygame.K_1:
                        if p.cast_ability("shield"): ability_to_cast = {"key": "shield"}
                    elif event.key == pygame.K_2:
                        if p.cast_ability("wall"): ability_to_cast = {"key": "wall"}
            
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

        for bullet in current_bullets:
            bullet_rect = pygame.Rect(bullet[0] - 5, bullet[1] - 5, 10, 10) 
            
            # Check Client Bullet vs Wall collision (Client prediction/visual check)
            wall_hit = False
            for wall in last_walls.values():
                if bullet_rect.colliderect(wall.rect):
                    p.deleteBullet(bullet)
                    wall_hit = True
                    break
            if wall_hit: continue

            for other_id, other_p in all_players.items():
                if other_id != p.id and other_p.hp > 0 and other_p.abilities["shield"].duration <= 0: # Client-side shield check
                    if bullet_rect.colliderect(other_p.rect):
                        p.deleteBullet(bullet)
                        hit_data.append({"target_id": other_id, "damage": 10})
                        break

        # --- NETWORK ---
        packet = {"player": p, "msg": msg_to_send, "hits": hit_data, "ability_cast": ability_to_cast} 
        server_data = n.send(packet)
        
        # 1. CHECK FOR NETWORK FAILURE IMMEDIATELY
        if server_data == "NETWORK_FAILURE": 
            n.disconnect() 
            run = False
            # display_error_message will be called *after* the loop, but call it here
            # to immediately display the message if needed, or rely on the final check.
            break # Exit the while loop immediately
            
        # 2. PROCESS SERVER DATA ONLY IF IT IS A DICTIONARY (NOT A STRING MARKER)
        # We know server_data is now the dict if we reached here
        all_players = server_data.get("players", {})
        chat_messages = server_data.get("chat", [])
        last_walls = server_data.get("walls", {})
        
        if p.id in all_players:
            server_p = all_players[p.id]
            p.hp = server_p.hp     
            p.setPose(server_p.x, server_p.y)
            # Sync server-authoritative ability state (cooldown/duration)
            for key, ability in server_p.abilities.items():
                if key in p.abilities:
                    p.abilities[key].cooldown = ability.cooldown
                    p.abilities[key].duration = ability.duration
                else:
                    # If server adds a new ability we don't have, take it
                    p.abilities[key] = ability

        # --- DRAWING ---
        draw_modern_grid(win, scroll)
        
        for wall in last_walls.values():
            wall.draw(win, scroll)

        for p_id, player in all_players.items():
            player.draw(win, scroll)
            
            # Draw names
            screen_px = player.x - scroll[0] + player.width // 2
            screen_py = player.y - (scroll[1] + 20)
            
            # Simple visibility check for text
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
        else:
            draw_text_freetype(FONT_UI, "Нажми ENTER для чата", (120, 120, 120), 10, input_y + 5)

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
            server_ip, nickname, selected_skin = result # NEW: Unpack skin
            game_loop(server_ip, nickname, selected_skin) 
    pygame.quit()
    
def display_error_message(message):
    """Simple blocking function to display a network error before returning to menu."""
    temp_surf = win.copy()
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) 
    temp_surf.blit(overlay, (0, 0))
    
    # Use the freetype function to draw text beautifully
    FONT_TITLE.render_to(temp_surf, (WIDTH//2 - 200, HEIGHT//2 - 50), "ERROR", C_DANGER)
    FONT_HUD.render_to(temp_surf, (WIDTH//2 - 200, HEIGHT//2 + 50), message, C_TEXT_MAIN)
    
    win.blit(temp_surf, (0, 0))
    pygame.display.update()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                waiting = False

if __name__ == "__main__":
    main_app()