import socket
import pickle

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
            # Сначала сериализуем, чтобы посчитать размер
            serialized_data = pickle.dumps(data)
            data_size = len(serialized_data)
            
            # Обновляем статистику
            self.traffic_stats["sent_total"] += data_size
            self.traffic_stats["last_packet_size"] = data_size
            self.traffic_stats["packets_sent"] += 1
            
            # Отправляем
            self.client.send(serialized_data)
            
            # Получаем ответ
            reply_data = self.client.recv(4096 * 32) 
            self.traffic_stats["recv_total"] += len(reply_data)
            
            if not reply_data:
                raise ConnectionAbortedError("Server closed connection.")
                
            return pickle.loads(reply_data)
            
        except (ConnectionResetError, ConnectionAbortedError, socket.error) as e:
            print(f"Network error (graceful exit required): {e}")
            return "NETWORK_FAILURE"

        except Exception as e:
            print(f"Serialization or other critical error: {e}")
            return "NETWORK_FAILURE"
            
    def disconnect(self):
        try:
            self.client.close()
        except Exception as e:
            print(f"Error closing socket: {e}")