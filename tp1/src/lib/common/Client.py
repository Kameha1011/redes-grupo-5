from socket import *
from lib.common.file_handling import get_file
from .protocol import Protocol
from ..constants import *
import os

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
            data = self.socket.recv(BUFFER_SIZE)

    def begin(self, p, filepath, filename):
        fileSize = os.path.getsize(filepath)
        syn_pkt = p.syn(filepath, fileSize, filename)
        self.send_message(syn_pkt.to_bytes())
        print("SYN enviado, esperando respuesta...")
        self.socket.settimeout(5.0)
        try:
            buf = self.socket.recv(HEADER_SIZE)
        except timeout:
            print("TIMEOUT")

    def upload_file(self, src_filepath: str, name: str, protocol_choice: int):
        prt = Protocol(OP_TYPE_UPLOAD, protocol_choice)
        self.begin(prt, src_filepath, name)

        fullPath = os.path.join(src_filepath, name)
        
        filebytes = get_file(fullPath)
        
        chunkSize = BUFFER_SIZE
        seqNum = 1
        
        for i in range(0, len(filebytes), chunkSize):
            chunk = filebytes[i:i+chunkSize]
            
            pkt = prt.compose(TYPE_DATA, chunk, seqNum)
            
            self.send_message(pkt.to_bytes())
            
            print(f"Enviando paquete {seqNum}...")

            seqNum += 1

        pktClose = prt.compose(TYPE_CLOSE, b"", seqNum)
        self.send_message(pktClose.to_bytes())
        print("Transferencia finalizada paquete TYPE_CLOSE enviado.")

    def download_file(self, dst_path: str, name: str):
        pass

    def close(self):
        self.socket.close()
