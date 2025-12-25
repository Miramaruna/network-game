import pygame
import math
import random
import time
import os
import json

names = []

def load_nicknames():
    global names
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "Config", "nicknames.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            names = data.get("names", [])
    except Exception as e:
        print(f"Ошибка загрузки nicknames.json: {e}")
        names = ["Bot_Vasyan", "CyberDemon", "RoboCop", "Data", "Marvin", "WALL-E", "Bender", "T-800", "C-3PO", "R2-D2"]
        
load_nicknames()

# --- CACHE (Оставляем как было) ---
PARTICLE_SURF_CACHE = {}
C_NEON_CYAN = (0, 255, 255)

def get_particle_surf(size, color, alpha):
    # Преобразуем список цветов в кортеж, чтобы использовать как ключ словаря
    color_tuple = tuple(color)
    key = (size, color_tuple, alpha)
    if key not in PARTICLE_SURF_CACHE:
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        s.fill((*color_tuple, alpha))
        PARTICLE_SURF_CACHE[key] = s
    return PARTICLE_SURF_CACHE[key]

class Ability:
    def __init__(self, name, cooldown_frames, duration_frames):
        self.name = name
        self.cooldown_max = cooldown_frames
        self.duration_max = duration_frames
        self.cooldown = 0
        self.duration = 0
    
    def activate(self, player_obj):
        if self.cooldown <= 0:
            self.duration = self.duration_max
            self.cooldown = self.cooldown_max
            return True
        return False
        
    def update(self):
        if self.duration > 0: self.duration -= 1
        if self.cooldown > 0: self.cooldown -= 1
        
class ShieldAbility(Ability):
    def __init__(self):
        super().__init__("SHIELD", cooldown_frames=300, duration_frames=180)

class WallAbility(Ability):
    def __init__(self):
        super().__init__("WALL", cooldown_frames=450, duration_frames=300)

class Wall:
    __slots__ = ('x', 'y', 'width', 'height', 'color', 'rect', 'lifetime', 'id', 'created_time')
    WALL_DURATION = 5.0 

    def __init__(self, x, y, wall_id):
        self.x = x
        self.y = y
        self.width = 100
        self.height = 10
        self.color = (150, 150, 255)
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.id = wall_id
        self.created_time = time.time()
        self.lifetime = Wall.WALL_DURATION 

    def draw(self, win, scroll):
        screen_x = self.x - scroll[0]
        screen_y = self.y - scroll[1]
        time_left = self.created_time + self.WALL_DURATION - time.time()
        alpha = 255
        if time_left < 1.0: 
            self.color = (255, 50, 50)
            if (time.time() * 10) % 1.0 < 0.5: alpha = 100

        wall_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        wall_surf.fill((100, 100, 200, 150))
        pygame.draw.rect(wall_surf, self.color, (0, 0, self.width, self.height), 2)
        wall_surf.set_alpha(alpha)
        win.blit(wall_surf, (screen_x, screen_y))

class Player:
    
    __slots__ = ('x', 'y', 'width', 'height', 'color', 'rect', 'vel', 'hp', 
                'bullets', 'id', 'nickname', 'last_move', 'trail_particles', 'skin_id', 'abilities', 
                'trail_color', 'outline_color')

    def __init__(self, x, y, width, height, color, p_id):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color # Это Body Color
        self.trail_color = color # По умолчанию след такой же как тело
        self.outline_color = (255, 255, 255) # По умолчанию белый
        
        self.rect = pygame.Rect(x, y, width, height)
        self.vel = 5
        self.hp = 100
        self.bullets = []
        self.id = p_id 
        self.nickname = f"Игрок_{p_id}"
        self.last_move = (0, 0) 
        self.trail_particles = []
        self.skin_id = "DEFAULT" 
        self.abilities = {
            "shield": ShieldAbility(),
            "wall": WallAbility(),
        }
    
    def cast_ability(self, ability_key):
        if ability_key in self.abilities:
            if self.abilities[ability_key].cooldown <= 0:
                self.abilities[ability_key].cooldown = self.abilities[ability_key].cooldown_max
                return True
        return False

    def draw(self, win, scroll):
        screen_x = self.x - scroll[0]
        screen_y = self.y - scroll[1]

        if screen_x < -100 or screen_x > 2000 or screen_y < -100 or screen_y > 2000:
            return

        # 1. Trail Animation (Используем self.trail_color)
        self._generate_trail_particles(screen_x, screen_y)
        self._draw_trail_particles(win)
        
        # 2. Body Drawing
        # Shadow
        pygame.draw.rect(win, (20, 20, 20), (screen_x + 3, screen_y + 3, self.width, self.height))
        # Body (Используем self.color)
        pygame.draw.rect(win, self.color, (screen_x + 1, screen_y + 1, self.width - 2, self.height - 2))
        # Outline (Используем self.outline_color)
        pygame.draw.rect(win, self.outline_color, (screen_x, screen_y, self.width, self.height), 3)

        # 3. Shield VFX
        if self.abilities["shield"].duration > 0:
            radius = self.width * 0.7
            s = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 150, 255, 100), (int(radius), int(radius)), int(radius))
            win.blit(s, (screen_x - radius + self.width//2, screen_y - radius + self.height//2))
        
        hp_pct = max(0, self.hp / 100)
        hp_bar_w = self.width + 10 
        hp_bar_h = 6
        
        # Центрирование над игроком
        bar_x = screen_x - 5 
        bar_y = screen_y - 15
        
        # Черная подложка
        pygame.draw.rect(win, (0, 0, 0), (bar_x, bar_y, hp_bar_w, hp_bar_h))
        
        # Цвет (Зеленый -> Желтый -> Красный)
        col = (0, 255, 0)
        if hp_pct < 0.6: col = (255, 255, 0)
        if hp_pct < 0.3: col = (255, 0, 0)
        
        # Сама полоска
        pygame.draw.rect(win, col, (bar_x, bar_y, int(hp_bar_w * hp_pct), hp_bar_h))
        
        # Тонкая неоновая рамка
        pygame.draw.rect(win, C_NEON_CYAN, (bar_x, bar_y, hp_bar_w, hp_bar_h), 1)
        
        # Цвет (Зеленый -> Желтый -> Красный)
        col = (0, 255, 0)
        if hp_pct < 0.6: col = (255, 255, 0)
        if hp_pct < 0.3: col = (255, 0, 0)
        
        # Сама полоска
        pygame.draw.rect(win, col, (bar_x, bar_y, int(hp_bar_w * hp_pct), hp_bar_h))
        
        # Тонкая рамка
        pygame.draw.rect(win, (255, 255, 255), (bar_x, bar_y, hp_bar_w, hp_bar_h), 1)

        # Bullets
        for bullet in self.bullets:
            bx = bullet[0] - scroll[0]
            by = bullet[1] - scroll[1]
            pygame.draw.circle(win, (255, 200, 0), (int(bx-bullet[2]*2), int(by-bullet[3]*2)), 3)
            pygame.draw.circle(win, (255, 200, 0), (int(bx-bullet[2]*1), int(by-bullet[3]*1)), 4)
            pygame.draw.circle(win, (255, 255, 255), (int(bx), int(by)), 5)
            pygame.draw.circle(win, (255, 0, 0), (int(bx), int(by)), 3)

    def _generate_trail_particles(self, screen_x, screen_y):
        dx, dy = self.last_move
        if dx != 0 or dy != 0:
            spawn_x = screen_x + self.width // 2 + (-dx) * (self.width//2)
            spawn_y = screen_y + self.height // 2 + (-dy) * (self.height//2)
            
            spawn_x += random.uniform(-10, 10)
            spawn_y += random.uniform(-10, 10)

            size = random.randint(3, 7)
            lifetime = random.randint(15, 30)
            # ВАЖНО: сохраняем цвет частицы при создании
            self.trail_particles.append([spawn_x, spawn_y, size, lifetime, self.trail_color])
    
    def _draw_trail_particles(self, win):
        new_particles = []
        rand_uniform = random.uniform
        
        for p in self.trail_particles:
            p[3] -= 1 
            if p[3] > 0:
                p[0] += rand_uniform(-0.5, 0.5)
                p[1] += rand_uniform(-0.5, 0.5)
                alpha = int(255 * (p[3] / 30))
                alpha = max(0, min(255, alpha))
                # Используем цвет из частицы (p[4]), который мы задали в _generate
                s = get_particle_surf(p[2], p[4], alpha)
                win.blit(s, (int(p[0]), int(p[1])))
                new_particles.append(p)
        self.trail_particles = new_particles

    def move(self, map_width, map_height):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_a] and self.x > 0: 
            self.x -= self.vel; dx = -1
        if keys[pygame.K_d] and self.x < map_width - self.width: 
            self.x += self.vel; dx = 1
        if keys[pygame.K_w] and self.y > 0: 
            self.y -= self.vel; dy = -1
        if keys[pygame.K_s] and self.y < map_height - self.height: 
            self.y += self.vel; dy = 1
        
        self.last_move = (dx, dy) 
        self.update(map_width, map_height)
        
    def setPose(self, x, y):
        self.x = x
        self.y = y
        self.update_rect()

    def update(self, map_width, map_height):
        self.update_rect()
        to_remove = []
        for bullet in self.bullets:
            bullet[0] += bullet[2]
            bullet[1] += bullet[3]
            if not (-100 < bullet[0] < map_width + 100 and -100 < bullet[1] < map_height + 100):
                to_remove.append(bullet)
        for b in to_remove: self.bullets.remove(b)

    def update_rect(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def deleteBullet(self, bullet):
        if bullet in self.bullets: self.bullets.remove(bullet)

    def shoot(self, target_x, target_y, scroll=None):
        if scroll:
            world_target_x = target_x + scroll[0]
            world_target_y = target_y + scroll[1]
        else:
            world_target_x = target_x
            world_target_y = target_y
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        dx = world_target_x - center_x
        dy = world_target_y - center_y
        angle = math.atan2(dy, dx)
        speed = 15 
        speed_x = speed * math.cos(angle)
        speed_y = speed * math.sin(angle)
        spawn_dist = 45
        spawn_x = center_x + (math.cos(angle) * spawn_dist)
        spawn_y = center_y + (math.sin(angle) * spawn_dist)
        self.bullets.append([spawn_x, spawn_y, speed_x, speed_y])
        
    def respawn(self, map_width, map_height):
        self.hp = 100
        self.bullets = [] 
        self.last_move = (0,0)

class Bot(Player):
    def __init__(self, x, y, width, height, color, p_id):
        super().__init__(x, y, width, height, color, p_id)
        
        self.nickname = f"[BOT] {random.choice(names)}"
        self.shoot_cooldown = 0
        self.change_dir_timer = 0
        self.random_dir = (0, 0)
        self.view_radius = 800
        
    def ai_move(self, all_players, map_width, map_height):
        # 1. Поиск ближайшей цели
        closest_dist = float('inf')
        target = None
        my_center = (self.x + self.width//2, self.y + self.height//2)
        
        if self.hp <= 0:
            self.x = random.randint(100, 2000 - 100)
            self.y = random.randint(100, 2000 - 100)
            self.hp = 100

        
        for p_id, p in all_players.items():
            if p.id != self.id and p.hp > 0: # Игнорируем мертвых
                other_center = (p.x + p.width//2, p.y + p.height//2)
                dist = math.sqrt((my_center[0]-other_center[0])**2 + (my_center[1]-other_center[1])**2)
                
                if dist < closest_dist and dist < self.view_radius:
                    closest_dist = dist
                    target = p

        dx, dy = 0, 0
        
        if target:
            # Логика боя
            t_center = (target.x + target.width//2, target.y + target.height//2)
            angle = math.atan2(t_center[1] - my_center[1], t_center[0] - my_center[0])
            
            dist_to_keep = 300
            if closest_dist > dist_to_keep:
                self.x += math.cos(angle) * (self.vel * 0.8)
                self.y += math.sin(angle) * (self.vel * 0.8)
                dx = 1 if math.cos(angle) > 0 else -1
                dy = 1 if math.sin(angle) > 0 else -1
            elif closest_dist < 150:
                self.x -= math.cos(angle) * (self.vel * 0.8)
                self.y -= math.sin(angle) * (self.vel * 0.8)
            
            if self.shoot_cooldown <= 0:
                aim_x = target.x + random.randint(-20, 20)
                aim_y = target.y + random.randint(-20, 20)
                self.shoot(aim_x, aim_y)
                self.shoot_cooldown = 40
                
        else:
            # Патруль
            if self.change_dir_timer <= 0:
                angle = random.uniform(0, math.pi * 2)
                self.random_dir = (math.cos(angle), math.sin(angle))
                self.change_dir_timer = 100
            
            self.x += self.random_dir[0] * 2
            self.y += self.random_dir[1] * 2
            self.change_dir_timer -= 1
            dx = 1 if self.random_dir[0] > 0 else -1
            dy = 1 if self.random_dir[1] > 0 else -1

        self.x = max(0, min(self.x, map_width - self.width))
        self.y = max(0, min(self.y, map_height - self.height))

        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
        self.last_move = (dx, dy)
        self.update(map_width, map_height)