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

H1_MAC = EthAddr("00:00:00:00:00:01")       # MAC del host externo (TODO: resolver mediante ARP)
PAT_PORT_MIN = 1024
PAT_PORT_MAX = 65535 # Numero magico de Hamelin

class ArpHandler():
    
    def __init__(self):
        self.arp_table = {}

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

    def create_pat_entry(self, protocol, private_ip, private_port, public_ip, destination_ip):
        nat_key = (protocol, private_ip, private_port)

        if nat_key in self.nat_table:
            return self.nat_table[nat_key]

        public_port = self.allocate_public_port()

        if public_port is None:
            log_color(RED, "No hay puertos PAT disponibles")
            return
        
        entry = {
            "public_ip": public_ip,
            "public_port": public_port,
            "private_ip": private_ip,
            "private_port": private_port,
            "timestamp": time.time(),
            "destination_ip": destination_ip,
        }
        self.nat_table[nat_key] = entry
        self.reverse_nat[(protocol, public_port)] = entry
        log_color(GREEN, "NAT CREATED")
        log_color(GREEN, f"PROTO: {protocol}")
        log_color(GREEN, f"PRIVATE: {private_ip}:{private_port}")
        log_color(GREEN, f"PUBLIC PORT: {public_port}")
        log_color(GREEN, f"DESTINATION: {destination_ip}")

        return entry

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

        if arp_pkt.opcode != arp.REQUEST:
            return

        source_ip = PRIVATE_IP
        source_mac = PRIVATE_MAC
        if target_ip == PUBLIC_IP:
            source_ip = PUBLIC_IP
            source_mac = PUBLIC_MAC
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

        if (
            protocol in ("TCP", "UDP")
            and ip_pkt.srcip.inNetwork(PRIVATE_SUBNET, PRIVATE_MASK)
            and not ip_pkt.dstip.inNetwork(PRIVATE_SUBNET, PRIVATE_MASK)
        ):
            pat_entry = self.nat_handler.create_pat_entry(protocol=protocol,
                private_ip=ip_pkt.srcip,
                private_port=src_port,
                public_ip=PUBLIC_IP,
                destination_ip=ip_pkt.dstip,)
            
            if not self.arp_handler.get_mac(packet.dst):
                self._send_arp_request(ip_pkt.dstip, PUBLIC_PORT, PUBLIC_IP, PUBLIC_MAC)
            return

        if ip_pkt.srcip.inNetwork(PRIVATE_SUBNET, PRIVATE_MASK):

            log_color(GREEN, f"MATCH: {ip_pkt.srcip} pertenece a la red privada {PRIVATE_SUBNET}/{PRIVATE_MASK}")

            # Instalar Flujo Saliente
            fm = of.ofp_flow_mod()
            fm.idle_timeout = 10

            # Filtro (Saliente)
            fm.match.nw_src = ip_pkt.srcip
            fm.match.dl_type = 0x800  # IPv4
            fm.match.in_port = in_port

            # Acción (Saliente)
            fm.actions.append(of.ofp_action_dl_addr.set_src(PUBLIC_MAC))
            fm.actions.append(of.ofp_action_dl_addr.set_dst(H1_MAC))
            fm.actions.append(of.ofp_action_output(port=PUBLIC_PORT))
            self.connection.send(fm)

            # Instalar Flujo Entrante (para respuesta)
            fm_back = of.ofp_flow_mod()
            fm_back.idle_timeout = 10

            # Filtro (Entrante)
            fm_back.match.nw_src = ip_pkt.dstip
            fm_back.match.nw_dst = ip_pkt.srcip
            fm_back.match.dl_type = 0x800  # IPv4
            fm_back.match.in_port = PUBLIC_PORT

            # Acción (Entrante)
            fm_back.actions.append(of.ofp_action_dl_addr.set_src(PRIVATE_MAC))
            fm_back.actions.append(of.ofp_action_dl_addr.set_dst(packet.src))
            fm_back.actions.append(of.ofp_action_output(port=in_port))
            self.connection.send(fm_back)

            # Reenviar paquete actual con MACs actualizadas (Los posteriores pasan por flujo)
            packet.src = PUBLIC_MAC
            packet.dst = H1_MAC
            msg = of.ofp_packet_out()
            msg.data = packet.pack()
            msg.actions.append(of.ofp_action_output(port=PUBLIC_PORT))
            log_color(CYAN, f"ENVIANDO: {ip_pkt.srcip} → {ip_pkt.dstip} | MAC: {PUBLIC_MAC} → {H1_MAC} | Out Port: {PUBLIC_PORT}")
            self.connection.send(msg)

        else:
            log_color(RED, f"NO MATCH: {ip_pkt.srcip} no pertenece a {PRIVATE_SUBNET}/{PRIVATE_MASK}")


def launch():

    def start_switch(event):
        log_color(YELLOW, f"Iniciando ProtoRouter para Switch {event.connection.dpid}")
        ProtoRouter(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
