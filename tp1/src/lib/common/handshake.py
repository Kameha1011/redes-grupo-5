from .packet import Packet
from .factory import create_protocol, protocol_id_from_choice
from socket import timeout, socket
from .constants import TYPE_SYN, BUFFER_SIZE, TYPE_SYN_ACK
from socket import AF_INET, SOCK_DGRAM, socket

class Handshake():

    def start(dest_host, dest_port, file_name: str, file_size: int, file_path: str, protocol: str, op_type: str):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.connect((dest_host, dest_port))
        seq_num = 0
        protocol_id = protocol_id_from_choice(protocol)
        # 0: filename, 1: filesize, 2: filepath
        data = f"{file_name}\0{file_size}\0{file_path}".encode()
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
        sock.settimeout(None)
        return create_protocol(protocol_id, op_type, sock)

    def ack(socket: socket, syn_pkt: Packet, addr: str ):
        socket.sendto(Packet(TYPE_SYN_ACK, syn_pkt.op_type, syn_pkt.protocol, b"SYN-ACK", syn_pkt.seq_num).to_bytes(), addr)
