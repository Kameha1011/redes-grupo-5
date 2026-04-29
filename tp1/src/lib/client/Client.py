from lib.common.file_handling import get_file
from ..common.handshake import Handshake
from ..common.constants import *
import os

class Client:
    def __init__(self, protocol_choice: str, host: str, port: int, op_type: str):
        self.protocol_choice = protocol_choice
        self.protocol = None
        self.op_type = op_type
        self.host = host
        self.port = port

    def start(self, file_path: str, file_name: str):
        file_size = os.path.getsize(file_path)
        protocol = Handshake.start(self.host, self.port, file_name, file_size, file_path, self.protocol_choice, self.op_type)
        self.set_protocol(protocol)

    def set_protocol(self, protocol):
        if protocol is None:
            raise NotImplementedError("Protocolo no implementado o invalido.")
        self.protocol = protocol

    def upload_file(self, src_filepath: str, name: str):
        if self.protocol == None:
            raise NotImplementedError("Debes iniciar el handshake primero")

        fullPath = os.path.join(src_filepath, name)
        filebytes = get_file(fullPath)
        chunkSize = self.protocol.get_chunk_size()
        
        for i in range(0, len(filebytes), chunkSize):
            chunk = filebytes[i:i+chunkSize]
            self.protocol.send_data_packet(chunk)
            
        self.protocol.end()

    def download_file(self, dst_path: str, name: str):
        pass
