import pygame
import math

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

    # --- ИЗМЕНЕНИЕ: Добавлен аргумент scroll ---
    def draw(self, win, scroll):
        # Вычисляем экранные координаты (реальные минус смещение камеры)
        screen_x = self.x - scroll[0]
        screen_y = self.y - scroll[1]

        # Тень
        pygame.draw.rect(win, (20, 20, 20), (screen_x + 3, screen_y + 3, self.width, self.height))
        
        # Основное тело
        pygame.draw.rect(win, self.color, (screen_x, screen_y, self.width, self.height))
        
        # Обводка
        pygame.draw.rect(win, (255, 255, 255), (screen_x, screen_y, self.width, self.height), 2)

        # Полоска HP
        pygame.draw.rect(win, (50, 0, 0), (screen_x, screen_y - 15, self.width, 8))
        if self.hp > 0:
            pygame.draw.rect(win, (0, 230, 0), (screen_x, screen_y - 15, self.width * (self.hp/300), 8))
        
        # Пули (тоже сдвигаем относительно камеры)
        for bullet in self.bullets:
            bx = bullet[0] - scroll[0]
            by = bullet[1] - scroll[1]
            pygame.draw.circle(win, (255, 200, 0), (int(bx), int(by)), 6)
            pygame.draw.circle(win, (255, 255, 255), (int(bx), int(by)), 3)

    def move(self, map_width, map_height):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT] and self.x > 0: self.x -= self.vel
        if keys[pygame.K_RIGHT] and self.x < map_width - self.width: self.x += self.vel
        if keys[pygame.K_UP] and self.y > 0: self.y -= self.vel
        if keys[pygame.K_DOWN] and self.y < map_height - self.height: self.y += self.vel
        
        self.update(map_width, map_height)

    def update(self, map_width, map_height):
        self.rect = (self.x, self.y, self.width, self.height)
        for bullet in self.bullets:
            bullet[0] += bullet[2]
            bullet[1] += bullet[3]
            # Удаляем пули, если они улетели за границы КАРТЫ (а не экрана)
            if bullet[0] > map_width + 100 or bullet[0] < -100 or bullet[1] > map_height + 100 or bullet[1] < -100:
                self.bullets.remove(bullet)
                
    def deleteBullet(self, bullet):
        self.bullets.remove(bullet)

    def shoot(self, target_x, target_y, scroll):
        # target_x/y - это координаты мыши на ЭКРАНЕ. 
        # Нам нужно перевести их в координаты МИРА, добавив scroll.
        world_target_x = target_x + scroll[0]
        world_target_y = target_y + scroll[1]

        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        dx = world_target_x - center_x
        dy = world_target_y - center_y
        angle = math.atan2(dy, dx)
        
        speed = 12
        speed_x = speed * math.cos(angle)
        speed_y = speed * math.sin(angle)
        
        spawn_distance = 45
        spawn_x = center_x + (math.cos(angle) * spawn_distance)
        spawn_y = center_y + (math.sin(angle) * spawn_distance)
        
        self.bullets.append([spawn_x, spawn_y, speed_x, speed_y])