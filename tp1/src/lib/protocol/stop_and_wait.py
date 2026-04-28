from .protocol import Protocol
from .packet import Packet
from ..constants import BUFFER_SIZE, TYPE_ACK, TYPE_DATA, STOP_AND_WAIT_PROTOCOL


class StopAndWait(Protocol):

    def __init__(self, op_type, server_port, server_host, window_size=10, chunk_size=1400, file=""):
        super().__init__(op_type, STOP_AND_WAIT_PROTOCOL, server_port, server_host, window_size, chunk_size, file)

    def send_data_packet(self, data: bytes):
        self.socket.send(Packet(TYPE_DATA, self.op_type, self.protocol, data, self.seq_num).to_bytes())
        while True:
            data = self.socket.recv(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            if ack_pkt.pkt_type == TYPE_ACK and ack_pkt.seq_num == self.seq_num:
                self.seq_num += 1
                break

    def end(self):
        self.send_close()
        self.socket.close()