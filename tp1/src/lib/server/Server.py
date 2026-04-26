import os
from socket import *
from ..constants import *
from lib.common.file_handling import save_file
# import threading
from lib.protocol.protocol import Protocol
from lib.protocol.packet import Packet

class Server:

    def __init__(self, storage_path: str, host: str, port: int):
        Server.init_storage_dir(storage_path)
        self.storage_path = storage_path
        self.host = host
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((host, port))

        self.buffers = {} # Experimental
        self.protocols = {}
        self.filenames = {}
        
        print(f"Socket listening on {host}:{port}")


    def init_storage_dir(storage_path: str):
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def start(self):
        
        while True:
            data, addr = self.socket.recvfrom(BUFFER_SIZE)
            # t = threading.Thread(target=self.handle_client, args=(data,addr))
            # t.start()
            self.handle_client(data, addr)
    
    def _sendSYNACK(self, pkt, addr):
        protocol = self.protocols.get(addr)
        if protocol:
            ack = protocol.syn_ack(pkt.seq_num)
            self.socket.sendto(ack.to_bytes(), addr)

    def _sendACK(self, pkt, addr):
        protocol = self.protocols.get(addr)
        if protocol:
            ack = protocol.ack(pkt.seq_num)
            self.socket.sendto(ack.to_bytes(), addr)

    def handle_client(self, data: bytes, addr):
        try:
            pkt = Packet.from_bytes(data)
        except Exception as e:
            print(f"Error parseando paquete de {addr}: {e}")
            return

        if pkt.pkt_type == TYPE_SYN:
            print(f"Handshake recibido SYN de {addr}")

            try:
                decodedData = pkt.data.decode().split('\0')
                filename = decodedData[0]
                filesize = int(decodedData[1])
                
                print(f"Cliente solicita subir: {filename} ({filesize} bytes)")

                if filesize > MAX_FILE_SIZE:
                    print(f"Solicitud rechazada para el cliente {addr}: el archivo supera el limite: ({filesize} bytes)")
                    return
                
                self.filenames[addr] = filename
            except Exception as e:
                print(f"Error al procesar data del SYN: {e}")
                return

            self.protocols[addr] = Protocol(pkt.op_type, pkt.protocol)
            self.protocols[addr].next_expected = 1
            self.buffers[addr] = bytes()
            self._sendSYNACK(pkt, addr)

        elif pkt.pkt_type == TYPE_DATA:
            if addr not in self.buffers:
                self.buffers[addr] = bytes()
                print(f"Iniciando recepción de {addr}")

            protocol = self.protocols.get(addr)
            if protocol and pkt.seq_num == protocol.next_expected:
                self.buffers[addr] += pkt.data
                protocol.next_expected += 1
                print(f"Paquete {pkt.seq_num} recibido {len(pkt.data)} bytes. Siguiente esperado: {protocol.next_expected}")
            else:
                print(f"Paquete {pkt.seq_num} ignorado (duplicado o fuera de orden).")

            self._sendACK(pkt, addr)

        elif pkt.pkt_type == TYPE_CLOSE:
            filename = self.filenames.get(addr)
            print(f"Transferencia finalizada paquete {addr} via TYPE_CLOSE para el archivo: {filename}")
            save_file(self.storage_path, filename, self.buffers[addr])
            del self.buffers[addr]
            del self.protocols[addr]
            del self.filenames[addr]
            self._sendACK(pkt, addr)
