from .protocol import Protocol
from .packet import Packet
from .constants import BUFFER_SIZE, TYPE_ACK, TYPE_CLOSE, TYPE_DATA, STOP_AND_WAIT_PROTOCOL
from socket import socket, timeout

class StopAndWait(Protocol):

    def __init__(
        self,
        op_type,
        socket: socket,
        window_size=10,
        chunk_size=1400,
        file="",
        ack_timeout=0.5,
        max_retries=10,
    ):
        super().__init__(op_type, STOP_AND_WAIT_PROTOCOL, socket, window_size, chunk_size, file)
        self.ack_timeout = ack_timeout
        self.max_retries = max_retries

    def send_data_packet(self, data: bytes, addr=None):
        pkt = Packet(TYPE_DATA, self.op_type, self.protocol, data, self.seq_num)
        self._send_and_wait_ack(pkt, addr)

    def receive_data_packet(self, pkt: Packet, addr=None):
        payloads = []
        if pkt.seq_num == self.next_expected:
            payloads.append(pkt.data)
            self.next_expected += 1
        ack_seq = pkt.seq_num if payloads else (self.next_expected - 1)
        self._send_ack(ack_seq, addr)
        return payloads

    def handle_close(self, pkt: Packet, addr=None):
        self._send_ack(pkt.seq_num, addr)
        return True

    def _send_ack(self, seq_num, addr=None):
        ack = self.ack(seq_num)
        if addr is None:
            self.socket.send(ack.to_bytes())
        else:
            self.socket.sendto(ack.to_bytes(), addr)

    def _send_and_wait_ack(self, pkt: Packet, addr=None):
        raw = pkt.to_bytes()
        previous_timeout = self.socket.gettimeout()
        try:
            for _ in range(self.max_retries):
                if addr:
                    self.socket.sendto(raw, addr)
                else:
                    self.socket.send(raw)

                self.socket.settimeout(self.ack_timeout)
                try:
                    data = self.socket.recv(BUFFER_SIZE)

                    if not Packet.compare_checksum(data):
                        print(f"[!] Checksum de ACK inválido. Retransmitiendo seq: {pkt.seq_num}...")
                        continue 
                    
                    ack_pkt = Packet.from_bytes(data)
                    
                    if ack_pkt.pkt_type == TYPE_ACK and ack_pkt.seq_num == pkt.seq_num:
                        self.seq_num += 1
                        return
                
                except (timeout, ValueError):
                    print(f"[!] Reintentando envío de paquete {pkt.seq_num}...")
                    continue
                
        finally:
            self.socket.settimeout(previous_timeout)
        raise TimeoutError("No se recibio ACK en Stop-and-Wait.")

    def end(self, addr=None):
        pkt = Packet(TYPE_CLOSE, self.op_type, self.protocol, b"", self.seq_num)
        self._send_and_wait_ack(pkt, addr)

        if not addr:
            # el unico que cierra la conexion es el cliente, el server mantiene siempre el socket activo para escuchar a cualq cliente
            self.socket.close()

    def receive_file(self, file):
        previous_timeout = self.socket.gettimeout()
        self.socket.settimeout(self.ack_timeout)
        try:
            while True:
                try:
                    buf, addr = self.socket.recvfrom(BUFFER_SIZE)
                    
                    if not Packet.compare_checksum(buf):
                        print(f"[!] Checksum inválido de {addr}. Paquete corrupto, descartando...")
                        continue
                    
                    pkt = Packet.from_bytes(buf)
                    
                    if pkt.pkt_type == TYPE_CLOSE:
                        self.handle_close(pkt, addr)
                        return
                        
                    if pkt.pkt_type == TYPE_DATA:
                        payloads = self.receive_data_packet(pkt, addr)
                        for data in payloads:
                            file.write(data)
                
                except (timeout, ValueError):
                    print(f"[!] Reintentando recibir paquete {pkt.seq_num}...")
                    continue
        finally:
            self.socket.settimeout(previous_timeout)
