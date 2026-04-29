import os
from socket import *
from ..constants import *
from lib.common.file_handling import save_file
from lib.protocol.packet import Packet
from lib.protocol.handshake import Handshake
from lib.protocol.factory import create_protocol

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
            self.handle_client(data, addr)

    def handle_handshake(self, packet: Packet, address: str):
            print(f"Handshake recibido SYN de {address}")
            decodedData = packet.data.decode().split('\0')
            filename = decodedData[0]
            filesize = int(decodedData[1])
            
            print(f"Cliente solicita subir: {filename} ({filesize} bytes)")

            if filesize > MAX_FILE_SIZE:
                raise BufferError(f"Solicitud rechazada para el cliente {address}: el archivo supera el limite: ({filesize} bytes)")
            
            self.filenames[address] = filename
            self.protocols[address] = create_protocol(packet.protocol, packet.op_type, self.socket)
            self.buffers[address] = bytes()

    def handle_client(self, data: bytes, addr):
        try:
            pkt = Packet.from_bytes(data)
        except Exception as e:
            print(f"Error parseando paquete de {addr}: {e}")
            return

        if pkt.pkt_type == TYPE_SYN:
            self.handle_handshake(pkt, addr)
            Handshake.ack(self.socket, pkt, addr)

        elif pkt.pkt_type == TYPE_DATA:
            if addr not in self.buffers:
                self.buffers[addr] = bytes()
                print(f"Iniciando recepción de {addr}")

            protocol = self.protocols.get(addr)
            if not protocol:
                print(f"Paquete {pkt.seq_num} ignorado (sin protocolo asociado).")
                return

            payloads = protocol.receive_data_packet(pkt, addr)
            for payload in payloads:
                self.buffers[addr] += payload
            if payloads:
                print(f"Paquete {pkt.seq_num} recibido {len(pkt.data)} bytes. Siguiente esperado: {protocol.next_expected}")
            else:
                print(f"Paquete {pkt.seq_num} ignorado (duplicado o fuera de orden).")

        elif pkt.pkt_type == TYPE_CLOSE:
            filename = self.filenames.get(addr)
            print(f"Transferencia finalizada paquete {addr} via TYPE_CLOSE para el archivo: {filename}")
            protocol = self.protocols.get(addr)
            if protocol:
                protocol.handle_close(pkt, addr)
            save_file(self.storage_path, filename, self.buffers[addr])
            del self.buffers[addr]
            del self.protocols[addr]
            del self.filenames[addr]
