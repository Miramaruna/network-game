import pygame, pygame.freetype
pygame.freetype.init()

# ЦВЕТА
C_BG_DEEP     = (5, 5, 10)
C_BG_LIGHT    = (20, 20, 35)
C_NEON_CYAN   = (0, 255, 240)
C_NEON_PINK   = (255, 0, 110)
C_NEON_GREEN  = (57, 255, 20)
C_TEXT_MAIN   = (240, 245, 255)
C_TEXT_DIM    = (100, 110, 130)
C_DANGER      = (255, 50, 50)
C_BG          = (10, 10, 20)
C_GRID_BRIGHT = (60, 60, 100)
C_GRID_DIM    = (30, 30, 50)
C_ACCENT      = (0, 255, 255)
C_TABLE_BG    = (10, 10, 15, 220) # Полупрозрачный фон для таблицы

MAP_WIDTH = 2000  # Эти значения должны соответствовать размерам карты
MAP_HEIGHT = 2000

# from client import get_screen_size

def get_font(name, size, bold=False):
    try:
        return pygame.freetype.SysFont(name, size, bold=bold)
    except:
        return pygame.freetype.SysFont("arial", size, bold=bold)

FONT_BIG   = get_font("impact, verendana, arial black", 70)
FONT_MED   = get_font("segoe ui, roboto, arial", 24)
FONT_SMALL = get_font("consolas, menlo", 14)

# --- ШРИФТЫ ---
FONT_CHOICES = ["arial", "dejavusans", "verdana"]
try:
    import pygame.freetype
    pygame.freetype.init()
    FONT_UI = pygame.freetype.SysFont(FONT_CHOICES, 16)
    FONT_HUD = pygame.freetype.SysFont(FONT_CHOICES, 20, bold=True)
    FONT_TITLE = pygame.freetype.SysFont(FONT_CHOICES, 70, bold=True)
    FONT_DEBUG = pygame.freetype.SysFont("consolas", 14)
    FONT_MED = pygame.freetype.SysFont(FONT_CHOICES, 24, bold=True)
    FONT_SMALL = pygame.freetype.SysFont(FONT_CHOICES, 14)
    FONT_TABLE = pygame.freetype.SysFont("consolas, menlo", 16, bold=True)
except:
    pass # Fallback если freetype не работает

def get_screen_size(surface):
    return surface.get_width(), surface.get_height()

class UIElement:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.hovered = False
        self.anim_progress = 0.0

    def update(self, mx, my):
        self.hovered = self.rect.collidepoint(mx, my)
        target = 1.0 if self.hovered else 0.0
        self.anim_progress += (target - self.anim_progress) * 0.2

class NeonButton(UIElement):
    def __init__(self, text, x, y, w=250, h=50, color=C_NEON_CYAN):
        super().__init__(x, y, w, h)
        self.text = text
        self.base_color = color
        self.text = text
        self.font = FONT_MED
        self.color = color
        
        self._pre_render()

    def draw(self, surface):
        
        scale_w = self.rect.w + (10 * self.anim_progress)
        scale_h = self.rect.h + (4 * self.anim_progress)
        
        draw_rect = pygame.Rect(0, 0, scale_w, scale_h)
        draw_rect.center = self.rect.center
        
        bg_alpha = 30 + (50 * self.anim_progress)
        s = pygame.Surface((draw_rect.w, draw_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (*self.base_color, int(bg_alpha)), s.get_rect(), border_radius=15)
        
        border_width = 2 if self.anim_progress < 0.5 else 3
        glow_alpha = 100 + (155 * self.anim_progress)
        pygame.draw.rect(s, (*self.base_color, int(glow_alpha)), s.get_rect(), border_width, border_radius=15)
        
        surface.blit(s, draw_rect.topleft)

        txt_col = C_TEXT_MAIN if self.hovered else C_TEXT_DIM
        text_surf, text_rect = FONT_MED.render(self.text, txt_col)
        text_rect.center = draw_rect.center
        
        shadow_surf, shadow_rect = FONT_MED.render(self.text, (0,0,0))
        shadow_rect.center = (draw_rect.centerx+2, draw_rect.centery+2)
        
        surface.blit(shadow_surf, shadow_rect)
        surface.blit(text_surf, text_rect)
        
    def _pre_render(self):
        # Рендерим текст заранее
        self.text_surf, self.text_rect = self.font.render(self.text, C_TEXT_MAIN)
        self.text_rect.center = self.rect.center
        
        # Создаем статичную подложку с конвертацией для скорости
        self.surface = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA).convert_alpha()
        # Рисуем рамку один раз
        pygame.draw.rect(self.surface, (*self.color, 40), (0, 0, self.rect.w, self.rect.h), border_radius=8)
        pygame.draw.rect(self.surface, self.color, (0, 0, self.rect.w, self.rect.h), 2, border_radius=8)

class NeonInput(UIElement):
    def __init__(self, label, value, x, y, w=300):
        super().__init__(x, y, w, 50)
        self.label = label
        self.value = value
        self.active = False
        
    def draw(self, surface, ticks):
        FONT_SMALL.render_to(surface, (self.rect.x, self.rect.y - 20), self.label, C_TEXT_DIM)
        
        box_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        box_color = (*C_BG_LIGHT, 200)
        pygame.draw.rect(box_surf, box_color, box_surf.get_rect(), border_radius=10)
        
        border_col = (*C_NEON_CYAN, 255) if self.active else (*C_TEXT_DIM, 100)
        pygame.draw.rect(box_surf, border_col, box_surf.get_rect(), 2, border_radius=10)
        
        surface.blit(box_surf, self.rect.topleft)
        
        display_txt = self.value
        if self.active and (ticks // 500) % 2 == 0:
            display_txt += "|"
            
        FONT_MED.render_to(surface, (self.rect.x + 15, self.rect.y + 12), display_txt, C_TEXT_MAIN)

class DebugInterface:
    def __init__(self):
        self.active = False
        self.bg_surf = pygame.Surface((320, 280), pygame.SRCALPHA)
        self.bg_surf.fill((0, 0, 0, 200)) 
        pygame.draw.rect(self.bg_surf, C_NEON_CYAN, self.bg_surf.get_rect(), 2, border_radius=5)

    def toggle(self):
        self.active = not self.active
        return self.active

    def draw(self, win, p, players, fps, network_obj):
        if not self.active: return
        win.blit(self.bg_surf, (10, 10))
        
        ping = max(0, int(network_obj.latency))
        ping_col = (0, 255, 0) if ping < 60 else (255, 255, 0) if ping < 120 else (255, 0, 0)

        stats_lines = [
            f"--- SYSTEM ---",
            f"FPS: {int(fps)}",
            f"PING: {ping} ms",
            f"ENTITIES: {len(players)}",
            f"--- PLAYER ---",
            f"POS: ({int(p.x)}, {int(p.y)})",
            f"HP: {p.hp}",
            f"--- NETWORK ---",
            f"UP: {network_obj.traffic_stats['sent_per_sec']:.1f} KB/s",
            f"DOWN: {network_obj.traffic_stats['recv_per_sec']:.1f} KB/s",
            f"TOTAL RECV: {network_obj.traffic_stats['recv_total'] / 1024:.1f} KB",
        ]

        y_offset = 20
        for line in stats_lines:
            col = ping_col if "PING" in line else (0, 255, 0)
            if "---" in line: col = C_NEON_CYAN
            FONT_DEBUG.render_to(win, (25, 10 + y_offset), line, col)
            y_offset += 18

def draw_text_freetype(font_obj, text, color, x, y, center=False, win=None):
    if not win: return
    shadow_surf, shadow_rect = font_obj.render(text, (0, 0, 0))
    main_surf, main_rect = font_obj.render(text, color)
    if center:
        main_rect.center = (x, y)
        shadow_rect.center = (x + 2, y + 2)
    else:
        main_rect.topleft = (x, y)
        shadow_rect.topleft = (x + 2, y + 2)
    win.blit(shadow_surf, shadow_rect)
    win.blit(main_surf, main_rect)
    
def draw_custom_cursor(win, mx, my):
    pygame.draw.circle(win, C_ACCENT, (mx, my), 8, 1)
    pygame.draw.line(win, C_ACCENT, (mx - 12, my), (mx + 12, my), 1)
    pygame.draw.line(win, C_ACCENT, (mx, my - 12), (mx, my + 12), 1)
    
def draw_modern_grid(win, scroll):
    WIDTH, HEIGHT = get_screen_size(win)
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

def draw_cyber_health(surface, x, y, w, h, current_hp, max_hp=100, anim_hp=None):
    if anim_hp is None: anim_hp = current_hp
    pct = max(0, min(1, current_hp / max_hp))
    anim_pct = max(0, min(1, anim_hp / max_hp))
    
    rect_bg = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, (20, 20, 30), rect_bg, border_radius=4)
    
    if anim_hp > current_hp:
        w_anim = int(w * anim_pct)
        pygame.draw.rect(surface, (200, 50, 50), (x, y, w_anim, h), border_radius=4)

    w_curr = int(w * pct)
    main_col = C_NEON_GREEN if pct > 0.5 else (255, 200, 0) if pct > 0.25 else C_DANGER
    
    if w_curr > 0:
        pygame.draw.rect(surface, main_col, (x, y, w_curr, h), border_radius=4)
        pygame.draw.rect(surface, (255, 255, 255, 100), (x, y, w_curr, h//3), border_radius=4)

    for i in range(1, 10):
        lx = x + (w * (i/10))
        pygame.draw.line(surface, (0, 0, 0), (lx, y), (lx, y+h), 2)

    pygame.draw.rect(surface, (255, 255, 255), rect_bg, 2, border_radius=4)
    
    txt_surf, txt_rect = FONT_HUD.render(f"{int(current_hp)} / {max_hp}", (255, 255, 255))
    shadow_surf, shadow_rect = FONT_HUD.render(f"{int(current_hp)} / {max_hp}", (0, 0, 0))
    
    text_w, text_h = txt_surf.get_size()
    tx = x + w//2 - text_w//2
    ty = y + h//2 - text_h//2
    surface.blit(shadow_surf, (tx+2, ty+2)) 
    surface.blit(txt_surf, (tx, ty))
    
# --- ФУНКЦИЯ ОТРИСОВКИ ТАБЛИЦЫ ЛИДЕРОВ (SCOREBOARD) ---
def draw_scoreboard(surface, players, my_id):
    w, h = get_screen_size(surface)
    board_w = 700
    board_h = 500
    x = w // 2 - board_w // 2
    y = h // 2 - board_h // 2
    
    # Фон
    s = pygame.Surface((board_w, board_h), pygame.SRCALPHA)
    pygame.draw.rect(s, C_TABLE_BG, s.get_rect(), border_radius=10)
    pygame.draw.rect(s, C_NEON_CYAN, s.get_rect(), 2, border_radius=10)
    
    # Заголовки
    headers = ["NICKNAME", "KILLS", "DEATHS", "K/D", "PING"]
    col_x = [30, 300, 400, 500, 600]
    
    for i, head in enumerate(headers):
        FONT_TABLE.render_to(s, (col_x[i], 20), head, C_TEXT_DIM)
    
    pygame.draw.line(s, C_NEON_CYAN, (20, 50), (board_w-20, 50), 1)
    
    # Сортировка игроков по убийствам
    sorted_players = sorted(players.values(), key=lambda p: p.kills, reverse=True)
    
    y_off = 70
    for p in sorted_players:
        if y_off > board_h - 40: break
        
        # Цвет строки (свой игрок выделен)
        row_col = C_NEON_GREEN if p.id == my_id else C_TEXT_MAIN
        
        # Расчет K/D
        kd = 0.0
        if p.deaths > 0: kd = p.kills / p.deaths
        elif p.kills > 0: kd = float(p.kills) # Если смертей 0, а убийства есть
        
        # Отрисовка данных
        FONT_TABLE.render_to(s, (col_x[0], y_off), str(p.nickname)[:18], row_col)
        FONT_TABLE.render_to(s, (col_x[1], y_off), str(p.kills), row_col)
        FONT_TABLE.render_to(s, (col_x[2], y_off), str(p.deaths), row_col)
        FONT_TABLE.render_to(s, (col_x[3], y_off), f"{kd:.1f}", row_col)
        
        # Пинг с цветом
        ping_val = p.ping
        ping_col = (0,255,0) if ping_val < 60 else (255,255,0) if ping_val < 120 else (255,0,0)
        FONT_TABLE.render_to(s, (col_x[4], y_off), f"{ping_val}ms", ping_col)
        
        y_off += 30
        
    surface.blit(s, (x, y))