# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# sender.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""UDP/TCP sender for GPS data."""

import json
import socket
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class NetworkSender:
    """Sends GPS data packets via UDP or TCP."""

    def __init__(self, target_ip: str, port: int = 12000, protocol: str = "udp"):
        self.target_ip = target_ip
        self.port = port
        self.protocol = protocol.lower()
        self._tcp_socket: Optional[socket.socket] = None

    def create_packet(
        self,
        lat: float,
        lon: float,
        alt_ft: float,
        speed_kts: float,
        heading: float,
        timestamp: Optional[datetime] = None,
    ) -> str:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        data = {
            "lat": lat,
            "lon": lon,
            "alt_ft": alt_ft,
            "speed_kts": speed_kts,
            "heading": heading,
            "timestamp": timestamp.isoformat(),
        }
        return json.dumps(data)

    def send(self, packet: str) -> bool:
        try:
            if self.protocol == "udp":
                return self._send_udp(packet)
            else:
                return self._send_tcp(packet)
        except Exception as e:
            logger.error(f"Failed to send packet: {e}")
            return False

    def _send_udp(self, packet: str) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(packet.encode(), (self.target_ip, self.port))
        logger.debug(f"Sent UDP packet to {self.target_ip}:{self.port}")
        return True

    def _send_tcp(self, packet: str) -> bool:
        if self._tcp_socket is None:
            self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_socket.connect((self.target_ip, self.port))
            logger.info(f"TCP connected to {self.target_ip}:{self.port}")

        self._tcp_socket.send(packet.encode() + b"\n")
        logger.debug(f"Sent TCP packet to {self.target_ip}:{self.port}")
        return True

    def close(self) -> None:
        if self._tcp_socket:
            self._tcp_socket.close()
            self._tcp_socket = None
            logger.info("TCP connection closed")
