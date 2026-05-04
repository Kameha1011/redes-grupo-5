import os
from socket import *
from ..common.constants import *
from lib.common.file_handling import save_file
from lib.common.handshake import Handshake
from lib.common.factory import create_protocol
from lib.common.packet import Packet
import threading
import queue

class Server:

    def __init__(self, storage_path: str, host: str, port: int):
        self.init_storage_dir(storage_path)
        self.storage_path = storage_path
        self.host = host
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((host, port))

        # multithreading
        self.clientDataQueues = {}
        self.clientDataQueueLock = threading.Lock() # Lock para clientDataQueues
        self.socketLock = threading.Lock() # Lock para socket
        
        print(f"Socket listening on {host}:{port}")

    def init_storage_dir(self, storage_path: str):
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def start(self):
        while True:
            try:
                self.socket.settimeout(1.0)
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                
                with self.clientDataQueueLock:
                    if addr not in self.clientDataQueues:
                        clientDataQueue = queue.Queue()
                        self.clientDataQueues[addr] = clientDataQueue
                        
                        thread = threading.Thread(target=self.handle_client, args=(addr, clientDataQueue))
                        thread.daemon = True
                        thread.start()
                
                # agregar al cliente a la cola

                self.clientDataQueues[addr].put(data)
                
            except timeout:
                continue
            except Exception as e:
                print(f"[MAIN ERROR] {e}")

    def handle_client(self, addr, clientDataQueue):
        buffer = bytes()
        protocol = None
        filename = None

        while True:
            try:
                # obtiene el data del client encolado con un timeout para no dejar threads zombies
                data = clientDataQueue.get(timeout=60)
                pkt = Packet.from_bytes(data)
                
                if pkt.pkt_type == TYPE_SYN:
                    try:
                        protocol, filename = self.handle_handshake(pkt, addr) 
                        Handshake.ack(self.socket, pkt, addr, self.socketLock)
                        
                        if pkt.op_type == OP_TYPE_DOWNLOAD:
                            print(f"Iniciando envío de archivo a {addr}...")
                            self.start_download_transfer(protocol, filename, addr, clientDataQueue)
                            # cuando termina la transferencia podemos cerrar este hilo
                            break 
                            
                    except Exception as e:
                        print(f"[!] Error de Handshake con {addr}: {e}")
                        break
                
                elif pkt.pkt_type == TYPE_DATA:
                    if not protocol:
                        print(f"Paquete {pkt.seq_num} ignorado (sin protocolo asociado).")
                        continue
                    
                    payloads = protocol.receive_data_packet(pkt, addr)
                    for payload in payloads:
                        buffer += payload
                    if payloads:
                        print(f"Paquete de {addr} seq_num: {pkt.seq_num} recibido {len(pkt.data)} bytes. Siguiente esperado: {protocol.next_expected}")
                    else:
                        print(f"Paquete de {addr} seq_num: {pkt.seq_num} ignorado (duplicado o fuera de orden).")
                
                elif pkt.pkt_type == TYPE_CLOSE:
                    if protocol:
                        protocol.handle_close(pkt, addr)
                    
                    if buffer:
                        save_file(self.storage_path, filename, buffer)
                    
                    print(f"Transferencia finalizada paquete {addr} via TYPE_CLOSE para el archivo: {filename}")
                    break

            except queue.Empty:
                print(f"[-] Timeout: Cerrando thread cliente {addr} por inactividad")
                break
            except Exception as e:
                print(f"Error thread con cliente {addr}: {e}")
                break
        
        # sacar al cliente de la cola
        with self.clientDataQueueLock:
            if addr in self.clientDataQueues:
                del self.clientDataQueues[addr]

    def handle_handshake(self, packet: Packet, address: str):
        print(f"Handshake recibido SYN de {address}")
        decodedData = packet.data.decode().split('\0')
        filename = decodedData[0]

        if packet.op_type == OP_TYPE_DOWNLOAD:
            print(f"Cliente solicita descargar: {filename}")
            fullPath = os.path.join(self.storage_path, filename)
            if not os.path.exists(fullPath):
                raise FileNotFoundError(f"El archivo {filename} no existe")
        else:
            filesize = int(decodedData[1])
            print(f"Cliente solicita subir: {filename} ({filesize} bytes)")
            if filesize > MAX_FILE_SIZE:
                raise BufferError(f"Solicitud rechazada para el cliente {address}: el archivo supera el limite: ({filesize} bytes)")
        
        protocol = create_protocol(packet.protocol, packet.op_type, self.socket, self.socketLock)

        return protocol, filename
    
    def start_download_transfer(self, protocol, filename, addr, clientDataQueue):
        fullPath = os.path.join(self.storage_path, filename)
        
        if not os.path.exists(fullPath):
            print(f"Archivo {filename} no encontrado en storage.")
            return

        with open(fullPath, 'rb') as f:
            while True:
                chunk = f.read(protocol.chunk_size)
                if not chunk:
                    break
                
                protocol.send_data_packet(chunk, addr, clientDataQueue)

        protocol.end(addr, clientDataQueue)
        print(f"Envío de {filename} a {addr} finalizado con éxito.")
