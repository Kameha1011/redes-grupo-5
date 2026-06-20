# Import some POX stuff
from pox.core import core                       # Main POX object
import pox.openflow.libopenflow_01 as of        # OpenFlow 1.0 library
from pox.lib.addresses import EthAddr, IPAddr   # Address types
from pox.lib.packet.arp import arp
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.tcp import tcp
from pox.lib.packet.udp import udp

import time

log = core.getLogger()
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"


def log_color(color, msg):
    log.info(f"{color}{msg}{RESET}")


PRIVATE_SUBNET = IPAddr("192.168.1.0")      # Red interna
PRIVATE_MASK = 24                           # Máscara de la red interna
PRIVATE_IP = IPAddr("192.168.1.254")        # IP del router en la red privada
PUBLIC_IP = IPAddr("200.0.0.254")           # IP del router en la red pública
PUBLIC_MAC = EthAddr("00:00:00:aa:aa:aa")   # MAC del router hacia la red pública
PRIVATE_MAC = EthAddr("00:00:00:bb:bb:bb")  # MAC del router hacia la red privada
PUBLIC_PORT = 1                             # Puerto del switch conectado a la red pública

PAT_PORT_MIN = 1024
PAT_PORT_MAX = 65535 # Numero magico de Hamelin

class ArpHandler():
    def __init__(self):
        self.arp_table = {}
        self.waiting_queue = {}

    def enqueue_packet(self, ip_addr, event):
        if ip_addr not in self.waiting_queue:
            self.waiting_queue[ip_addr] = []
        self.waiting_queue[ip_addr].append(event)
        log_color(YELLOW, f"Paquete hacia {ip_addr} encolado (esperando ARP). Total encolados: {len(self.waiting_queue[ip_addr])}")

    def dequeue_packets(self, ip_addr):
        if ip_addr in self.waiting_queue:
            packets = self.waiting_queue.pop(ip_addr)
            log_color(GREEN, f"Desencolando {len(packets)} paquetes hacia {ip_addr}")
            return packets
        return []

    def _dump_arp_table(self):
        log_color(CYAN, "--- ARP TABLE ---")
        log_color(CYAN, "IP\t\tMAC\t\t\tPORT\tAGE")
        for ip, data in self.arp_table.items():
            age = time.time() - data["timestamp"]
            log_color(CYAN, f"{ip}\t{data['mac']}\t{data['port']}\t{age:.2f}s")
        log_color(CYAN, "-----------------")
    
    def learn_arp_entry(self, ip_addr, mac_addr, port):
        if ip_addr not in self.arp_table:
            log_color(GREEN, f"Entrada aprendida: {ip_addr} -> {mac_addr} en puerto {port}")
        else:
            log_color(GREEN, f"Entrada refrescada: {ip_addr} -> {mac_addr} en puerto {port}")
        self.arp_table[ip_addr] = {
            "mac": mac_addr,
            "port": port,
            "timestamp": time.time(),
        }
        self._dump_arp_table()

    def get_mac(self, ip_addr):
        if ip_addr in self.arp_table:
            return self.arp_table[ip_addr]["mac"]
        return None

    def get_port(self, ip_addr):
        if ip_addr in self.arp_table:
            return self.arp_table[ip_addr]["port"]
        return None
    
    def create_arp_reply(self, target_ip, target_mac, target_port, source_ip, source_mac):
        reply = arp()
        reply.hwtype = arp.HW_TYPE_ETHERNET
        reply.prototype = ethernet.IP_TYPE
        reply.hwlen = 6
        reply.protolen = 4
        reply.opcode = arp.REPLY
        reply.hwdst = target_mac
        reply.protodst = target_ip
        reply.hwsrc = source_mac
        reply.protosrc = source_ip

        ether = ethernet()
        ether.type = ethernet.ARP_TYPE
        ether.src = source_mac
        ether.dst = target_mac
        ether.payload = reply

        msg = of.ofp_packet_out()
        msg.data = ether.pack()
        msg.actions.append(of.ofp_action_output(port=target_port))

        return msg
    
    def create_arp_request(self, target_ip, out_port, source_ip, source_mac):
        request = arp()
        request.hwtype = arp.HW_TYPE_ETHERNET
        request.prototype = ethernet.IP_TYPE
        request.hwlen = 6
        request.protolen = 4
        request.opcode = arp.REQUEST
        request.hwdst = EthAddr("00:00:00:00:00:00")
        request.protodst = target_ip
        request.hwsrc = source_mac
        request.protosrc = source_ip

        ether = ethernet()
        ether.type = ethernet.ARP_TYPE
        ether.src = source_mac
        ether.dst = EthAddr("ff:ff:ff:ff:ff:ff")
        ether.payload = request

        msg = of.ofp_packet_out()
        msg.data = ether.pack()
        msg.actions.append(of.ofp_action_output(port=out_port))

        return msg
        
class NatHandler():
    def __init__(self):
        self.nat_table = {}
        self.reverse_nat = {}
        self.public_port_pool = set(range(PAT_PORT_MIN, PAT_PORT_MAX + 1))

    def allocate_public_port(self):
        if not self.public_port_pool:
            return None

        public_port = min(self.public_port_pool)
        self.public_port_pool.remove(public_port)
        return public_port

    def release_public_port(self, public_port):
        if PAT_PORT_MIN <= public_port <= PAT_PORT_MAX:
            self.public_port_pool.add(public_port)

    def _dump_nat_table(self):
        log_color(CYAN, "--- NAT TABLE ---")
        log_color(CYAN, "PROTO\tPRIVATE\t\tPUBLIC\t\t\tAGE")
        for nat_key, data in self.nat_table.items():
            protocol, private_ip, private_port = nat_key
            public_ip = data["public_ip"]
            public_port = data["public_port"]
            age = time.time() - data["timestamp"]
            log_color(CYAN, f"{protocol}\t{private_ip}:{private_port}\t\t{public_ip}:{public_port}\t\t{age:.2f}s")
        log_color(CYAN, "-----------------")

    def create_pat_entry(self, protocol, private_ip, private_port, public_ip):
        nat_key = (protocol, private_ip, private_port)

        if nat_key in self.nat_table:
            return self.nat_table[nat_key]

        public_port = self.allocate_public_port()

        if public_port is None:
            log_color(RED, "No hay puertos PAT disponibles")
            return None
        
        reverse_nat_key = (protocol, public_ip, public_port)
        nat_timestamp = time.time()

        nat_entry = {
            "public_ip": public_ip,
            "public_port": public_port,
            "timestamp": nat_timestamp,
        }
        self.nat_table[nat_key] = nat_entry
        
        self.reverse_nat[reverse_nat_key] = {
            "private_ip": private_ip,
            "private_port": private_port,
            "timestamp": nat_timestamp,
        }

        # log_color(GREEN, "NAT CREATED")
        # log_color(GREEN, f"PROTO: {protocol}")
        # log_color(GREEN, f"PRIVATE: {private_ip}:{private_port}")
        # log_color(GREEN, f"PUBLIC: {public_ip}:{public_port}")
        
        self._dump_nat_table()

        return nat_entry

    def get_reverse_entry(self, protocol, public_ip, public_port):
        reverse_key = (protocol, public_ip, public_port)
        if reverse_key in self.reverse_nat:
            return self.reverse_nat[reverse_key]
        return None

class ProtoRouter(object):
    def __init__(self, connection):
        self.connection = connection
        self.arp_handler = ArpHandler()
        self.nat_handler = NatHandler()
        connection.addListeners(self)

    def _handle_PacketIn(self, event):
        if not event.parsed.parsed:
            log.warning("[DROP] PacketIn con trama no reconocida. POX no pudo decodificar el paquete.")
            return

        if event.parsed.type == ethernet.ARP_TYPE:
            self.handle_arp(event)
        elif event.parsed.type == ethernet.IP_TYPE:
            self.handle_ip(event)
        else:
            log_color(YELLOW, f"Paquete ignorado: protocolo distinto de IPv4.")

    def _get_transport_fields(self, ip_pkt):
        transport = ip_pkt.next

        if isinstance(transport, tcp):
            return "TCP", transport.srcport, transport.dstport

        if isinstance(transport, udp):
            return "UDP", transport.srcport, transport.dstport

        return None, None, None

    def _send_arp_reply(self, target_ip, target_mac, target_port, source_ip, source_mac):
        msg = self.arp_handler.create_arp_reply(target_ip, target_mac, target_port, source_ip, source_mac)
        log_color(CYAN, f"ARP Reply generado por el controlador: {source_ip} is-at {source_mac} -> {target_ip}")
        self.connection.send(msg)

    def _send_arp_request(self, target_ip, out_port, source_ip, source_mac):
        msg = self.arp_handler.create_arp_request(target_ip, out_port, source_ip, source_mac)
        log_color(CYAN, f"ARP Request generado por el controlador: {source_ip} ({source_mac}) pregunta por {target_ip}")
        self.connection.send(msg)

    def handle_arp(self, event):
        packet = event.parsed
        arp_pkt = packet.payload
        in_port = event.port

        if arp_pkt is None:
            log.warning("[DROP] Trama ARP sin payload válido.")
            return

        sender_ip = arp_pkt.protosrc
        sender_mac = arp_pkt.hwsrc
        target_ip = arp_pkt.protodst

        if arp_pkt.opcode == arp.REQUEST:
            log_color(YELLOW, f"ARP Request recibido: {sender_ip} ({sender_mac}) -> {target_ip}")
        elif arp_pkt.opcode == arp.REPLY:
            log_color(YELLOW, f"ARP Reply recibido: {sender_ip} ({sender_mac}) -> {target_ip}")
        else:
            log_color(YELLOW, f"ARP recibido con opcode no soportado: {arp_pkt.opcode}")

        self.arp_handler.learn_arp_entry(sender_ip, sender_mac, in_port)

        # Desencolar y procesar paquetes que estaban esperando esta MAC
        events_to_resume = self.arp_handler.dequeue_packets(sender_ip)
        for ev in events_to_resume:
            self._handle_PacketIn(ev)

        if arp_pkt.opcode != arp.REQUEST:
            return

        if target_ip == PUBLIC_IP:
            source_ip = PUBLIC_IP
            source_mac = PUBLIC_MAC
        elif target_ip == PRIVATE_IP:
            source_ip = PRIVATE_IP
            source_mac = PRIVATE_MAC
        else:
            # Si alguien pregunta por una IP que no es nuestra, ignoramos el paquete.
            # (El switch se encargará de forwardearlo si es tráfico L2 normal, o lo ignoramos)
            return
            
        self._send_arp_reply(
            target_ip=sender_ip,
            target_mac=sender_mac,
            target_port=in_port,
            source_ip=source_ip,
            source_mac=source_mac, # Acá es donde el switch/router comparte su MAC address (ya sea de su interfaz pública o privada)
        )

    def handle_ip(self, event):
        packet = event.parsed
        ip_pkt = packet.payload
        in_port = event.port

        log_color(
            YELLOW, f"RECIBIDO: {ip_pkt.srcip} → {ip_pkt.dstip} | "
            f"MAC: {packet.src} → {packet.dst} | In Port: {in_port}")

        protocol, src_port, dst_port = self._get_transport_fields(ip_pkt)

        if ip_pkt.srcip.inNetwork(PRIVATE_SUBNET, PRIVATE_MASK):

            log_color(GREEN, f"MATCH: {ip_pkt.srcip} pertenece a la red privada {PRIVATE_SUBNET}/{PRIVATE_MASK}")

            target_mac = self.arp_handler.get_mac(ip_pkt.dstip)
            if not target_mac:
                self.arp_handler.enqueue_packet(ip_pkt.dstip, event)
                self._send_arp_request(target_ip=ip_pkt.dstip, out_port=PUBLIC_PORT, source_ip=PUBLIC_IP, source_mac=PUBLIC_MAC)
                return

            if protocol not in ("TCP", "UDP"):
                log_color(RED, "Tráfico saliente descartado (No es TCP ni UDP)")
                return

            pat_entry = self.nat_handler.create_pat_entry(
                protocol=protocol,
                private_ip=ip_pkt.srcip,
                private_port=src_port,
                public_ip=PUBLIC_IP,
            )

            if not pat_entry:
                log_color(RED, "[DROP] No se pudo crear entrada PAT")
                return

            public_port = pat_entry["public_port"]

            # Instalar Flujo Saliente
            fm = of.ofp_flow_mod()
            fm.idle_timeout = 10

            # Filtro (Saliente)
            fm.match.nw_src = ip_pkt.srcip
            fm.match.nw_dst = ip_pkt.dstip
            fm.match.dl_type = 0x800  # IPv4
            fm.match.nw_proto = ip_pkt.protocol
            fm.match.tp_src = src_port
            fm.match.tp_dst = dst_port
            fm.match.in_port = in_port

            # Acción (Saliente)
            fm.actions.append(of.ofp_action_nw_addr.set_src(PUBLIC_IP))
            fm.actions.append(of.ofp_action_tp_port.set_src(public_port))
            fm.actions.append(of.ofp_action_dl_addr.set_src(PUBLIC_MAC))
            fm.actions.append(of.ofp_action_dl_addr.set_dst(target_mac))
            fm.actions.append(of.ofp_action_output(port=PUBLIC_PORT))
            self.connection.send(fm)

            # Instalar Flujo Entrante (para respuesta)
            fm_back = of.ofp_flow_mod()
            fm_back.idle_timeout = 10

            # Filtro (Entrante)
            fm_back.match.nw_src = ip_pkt.dstip
            fm_back.match.nw_dst = PUBLIC_IP
            fm_back.match.dl_type = 0x800  # IPv4
            fm_back.match.nw_proto = ip_pkt.protocol
            fm_back.match.tp_src = dst_port
            fm_back.match.tp_dst = public_port
            fm_back.match.in_port = PUBLIC_PORT

            # Acción (Entrante)
            fm_back.actions.append(of.ofp_action_nw_addr.set_dst(ip_pkt.srcip))
            fm_back.actions.append(of.ofp_action_tp_port.set_dst(src_port))
            fm_back.actions.append(of.ofp_action_dl_addr.set_src(PRIVATE_MAC))
            fm_back.actions.append(of.ofp_action_dl_addr.set_dst(packet.src))
            fm_back.actions.append(of.ofp_action_output(port=in_port))
            self.connection.send(fm_back)

            # Reenviar paquete actual modificado
            ip_pkt.srcip = PUBLIC_IP
            if protocol == "TCP":
                ip_pkt.next.srcport = public_port
            elif protocol == "UDP":
                ip_pkt.next.srcport = public_port
            
            # Borrar checksums para que POX los recalcule
            ip_pkt.csum = None
            ip_pkt.next.csum = None

            packet.src = PUBLIC_MAC
            packet.dst = target_mac

            msg = of.ofp_packet_out()
            msg.data = packet.pack()
            msg.actions.append(of.ofp_action_output(port=PUBLIC_PORT))
            log_color(CYAN, f"NAT OUT: {ip_pkt.srcip}:{public_port} → {ip_pkt.dstip}:{dst_port} | Out: {PUBLIC_PORT}")
            self.connection.send(msg)

        else: # IP fuente viene de 200.0.0.0/24
            log_color(GREEN, f"Tráfico entrante: {ip_pkt.srcip} -> {ip_pkt.dstip}")

            if protocol not in ("TCP", "UDP"):
                log_color(RED, "Tráfico entrante descartado (No es TCP ni UDP)")
                return

            if ip_pkt.dstip != PUBLIC_IP:
                log_color(RED, f"Tráfico entrante descartado (Destino no es la IP pública {PUBLIC_IP})")
                return

            reverse_entry = self.nat_handler.get_reverse_entry(protocol, ip_pkt.dstip, dst_port)
            if not reverse_entry:
                log_color(RED, f"[DROP] No hay conexión PAT activa para {protocol} puerto {dst_port}")
                return

            private_ip = reverse_entry["private_ip"]
            private_port = reverse_entry["private_port"]

            target_mac = self.arp_handler.get_mac(private_ip)
            target_port = self.arp_handler.get_port(private_ip)

            if not target_mac or not target_port:
                self.arp_handler.enqueue_packet(private_ip, event)
                self._send_arp_request(target_ip=private_ip, out_port=of.OFPP_FLOOD, source_ip=PRIVATE_IP, source_mac=PRIVATE_MAC)
                return

            # Instalar Flujo Entrante (Público -> Privado)
            fm = of.ofp_flow_mod()
            fm.idle_timeout = 10

            # Filtro (Entrante)
            fm.match.nw_src = ip_pkt.srcip
            fm.match.nw_dst = PUBLIC_IP
            fm.match.dl_type = 0x800  # IPv4
            fm.match.nw_proto = ip_pkt.protocol
            fm.match.tp_src = src_port
            fm.match.tp_dst = dst_port
            fm.match.in_port = in_port

            # Acción (Entrante)
            fm.actions.append(of.ofp_action_nw_addr.set_dst(private_ip))
            fm.actions.append(of.ofp_action_tp_port.set_dst(private_port))
            fm.actions.append(of.ofp_action_dl_addr.set_src(PRIVATE_MAC))
            fm.actions.append(of.ofp_action_dl_addr.set_dst(target_mac))
            fm.actions.append(of.ofp_action_output(port=target_port))
            self.connection.send(fm)

            # Instalar Flujo Saliente (Privado -> Público) para la respuesta
            fm_back = of.ofp_flow_mod()
            fm_back.idle_timeout = 10

            # Filtro (Saliente)
            fm_back.match.nw_src = private_ip
            fm_back.match.nw_dst = ip_pkt.srcip
            fm_back.match.dl_type = 0x800  # IPv4
            fm_back.match.nw_proto = ip_pkt.protocol
            fm_back.match.tp_src = private_port
            fm_back.match.tp_dst = src_port
            fm_back.match.in_port = target_port

            # Acción (Saliente)
            fm_back.actions.append(of.ofp_action_nw_addr.set_src(PUBLIC_IP))
            fm_back.actions.append(of.ofp_action_tp_port.set_src(dst_port))
            fm_back.actions.append(of.ofp_action_dl_addr.set_src(PUBLIC_MAC))
            fm_back.actions.append(of.ofp_action_dl_addr.set_dst(packet.src))
            fm_back.actions.append(of.ofp_action_output(port=in_port))
            self.connection.send(fm_back)

            # Reenviar paquete actual modificado
            ip_pkt.dstip = private_ip
            if protocol == "TCP":
                ip_pkt.next.dstport = private_port
            elif protocol == "UDP":
                ip_pkt.next.dstport = private_port

            ip_pkt.csum = None
            ip_pkt.next.csum = None

            packet.src = PRIVATE_MAC
            packet.dst = target_mac
            
            msg = of.ofp_packet_out()
            msg.data = packet.pack()
            msg.actions.append(of.ofp_action_output(port=target_port))
            log_color(CYAN, f"NAT IN: {ip_pkt.srcip}:{src_port} → {private_ip}:{private_port} | Out: {target_port}")
            self.connection.send(msg)


def launch():

    def start_switch(event):
        log_color(YELLOW, f"Iniciando ProtoRouter para Switch {event.connection.dpid}")
        ProtoRouter(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
