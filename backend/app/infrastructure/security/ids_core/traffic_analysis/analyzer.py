from scapy.all import IP, TCP
from collections import defaultdict, deque
import time

class TrafficAnalyzer:
    def __init__(self, window_seconds: float = 10.0):
        # Per-flow stats: (src,dst,sp,dp) -> stats
        self.flow_stats = defaultdict(lambda: {
            'packet_count': 0,
            'byte_count': 0,
            'start_time': None,
            'last_time': None
        })

        # Recent activity windows for higher-level features
        # src_ip -> deque of (timestamp, dst_port)
        self.src_ports = defaultdict(deque)
        # dst_ip -> deque of timestamps for SYN packets
        self.dst_syns = defaultdict(deque)

        self.window = float(window_seconds)

    def _purge_old(self, dq: deque, now: float):
        # remove entries older than window seconds
        cutoff = now - self.window
        while dq and dq[0][0] < cutoff:
            dq.popleft()

    def analyze_packet(self, packet):
        if IP in packet and TCP in packet:
            ip_src = packet[IP].src
            ip_dst = packet[IP].dst
            port_src = packet[TCP].sport
            port_dst = packet[TCP].dport

            flow_key = (ip_src, ip_dst, port_src, port_dst)

            # Update flow statistics
            stats = self.flow_stats[flow_key]
            stats['packet_count'] += 1
            stats['byte_count'] += len(packet)
            current_time = getattr(packet, 'time', None) or time.time()

            if not stats['start_time']:
                stats['start_time'] = current_time
            stats['last_time'] = current_time

            # Update source port history (for port-scan detection)
            self.src_ports[ip_src].append((current_time, port_dst))
            # Purge old entries
            # entries are (timestamp, port)
            while self.src_ports[ip_src] and self.src_ports[ip_src][0][0] < current_time - self.window:
                self.src_ports[ip_src].popleft()

            # Update destination SYN history (for SYN flood detection)
            flags = packet[TCP].flags
            # Scapy represents flags as string sometimes; check for 'S' or numeric
            is_syn = (str(flags) == 'S') or (int(flags) & 0x02 == 0x02)
            if is_syn:
                self.dst_syns[ip_dst].append(current_time)
                while self.dst_syns[ip_dst] and self.dst_syns[ip_dst][0] < current_time - self.window:
                    self.dst_syns[ip_dst].popleft()

            return self.extract_features(packet, stats, ip_src, ip_dst)
        return None

    def extract_features(self, packet, stats, ip_src, ip_dst):
        now = getattr(packet, 'time', None) or time.time()

        # Flow duration
        duration = 0.0
        if stats['start_time'] is not None and stats['last_time'] is not None:
            duration = stats['last_time'] - stats['start_time']

        # Window-based packet/byte rates (use counts within window)
        # Count packets in flow within window: we don't store per-packet timestamps per-flow,
        # approximate by using flow packet_count and duration when possible; fallback to 0.
        if duration and duration > 0:
            packet_rate = stats['packet_count'] / max(duration, 1e-6)
            byte_rate = stats['byte_count'] / max(duration, 1e-6)
        else:
            # Use window-based approximations: count recent src_ports entries for this src
            recent_ports = [p for t, p in self.src_ports[ip_src] if t >= now - self.window]
            packet_rate = len(recent_ports) / max(self.window, 1e-6)
            # approximate byte rate with average packet size assumption
            byte_rate = stats['byte_count'] / max(self.window, 1e-6)

        tcp_flags = packet[TCP].flags if TCP in packet else None
        window_size = packet[TCP].window if TCP in packet else None

        # High-level features
        unique_dst_ports = len({p for t, p in self.src_ports[ip_src] if t >= now - self.window})
        dest_syn_count = len([t for t in self.dst_syns[ip_dst] if t >= now - self.window])

        return {
            'packet_size': len(packet),
            'flow_duration': duration,
            'packet_rate': float(packet_rate),
            'byte_rate': float(byte_rate),
            'tcp_flags': str(tcp_flags),
            'window_size': window_size,
            'unique_dst_ports': unique_dst_ports,
            'dest_syn_count': dest_syn_count
        }
