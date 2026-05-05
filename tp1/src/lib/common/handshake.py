from .packet import Packet
from .protocol_factory import create_protocol, protocol_id_from_choice
from socket import timeout, socket
from .constants import TYPE_SYN, BUFFER_SIZE, TYPE_SYN_ACK
from socket import AF_INET, SOCK_DGRAM, socket
from ..common.constants import *
import threading

class Handshake():

    def start(dest_host, dest_port, file_name: str, file_size: int, file_path: str, protocol: str, op_type: str):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.connect((dest_host, dest_port))
        seq_num = 0
        protocol_id = protocol_id_from_choice(protocol)
        if op_type == OP_TYPE_UPLOAD:
            # 0: filename, 1: filesize
            data = f"{file_name}\0{file_size}".encode()
        else:
            # 0: filename
            data = f"{file_name}".encode()

        syn = Packet(TYPE_SYN, op_type, protocol_id, data, seq_num)
        sock.send(syn.to_bytes())
        sock.settimeout(5.0)

        try:
            buf = sock.recv(BUFFER_SIZE)
            pkt = Packet.from_bytes(buf)
            
            if pkt.pkt_type != TYPE_SYN_ACK:
                raise ValueError("Se recibió un paquete que no es del tipo syn-ack.")
            print("Handshake exitoso. Conexión establecida.")
        except timeout:
            raise TimeoutError("Timeout, el servidor no respondió la conexión.")
        sock.settimeout(1.0)
        return create_protocol(protocol_id, op_type, sock, socketLock=None)
    
    def ack(socket: socket, syn_pkt: Packet, addr: str, lock: threading.Lock = None):
        pkt_bytes = Packet(TYPE_SYN_ACK, syn_pkt.op_type, syn_pkt.protocol, b"SYN-ACK", syn_pkt.seq_num).to_bytes()
        if lock:
            with lock:
                socket.sendto(pkt_bytes, addr)
        else:
            socket.sendto(pkt_bytes, addr)
