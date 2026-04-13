from socket import *

class Client:
    def __init__(self, server_host: str, server_port: int):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = socket(AF_INET, SOCK_DGRAM)
    
    def send_message(self, message: bytes):
        self.socket.sendto(message,(self.server_host, self.server_port))
    
    def wait_response(self) -> bytes:
        while True:
            data, addr = self.socket.recvfrom(1024)
            print(f"Server in {addr} says: {data.decode()}")
