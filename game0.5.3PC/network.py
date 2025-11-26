import socket
import pickle

class Network:
    def __init__(self, server_ip):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_ip
        self.port = 5555
        self.addr = (self.server, self.port)
        self.p = self.connect()

    def getP(self):
        return self.p

    def connect(self):
        try:
            self.client.settimeout(5)
            self.client.connect(self.addr)
            return pickle.loads(self.client.recv(4096))
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
            self.client.send(pickle.dumps(data))
            reply_data = self.client.recv(4096 * 32) 
            
            if not reply_data:
                # Server closed the connection gracefully (no data received)
                raise ConnectionAbortedError("Server closed connection.")
                
            return pickle.loads(reply_data)
            
        except (ConnectionResetError, ConnectionAbortedError, socket.error) as e:
            # Crucial: Catch all major network failures
            print(f"Network error (graceful exit required): {e}")
            return "NETWORK_FAILURE" # Signal for client.py to exit gracefully

        except Exception as e:
            # General catch-all for errors like pickle corruption
            print(f"Serialization or other critical error: {e}")
            return "NETWORK_FAILURE"
            
    def disconnect(self):
        try:
            self.client.close()
        except Exception as e:
            print(f"Error closing socket: {e}")