import os
from socket import *
from ..common.constants import *
from lib.common.file_handling import save_file
from lib.common.file_handling import *
from lib.common.factory import create_protocol
from lib.common.packet import Packet
from lib.common.logger import Logger
from lib.common.selective_repeat import SelectiveRepeat
from lib.common.exceptions import *
import queue

class Server:

    def __init__(self, storage_path: str, host: str, port: int):
        self.init_storage_dir(storage_path)
        self.logger = Logger.get_logger("SERVER")
        self.storage_path = storage_path
        self.host = host
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((host, port))
        self.buffers = {} # Experimental
        self.protocols = {} 
        self.filenames = {}
        self.files = {}
        self.logger.info(f"Socket listening on {host}:{port}")


    def init_storage_dir(self, storage_path: str):
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def start(self):
        while True:
            data, addr = self.socket.recvfrom(BUFFER_SIZE)
            #self.handle_client(data, addr)
            self.handle_clientt(data, addr)

    def handle_clientt(self, data, addr):
        event = None
        if addr in self.protocols:
                protocol = self.protocols[addr]
                event = protocol.handle_packet(data)
        else:
            try:
                protocol = SelectiveRepeat()
                event = protocol.handle_handshake(data)
                self.protocols[addr] = protocol
                # se debería usar filesize para chequear 
                # que el archivo se subió correctamente
                self.socket.sendto(protocol.syn_ack_to_bytes(), addr)
                self.logger.info(
                    f"Conexión con {addr[0]}:{addr[1]} establecida"
                )
            except Exception as e:
                print("ERROR: ", e)
                self.logger.info(
                    f"No pudo establecerse conexión con el cliente {addr[0]}:{addr[1]}"
                )
        if event:
            self.handle_event(event, addr, protocol)
                        
    def handle_event(self, event, addr, protocol):
        if event.type == EVENT_TYPE_HANDSHAKE:
            self.handle_handshake(addr, event)
        if event.type == EVENT_TYPE_DATA:
            self.handle_data(event, addr, protocol)
        if event.type == EVENT_TYPE_ACK:
            self.handle_ack(event.next_packages, protocol)
        if event.type == EVENT_TYPE_CLOSE:
            self.handle_close(addr, protocol)
    def handle_handshake(self, addr, event):
        if(event.op_type == OP_TYPE_DOWNLOAD):
            pass
        else:
            self.files[addr] = create_file(event.filename)

    def handle_data(self, event, addr, protocol):
        # data es el chunk de bytes que tiene que ir al archivo
        # llega seq_num = los sequence numbers que hay que hacer ack
        # llega data = la data que hay que ubicar en el archivo
        #self.logger.info(f"llegaron los sequence: {event.ack}")
        self.socket.sendto(protocol.ack(event.ack), addr)
        #self.logger.debug(f"Escribiendo: {event.data}")
        write_chunk(self.files[addr], b"".join(event.data))

    def handle_ack(self, window_slide, protocol):
        pass

    def handle_close(self, addr, event):
        self.files[addr].close()
