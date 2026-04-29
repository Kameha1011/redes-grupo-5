from .protocol import Protocol
from .packet import Packet
from ..constants import BUFFER_SIZE, TYPE_ACK, TYPE_CLOSE, TYPE_DATA, STOP_AND_WAIT_PROTOCOL
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

    def send_data_packet(self, data: bytes):
        pkt = Packet(TYPE_DATA, self.op_type, self.protocol, data, self.seq_num)
        self._send_and_wait_ack(pkt)

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

    def _send_and_wait_ack(self, pkt: Packet):
        raw = pkt.to_bytes()
        previous_timeout = self.socket.gettimeout()
        try:
            for _ in range(self.max_retries):
                self.socket.send(raw)
                self.socket.settimeout(self.ack_timeout)
                try:
                    data = self.socket.recv(BUFFER_SIZE)
                except timeout:
                    continue
                try:
                    ack_pkt = Packet.from_bytes(data)
                except ValueError:
                    continue
                if ack_pkt.pkt_type == TYPE_ACK and ack_pkt.seq_num == pkt.seq_num:
                    self.seq_num += 1
                    return
        finally:
            self.socket.settimeout(previous_timeout)
        raise TimeoutError("No se recibio ACK en Stop-and-Wait.")

    def end(self):
        pkt = Packet(TYPE_CLOSE, self.op_type, self.protocol, b"", self.seq_num)
        self._send_and_wait_ack(pkt)
        self.socket.close()