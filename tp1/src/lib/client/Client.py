from lib.common.file_handling import get_file
from ..common.handshake import Handshake
from ..common.constants import *
from lib.common.packet import Packet
import os

class Client:
    def __init__(self, protocol_choice: str, host: str, port: int, op_type: str):
        self.protocol_choice = protocol_choice
        self.protocol = None
        self.op_type = op_type
        self.host = host
        self.port = port

    def start(self, file_path: str, file_name: str):
        if self.op_type == OP_TYPE_UPLOAD:
            fullPath = os.path.join(file_path, file_name)
            fileSize = os.path.getsize(fullPath)
        else:
            fileSize = 0
        protocol = Handshake.start(self.host, self.port, file_name, fileSize, file_path, self.protocol_choice, self.op_type)
        self.set_protocol(protocol)

    def set_protocol(self, protocol):
        if protocol is None:
            raise NotImplementedError("Protocolo no implementado o invalido.")
        self.protocol = protocol

    def upload_file(self, src_filepath: str, name: str):
        if self.protocol == None:
            raise NotImplementedError("Debes iniciar el handshake primero")

        fullPath = os.path.join(src_filepath, name)
        fileSize = get_file(fullPath)
        chunkSize = self.protocol.get_chunk_size()
        
        for i in range(0, len(fileSize), chunkSize):
            chunk = fileSize[i:i+chunkSize]
            self.protocol.send_data_packet(chunk)
            
        self.protocol.end()

    def download_file(self, dst_path: str, name: str):
        if self.protocol is None:
            raise NotImplementedError("Debes iniciar el handshake primero")

        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
        
        fullPath = os.path.join(dst_path, name)

        try:
            # open file modo 'wb' (write binary)
            with open(fullPath, 'wb') as file:
                print(f"Descargando {name} en {dst_path}...")
                self.protocol.receive_file(file)
                
            print(f"Descarga de '{name}' finalizada con éxito!")
            
        except TimeoutError as e:
            print(f"TIMEOUT: {e}")
            
        except Exception as e:
            print(f"Error: {e}")
