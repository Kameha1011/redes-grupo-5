import struct 
import zlib
from ..constants import *

class Packet:

    # header format: 
    #   | package type (3bits) | op (1bit) | prt (1bit) | payload lenght (27bits)   |
    #   |                     checksum CRC32 (4bytes)                               |
    #   |                       package id (4bytes)                                 |


# TYPE_SYN = 0
# TYPE_SYN_ACK = 1
# TYPE_ACK = 2
# TYPE_DATA = 3
# TYPE_CLOSE = 4
# TYPE_NACK = 5

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

        header_part = struct.pack(HEADER_FORMAT, info, 0, self.seq_num)
        self.crc = zlib.crc32(header_part + payload)

        header = struct.pack(HEADER_FORMAT, info, self.crc, self.seq_num)
        return header + payload

    def _compose_info_field(self):
        info = 0
        
        # pktType: bits 31-29
        info |= (self.pkt_type << (INFO_FIELD_SIZE - PKT_TYPE_FIELD_SIZE))
        
        # Op: bit 28
        info |= (self.op_type << (INFO_FIELD_SIZE - PKT_TYPE_FIELD_SIZE - OP_TYPE_FIELD_SIZE))
        
        # Protocol: bit 27
        info |= (self.protocol << (INFO_FIELD_SIZE - PKT_TYPE_FIELD_SIZE - OP_TYPE_FIELD_SIZE - PROTOCOL_FIELD_SIZE))
        
        payload_mask = (1 << PAYLOAD_LENGTH_FIELD_SIZE) - 1
        
        info |= (self.data_length & payload_mask)
        
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
        
        header, crc, seq_num = struct.unpack(HEADER_FORMAT, raw_bytes[:cls.HEADER_SIZE])
        
        pkt_type = (header >> (INFO_FIELD_SIZE - PKT_TYPE_FIELD_SIZE)) & 0x07
        op_type = (header >> (INFO_FIELD_SIZE - PKT_TYPE_FIELD_SIZE - OP_TYPE_FIELD_SIZE)) & 0x01
        protocol = (header >> (INFO_FIELD_SIZE - PKT_TYPE_FIELD_SIZE - OP_TYPE_FIELD_SIZE - PROTOCOL_FIELD_SIZE)) & 0x01

        payload_mask = (1 << PAYLOAD_LENGTH_FIELD_SIZE) - 1
        
        data_len = header & payload_mask
        
        payload = raw_bytes[cls.HEADER_SIZE : cls.HEADER_SIZE + data_len]
        
        headerToVerify = struct.pack(HEADER_FORMAT, header, 0, seq_num)
        if zlib.crc32(headerToVerify + payload) != crc:
            print(f"WARNING: CRC mismatch en paquete {seq_num}")
            pass
        
        pkt = cls(pkt_type, op_type, protocol, payload, seq_num)
        pkt.crc = crc
        return pkt
