from Packet import Packet

class Receiver:
    
    def __init__(self, window_size: int):
        self.rcv_base = 0
        self.window_size = window_size
        self.buffer = [None for _ in range(self.window_size)]
        self.ack_tracker = [False for _ in range(self.window_size)]

    def receive(self, packet: Packet) -> list[Packet]:
        if packet.sequence_number >= self.rcv_base - self.window_size and packet.sequence_number <= self.rcv_base - 1:
            return [Packet(packet.sequence_number, True)]

        to_dispatch = []
        self.ack_tracker[packet.sequence_number % self.window_size] = True
        self.buffer[packet.sequence_number % self.window_size] = packet

        if packet.sequence_number == self.rcv_base:
            for i in range(self.rcv_base, self.rcv_base + self.window_size):
                if not self.ack_tracker[i]:
                    self.rcv_base = i
                    break
                to_dispatch.append(self.buffer[i])
        
        return to_dispatch
