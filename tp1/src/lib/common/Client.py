from socket import *
from lib.common.file_handling import get_file
from protocol import Protocol
from constants import *

class Client:
    def __init__(self, server_host: str, server_port: int):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        # self.socket.bind(('localhost', 0)) # Bind to any available port

        # Fijar la dirección del servidor para evitar tener que especificarla en cada envío
        self.socket.connect((server_host, server_port))
    
    def send_message(self, message: bytes):
        # self.socket.send(message,(self.server_host, self.server_port))
        self.socket.send(message)
    
    def wait_response(self) -> bytes:
        while True:
            # data, addr = self.socket.recvfrom(1024)
            # print(f"Server in {addr} says: {data.decode()}")
            data = self.socket.recv(1024)

    def begin(self, p, filepath, filename):
        syn_pkt = p.syn(filepath, filename)
        self.send_message(syn_pkt)
        buf = self.socket.recv(HEADER_SIZE)
        p

    def upload_file(self, src_filepath: str, name: str):
        prt = Protocol(OP_TYPE_UPLOAD)
        self.begin(prt, src_filepath, name)
        
        file_bytes = get_file(src_filepath)
        
        # Simulate several packets by sending the file in chunks
        chunk_size = 1024
        for i in range(0, len(file_bytes), chunk_size):
            chunk = file_bytes[i:i+chunk_size]
            self.socket.send(chunk)
        # Send EOF to indicate the end of the file
        self.socket.send(b"EOF")



        # Alternative: send the whole file at once (not recommended for large files)
        # self.socket.send(file_bytes)

    def download_file(self, dst_path: str, name: str):
        pass

    def close(self):
        self.socket.close()
