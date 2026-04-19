from Packet import Packet

class Sender:
    
    def __init__(self):
        self.send_base = 0
        self.window_size = 1024
        self.next_sn = 0
        self.min_unack = 0
        self.buffer_window = [False for _ in range(self.window_size)]
        self.timers = [False for _ in range(self.window_size)] # https://stackoverflow.com/questions/40113972/simulate-multiple-virtual-timers-with-one-physical-timer

    def feed(self, data: bytes):
        if self.buffer_window[len(self.buffer_window)-1]:
            raise MemoryError("Sender window is full")

    def send(self):
        pass

    def handle_ack(self, packet: Packet):
        """"""
        pass

