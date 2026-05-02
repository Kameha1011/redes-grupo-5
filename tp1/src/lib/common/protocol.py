from .constants import *
import struct
from .packet import Packet
from socket import *
import struct
from abc import ABC, abstractmethod
import os
from lib.common.logger import Logger

class Protocol(ABC):

    def __init__(
                 self, 
                 op_type: str, 
                 prt: str,
                 socket: socket,
                 window_size=10, 
                 chunk_size=1400,
                 file = ""
                 ):
        self.socket = socket
        self.logger = Logger.get_logger("PROTOCOL")
        self.op_type = op_type
        self.protocol = prt
        self.window_size = window_size
        self.chunk_size = chunk_size
        self.window = {} # sequence_number : data
        self.seq_num = 1
        self.next_expected = 1
        self.file = file

    def get_chunk_size(self) -> int:
        return self.chunk_size

    def compose(self, pkt_type, data):
        #composes data packet and returns packet
        pkt = Packet(pkt_type, self.op_type, self.protocol, data, self.seq_num)
        return pkt

    def ack(self, seq):
        # creates ACK packet
        ack = Packet(TYPE_ACK, self.op_type, self.protocol, b"", seq)
        return ack

    def get_needed_bytes(self):
        # returns # of bytes needed to complete window
        free_spaces = self.window_size - len(self.window)
        return free_spaces * self.chunk_size
    
    def push_payload(self, data):  
        # creates list of packages
        pkts = []
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i: i + self.chunk_size]
            pkt = self.compose(TYPE_DATA, chunk)
            self.window[pkt.seq_num] = pkt
            pkts.append(pkt)
        return pkts
    
    def parse_raw(self, raw_bytes):
        # esta linea debería hacerse con un método de packet quizas
        # para encapsular lógica
        info, seq, crc = struct.unpack(Packet.HEADER_FORMAT, raw_bytes)
        # hay que chequear el CRC que es el checksum con 
        # Packet.compare_checksum(raw_bytes)
        pkt_type, op_type, protocol, payload_length = Packet.parse_info_bytes(info)
        if(pkt_type == TYPE_SYN):
            data = []
        else: 
            data = raw_bytes[Packet.HEADER_SIZE:Packet.HEADER_SIZE + payload_length]

        if seq < self.next_expected:
            return
        if seq not in self.window:
            self.window[seq] = data
        while self.next_expected in self.window:
            file_data = self.window.pop(self.next_expected)
            self.file.write(file_data)
            self.next_expected += 1

    # @staticmethod
    # def parse_info_bytes(info):
    #     # esta operación deberia ir en Packet
    #     # bitwise operations
    #     #tttoplllllllllllllllllllllllllll
    #     pkt_type = info >> 29
    #     op_type = (info >> 28) & OP_TYPE_MASK
    #     protocol = (info >> 27) & PROTOCOL_MASK
    #     payload_length = info & PAYLOAD_LENGTH_MASK
    #     return pkt_type, op_type, protocol, payload_length

    def start(self, file_path: str, file_name: str):
        file_size = os.path.getsize(file_path)
        syn_pkt = self.syn(file_path, file_name, file_size)
        self.socket.send(syn_pkt.to_bytes())
        self.socket.settimeout(5.0)

        try:
            buf = self.socket.recv(HEADER_SIZE)
            pkt = Packet.from_bytes(buf)
            
            if pkt.pkt_type != TYPE_SYN_ACK:
                raise ValueError("Se recibió un paquete que no es del tipo syn-ack.")
            print("Handshake exitoso. Conexión establecida.")
        except timeout:
            raise TimeoutError("Timeout, el servidor no respondió la conexión.")
        finally:
            self.socket.settimeout(None)

    def send_close(self):
        pkt_close = Packet(TYPE_CLOSE, self.op_type, self.protocol, b"", self.seq_num)
        self.socket.send(pkt_close.to_bytes())
        print("Transferencia finalizada paquete TYPE_CLOSE enviado.")

    @abstractmethod
    def send_data_packet(self, data: bytes):
        pass

    @abstractmethod
    def receive_data_packet(self, pkt: Packet, addr=None):
        pass

    @abstractmethod
    def handle_close(self, pkt: Packet, addr=None):
        pass

    @abstractmethod
    def end(self):
        pass

