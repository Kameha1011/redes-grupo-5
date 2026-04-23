class Packet:
    
    def __init__(self, initial_sn: int, is_ack: bool):
        self.sequence_number = initial_sn
        self.is_ack = is_ack