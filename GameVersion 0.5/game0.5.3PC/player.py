import pygame
import math
import random
import time

# Pre-generate particle surfaces to avoid creating them every frame
# Dictionary mapping size -> surface with alpha support
PARTICLE_SURF_CACHE = {}

def get_particle_surf(size, color, alpha):
    key = (size, color, alpha)
    if key not in PARTICLE_SURF_CACHE:
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        s.fill((*color, alpha))
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
        """Server-side activation logic. Returns True if successful."""
        if self.cooldown <= 0:
            self.duration = self.duration_max
            self.cooldown = self.cooldown_max
            return True
        return False
        
    def update(self):
        """Called every frame by the server."""
        if self.duration > 0:
            self.duration -= 1
        if self.cooldown > 0:
            self.cooldown -= 1
        
class ShieldAbility(Ability):
    def __init__(self):
        super().__init__("SHIELD", cooldown_frames=300, duration_frames=180) # 30s cooldown, 3s duration (at 60 FPS)

class WallAbility(Ability):
    def __init__(self):
        super().__init__("WALL", cooldown_frames=450, duration_frames=300) # 45s cooldown, Wall life tracked by Wall object

class Wall:
    __slots__ = ('x', 'y', 'width', 'height', 'color', 'rect', 'lifetime', 'id', 'created_time')
    
    WALL_DURATION = 5.0 # seconds

    def __init__(self, x, y, wall_id):
        self.x = x
        self.y = y
        self.width = 100
        self.height = 10
        self.color = (150, 150, 255) # Neon purple/blue
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.id = wall_id
        self.created_time = time.time()
        self.lifetime = Wall.WALL_DURATION # Server tracks actual time

    def draw(self, win, scroll):
        screen_x = self.x - scroll[0]
        screen_y = self.y - scroll[1]
        
        # Simple VFX: Blinking effect for remaining time
        time_left = self.created_time + self.WALL_DURATION - time.time()
        alpha = 255
        if time_left < 1.0: # Blink red when almost gone
            self.color = (255, 50, 50)
            if (time.time() * 10) % 1.0 < 0.5:
                 alpha = 100

        wall_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Inner glow
        wall_surf.fill((100, 100, 200, 150))
        # Solid border
        pygame.draw.rect(wall_surf, self.color, (0, 0, self.width, self.height), 2)
        wall_surf.set_alpha(alpha)
        
        win.blit(wall_surf, (screen_x, screen_y))

class Player:
    # __slots__ restricts the object to these specific attributes, saving massive RAM
    __slots__ = ('x', 'y', 'width', 'height', 'color', 'rect', 'vel', 'hp', 
                'bullets', 'id', 'nickname', 'last_move', 'trail_particles', 
                'is_respawning', 'is_dead', 'skin_id', 'abilities')

    def __init__(self, x, y, width, height, color, p_id):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        # Optimization: Create Rect once and update it, rather than creating new Rects constantly
        self.rect = pygame.Rect(x, y, width, height)
        self.vel = 5
        self.hp = 100
        self.bullets = []
        self.id = p_id 
        self.nickname = f"Игрок_{p_id}"
        self.last_move = (0, 0) 
        self.trail_particles = []
        self.is_respawning = False
        self.is_dead = False,
        self.skin_id = "DEFAULT" # New attribute for skin system
        self.abilities = {
            "shield": ShieldAbility(),
            "wall": WallAbility(),
        }
    
    def cast_ability(self, ability_key):
        if ability_key in self.abilities:
            # On the client, we just reset the cooldown locally for UI/Prediction
            # The server will confirm the true activation
            if self.abilities[ability_key].cooldown <= 0:
                self.abilities[ability_key].cooldown = self.abilities[ability_key].cooldown_max
                return True
        return False

    def draw(self, win, scroll):
        screen_x = self.x - scroll[0]
        screen_y = self.y - scroll[1]

        # OPTIMIZATION: Culling (Don't draw if completely off-screen)
        # Assuming screen size approx 900x700, adding buffer
        if screen_x < -100 or screen_x > 1000 or screen_y < -100 or screen_y > 800:
            return

        # 1. Trail Animation
        self._generate_trail_particles(screen_x, screen_y)
        self._draw_trail_particles(win)
        
        # 2. Body Drawing (Skin Placeholder)
        # Shadow
        pygame.draw.rect(win, (20, 20, 20), (screen_x + 3, screen_y + 3, self.width, self.height))
        # Body (Use self.color as fallback for skin)
        pygame.draw.rect(win, self.color, (screen_x + 1, screen_y + 1, self.width - 2, self.height - 2))
        # Outline
        pygame.draw.rect(win, (255, 255, 255), (screen_x, screen_y, self.width, self.height), 3)

        # 3. Shield VFX Drawing (Client-side draw for active shield)
        if self.abilities["shield"].duration > 0:
            # Draw a translucent blue circle
            radius = self.width * 0.7
            s = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 150, 255, 100), (int(radius), int(radius)), int(radius)) # Semi-transparent blue
            win.blit(s, (screen_x - radius + self.width//2, screen_y - radius + self.height//2))

        # 3. HP Bar
        hp_pct = self.hp / 100
        hp_bar_w = int(self.width * hp_pct)
        hp_color = (0, 255, 0) if self.hp > 30 else (255, 50, 50)
        
        pygame.draw.rect(win, (50, 50, 50), (screen_x, screen_y - 15, self.width, 8))
        pygame.draw.rect(win, hp_color, (screen_x, screen_y - 15, hp_bar_w, 8))
        pygame.draw.rect(win, (255, 255, 255), (screen_x, screen_y - 15, self.width, 8), 1)

        for i, bullet in enumerate(self.bullets):
            bx = bullet[0] - scroll[0]
            by = bullet[1] - scroll[1]
            
            # Неоновый след
            pygame.draw.circle(win, (255, 200, 0), (int(bx-bullet[2]*2), int(by-bullet[3]*2)), 3)
            pygame.draw.circle(win, (255, 200, 0), (int(bx-bullet[2]*1), int(by-bullet[3]*1)), 4)
            # Основная пуля
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
            self.trail_particles.append([spawn_x, spawn_y, size, lifetime, self.color])
    
    def _draw_trail_particles(self, win):
        new_particles = []
        rand_uniform = random.uniform # Local optimization
        
        for p in self.trail_particles:
            p[3] -= 1 
            if p[3] > 0:
                p[0] += rand_uniform(-0.5, 0.5)
                p[1] += rand_uniform(-0.5, 0.5)
                
                # Use Cached Surface instead of creating new one
                alpha = int(255 * (p[3] / 30))
                # Clamp alpha for safety
                alpha = max(0, min(255, alpha))
                
                # Get surface from cache
                s = get_particle_surf(p[2], p[4], alpha)
                win.blit(s, (int(p[0]), int(p[1])))
                new_particles.append(p)
        
        self.trail_particles = new_particles

    def move(self, map_width, map_height):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        
        if keys[pygame.K_a] and self.x > 0: 
            self.x -= self.vel
            dx = -1
        if keys[pygame.K_d] and self.x < map_width - self.width: 
            self.x += self.vel
            dx = 1
        if keys[pygame.K_w] and self.y > 0: 
            self.y -= self.vel
            dy = -1
        if keys[pygame.K_s] and self.y < map_height - self.height: 
            self.y += self.vel
            dy = 1
        
        self.last_move = (dx, dy) 
        self.update(map_width, map_height)
        
    def setPose(self, x, y):
        self.x = x
        self.y = y
        self.update_rect() # Sync rect immediately
        return

    def update(self, map_width, map_height):
        self.update_rect()
        
        # Bullet update
        # Using list comprehension for filtering might be slightly faster, 
        # but in-place modification is fine here.
        to_remove = []
        for bullet in self.bullets:
            bullet[0] += bullet[2]
            bullet[1] += bullet[3]
            if not (-100 < bullet[0] < map_width + 100 and -100 < bullet[1] < map_height + 100):
                to_remove.append(bullet)
        
        for b in to_remove:
            self.bullets.remove(b)

    def update_rect(self):
        # Update the existing rect object properties
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def deleteBullet(self, bullet):
        if bullet in self.bullets:
            self.bullets.remove(bullet)

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
        
        spawn_distance = 45
        spawn_x = center_x + (math.cos(angle) * spawn_distance)
        spawn_y = center_y + (math.sin(angle) * spawn_distance)
        
        self.bullets.append([spawn_x, spawn_y, speed_x, speed_y])
        
    def respawn(self, map_width, map_height):
        self.hp = 100
        self.bullets = [] 
        self.last_move = (0,0)
        self.is_dead = False
        self.is_respawning = False

class Bot(Player):
    # Slots for Bot-specific attributes
    __slots__ = ('shoot_cooldown', 'change_dir_timer', 'random_dir', 'view_radius')

    def __init__(self, x, y, width, height, color, p_id):
        super().__init__(x, y, width, height, color, p_id)
        names = ["Terminator", "HAL-9000", "Skynet", "GLaDOS", "Bot_Vasyan", "CyberDemon", "RoboCop", "Data", "Marvin", "WALL-E", "Bender", "T-800", "C-3PO", "R2-D2", "Optimus", "Megatron", "Ultron", "Jarvis", "Sonny", "Chappie", "ED-209", "Claptrap", "Droid", "Machine", "Cyborg"]
        self.nickname = f"[BOT] {random.choice(names)}"
        self.shoot_cooldown = 0
        self.change_dir_timer = 0
        self.random_dir = (0, 0)
        self.view_radius = 800
        
    def ai_move(self, all_players, map_width, map_height):
        # OPTIMIZATION: Use Squared Distance to avoid math.sqrt
        closest_dist_sq = float('inf')
        target = None
        my_center_x = self.x + self.width//2
        my_center_y = self.y + self.height//2
        
        view_radius_sq = self.view_radius ** 2

        for p_id, p in all_players.items():
            if p.id != self.id and p.hp > 0:
                other_center_x = p.x + p.width//2
                other_center_y = p.y + p.height//2
                
                # Dist Squared
                dx = my_center_x - other_center_x
                dy = my_center_y - other_center_y
                dist_sq = dx*dx + dy*dy
                
                if dist_sq < closest_dist_sq and dist_sq < view_radius_sq:
                    closest_dist_sq = dist_sq
                    target = p

        dx, dy = 0, 0
        
        if target:
            t_center_x = target.x + target.width//2
            t_center_y = target.y + target.height//2
            
            angle = math.atan2(t_center_y - my_center_y, t_center_x - my_center_x)
            
            # 300^2 = 90000
            if closest_dist_sq > 90000:
                self.x += math.cos(angle) * (self.vel * 0.8)
                self.y += math.sin(angle) * (self.vel * 0.8)
                dx = 1 if math.cos(angle) > 0 else -1
                dy = 1 if math.sin(angle) > 0 else -1
            elif closest_dist_sq < 22500: # 150^2
                self.x -= math.cos(angle) * (self.vel * 0.8)
                self.y -= math.sin(angle) * (self.vel * 0.8)
            
            if self.shoot_cooldown <= 0:
                aim_x = target.x + random.randint(-20, 20)
                aim_y = target.y + random.randint(-20, 20)
                self.shoot(aim_x, aim_y)
                self.shoot_cooldown = 40
                
        else:
            if self.change_dir_timer <= 0:
                angle = random.uniform(0, math.pi * 2)
                self.random_dir = (math.cos(angle), math.sin(angle))
                self.change_dir_timer = 100
            
            self.x += self.random_dir[0] * 2
            self.y += self.random_dir[1] * 2
            self.change_dir_timer -= 1
            dx = 1 if self.random_dir[0] > 0 else -1
            dy = 1 if self.random_dir[1] > 0 else -1
            
        if self.hp < 30 and self.abilities["shield"].cooldown <= 0:
            self.abilities["shield"].activate(self)

        self.x = max(0, min(self.x, map_width - self.width))
        self.y = max(0, min(self.y, map_height - self.height))

        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
        self.last_move = (dx, dy)
        self.update(map_width, map_height)
        
        self.abilities["shield"].update()
        self.abilities["wall"].update() # Update all abilities