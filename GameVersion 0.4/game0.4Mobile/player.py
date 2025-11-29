import pygame
import math
import random

class Player:
    def __init__(self, x, y, width, height, color, p_id):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rect = (x, y, width, height)
        self.vel = 5
        self.hp = 100
        self.bullets = []
        self.id = p_id 
        # --- СВОЙСТВА ДЛЯ СИНХРОНИЗАЦИИ ---
        self.nickname = f"Игрок_{p_id}"
        self.last_move = (0, 0) # (dx, dy) для синхронизации следа
        self.trail_particles = [] # Частицы следа

    def draw(self, win, scroll):
        screen_x = self.x - scroll[0]
        screen_y = self.y - scroll[1]

        # 1. Анимация СЛЕДА (Trail)
        # Генерируем частицы на основе self.last_move
        self._generate_trail_particles(screen_x, screen_y)
        self._draw_trail_particles(win)
        
        # 2. Основное тело
        
        # Тень
        pygame.draw.rect(win, (20, 20, 20), (screen_x + 3, screen_y + 3, self.width, self.height))
        
        # Обводка (более яркая)
        pygame.draw.rect(win, (255, 255, 255), (screen_x, screen_y, self.width, self.height), 3)
        
        # Основное тело
        pygame.draw.rect(win, self.color, (screen_x + 1, screen_y + 1, self.width - 2, self.height - 2))

        # 3. Полоска HP (Неоновый эффект)
        hp_bar_w = self.width * (self.hp/100)
        hp_color = (0, 255, 0) if self.hp > 30 else (255, 50, 50) # Красный при низком HP
        
        # Фон
        pygame.draw.rect(win, (50, 50, 50), (screen_x, screen_y - 15, self.width, 8))
        # Заполнение (яркое)
        pygame.draw.rect(win, hp_color, (screen_x, screen_y - 15, hp_bar_w, 8))
        # Неоновая обводка
        pygame.draw.rect(win, (255, 255, 255), (screen_x, screen_y - 15, self.width, 8), 1)

        # 4. Пули (С неоновым следом)
        for i, bullet in enumerate(self.bullets):
            bx = bullet[0] - scroll[0]
            by = bullet[1] - scroll[1]
            
            # Неоновый след
            pygame.draw.circle(win, (255, 200, 0), (int(bx-bullet[2]*2), int(by-bullet[3]*2)), 3)
            pygame.draw.circle(win, (255, 200, 0), (int(bx-bullet[2]*1), int(by-bullet[3]*1)), 4)
            # Основная пуля
            pygame.draw.circle(win, (255, 255, 255), (int(bx), int(by)), 5)
            pygame.draw.circle(win, (255, 0, 0), (int(bx), int(by)), 3)


    # --- МЕТОДЫ ДЛЯ ЧАСТИЦ СЛЕДА (Используют self.last_move) ---
    def _generate_trail_particles(self, screen_x, screen_y):
        """Генерирует частицы на основе self.last_move (движения), которое синхронизируется по сети."""
        dx, dy = self.last_move
        
        # Генерируем частицы только если игрок движется
        if dx != 0 or dy != 0:
            # Создаем частицы сзади (используем обратное направление движения)
            spawn_x = screen_x + self.width // 2 + (-dx) * (self.width//2)
            spawn_y = screen_y + self.height // 2 + (-dy) * (self.height//2)
            
            # Добавляем случайное смещение
            spawn_x += random.uniform(-10, 10)
            spawn_y += random.uniform(-10, 10)

            # Размер и скорость затухания
            size = random.randint(3, 7)
            lifetime = random.randint(15, 30)
            # Цвет берем из цвета игрока
            self.trail_particles.append([spawn_x, spawn_y, size, lifetime, self.color])
    
    def _draw_trail_particles(self, win):
        new_particles = []
        for p in self.trail_particles:
            p[3] -= 1 # Уменьшаем время жизни (lifetime)
            
            if p[3] > 0:
                # Движение частицы (медленно дрейфует)
                p[0] += random.uniform(-0.5, 0.5)
                p[1] += random.uniform(-0.5, 0.5)
                
                # Вычисляем альфа-канал на основе времени жизни
                alpha = int(255 * (p[3] / 30)) 
                
                # Рисуем частицу
                s = pygame.Surface((p[2], p[2]), pygame.SRCALPHA)
                
                r, g, b = p[4]
                faded_color = (min(255, r + 50), min(255, g + 50), min(255, b + 50), alpha)
                s.fill(faded_color)
                
                win.blit(s, (int(p[0]), int(p[1])))
                new_particles.append(p)
        
        self.trail_particles = new_particles
    # --- КОНЕЦ МЕТОДОВ ДЛЯ ЧАСТИЦ СЛЕДА ---

    # --- НОВЫЙ МЕТОД ДЛЯ МОБИЛЬНОГО УПРАВЛЕНИЯ ---
    def move_mobile(self, map_width, map_height, move_vector):
        """Двигает игрока на основе нормализованного вектора с джойстика."""
        dx_norm, dy_norm = move_vector
        
        if dx_norm != 0 or dy_norm != 0:
            # Умножаем скорость на нормализованный вектор
            self.x += self.vel * dx_norm
            self.y += self.vel * dy_norm
        
        # Ограничения карты
        self.x = max(0, min(self.x, map_width - self.width))
        self.y = max(0, min(self.y, map_height - self.height))
        
        # Обновляем last_move для анимации следа (используем направление)
        # Округляем до -1, 0 или 1, чтобы синхронизация была дискретной
        self.last_move = (int(round(dx_norm)), int(round(dy_norm))) 
        
        self.update(map_width, map_height)

    def update(self, map_width, map_height):
        self.rect = (self.x, self.y, self.width, self.height)
        
        # Вращение/движение пули
        for bullet in self.bullets:
            bullet[0] += bullet[2]
            bullet[1] += bullet[3]
            # Удаляем пули, если они улетели за границы КАРТЫ (а не экрана)
            if bullet[0] > map_width + 100 or bullet[0] < -100 or bullet[1] > map_height + 100 or bullet[1] < -100:
                # В client.py пули удаляются при попадании. 
                # Здесь удаляем только те, что улетели за карту.
                self.bullets.remove(bullet)
                
    def deleteBullet(self, bullet):
        self.bullets.remove(bullet)

    def shoot(self, target_x, target_y, scroll):
        # ... (логика стрельбы без изменений) ...
        world_target_x = target_x + scroll[0]
        world_target_y = target_y + scroll[1]

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