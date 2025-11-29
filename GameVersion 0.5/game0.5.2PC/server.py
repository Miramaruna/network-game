import socket
from _thread import *
import pickle
import time
import random
import pygame
from player import Player, Bot 

server = "192.168.0.105" 
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen(4)
print(f"Сервер запущен. Порт: {port}")

players = {}
chat_log = ["Сервер онлайн!", "Напиши /bot для спавна врага!"] 
current_id = 0
MAP_WIDTH = 2000
MAP_HEIGHT = 2000

def bot_simulation_thread():
    """Bot logic loop"""
    while True:
        try:
            time.sleep(0.03) 
            current_players_list = list(players.items())
            
            for p_id, p in current_players_list:
                if p_id not in players: continue 
                
                # 1. Move Bot
                if isinstance(p, Bot):
                    p.ai_move(players, MAP_WIDTH, MAP_HEIGHT)
                
                # 2. Server-side Bullet Collision (for bots)
                if isinstance(p, Bot): 
                    bullets_to_remove = []
                    for bullet in p.bullets:
                        b_rect = pygame.Rect(bullet[0]-5, bullet[1]-5, 10, 10)
                        
                        for target_id, target in players.items():
                            if target_id != p_id and target.hp > 0:
                                # Optimization: Use the target's existing rect
                                if b_rect.colliderect(target.rect):
                                    bullets_to_remove.append(bullet)
                                    target.hp -= 10
                                    
                                    if target.hp <= 0:
                                        chat_log.append(f"[KILL] {p.nickname} уничтожил {target.nickname}!")
                                        target.respawn(MAP_WIDTH, MAP_HEIGHT)
                                    break
                    
                    for b in bullets_to_remove:
                        if b in p.bullets: p.bullets.remove(b)

        except Exception as e:
            print(f"[BOT THREAD ERROR]: {e}")

def threaded_client(conn, player_id):
    global chat_log, current_id
    
    conn.send(pickle.dumps(players[player_id]))
    chat_log.append(f"[SERVER] Игрок {player_id} присоединился!")
    
    while True:
        try:
            data = pickle.loads(conn.recv(4096*32))
            if not data: break
            
            p_obj = data.get("player")
            new_msg = data.get("msg")
            hit_data = data.get("hits", []) 
            
            if p_obj:
                if player_id in players:
                    current_hp = players[player_id].hp
                    players[player_id] = p_obj 
                    players[player_id].hp = current_hp
                    
                    # Ensure the server-side rect is updated immediately
                    players[player_id].update_rect()
                    
                    # print(p_obj.hp)
                    if p_obj.hp <= 0:
                        # print("RESPAWNING PLAYER ON SERVER")
                        server_p = players[player_id] # Берем реального игрока на сервере

                        # --- ФИКС РЕСПАВНА ---
                        server_p.x = random.randint(100, MAP_WIDTH - 100)
                        server_p.y = random.randint(100, MAP_HEIGHT - 100)
                        # print(server_p.x, server_p.y, "|", p_obj.x, p_obj.y)
                            
                        p_obj.respawn(MAP_WIDTH, MAP_HEIGHT)

            for hit in hit_data:
                target_id = hit["target_id"]
                dmg = hit["damage"]
                
                if target_id in players:
                    target = players[target_id]
                    target.hp -= dmg 
                    
                    if target.hp <= 0:
                        killer_name = players[player_id].nickname
                        victim_name = target.nickname
                        chat_log.append(f"[KILL] {killer_name} уничтожил {victim_name}!")
                        # target.respawn(MAP_WIDTH, MAP_HEIGHT)

            player_nick = getattr(p_obj, 'nickname', f"Игрок {player_id}")
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
                    chat_log.append(f"{player_nick}: {new_msg}")
                if len(chat_log) > 20: chat_log.pop(0)

            reply = {"players": players, "chat": chat_log}
            conn.sendall(pickle.dumps(reply))
            
        except Exception as e:
            print(f"Ошибка с игроком {player_id}: {e}")
            break

    print(f"Игрок {player_id} отключился")
    if player_id in players: del players[player_id]
    conn.close()

start_new_thread(bot_simulation_thread, ())

while True:
    conn, addr = s.accept()
    players[current_id] = Player(random.randint(100, 800), random.randint(100, 800), 50, 50, (0, 255, 255), current_id)
    start_new_thread(threaded_client, (conn, current_id))
    current_id += 1