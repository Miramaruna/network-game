import tkinter as tk
from tkinter import messagebox
import socket
import pickle
import time
import math
import threading

# --- НАСТРОЙКИ ---
WIDTH = 800
HEIGHT = 600
TITLE = "Sahur Shooter: Tkinter Edition"

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def rgb_to_hex(rgb):
    """Конвертирует (255, 0, 0) в '#ff0000' для Tkinter"""
    try:
        return "#%02x%02x%02x" % rgb
    except:
        return "#FFFFFF" # Дефолтный белый при ошибке

# --- ЗАМЕНА PYGAME.RECT (Для совместимости) ---
# Убедитесь, что в server.py и player.py используется этот же класс вместо pygame.Rect
class Rect:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    
    # Свойства для удобства (как в Pygame)
    @property
    def left(self): return self.x
    @property
    def right(self): return self.x + self.w
    @property
    def top(self): return self.y
    @property
    def bottom(self): return self.y + self.h
    @property
    def centerx(self): return self.x + self.w / 2
    @property
    def centery(self): return self.y + self.h / 2

    def colliderect(self, other):
        return (self.x < other.x + other.w and
                self.x + self.w > other.x and
                self.y < other.y + other.h and
                self.y + self.h > other.y)

# --- СЕТЕВАЯ ЧАСТЬ (Встроенная, чтобы не зависеть от старого network.py) ---
class SimpleNetwork:
    def __init__(self, ip):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = ip
        self.port = 5555
        self.addr = (self.server, self.port)
        self.p = self.connect()

    def getP(self):
        return self.p

    def connect(self):
        try:
            self.client.settimeout(5)
            self.client.connect(self.addr)
            # Получаем первый пакет (игрок)
            return pickle.loads(self.client.recv(4096 * 4))
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return None

    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
            return pickle.loads(self.client.recv(4096 * 16))
        except socket.error as e:
            print(e)
            return None

# --- ОСНОВНОЕ ПРИЛОЖЕНИЕ ---
class GameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITLE)
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.resizable(False, False)
        
        # Переменные игры
        self.network = None
        self.player = None
        self.scroll_x = 0
        self.scroll_y = 0
        self.keys_pressed = {}
        self.mouse_pos = (0, 0)
        
        # UI Состояния
        self.setup_menu()

    def setup_menu(self):
        """Создает меню входа"""
        self.menu_frame = tk.Frame(self, bg="#101020")
        self.menu_frame.pack(fill="both", expand=True)

        tk.Label(self.menu_frame, text="SAHUR SHOOTER", font=("Arial", 30, "bold"), 
                 bg="#101020", fg="#00FFFF").pack(pady=50)

        tk.Label(self.menu_frame, text="IP Адрес:", bg="#101020", fg="white").pack()
        self.entry_ip = tk.Entry(self.menu_frame, font=("Arial", 12))
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.pack(pady=5)

        tk.Label(self.menu_frame, text="Никнейм:", bg="#101020", fg="white").pack()
        self.entry_nick = tk.Entry(self.menu_frame, font=("Arial", 12))
        self.entry_nick.insert(0, f"Player{int(time.time())%100}")
        self.entry_nick.pack(pady=5)

        btn = tk.Button(self.menu_frame, text="ПОДКЛЮЧИТЬСЯ", font=("Arial", 14, "bold"),
                        bg="#00FFFF", fg="black", command=self.start_game)
        btn.pack(pady=30)

    def start_game(self):
        """Инициализация соединения и запуск игры"""
        ip = self.entry_ip.get()
        nick = self.entry_nick.get()

        try:
            self.network = SimpleNetwork(ip)
            self.player = self.network.getP()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")
            return

        if not self.player:
            messagebox.showerror("Ошибка", "Сервер не ответил или вернул пустые данные.")
            return

        # Инициализация игрока
        self.player.nickname = nick
        # Отправляем INIT пакет
        self.network.send({"type": "INIT", "nick": nick, "skin": "DEFAULT"})

        # Убираем меню, создаем холст
        self.menu_frame.destroy()
        self.canvas = tk.Canvas(self, width=WIDTH, height=HEIGHT, bg="#050510", highlightthickness=0)
        self.canvas.pack()

        # Биндим управление
        self.bind("<KeyPress>", self.on_key_down)
        self.bind("<KeyRelease>", self.on_key_up)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_click)
        
        # Запускаем игровой цикл
        self.last_time = time.time()
        self.game_loop()

    # --- INPUT HANDLERS ---
    def on_key_down(self, event):
        self.keys_pressed[event.keysym.lower()] = True

    def on_key_up(self, event):
        self.keys_pressed[event.keysym.lower()] = False

    def on_mouse_move(self, event):
        self.mouse_pos = (event.x, event.y)

    def on_click(self, event):
        if self.player:
            # Стрельба: передаем абсолютные координаты мира (экран + скролл)
            # Внимание: метод shoot должен быть в player.py и не зависеть от pygame
            self.player.shoot(event.x, event.y, (self.scroll_x, self.scroll_y))

    # --- ИГРОВОЙ ЦИКЛ ---
    def game_loop(self):
        # 1. Логика движения (адаптация под отсутствие pygame.key)
        # Нам нужно вручную изменить координаты игрока здесь или передать флаги в player.move
        # Допустим, мы меняем их прямо здесь для простоты, если player.move зависит от pygame
        vel = getattr(self.player, 'vel', 5)
        map_w, map_h = 2000, 2000 # Размер карты
        
        if self.keys_pressed.get('a') and self.player.x > 0: self.player.x -= vel
        if self.keys_pressed.get('d') and self.player.x < map_w: self.player.x += vel
        if self.keys_pressed.get('w') and self.player.y > 0: self.player.y -= vel
        if self.keys_pressed.get('s') and self.player.y < map_h: self.player.y += vel
        
        # Обновляем rect (если он есть)
        if hasattr(self.player, 'rect'):
            self.player.rect.x = self.player.x
            self.player.rect.y = self.player.y

        # 2. Сеть
        try:
            packet = {"type": "UPDATE", "player": self.player}
            server_data = self.network.send(packet)
            
            if server_data:
                players = server_data.get("players", {})
                walls = server_data.get("walls", {})
                
                # Синхронизация HP
                if self.player.id in players:
                    self.player.hp = players[self.player.id].hp
            else:
                players, walls = {}, {}
        except Exception as e:
            print(f"Network loop error: {e}")
            players, walls = {}, {}

        # 3. Камера
        target_x = self.player.x - WIDTH // 2 + self.player.width // 2
        target_y = self.player.y - HEIGHT // 2 + self.player.height // 2
        self.scroll_x += (target_x - self.scroll_x) * 0.1
        self.scroll_y += (target_y - self.scroll_y) * 0.1

        # 4. Отрисовка
        self.render(players, walls)

        # Рекурсивный вызов (60 FPS ~ 16ms)
        self.after(16, self.game_loop)

    def render(self, players, walls):
        self.canvas.delete("all")
        
        # 1. Сетка (Фон)
        off_x = -int(self.scroll_x) % 100
        off_y = -int(self.scroll_y) % 100
        
        # Вертикальные линии
        for x in range(off_x, WIDTH, 100):
            self.canvas.create_line(x, 0, x, HEIGHT, fill="#1A1A2E")
        # Горизонтальные линии
        for y in range(off_y, HEIGHT, 100):
            self.canvas.create_line(0, y, WIDTH, y, fill="#1A1A2E")

        # 2. Стены
        for w in walls.values():
            screen_x = w.x - self.scroll_x
            screen_y = w.y - self.scroll_y
            self.canvas.create_rectangle(
                screen_x, screen_y, 
                screen_x + w.width, screen_y + w.height,
                fill="#5555FF", outline="#CCCCFF"
            )

        # 3. Игроки
        for pid, p in players.items():
            screen_x = p.x - self.scroll_x
            screen_y = p.y - self.scroll_y
            
            # Пропуск, если вне экрана
            if screen_x < -50 or screen_x > WIDTH+50 or screen_y < -50 or screen_y > HEIGHT+50:
                continue

            # Цвет тела
            col = rgb_to_hex(p.color) if isinstance(p.color, (list, tuple)) else "#00FFFF"
            
            # Тело
            self.canvas.create_rectangle(
                screen_x, screen_y,
                screen_x + p.width, screen_y + p.height,
                fill=col, outline="white"
            )
            
            # Никнейм
            self.canvas.create_text(
                screen_x + p.width/2, screen_y - 20,
                text=getattr(p, 'nickname', 'Player'), fill="white", font=("Arial", 10)
            )

            # HP Bar
            hp_pct = max(0, p.hp / 100)
            hp_color = "#00FF00" if hp_pct > 0.4 else "#FF0000"
            self.canvas.create_rectangle(screen_x, screen_y - 10, screen_x + p.width, screen_y - 5, fill="#333")
            self.canvas.create_rectangle(screen_x, screen_y - 10, screen_x + (p.width * hp_pct), screen_y - 5, fill=hp_color)

            # Пули
            for b in p.bullets:
                bx = b[0] - self.scroll_x
                by = b[1] - self.scroll_y
                self.canvas.create_oval(bx-3, by-3, bx+3, by+3, fill="yellow")

        # HUD (Интерфейс)
        self.canvas.create_text(50, 20, text=f"HP: {self.player.hp}", fill="white", font=("Courier", 16, "bold"), anchor="w")
        self.canvas.create_text(50, 40, text=f"POS: {int(self.player.x)}, {int(self.player.y)}", fill="#AAAAAA", font=("Courier", 10), anchor="w")

if __name__ == "__main__":
    app = GameApp()
    app.mainloop()