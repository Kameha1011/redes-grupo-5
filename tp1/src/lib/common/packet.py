import struct 
import zlib
from ..constants import *

class Packet:

    # header format: 
    #   | package type (3bits) | op (1bit) | prt (1bit) | payload lenght (27bits)   |
    #   |                     checksum CRC32 (4bytes)                               |
    #   |                       package id (4bytes)                                 |


    # TYPE_DATA = 1
    # TYPE_ACK = 2
    # TYPE_CLOSE = 3
    # TYPE_SYN = 4

    HEADER_FORMAT = "!III" # ! = ordenado Big Endian ; I = 4 bytes integer => 12 bytes header
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, pkt_type, op_type, protocol, data=b"", seq_num=0):
        self.pkt_type = pkt_type
        self.seq_num = seq_num
        self.data = data
        self.op_type = op_type
        self.protocol = protocol
        self.crc = 0
        self.data_length = len(self.data)

    def to_bytes(self):
        # creates header and concatenates with data
        info = self._compose_info_field()

        if isinstance(self.data, str):
            payload = self.data.encode()
        else:
            payload = self.data

        header_part = struct.pack('!II', info, self.seq_num)
        crc = zlib.crc32(header_part + payload)
        header = struct.pack('!III', info, self.seq_num, crc)
        return header + payload

    def _compose_info_field(self):
        # creates first 4 bytes of header
        info = 0 
        info |= (self.pkt_type << 29) | (self.op_type << 28) | (self.protocol << 27)
        info |= (self.data_length & PAYLOAD_LENGTH_FIELD_SIZE)
        return info
    
    # def from_bytes(cls, raw_bytes):
    #     # creates Packet instance from bytes
    #     if len(raw_bytes) < cls.HEADER_SIZE:
    #         return None
        
    #     # Extraemos el encabezado
    #     header_raw = raw_bytes[:cls.HEADER_SIZE]
    #     pkt_type, seq_num, data_len = struct.unpack(cls.HEADER_FORMAT, header_raw)
        
    #     # Extraemos los datos
    #     data = raw_bytes[cls.HEADER_SIZE : cls.HEADER_SIZE + data_len]
    #     return pkt_type, seq_num, data
    

    @staticmethod
    def compare_checksum(raw_packet):
        # get checksum from raw bytes
        expected_checksum = struct.unpack_from("!I", raw_packet, 4)[0]
        # recompose packet with 0 in checksum field
        packet_to_validate = raw_packet[:4] + b'\x00\x00\x00\x00' + raw_packet[8:]
        real_checksum = zlib.crc32(packet_to_validate)
        return expected_checksum == real_checksum
    
    @classmethod
    def from_bytes(cls, raw_bytes):
        if len(raw_bytes) < cls.HEADER_SIZE:
            raise ValueError("Paquete corto para procesar")
        
        header, seq_num, crc = struct.unpack(cls.HEADER_FORMAT, raw_bytes[:cls.HEADER_SIZE])
        
        pkt_type = (header >> 29) & 0x07
        op_type = (header >> 28) & 0x01
        protocol = (header >> 27) & 0x01
        data_len = header & 0x07FFFFFF 
        
        payload = raw_bytes[cls.HEADER_SIZE : cls.HEADER_SIZE + data_len]
        
        pkt = cls(pkt_type, op_type, protocol, payload, seq_num)
        pkt.crc = crc
        return pkt
    