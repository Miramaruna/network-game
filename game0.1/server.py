import socket
from _thread import *
import pickle
from player import Player

server = "" 
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen(4)
print(f"Сервер запущен. Порт: {port}")

players = {}
chat_log = ["Сервер онлайн!"] 
current_id = 0

# --- КОНСТАНТЫ КАРТЫ ---
# Задаем размер мира, чтобы все клиенты знали границы
MAP_WIDTH = 2000
MAP_HEIGHT = 2000

def threaded_client(conn, player_id):
    global chat_log
    
    # Отправляем настройки карты первым делом (можно упаковать в игрока или отдельно, 
    # но пока просто отправим игрока, а карту зашьем в код клиента для простоты)
    conn.send(pickle.dumps(players[player_id]))
    
    # --- СООБЩЕНИЕ О ВХОДЕ ---
    join_msg = f"[SERVER] Игрок {player_id} присоединился к бою!"
    print(join_msg)
    chat_log.append(join_msg)
    
    while True:
        try:
            data = pickle.loads(conn.recv(4096*2))

            if not data:
                break
            
            p_obj = data.get("player")
            new_msg = data.get("msg")
            
            if p_obj:
                players[player_id] = p_obj
                
            if new_msg:
                # Если сообщение начинается с [KILL], это системное сообщение
                if new_msg.startswith("[KILL]"):
                    clean_msg = new_msg.replace("[KILL]", "[💀]")
                    chat_log.append(clean_msg)
                else:
                    chat_log.append(f"Игрок {player_id}: {new_msg}")
                
                if len(chat_log) > 20: 
                    chat_log.pop(0)

            reply = {
                "players": players,
                "chat": chat_log
            }
            
            conn.sendall(pickle.dumps(reply))
            
        except Exception as e:
            print(f"Ошибка (ID {player_id}): {e}")
            break

    # --- СООБЩЕНИЕ О ВЫХОДЕ ---
    leave_msg = f"[SERVER] Игрок {player_id} покинул игру."
    print(leave_msg)
    chat_log.append(leave_msg)
    
    if player_id in players:
        del players[player_id]
    conn.close()

while True:
    conn, addr = s.accept()
    
    colors = [(231, 76, 60), (52, 152, 219), (46, 204, 113), (241, 196, 15), (155, 89, 182), (26, 188, 156)]
    color = colors[current_id % len(colors)]
    
    # Спавним в случайном месте (или в центре)
    start_x = 1000 # Середина карты 2000x2000
    start_y = 1000
    players[current_id] = Player(start_x, start_y, 50, 50, color, current_id)
    
    start_new_thread(threaded_client, (conn, current_id))
    current_id += 1