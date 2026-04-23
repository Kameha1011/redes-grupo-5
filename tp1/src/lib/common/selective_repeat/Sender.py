from Packet import Packet
import time

TIMEOUT_MS = 2500

class Sender:
    
    def __init__(self, window_size: int):
        self.send_base = 0
        self.window_size = window_size
        self.next_sn = 0
        self.buffer= [None for _ in range(self.window_size)]
        self.ack_tracker = [False for _ in range(self.window_size)]
        self.timer = time.time()
        self.timers = [0 for _ in range(self.window_size)] # https://stackoverflow.com/questions/40113972/simulate-multiple-virtual-timers-with-one-physical-timer

    def feed(self, packet: Packet):
        if self.buffer[self.window_size - 1]:
            raise MemoryError("Sender window is full")
        
        self.buffer[self.next_sn % self.window_size] = packet
        self.ack_tracker[self.next_sn % self.window_size] = False
        self.timers[self.next_sn % self.window_size] = time.time() - self.timer
        self.next_sn += 1

    def handle_ack(self, packet: Packet) -> list[Packet]:
        pending_ack = []
        self.ack_tracker[packet.sequence_number % self.window_size] = True
        self.buffer[packet.sequence_number % self.window_size] = None
        self.timers[packet.sequence_number % self.window_size] = 0
        if packet.sequence_number == self.send_base:
            for i in range(self.send_base, len(self.ack_tracker)):
                if not self.ack_tracker[i]:
                    self.send_base = i
                    break
                pending_ack.append(self.buffer[i])
        return pending_ack
    
    def check_timers(self) -> list[Packet]:
        elapsed = time.time() - self.timer
        to_resend = []

        for i, packet in enumerate(self.buffer):
            if packet is None or self.ack_tracker[i]:
                continue

            if elapsed - self.timers[i] >= TIMEOUT_MS:
                to_resend.append(packet)
                self.timers[i] = elapsed

        return to_resend
