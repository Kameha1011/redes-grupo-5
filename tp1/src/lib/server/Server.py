import os
from socket import *

from lib.common.file_handling import save_file
# import threading

BUFFER_SIZE=1024

class Server:

    def __init__(self, storage_path: str, host: str, port: int):
        Server.init_storage_dir(storage_path)
        self.storage_path = storage_path
        self.host = host
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((host, port))

        self.buffers = {} # Experimental
        
        print(f"Socket listening on {host}:{port}")


    def init_storage_dir(storage_path: str):
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def start(self):
        
        while True:
            data, addr = self.socket.recvfrom(BUFFER_SIZE)
            # t = threading.Thread(target=self.handle_client, args=(data,addr))
            # t.start()
            self.handle_client(data, addr)
            
    
    def handle_client(self, data: bytes, addr):
        # parsed_data = data.decode()
        # print(f"{addr} says: {parsed_data}")
        # print(f"Answering a Hi! to {addr}")
        # self.socket.sendto("Hi!".encode(), addr)


        # What follows is experimental!

        if addr not in self.buffers:
            self.buffers[addr] = bytes()

        self.buffers[addr] += data

        if self.buffers[addr].endswith(b"EOF"):
            print(f"Received complete file from {addr}")
            save_file(self.storage_path, f"file_from_{addr[0]}_{addr[1]}.dat", self.buffers[addr][:-3]) # Remove EOF
            del self.buffers[addr]
