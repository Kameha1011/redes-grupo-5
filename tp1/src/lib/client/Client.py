from socket import *
from lib.common.file_handling import *
from ..common.selective_repeat import SelectiveRepeat
from ..common.packet import Packet
from ..common.constants import *
from lib.common.logger import Logger
import time
import os

class Client:
    
    def __init__(self, 
                 protocol, 
                 server_host: str, 
                 server_port: int,
                 op_type):
        self.logger = Logger.get_logger("CLIENT")
        self.server_addr = (server_host, server_port)
        self.start_socket(self.server_addr)
        self.protocol = SelectiveRepeat()
        self.file = None
        self.op_type = op_type
    
    def start_socket(self, server_addr):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.connect(self.server_addr)
        self.logger.info(
            f"Cliente listo. Puerto: {self.socket.getsockname()[1]}")
    
    def send_message(self, message: bytes):
        self.socket.send(message)
    
    def wait_response(self) -> bytes:
        while True:
            data, addr = self.socket.recvfrom(BUFFER_SIZE)
            return addr, self.protocol.handle_packet(data)

    def upload_file(self, path, save_name):
        init = time.time()
        self.file = open_file(path)
        filesize = get_size(path)
        # handshake
        syn = self.protocol.syn(save_name, filesize)
        self.send_message(syn)
        addr, event = self.wait_response()
        if event:
            self.handle_event(event, addr, self.protocol)
        # fin handshake
        package_window = read_chunk(self.file, WINDOW_SIZE*PAYLOAD_SIZE)
        for i in self.protocol.push_payload(package_window):
            self.socket.send(i)
        while self.file:
            data, addr = self.socket.recvfrom(BUFFER_SIZE)
            event = self.protocol.handle_packet(data)
            self.handle_event(event, addr, self.protocol)
        fin = time.time()
        elapsed = fin - init
        self.logger.info(f"Finished in: {elapsed}")

    def handle_event(self, event, addr, protocol):
        if event.type == EVENT_TYPE_SYN_ACK:
            self.handle_syn_ack(event, addr)
        if event.type == EVENT_TYPE_DATA:
            self.handle_data(event, addr, protocol)
        if event.type == EVENT_TYPE_ACK:
            self.handle_ack(event.next, protocol)
            
    def download_file(self, dst_path: str, name: str):
        pass

    def handle_syn_ack(self, event, addr):
        self.logger.debug(f"SUCCESS: Conexion establecida con {addr[0]}:{addr[1]}")
    def close(self):
        self.socket.close()

    def handle_handshake():
        pass

    def handle_ack(self, advance, protocol):
        package_window = read_chunk(self.file, advance*PAYLOAD_SIZE)
        if not package_window:
            self.file.close()
            self.file = None
            fin = protocol.fin()
            self.socket.send(fin)
            self.logger.debug("Archivo cerrado")
        for i in protocol.push_payload(package_window):
            self.socket.send(i)