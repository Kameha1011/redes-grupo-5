import os
from socket import *
from ..common.selective_repeat.Sender import Sender
from ..common.selective_repeat.Receiver import Receiver
from ..common.selective_repeat.Packet import Packet
import threading

BUFFER_SIZE=1024

class Server:

    def __init__(self, storage_path: str, host: str, port: int):
        Server.init_storage_dir(storage_path)
        self.storage_path = storage_path
        self.host = host
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((host, port))
        self.sender = Sender()
        self.receiver = Receiver()
        print(f"Socket listening on {host}:{port}")


    def init_storage_dir(storage_path: str):
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def start(self):
        
        while True:
            data, addr = self.socket.recvfrom(BUFFER_SIZE)
            t = threading.Thread(target=self.handle_client, args=(data,addr))
            t.start()
            
    
    def handle_client(self, data: bytes, addr):
        parsed_data = data.decode()
        print(f"{addr} says: {parsed_data}")
        print(f"Answering a Hi! to {addr}")

        self.socket.sendto("Hi!".encode(), addr)

    def demultiplex(self, packet: Packet):
        pass