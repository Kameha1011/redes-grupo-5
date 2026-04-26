import os
from socket import *
from ..constants import *

from lib.common.file_handling import save_file
# import threading
from lib.common.protocol import Packet, TYPE_DATA, TYPE_CLOSE


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
        try:
            pkt = Packet.from_bytes(data)
        except Exception as e:
            print(f"Error parseando paquete de {addr}: {e}")
            return

        if addr not in self.buffers:
            self.buffers[addr] = bytes()
            print(f"Iniciando recepción de {addr}")

        if pkt.pkt_type == TYPE_DATA:
            self.buffers[addr] += pkt.data

        elif pkt.pkt_type == TYPE_CLOSE:
            print(f"Transferencia finalizada paquete {addr} via TYPE_CLOSE")
            
            filename = f"upload_{addr[1]}.bin"
            
            save_file(self.storage_path, filename, self.buffers[addr])
            
            del self.buffers[addr]
