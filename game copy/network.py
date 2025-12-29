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
        
        # --- TELEMETRY & STATS ---
        self.latency = 0  # Ping в мс
        self.last_time_check = time.time()
        
        self.traffic_stats = {
            "sent_total": 0,
            "recv_total": 0,
            "sent_per_sec": 0,    # New: KB/s upload
            "recv_per_sec": 0,    # New: KB/s download
            "last_packet_size_sent": 0,
            "last_packet_size_recv": 0,
            "packets_sent": 0,
            "packets_recv": 0,
        }
        
        # Временные счетчики для расчета скорости в секунду
        self._temp_sent = 0
        self._temp_recv = 0
        self._temp_packets_sent = 0
        self._temp_packets_recv = 0
        
        self.p = self.connect()

    def getP(self):
        return self.p

    def connect(self):
        try:
            self.client.settimeout(5)
            self.client.connect(self.addr)
            raw_data = self.client.recv(8192) # Увеличил буфер инициализации
            self.traffic_stats["recv_total"] += len(raw_data)
            return pickle.loads(raw_data)
        except Exception as e:
            print(f"Connection failed: {e}")
            self.disconnect()
            return None

    def _update_rates(self):
        """Обновляет показатели скорости раз в секунду"""
        now = time.time()
        diff = now - self.last_time_check
        if diff >= 1.0:
            self.traffic_stats["sent_per_sec"] = self._temp_sent / diff / 1024 # KB/s
            self.traffic_stats["recv_per_sec"] = self._temp_recv / diff / 1024 # KB/s
            self._temp_sent = 0
            self._temp_recv = 0
            self.last_time_check = now

    def send(self, data):
        try:
            start_time = time.perf_counter()
            
            # 1. Подготовка и отправка данных с заголовком
            serialized_data = pickle.dumps(data)
            data_size = len(serialized_data)
            length_prefix = struct.pack('>I', data_size) # 4 байта длины
            
            self.client.sendall(length_prefix + serialized_data)
            
            # Обновление статистики отправки
            self.traffic_stats["sent_total"] += data_size
            self.traffic_stats["packets_sent"] += 1
            self._temp_sent += data_size

            # 2. Получение ответа: сначала читаем 4 байта длины
            header = self.client.recv(4)
            if not header or len(header) < 4:
                return None
            
            msg_len = struct.unpack('>I', header)[0]
            
            # 3. Читаем тело сообщения целиком (в цикле)
            chunks = []
            bytes_recd = 0
            while bytes_recd < msg_len:
                # Читаем остаток данных
                chunk = self.client.recv(min(msg_len - bytes_recd, 4096 * 32))
                if not chunk:
                    raise RuntimeError("Соединение разорвано")
                chunks.append(chunk)
                bytes_recd += len(chunk)
            
            full_data = b''.join(chunks)
            
            # Статистика приема и пинг
            end_time = time.perf_counter()
            self.latency = (end_time - start_time) * 1000
            self.traffic_stats["recv_total"] += len(full_data)
            self.traffic_stats["packets_recv"] += 1
            self._temp_recv += len(full_data)
            self._update_rates()

            return pickle.loads(full_data)
            
        except (socket.error, pickle.UnpicklingError) as e:
            print(f"Network error: {e}")
            return None
            
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