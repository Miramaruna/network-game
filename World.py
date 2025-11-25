import pygame
import sys

# --- Настройки ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PLAYER_SPEED = 5

# Цвета
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GRAY = (50, 50, 50)

# --- Класс Камеры ---
class Camera:
    def __init__(self, width, height):
        # camera_rect хранит смещение (x, y) и размеры всей карты
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        """Возвращает новый прямоугольник (Rect), смещенный относительно камеры. 
           Используется для отрисовки."""
        return entity.rect.move(self.camera_rect.topleft)

    def update(self, target):
        """Обновляет позицию камеры, чтобы следить за целью (игроком)."""
        # Мы хотим, чтобы игрок был в центре экрана
        x = -target.rect.x + int(SCREEN_WIDTH / 2)
        y = -target.rect.y + int(SCREEN_HEIGHT / 2)

        # Ограничение камеры (чтобы не выходила за пределы карты)
        # Если не нужно ограничение, эти строки можно убрать
        x = min(0, x)  # Левая граница
        y = min(0, y)  # Верхняя граница
        x = max(-(self.width - SCREEN_WIDTH), x)   # Правая граница
        y = max(-(self.height - SCREEN_HEIGHT), y) # Нижняя граница

        self.camera_rect = pygame.Rect(x, y, self.width, self.height)

# --- Класс Игрока ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED
        if keys[pygame.K_UP]:
            self.rect.y -= PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            self.rect.y += PLAYER_SPEED

        # Ограничиваем игрока размерами карты (3000x2000)
        self.rect.x = max(0, min(self.rect.x, 3000 - 30))
        self.rect.y = max(0, min(self.rect.y, 2000 - 30))

# --- Основной цикл ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Камера в Pygame")
    clock = pygame.time.Clock()

    # Создаем карту размером больше экрана (3000x2000)
    total_level_width = 3000
    total_level_height = 2000

    # Создаем камеру
    camera = Camera(total_level_width, total_level_height)

    # Создаем игрока
    player = Player(400, 300)

    # Создаем несколько препятствий (чтобы было видно движение)
    obstacles = []
    for i in range(20):
        rect = pygame.Rect(i * 150, i * 100, 50, 50)
        obstacles.append(rect)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 1. Обновление логики
        player.update()
        camera.update(player) # Камера "смотрит" на игрока

        # 2. Отрисовка
        screen.fill(GRAY)

        # Рисуем сетку или препятствия, применяя смещение камеры
        for obs in obstacles:
            # ВАЖНО: Мы создаем временный Rect, сдвинутый камерой
            obs_on_screen = obs.move(camera.camera_rect.topleft)
            pygame.draw.rect(screen, RED, obs_on_screen)
        
        # Рисуем границы мира (рамка)
        world_border = pygame.Rect(0, 0, total_level_width, total_level_height)
        pygame.draw.rect(screen, WHITE, world_border.move(camera.camera_rect.topleft), 2)

        # Рисуем игрока с учетом камеры
        screen.blit(player.image, camera.apply(player))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()