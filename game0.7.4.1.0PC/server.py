import socket
from _thread import *
import threading
import pickle
import time
import random
import pygame
import struct
import sys
from player import Player, Bot, Wall

# Константы
MAP_WIDTH = 2000
MAP_HEIGHT = 2000
WALL_WIDTH = 100
WALL_HEIGHT = 10
BROADCAST_PORT = 5556
MAGIC_MESSAGE = b"NEON_DISCOVERY"

# Глобальные переменные сервера
players = {}
chat_log = []
static_entities = {}
current_id = 0
wall_id_counter = 0
server_running = False

def reset_server_state():
    global players, chat_log, static_entities, current_id, wall_id_counter, server_running
    players = {}
    chat_log = ["Сервер запущен!", "Напиши /bot для врагов"]
    static_entities = {}
    current_id = 0
    wall_id_counter = 0
    server_running = True

def udp_broadcast_listener():
    """Слушает широковещательные запросы и отвечает на них"""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        udp_sock.bind(('', BROADCAST_PORT))
    except Exception as e:
        print(f"[UDP] Ошибка бинда порта обнаружения: {e}")
        return

    print("[UDP] Сервер обнаружения активен")
    
    while server_running:
        try:
            udp_sock.settimeout(2.0)
            try:
                data, addr = udp_sock.recvfrom(1024)
            except socket.timeout:
                continue
                
            if data == MAGIC_MESSAGE:
                # ФИЛЬТР: Считаем только реальных игроков (не ботов)
                real_players_count = len([p for p in players.values() if not isinstance(p, Bot)])
                
                # Отвечаем: NEON_SERVER|ServerName|PlayerCount
                response = f"NEON_SERVER|Neon Arena|{real_players_count}".encode('utf-8')
                udp_sock.sendto(response, addr)
        except Exception as e:
            if server_running: print(f"[UDP Error] {e}")
    
    udp_sock.close()

def bot_simulation_thread():
    global static_entities
    while server_running:
        try:
            time.sleep(0.03)
            current_players_list = list(players.items())
            
            for p_id, p in current_players_list:
                if p_id not in players: continue 
                
                p.abilities["shield"].update()
                p.abilities["wall"].update()

                if isinstance(p, Bot):
                    p.ai_move(players, MAP_WIDTH, MAP_HEIGHT)
                
                bullets_to_remove = []
                for bullet in p.bullets:
                    b_rect = pygame.Rect(bullet[0]-5, bullet[1]-5, 10, 10)
                    wall_hit = False
                    for wall in static_entities.values():
                        if b_rect.colliderect(wall.rect):
                            bullets_to_remove.append(bullet)
                            wall_hit = True
                            break
                    if wall_hit: continue

                    if isinstance(p, Bot): 
                        for target_id, target in players.items():
                            if target_id != p_id and target.hp > 0 and target.abilities["shield"].duration <= 0:
                                if b_rect.colliderect(target.rect):
                                    bullets_to_remove.append(bullet)
                                    target.hp -= 10
                                    if target.hp <= 0:
                                        chat_log.append(f"[KILL] {p.nickname} уничтожил {target.nickname}!")
                                    break
                
                for b in bullets_to_remove:
                    if b in p.bullets: p.bullets.remove(b)
                
        except Exception as e:
            print(f"[BOT THREAD ERROR]: {e}")

def server_works():
    """Очистка старых стен"""
    walls_to_remove = []
    for w_id, wall in static_entities.items():
        if time.time() - wall.created_time >= Wall.WALL_DURATION:
            walls_to_remove.append(w_id)
    for w_id in walls_to_remove:
        del static_entities[w_id]

def threaded_client(conn, player_id):
    global chat_log, current_id, static_entities, wall_id_counter

    last_chat_index = len(chat_log)
    
    conn.send(pickle.dumps(players[player_id]))
    
    while server_running:
        try:
            # data = pickle.loads(conn.recv(4096*32))
            # if not data: break
            
            header = conn.recv(4)
            if not header: break
            
            msg_len = struct.unpack('>I', header)[0]
            
            # 2. Читаем сами данные
            chunks = []
            bytes_recd = 0
            while bytes_recd < msg_len:
                chunk = conn.recv(min(msg_len - bytes_recd, 8192))
                if not chunk: break
                chunks.append(chunk)
                bytes_recd += len(chunk)
            
            data = pickle.loads(b''.join(chunks))
            
            if isinstance(data, dict) and data.get("type") == "INIT":
                players[player_id].skin_id = data.get("skin", "DEFAULT")
                players[player_id].nickname = data.get("nick", f"Player {player_id}")
                # p_obj = data.get("player")
                reply = {"players": players, "chat": chat_log, "walls": static_entities}
                conn.sendall(pickle.dumps(reply))
                continue
            
            # if isinstance(data, dict) and data.get("type") == "ONLYPLAYER":
            #     p_obj = data.get("player")
            #     new_msg = None
            #     hit_data = data.get("hits", [])
            #     ability_cast = None
            #     # print("ONLYPLAYER received")

            # if isinstance(data, dict) and data.get("type") == "FULLPACKET":
            #     p_obj = data.get("player")
            #     new_msg = data.get("msg")
            #     hit_data = data.get("hits", [])
            #     ability_cast = data.get("ability_cast")
            #     print("FULLPACKET received")
            #     print(hit_data)
            #     continue
            
            if isinstance(data, dict) and data.get("type") == "UPDATE":
                p_obj = data.get("player")
                
                # Инициализируем переменные, которые могут отсутствовать в пакете
                new_msg = None
                hit_data = []
                ability_cast = None

                # Проверяем, есть ли дополнительные данные, используя .get() или "in dict"
                
                # 1. Получаем hit_data (если есть)
                if "hits" in data:
                    hit_data = data["hits"]
                    # print("Received hits data:", hit_data) # Отладка: должно срабатывать при выстреле

                # 2. Получаем сообщение (если есть)
                if "msg" in data:
                    new_msg = data["msg"]
                    # Здесь должна быть логика добавления new_msg в chat_log

                # 3. Получаем способность (если есть)
                if "ability_cast" in data:
                    ability_cast = data["ability_cast"]
        
            # p_obj = data.get("player")
            # new_msg = data.get("msg")
            # hit_data = data.get("hits", []) 
            # ability_cast = data.get("ability_cast")
            
            if p_obj and player_id in players:
                current_hp = players[player_id].hp
                current_abilities = players[player_id].abilities
                players[player_id] = p_obj 
                players[player_id].hp = current_hp
                players[player_id].abilities = current_abilities
                players[player_id].update_rect()
                
                server_works() # Проверка стен
                
                if p_obj.hp <= 0:
                    players[player_id].x = random.randint(100, MAP_WIDTH - 100)
                    players[player_id].y = random.randint(100, MAP_HEIGHT - 100)
                    p_obj.respawn(MAP_WIDTH, MAP_HEIGHT)

            for hit in hit_data:
                target_id = hit["target_id"]
                if target_id in players:
                    target = players[target_id]
                    # if target.abilities["shield"].duration > 0:
                    #     continue 
                    target.hp -= hit["damage"]
                    if target.hp <= 0:
                        chat_log.append(f"[KILL] {players[player_id].nickname} -> {target.nickname}")

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
                
            reply = {"players": players, "walls": static_entities}
            
            current_chat_len = len(chat_log)
            new_messages_count = current_chat_len - last_chat_index
                
            if new_messages_count > 0:
                # Отправляем только новые сообщения
                reply["chat"] = chat_log[last_chat_index:]
                # Обновляем индекс для следующего кадра
                last_chat_index = current_chat_len

            # reply = {"players": players, "chat": chat_log, "walls": static_entities}
            # conn.sendall(pickle.dumps(reply))
            reply_serialized = pickle.dumps(reply)
            reply_len = struct.pack('>I', len(reply_serialized))
            conn.sendall(reply_len + reply_serialized)
            
        except Exception as e:
            break

    if player_id in players: del players[player_id]
    conn.close()

def start_server_instance(bind_ip="0.0.0.0"):
    """Основная функция запуска сервера"""
    global current_id, server_running
    
    reset_server_state()
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        s.bind((bind_ip, 5555))
    except socket.error as e:
        print(f"Server Bind Error: {e}")
        return

    s.listen(4)
    print(f"Сервер запущен на {bind_ip}:5555")
    
    # Запускаем фоновые потоки
    start_new_thread(bot_simulation_thread, ())
    start_new_thread(udp_broadcast_listener, ()) # Поток обнаружения
    
    # Главный цикл принятия подключений
    while server_running:
        try:
            conn, addr = s.accept()
            print(f"Подключился: {addr}")
            players[current_id] = Player(random.randint(100, 800), random.randint(100, 800), 50, 50, (0, 255, 255), current_id)
            start_new_thread(threaded_client, (conn, current_id))
            current_id += 1
        except OSError:
            break # Сокет закрыт

# Блок для прямого запуска файла server.py
if __name__ == "__main__":
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]; s.close()
            return ip
        except: return "127.0.0.1"

    print(f"Локальный IP: {get_local_ip()}")
    start_server_instance()