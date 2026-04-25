import constants
import struct
from packet import Packet

class Protocol:

    def __init__(self, 
                 op_type, 
                 prt,
                 window_size=10, 
                 chunk_size=1400,
                 file = ""
                 ):
        self.op_type = op_type
        self.protocol = prt
        self.window_size = window_size
        self.chunk_size = chunk_size
        self.window = {} # sequence_number : data
        self.seq = 0
        self.next_expected = 0
        self.file = file

    def compose(self, pkt_type, data):
        #composes data packet and returns packet
        pkt = Packet(pkt_type, self.op_type, self.protocol, data, self.seq)
        self.seq = self.seq + 1
        return pkt
    
    def syn(self, filename, file_size, filepath):
        # creates SYN package with:
        # data as filename
        # file size as sequence number
        data = filepath + '\0' + filename
        syn = Packet(constants.TYPE_SYN, self.op_type, self.protocol, data, file_size)
        return syn
    
    def ack(self, seq):
        # creates ACK packet
        ack = Packet(constants.TYPE_ACK, self.op_type, self.protocol, seq)
        return ack

    def get_needed_bytes(self):
        # returns # of bytes needed to complete window
        free_spaces = self.window_size - len(self.window)
        return free_spaces * self.chunk_size
    
    def push_payload(self, data):  
        # creates list of packages
        pkts = []
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i: i + self.chunk_size]
            pkt = self.compose(constants.TYPE_DATA, chunk)
            self.window[pkt.seq_num] = pkt
            pkts.append(pkt)
        return pkts
    
    def parse_raw(self, raw_bytes):
        # esta linea debería hacerse con un método de packet quizas
        # para encapsular lógica
        info, seq, crc = struct.unpack(Packet.HEADER_FORMAT, raw_bytes)
        # hay que chequear el CRC que es el checksum con 
        # Packet.compare_checksum(raw_bytes)
        pkt_type, op_type, protocol, payload_length = self.parse_info_bytes(info)
        if(pkt_type == constants.TYPE_SYN):
            data = []
        else: 
            data = raw_bytes[Packet.HEADER_SIZE:Packet.HEADER_SIZE + payload_length]

        if seq < self.next_expected:
            return
        if seq not in self.window:
            self.window[seq] = data
        while self.next_expected in self.window:
            file_data = self.window.pop(self.next_expected)
            self.file.write(file_data)
            self.next_expected += 1

    def parse_info_bytes(info):
        # esta operación deberia ir en Packet
        # bitwise operations
        #tttoplllllllllllllllllllllllllll
        pkt_type = info >> 29
        op_type = (info >> 28) & constants.OP_TYPE_MASK
        protocol = (info >> 27) & constants.PROTOCOL_MASK
        payload_length = info & constants.PAYLOAD_LENGTH_MASK
        return pkt_type, op_type, protocol, payload_length
    
    
    def _handle_file_data():
        pass
