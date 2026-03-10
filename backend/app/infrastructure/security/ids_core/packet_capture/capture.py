from scapy.all import sniff, IP, TCP
import threading
import queue
from typing import Optional, Callable

class PacketCapture:
    """Simple packet capture wrapper using scapy.

    - Put TCP/IP packets into an internal queue.
    - Optionally call a user-provided packet_handler for each packet.
    """
    def __init__(self, packet_handler: Optional[Callable] = None):
        self.packet_queue: "queue.Queue" = queue.Queue()
        self.stop_capture = threading.Event()
        self.packet_handler = packet_handler
        self.capture_thread: Optional[threading.Thread] = None

    def packet_callback(self, packet):
        if IP in packet and TCP in packet:
            self.packet_queue.put(packet)
            if self.packet_handler:
                try:
                    self.packet_handler(packet)
                except Exception:
                    # Ignore handler errors to keep capture running
                    pass

    def start_capture(self, interface: Optional[str] = None):
        """Start background thread capturing on `interface`.

        If `interface` is None, scapy/snip will pick the default.
        """
        def capture_thread():
            sniff(iface=interface,
                  prn=self.packet_callback,
                  store=0,
                  stop_filter=lambda _: self.stop_capture.is_set())

        self.stop_capture.clear()
        self.capture_thread = threading.Thread(target=capture_thread, daemon=True)
        self.capture_thread.start()

    def stop(self, timeout: Optional[float] = 5.0):
        self.stop_capture.set()
        if self.capture_thread:
            self.capture_thread.join(timeout=timeout)

    def get_packet(self, timeout: Optional[float] = None):
        try:
            return self.packet_queue.get(timeout=timeout)
        except queue.Empty:
            return None
