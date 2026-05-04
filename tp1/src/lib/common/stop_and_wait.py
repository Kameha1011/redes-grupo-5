from .protocol import Protocol
from .packet import Packet
from .constants import BUFFER_SIZE, TYPE_ACK, TYPE_CLOSE, TYPE_DATA, STOP_AND_WAIT_PROTOCOL
from socket import socket, timeout
import threading
import queue

class StopAndWait(Protocol):

    def __init__(
        self,
        op_type,
        socket: socket,
        socketLock: threading.Lock= None,
        window_size=10,
        chunk_size=1400,
        file="",
        ack_timeout=1.0,
        max_retries=10,
    ):
        super().__init__(op_type, STOP_AND_WAIT_PROTOCOL, socket, socketLock, window_size, chunk_size, file)
        self.socketLock = socketLock
        self.ack_timeout = ack_timeout
        self.max_retries = max_retries
    
    def send_data_packet(self, data: bytes, addr=None, clientDataQueue=None):
        pkt = Packet(TYPE_DATA, self.op_type, self.protocol, data, self.seq_num)
        self._send_and_wait_ack(pkt, addr=addr, clientDataQueue=clientDataQueue)

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
        self.safe_send(ack.to_bytes(), addr)
    
    def _send_and_wait_ack(self, pkt: Packet, addr=None, clientDataQueue=None):
        previous_timeout = self.socket.gettimeout()
        try:
            for _ in range(self.max_retries):
                self.safe_send(pkt.to_bytes(), addr)
                
                self.socket.settimeout(self.ack_timeout)
                try:
                    if clientDataQueue is not None:
                        # Para el Servidor con thread
                        try:
                            data = clientDataQueue.get(timeout=self.ack_timeout)
                        except queue.Empty:
                            raise timeout # para entrar al catch
                    else:
                        # Para el cliente
                        self.socket.settimeout(self.ack_timeout)
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
            if clientDataQueue is None:
                self.socket.settimeout(previous_timeout)
        raise TimeoutError("No se recibio ACK en Stop-and-Wait.")

    def end(self, addr=None, clientDataQueue=None):
        pkt = Packet(TYPE_CLOSE, self.op_type, self.protocol, b"", self.seq_num)
        self._send_and_wait_ack(pkt, addr=addr, clientDataQueue=clientDataQueue)

        if not addr:
            # el unico que cierra la conexion es el cliente, el server mantiene siempre el socket activo para escuchar a cualq cliente
            self.socket.close()

    def receive_file(self, file):
        previous_timeout = self.socket.gettimeout()
        self.socket.settimeout(float(self.ack_timeout)) 
        pkt = None
        consecutiveTimeouts = 0
        maxTimeouts = self.max_retries
        try:
            while consecutiveTimeouts < maxTimeouts:
                try:
                    buf = self.socket.recv(BUFFER_SIZE)

                    if not Packet.compare_checksum(buf):
                        print(f"[!] Checksum inválido. Paquete corrupto, descartando...")
                        continue
                    
                    pkt = Packet.from_bytes(buf)
                    
                    if pkt.pkt_type == TYPE_CLOSE:
                        self.handle_close(pkt)
                        return
                        
                    if pkt.pkt_type == TYPE_DATA:
                        payloads = self.receive_data_packet(pkt)
                        for data in payloads:
                            file.write(data)
                
                except (timeout, ValueError):
                    consecutiveTimeouts += 1
                    if pkt:
                        print(f"[!] Reintentando recibir tras paquete {pkt.seq_num}...")
                    else:
                        print("[!] Timeout: Esperando primer paquete de datos...")
                    continue
            
            raise TimeoutError(f"Transferencia fallida: se alcanzó el máximo de reintentos ({self.max_retries})")
        finally:
            self.socket.settimeout(previous_timeout)
