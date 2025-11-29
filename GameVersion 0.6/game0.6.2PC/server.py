import socket
from _thread import *
import pickle
import time
import random
import pygame
import os
from player import Player, Bot, Wall

def get_local_ip():
    """Автоматически определяет локальный IP"""
    try:
        # Создаем временное соединение чтобы определить IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def get_external_ip():
    """Пытается определить внешний IP"""
    try:
        import requests
        return requests.get('https://api.ipify.org', timeout=3).text
    except:
        return "НЕОПРЕДЕЛЕН (проверьте на whatismyipaddress.com)"

# Настройки сервера
server = "0.0.0.0"  # Слушаем на всех интерфейсах
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Переиспользование порта

try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen(4)

# Выводим информацию для подключения
local_ip = get_local_ip()
external_ip = get_external_ip()

print("=" * 50)
print(f"Сервер запущен!")
print(f"Порт: {port}")
print(f"Локальный IP для подключения в той же сети: {local_ip}")
print(f"Внешний IP для подключения из интернета: {external_ip}")
print("=" * 50)
print("ВАЖНО: Для внешних подключений настройте проброс порта 5555 на роутере!")
print("=" * 50)

players = {}
chat_log = [
    "Сервер онлайн!", 
    "Напиши /bot для спавна врага!",
    f"Подключение: {local_ip}:{port}"
] 
current_id = 0
MAP_WIDTH = 2000
MAP_HEIGHT = 2000
static_entities = {} 
wall_id_counter = 0
WALL_WIDTH = 100
WALL_HEIGHT = 10

def bot_simulation_thread():
    """Bot logic loop, now handles ability updates and Wall collisions."""
    global static_entities
    
    while True:
        try:
            time.sleep(0.03) 
            current_players_list = list(players.items())
            
            # --- 1. Update Abilities and Handle Bot Movement/Shooting ---
            for p_id, p in current_players_list:
                if p_id not in players: continue 
                
                # Update player/bot abilities (Server-authoritative cooldown/duration)
                p.abilities["shield"].update()
                p.abilities["wall"].update()

                # Move Bot (Existing logic)
                if isinstance(p, Bot):
                    p.ai_move(players, MAP_WIDTH, MAP_HEIGHT)
                
                # --- 2. Server-side Bullet Collision (for bots and players) ---
                bullets_to_remove = []
                # Check for walls blocking bullets (New)
                for bullet in p.bullets:
                    b_rect = pygame.Rect(bullet[0]-5, bullet[1]-5, 10, 10)
                    
                    # Check Bullet vs Wall collision
                    wall_hit = False
                    for wall in static_entities.values():
                        if b_rect.colliderect(wall.rect):
                            bullets_to_remove.append(bullet)
                            wall_hit = True
                            break
                    if wall_hit: continue

                    # Check Bullet vs Player collision (Only needed for Bot bullets here)
                    if isinstance(p, Bot): # Only Bots need server-side bullet collision
                        for target_id, target in players.items():
                            # Shield check: If target has active shield, block damage
                            if target_id != p_id and target.hp > 0 and target.abilities["shield"].duration <= 0:
                                if b_rect.colliderect(target.rect):
                                    bullets_to_remove.append(bullet)
                                    target.hp -= 10
                                    
                                    if target.hp <= 0:
                                        chat_log.append(f"[KILL] {p.nickname} уничтожил {target.nickname}!")
                                        # target.respawn(MAP_WIDTH, MAP_HEIGHT)
                                    break
                
                for b in bullets_to_remove:
                    if b in p.bullets: p.bullets.remove(b)

            
                
        except Exception as e:
            print(f"[BOT THREAD ERROR]: {e}")
            
def server_works():
    """Handles timed events like Wall expiration."""
    walls_to_remove = []
    for w_id, wall in static_entities.items():
        if time.time() - wall.created_time >= Wall.WALL_DURATION:
            walls_to_remove.append(w_id)
                
    for w_id in walls_to_remove:
        del static_entities[w_id]

def threaded_client(conn, player_id):
    global chat_log, current_id, static_entities, wall_id_counter
    
    conn.send(pickle.dumps(players[player_id]))
    chat_log.append(f"[SERVER] Игрок {player_id} присоединился!")
    
    while True:
        try:
            data = pickle.loads(conn.recv(4096*32))
            if not data: break
            
            # --- НОВЫЙ КОД НАЧАЛО: Обработка пакета инициализации ---
            if isinstance(data, dict) and data.get("type") == "INIT":
                print("Получен INIT пакет от игрока", player_id)
                skin_to_set = data.get("skin", "DEFAULT")
                nick_to_set = data.get("nick", f"Игрок {player_id}")
                
                # Устанавливаем данные на сервере один раз
                players[player_id].skin_id = skin_to_set
                players[player_id].nickname = nick_to_set
                
                print(f"Игрок {player_id} выбрал скин: {skin_to_set}")
                
                # Отправляем ответ клиенту (обновленный список игроков)
                reply = {"players": players, "chat": chat_log, "walls": static_entities}
                conn.sendall(pickle.dumps(reply))
                continue
            
            p_obj = data.get("player")
            new_msg = data.get("msg")
            hit_data = data.get("hits", []) 
            ability_cast = data.get("ability_cast") # NEW: Ability cast request
            # player_nick = getattr(p_obj, 'nickname', f"Игрок {player_id}")
            
            if p_obj:
                if player_id in players:
                    # Preserve server-side HP, abilities, and Wall status
                    current_hp = players[player_id].hp
                    current_abilities = players[player_id].abilities
                    # current_nickname = players[player_id].nickname
                    # current_skin_id = players[player_id].skin_id  # Сохраняем скин
                    # print(f"Обновление игрока {player_id}: HP={current_hp}, Abilities={current_abilities}")
                    
                    players[player_id] = p_obj 
                    players[player_id].hp = current_hp
                    players[player_id].abilities = current_abilities
                    # players[player_id].nickname = player_nick
                    # players[player_id].skin_id = current_skin_id  # Восстанавливаем скин
                    
                    # Ensure the server-side rect is updated immediately
                    players[player_id].update_rect()
                    
                    server_works()
                    
                    # Respawn check (Existing logic)
                    if p_obj.hp <= 0:
                        server_p = players[player_id] 
                        server_p.x = random.randint(100, MAP_WIDTH - 100)
                        server_p.y = random.randint(100, MAP_HEIGHT - 100)
                        p_obj.respawn(MAP_WIDTH, MAP_HEIGHT)

            for hit in hit_data:
                target_id = hit["target_id"]
                dmg = hit["damage"]
                
                if target_id in players:
                    target = players[target_id]
                    
                    # Shield Check (Server-authoritative damage block)
                    if target.abilities["shield"].duration > 0:
                        chat_log.append(f"[SHIELD] {target.nickname} заблокировал урон!")
                        continue # Damage blocked
                        
                    target.hp -= dmg 
                    
                    if target.hp <= 0:
                        killer_name = players[player_id].nickname
                        victim_name = target.nickname
                        chat_log.append(f"[KILL] {killer_name} уничтожил {victim_name}!")
                        # target.respawn is handled by next update (p_obj.hp <= 0 check)
                        
            if ability_cast and player_id in players:
                ability_key = ability_cast["key"]
                
                if ability_key == "wall":
                    # Activation: Tries to activate ability on server
                    if players[player_id].abilities["wall"].activate(players[player_id]):
                        wall_id_counter += 1
                        # Wall spawns at player's current location (center)
                        w_x = players[player_id].x + players[player_id].width//2 - WALL_WIDTH//2 # assuming WALL_WIDTH is defined in Wall class
                        w_y = players[player_id].y + players[player_id].height + 5 # Spawn slightly in front
                        static_entities[wall_id_counter] = Wall(w_x, w_y, wall_id_counter)
                        chat_log.append(f"[ABILITY] {players[player_id].nickname} создал СТЕНУ!")
                
                elif ability_key == "shield":
                    players[player_id].abilities["shield"].activate(players[player_id])

            if new_msg:
                if new_msg.startswith("/bot"):
                    msgCount = new_msg.split()
                    count = int(msgCount[1]) if len(msgCount) > 1 else 1
                    for _ in range(count):
                        bot_id = current_id + 1000
                        current_id += 1
                        players[bot_id] = Bot(random.randint(100,1000), random.randint(100,1000), 50, 50, (255,0,0), bot_id)
                        chat_log.append(f"[SERVER] Бот создан!")
                else:
                    chat_log.append(f"{players[player_id].nickname}: {new_msg}")
                if len(chat_log) > 20: chat_log.pop(0)

            reply = {"players": players, "chat": chat_log, "walls": static_entities} # NEW: Include walls
            conn.sendall(pickle.dumps(reply))
            
        except Exception as e:
            print(f"Ошибка с игроком {player_id}: {e}")
            break

    print(f"Игрок {player_id} отключился")
    if player_id in players: del players[player_id]
    conn.close()

start_new_thread(bot_simulation_thread, ())
# start_new_thread(server_works())
# server_works()

while True:
    conn, addr = s.accept()
    players[current_id] = Player(random.randint(100, 800), random.randint(100, 800), 50, 50, (0, 255, 255), current_id)
    start_new_thread(threaded_client, (conn, current_id))
    current_id += 1