import pygame, math
from client import win, get_font, MAP_WIDTH, MAP_HEIGHT, WIDTH, HEIGHT

C_BG_DEEP     = (5, 5, 10)       # Почти черный
C_BG_LIGHT    = (20, 20, 35)     # Светлее для полей
C_NEON_CYAN   = (0, 255, 240)    # Основной акцент
C_NEON_PINK   = (255, 0, 110)    # Вторичный акцент (враги/выход)
C_NEON_GREEN  = (57, 255, 20)    # Успех
C_TEXT_MAIN   = (240, 245, 255)  # Белый с оттенком
C_TEXT_DIM    = (100, 110, 130)  # Серый текст
C_OVERLAY     = (0, 0, 0, 120)   # Затемнение
C_ACCENT = (0, 255, 255)

C_DANGER = (255, 50, 50)
C_BG = (10, 10, 20)
C_GRID_DIM = (30, 30, 50)
C_GRID_BRIGHT = (60, 60, 100)
    
class DebugInterface:
    def __init__(self):
        self.active = False
        self.bg_surf = pygame.Surface((320, 260), pygame.SRCALPHA) # Чуть увеличил размер
        self.bg_surf.fill((0, 0, 0, 200)) 
        pygame.draw.rect(self.bg_surf, C_NEON_CYAN, self.bg_surf.get_rect(), 2, border_radius=5)

    def toggle(self):
        self.active = not self.active
        return self.active

    def draw(self, win, p, players, fps, network_obj):
        if not self.active:
            return

        win.blit(self.bg_surf, (10, 10))
        
        # Цвет пинга
        # ping = int(network_obj.latency)
        ping = max(0, int(network_obj.latency))
        ping_col = (0, 255, 0) if ping < 60 else (255, 255, 0) if ping < 120 else (255, 0, 0)

        stats_lines = [
            f"--- SYSTEM ---",
            f"FPS: {int(fps)}",
            f"PING: {ping} ms",  # PING HERE
            f"ENTITIES: {len(players)}",
            f"--- PLAYER ---",
            f"POS: ({int(p.x)}, {int(p.y)})",
            f"HP: {p.hp}",
            f"--- NETWORK ---",
            f"UP: {network_obj.traffic_stats['sent_per_sec']:.1f} KB/s",
            f"DOWN: {network_obj.traffic_stats['recv_per_sec']:.1f} KB/s",
            f"TOTAL SENT: {network_obj.traffic_stats['sent_total'] / 1024:.1f} KB", # Поправил на MB если число большое, но пока оставим KB
            f"PACKET SIZE: {network_obj.traffic_stats['last_packet_size_recv']} B",
        ]

        y_offset = 20
        for line in stats_lines:
            col = ping_col if "PING" in line else (0, 255, 0)
            if "---" in line: col = C_NEON_CYAN
            
            # Рендер текста
            # txt = FONT_DEBUG.render(line, True, col)
            # win.blit(txt, (25, 10 + y_offset))
            FONT_DEBUG.render_to(win, (25, 10 + y_offset), line, col)
            y_offset += 18

FONT_BIG   = get_font("impact, verendana, arial black", 70)
FONT_MED   = get_font("segoe ui, roboto, arial", 24)
FONT_SMALL = get_font("consolas, menlo", 14)
# FONT_CHOICES = ["arial", "consolas"]
FONT_CHOICES = ["arial", "dejavusans", "verdana"] 
try:
    FONT_UI = pygame.freetype.Font("arial", 16)
    FONT_HUD = pygame.freetype.Font("arial", 20)
    FONT_TITLE = pygame.freetype.Font("arial", 70)
    FONT_DEBUG = pygame.freetype.SysFont("consolas", 14) # Моноширинный шрифт для дебага
except:
    FONT_UI = pygame.freetype.SysFont(FONT_CHOICES, 16)
    FONT_HUD = pygame.freetype.SysFont(FONT_CHOICES, 20, bold=True)
    FONT_TITLE = pygame.freetype.SysFont(FONT_CHOICES, 70, bold=True)
    FONT_DEBUG = pygame.freetype.SysFont("courier", 14)

class UIElement:
    """Базовый класс для UI с анимацией"""
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.hovered = False
        self.anim_progress = 0.0 # 0.0 to 1.0

    def update(self, mx, my):
        self.hovered = self.rect.collidepoint(mx, my)
        target = 1.0 if self.hovered else 0.0
        # Лерп (плавная интерполяция)
        self.anim_progress += (target - self.anim_progress) * 0.2

class NeonButton(UIElement):
    def __init__(self, text, x, y, w=250, h=50, color=C_NEON_CYAN, action=None):
        super().__init__(x, y, w, h)
        self.text = text
        self.base_color = color
        self.action = action

    def draw(self, surface):
        # Эффект "дыхания" и расширения при наведении
        scale_w = self.rect.w + (10 * self.anim_progress)
        scale_h = self.rect.h + (4 * self.anim_progress)
        
        # Центрируем относительно оригинальной позиции
        draw_rect = pygame.Rect(0, 0, scale_w, scale_h)
        draw_rect.center = self.rect.center
        
        # Цвет фона (полупрозрачный)
        bg_alpha = 30 + (50 * self.anim_progress)
        s = pygame.Surface((draw_rect.w, draw_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (*self.base_color, int(bg_alpha)), s.get_rect(), border_radius=15)
        
        # Неоновая обводка (Glow)
        border_width = 2 if self.anim_progress < 0.5 else 3
        glow_alpha = 100 + (155 * self.anim_progress)
        pygame.draw.rect(s, (*self.base_color, int(glow_alpha)), s.get_rect(), border_width, border_radius=15)
        
        surface.blit(s, draw_rect.topleft)

        # Текст
        txt_col = C_TEXT_MAIN if self.hovered else C_TEXT_DIM
        text_surf, text_rect = FONT_MED.render(self.text, txt_col)
        text_rect.center = draw_rect.center
        
        # Тень текста для читаемости
        shadow_surf, shadow_rect = FONT_MED.render(self.text, (0,0,0))
        shadow_rect.center = (draw_rect.centerx+2, draw_rect.centery+2)
        
        surface.blit(shadow_surf, shadow_rect)
        surface.blit(text_surf, text_rect)

class NeonInput(UIElement):
    def __init__(self, label, value, x, y, w=300):
        super().__init__(x, y, w, 50)
        self.label = label
        self.value = value
        self.active = False
        
    def draw(self, surface, ticks):
        # Фон поля
        color = C_NEON_CYAN if self.active else (60, 60, 80)
        
        # Label (над полем)
        FONT_SMALL.render_to(surface, (self.rect.x, self.rect.y - 20), self.label, C_TEXT_DIM)
        
        # Основной бокс
        box_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        box_color = (*C_BG_LIGHT, 200)
        pygame.draw.rect(box_surf, box_color, box_surf.get_rect(), border_radius=10)
        
        # Обводка
        border_col = (*C_NEON_CYAN, 255) if self.active else (*C_TEXT_DIM, 100)
        pygame.draw.rect(box_surf, border_col, box_surf.get_rect(), 2, border_radius=10)
        
        surface.blit(box_surf, self.rect.topleft)
        
        # Текст внутри
        display_txt = self.value
        if self.active and (ticks // 500) % 2 == 0:
            display_txt += "|"
            
        FONT_MED.render_to(surface, (self.rect.x + 15, self.rect.y + 12), display_txt, C_TEXT_MAIN)
        
def draw_text_freetype(font_obj, text, color, x, y, center=False):
    if isinstance(font_obj, pygame.font.Font):
        font_obj.render(text, True, color)
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
    
def draw_custom_cursor(mx, my):
    pygame.draw.circle(win, C_ACCENT, (mx, my), 8, 1)
    pygame.draw.line(win, C_ACCENT, (mx - 12, my), (mx + 12, my), 1)
    pygame.draw.line(win, C_ACCENT, (mx, my - 12), (mx, my + 12), 1)
    
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
        
def draw_vignette(surface):
    """Затемнение по краям"""
    vignette_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for x in range(WIDTH):
        for y in range(HEIGHT):
            dx = x - WIDTH // 2
            dy = y - HEIGHT // 2
            dist = math.sqrt(dx**2 + dy**2)
            alpha = min(255, int(dist / (WIDTH * 0.65) * 255))
            if alpha > 40:
                vignette_surf.set_at((x, y), (0, 0, 0, alpha))
                

def draw_cyber_health(surface, x, y, w, h, current_hp, max_hp=100, anim_hp=None):
    """
    Рисует стилизованный Health Bar.
    anim_hp - это 'медленное' здоровье для эффекта получения урона.
    """
    if anim_hp is None: anim_hp = current_hp
    
    pct = max(0, min(1, current_hp / max_hp))
    anim_pct = max(0, min(1, anim_hp / max_hp))
    
    # 1. Подложка (Background)
    # Делаем скошенные углы
    rect_bg = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, (20, 20, 30), rect_bg, border_radius=4)
    
    # 2. Анимированный урон (Красный шлейф)
    if anim_hp > current_hp:
        w_anim = int(w * anim_pct)
        pygame.draw.rect(surface, (200, 50, 50), (x, y, w_anim, h), border_radius=4)

    # 3. Основное здоровье (Градиент или Solid)
    w_curr = int(w * pct)
    
    # Выбор цвета в зависимости от HP
    main_col = C_NEON_GREEN
    if pct < 0.5: main_col = (255, 200, 0)
    if pct < 0.25: main_col = C_DANGER
    
    if w_curr > 0:
        # Рисуем полоску
        hp_rect = pygame.Rect(x, y, w_curr, h)
        pygame.draw.rect(surface, main_col, hp_rect, border_radius=4)
        
        # Эффект "блика" сверху
        pygame.draw.rect(surface, (255, 255, 255, 100), (x, y, w_curr, h//3), border_radius=4)

    # 4. Сетка / Сегменты (Grid lines)
    # Рисуем черные вертикальные линии каждые 10%
    for i in range(1, 10):
        lx = x + (w * (i/10))
        pygame.draw.line(surface, (0, 0, 0), (lx, y), (lx, y+h), 2)

    # 5. Рамка (Border)
    pygame.draw.rect(surface, (255, 255, 255), rect_bg, 2, border_radius=4)
    
    # 6. Текст
    hp_text = f"{int(current_hp)} / {max_hp}"
    # txt_surf = FONT_HUD.render(hp_text, True, (255, 255, 255))
    # # Тень текста
    # shadow = FONT_HUD.render(hp_text, True, (0, 0, 0))
    
    # # Центрируем текст
    # tx = x + w//2 - txt_surf.get_width()//2
    # ty = y + h//2 - txt_surf.get_height()//2
    
    # surface.blit(shadow, (tx+1, ty+1))
    # surface.blit(txt_surf, (tx, ty))
    
    # FONT_HUD.render возвращает (Surface, Rect). Распаковываем!
    txt_surf, txt_rect = FONT_HUD.render(hp_text, (255, 255, 255))
    shadow_surf, shadow_rect = FONT_HUD.render(hp_text, (0, 0, 0))

    # Получаем размер текста
    text_w, text_h = txt_surf.get_size()
    
    # Центрируем текст
    tx = x + w//2 - text_w//2
    ty = y + h//2 - text_h//2
    
    # Рисуем тень и основной текст
    surface.blit(shadow_surf, (tx+2, ty+2)) 
    surface.blit(txt_surf, (tx, ty))