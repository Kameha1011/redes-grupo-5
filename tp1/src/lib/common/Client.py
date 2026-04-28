from lib.common.file_handling import get_file
from ..protocol.protocol import Protocol
from ..constants import *
import os

class Client:
    def __init__(self, protocol: Protocol):
        self.protocol = protocol

    def upload_file(self, src_filepath: str, name: str):
        self.protocol.start(src_filepath, name)

        fullPath = os.path.join(src_filepath, name)
        filebytes = get_file(fullPath)
        chunkSize = self.protocol.get_chunk_size()
        
        for i in range(0, len(filebytes), chunkSize):
            chunk = filebytes[i:i+chunkSize]
            self.protocol.send_data_packet(chunk)
            
        self.protocol.end()


    def download_file(self, dst_path: str, name: str):
        pass

