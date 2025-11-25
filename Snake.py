import pygame
import random
import sys

# --- Инициализация Pygame ---
pygame.init()

# --- Константы ---
# Размеры окна
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

# Цвета (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (213, 50, 80)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 200, 0)
BLUE = (50, 153, 213)
BG_COLOR = (240, 240, 220) # Песочный цвет фона

# Размер одного блока змейки и еды
BLOCK_SIZE = 20

# Скорость игры (FPS - кадры в секунду). Чем больше, тем быстрее.
SNAKE_SPEED = 10

# Настройка экрана и шрифтов
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Змейка на Pygame')

clock = pygame.time.Clock()
font_style = pygame.font.SysFont("bahnschrift", 25)
score_font = pygame.font.SysFont("comicsansms", 20)

# --- Функции ---

def your_score(score):
    """Отображает счет на экране"""
    value = score_font.render("Счет: " + str(score), True, BLACK)
    screen.blit(value, [10, 10])

def draw_snake(snake_block, snake_list):
    """Рисует змейку, snake_block - размер блока, snake_list - список сегментов змейки пример: [[x1, y1], [x2, y2], ...]"""
    for i, segment in enumerate(snake_list):
        # Голова чуть темнее
        color = DARK_GREEN if i == len(snake_list) - 1 else GREEN
        # Рисуем прямоугольник: [x, y, ширина, высота]
        pygame.draw.rect(screen, color, [segment[0], segment[1], snake_block, snake_block])

def message(msg, color):
    """Отображает сообщение в центре экрана"""
    mesg = font_style.render(msg, True, color)
    text_rect = mesg.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    screen.blit(mesg, text_rect)

def gameLoop():
    """Главный цикл игры"""
    game_over = False
    game_close = False

    # Начальная позиция головы (середина экрана)
    x1 = SCREEN_WIDTH / 2
    y1 = SCREEN_HEIGHT / 2

    # Изменение позиции (направление движения)
    x1_change = 0
    y1_change = 0

    # Тело змейки и её начальная длина
    snake_List = []
    Length_of_snake = 3
    
    # Сразу задаем начальное направление (например, вправо)
    x1_change = BLOCK_SIZE
    y1_change = 0

    # Генерация первой еды. 
    # Формула нужна, чтобы еда появлялась ровно по сетке, кратной BLOCK_SIZE
    foodx = round(random.randrange(0, SCREEN_WIDTH - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
    foody = round(random.randrange(0, SCREEN_HEIGHT - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE

    while not game_over:

        # --- Экран проигрыша ---
        while game_close == True:
            screen.fill(BG_COLOR)
            message("Вы проиграли! Q - Выход, C - Играть снова", RED)
            your_score(Length_of_snake - 3)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        gameLoop() # Рестарт игры

        # --- Обработка событий (нажатия клавиш) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                # Запрещаем мгновенный разворот на 180 градусов
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    if x1_change != BLOCK_SIZE:
                        x1_change = -BLOCK_SIZE
                        y1_change = 0
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    if x1_change != -BLOCK_SIZE:
                        x1_change = BLOCK_SIZE
                        y1_change = 0
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    if y1_change != BLOCK_SIZE:
                        y1_change = -BLOCK_SIZE
                        x1_change = 0
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    if y1_change != -BLOCK_SIZE:
                        y1_change = BLOCK_SIZE
                        x1_change = 0

        # --- Логика движения и столкновений ---
        
        # Проверка столкновения со стенами
        if x1 >= SCREEN_WIDTH or x1 < 0 or y1 >= SCREEN_HEIGHT or y1 < 0:
            game_close = True

        # Обновление позиции головы
        x1 += x1_change
        y1 += y1_change

        # Отрисовка фона
        screen.fill(BG_COLOR)
        
        # Отрисовка еды
        pygame.draw.rect(screen, RED, [foodx, foody, BLOCK_SIZE, BLOCK_SIZE])
        
        # Обновление тела змейки
        snake_Head = []
        snake_Head.append(x1)
        snake_Head.append(y1)
        snake_List.append(snake_Head)

        # Если длина списка больше реальной длины змейки, удаляем хвост
        if len(snake_List) > Length_of_snake:
            del snake_List[0]

        # Проверка столкновения с самим собой
        # Проверяем, есть ли координаты головы в остальной части тела
        for x in snake_List[:-1]:
            if x == snake_Head:
                game_close = True

        draw_snake(BLOCK_SIZE, snake_List)
        your_score(Length_of_snake - 3)

        pygame.display.update()

        # --- Проверка поедания еды ---
        # Pygame позволяет легко проверять столкновения прямоугольников
        snake_rect = pygame.Rect(x1, y1, BLOCK_SIZE, BLOCK_SIZE)
        food_rect = pygame.Rect(foodx, foody, BLOCK_SIZE, BLOCK_SIZE)
        
        if snake_rect.colliderect(food_rect):
             # Еда съедена!
            foodx = round(random.randrange(0, SCREEN_WIDTH - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
            foody = round(random.randrange(0, SCREEN_HEIGHT - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
            Length_of_snake += 1

        # Контроль скорости игры
        clock.tick(SNAKE_SPEED)

    # Выход из игры
    pygame.quit()
    sys.exit()

# Запуск игры
if __name__ == "__main__":
    gameLoop()