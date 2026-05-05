from .constants import *
import struct
from .packet import Packet
from socket import *
import struct
from abc import ABC, abstractmethod
import os
from lib.common.logger import Logger
import time

class Protocol(ABC):

    def __init__(
                 self, 
                 op_type: str, 
                 window_size=WINDOW_SIZE, 
                 chunk_size=PAYLOAD_SIZE,
                 file = ""
                 ):
        self.logger = Logger.get_logger("PROTOCOL")
        self.op_type = op_type
        self.window_size = window_size
        self.chunk_size = chunk_size
        self.window = {} # sequence_number : data
        self.seq_num = 1
        self.next_expected = 1

    def get_chunk_size(self) -> int:
        return self.chunk_size

    def compose(self, pkt_type, data):
        #composes data packet and returns packet
        pkt = Packet(pkt_type, self.op_type, self.protocol, data, self.seq_num)
        return pkt

    
    def ack(self, seq):
        # creates ACK packet
        ack = Packet(TYPE_ACK, self.op_type, self.protocol, b"", seq)
        return ack
    
    def push_payload(self, data):  
        # creates list of packages
        pkts = []
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i: i + self.chunk_size]
            pkt = self.compose(TYPE_DATA, chunk)
            self.window[pkt.seq_num] = pkt
            pkts.append(pkt)
        return pkts

