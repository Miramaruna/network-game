import socket
import pickle
import struct
import time

# Порт для поиска серверов (UDP)
BROADCAST_PORT = 5556
MAGIC_MESSAGE = b"NEON_DISCOVERY"

class Network:
    def __init__(self, server_ip):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_ip
        self.port = 5555
        self.addr = (self.server, self.port)
        
        # --- DEBUG STATS ---
        self.traffic_stats = {
            "sent_total": 0,
            "recv_total": 0,
            "last_packet_size": 0,
            "packets_sent": 0
        }
        
        self.p = self.connect()

    def getP(self):
        return self.p

    def connect(self):
        try:
            self.client.settimeout(5)
            self.client.connect(self.addr)
            raw_data = self.client.recv(4096)
            self.traffic_stats["recv_total"] += len(raw_data)
            return pickle.loads(raw_data)
        except (socket.timeout, ConnectionRefusedError, socket.gaierror):
            print(f"Connection failed: Server not reachable at {self.server}:{self.port}")
            self.disconnect() 
            return None
        except Exception as e:
            print(f"Unexpected error during connection: {e}")
            self.disconnect()
            return None

    def send(self, data):
        try:
            serialized_data = pickle.dumps(data)
            data_size = len(serialized_data)
            
            self.traffic_stats["sent_total"] += data_size
            self.traffic_stats["last_packet_size"] = data_size
            self.traffic_stats["packets_sent"] += 1
            
            self.client.send(serialized_data)
            
            reply_data = self.client.recv(4096 * 32) 
            self.traffic_stats["recv_total"] += len(reply_data)
            
            if not reply_data:
                raise ConnectionAbortedError("Server closed connection.")
                
            return pickle.loads(reply_data)
            
        except (ConnectionResetError, ConnectionAbortedError, socket.error) as e:
            # print(f"Network error (graceful exit required): {e}")
            return "NETWORK_FAILURE"

        except Exception as e:
            print(f"Serialization or other critical error: {e}")
            return "NETWORK_FAILURE"
            
    def disconnect(self):
        try:
            self.client.close()
        except Exception as e:
            print(f"Error closing socket: {e}")

class LANScanner:
    @staticmethod
    def scan(timeout=1.0):
        print("Сканирование локальной сети...")
        interfaces = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        interfaces.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        interfaces.settimeout(timeout)
        
        found_servers = []
        start_time = time.time()
        
        try:
            # Отправляем широковещательный запрос
            interfaces.sendto(MAGIC_MESSAGE, ('<broadcast>', BROADCAST_PORT))
            
            while time.time() - start_time < timeout:
                try:
                    data, addr = interfaces.recvfrom(1024)
                    msg = data.decode('utf-8')
                    if msg.startswith("NEON_SERVER|"):
                        # Формат ответа: NEON_SERVER|ServerName|PlayerCount
                        parts = msg.split("|")
                        server_info = {
                            "ip": addr[0],
                            "name": parts[1] if len(parts) > 1 else "Unknown",
                            "players": parts[2] if len(parts) > 2 else "?"
                        }
                        # Избегаем дубликатов
                        if not any(s['ip'] == server_info['ip'] for s in found_servers):
                            found_servers.append(server_info)
                except socket.timeout:
                    break
                except OSError:
                    break
        except Exception as e:
            print(f"Ошибка сканирования: {e}")
        finally:
            interfaces.close()
            
        return found_servers