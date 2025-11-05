"""
Wazuh Event Forwarder
Sends DLP events to Wazuh manager via syslog
"""

import json
import socket
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WazuhForwarder:
    """
    Forwards DLP events to Wazuh SIEM
    """

    def __init__(
        self,
        wazuh_host: str,
        wazuh_port: int = 1514,
        protocol: str = "udp",
    ):
        """
        Initialize Wazuh forwarder

        Args:
            wazuh_host: Wazuh manager hostname/IP
            wazuh_port: Wazuh manager port (default: 1514)
            protocol: Protocol to use (udp or tcp)
        """
        self.wazuh_host = wazuh_host
        self.wazuh_port = wazuh_port
        self.protocol = protocol.lower()
        self.socket: Optional[socket.socket] = None

        if self.protocol == "tcp":
            self._connect_tcp()

    def _connect_tcp(self) -> None:
        """
        Establish TCP connection to Wazuh
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.wazuh_host, self.wazuh_port))
            logger.info(f"Connected to Wazuh at {self.wazuh_host}:{self.wazuh_port} via TCP")
        except Exception as e:
            logger.error(f"Failed to connect to Wazuh: {e}")
            raise

    def _format_syslog_message(self, event: Dict[str, Any]) -> str:
        """
        Format event as syslog message

        Args:
            event: DLP event dictionary

        Returns:
            Formatted syslog message
        """
        # RFC 3164 format
        priority = 133  # facility=16 (local0), severity=5 (notice)
        timestamp = datetime.utcnow().strftime("%b %d %H:%M:%S")
        hostname = socket.gethostname()
        program = "cybersentinel-dlp"

        # Convert event to JSON
        event_json = json.dumps(event)

        # Construct syslog message
        message = f"<{priority}>{timestamp} {hostname} {program}: {event_json}"

        return message

    def forward_event(self, event: Dict[str, Any]) -> bool:
        """
        Forward DLP event to Wazuh

        Args:
            event: DLP event to forward

        Returns:
            True if successful, False otherwise
        """
        try:
            # Format message
            message = self._format_syslog_message(event)

            # Send via appropriate protocol
            if self.protocol == "udp":
                self._send_udp(message)
            elif self.protocol == "tcp":
                self._send_tcp(message)
            else:
                raise ValueError(f"Unsupported protocol: {self.protocol}")

            logger.debug(f"Forwarded event {event.get('id')} to Wazuh")
            return True

        except Exception as e:
            logger.error(f"Failed to forward event to Wazuh: {e}")
            return False

    def _send_udp(self, message: str) -> None:
        """
        Send message via UDP

        Args:
            message: Formatted syslog message
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(message.encode('utf-8'), (self.wazuh_host, self.wazuh_port))
        finally:
            sock.close()

    def _send_tcp(self, message: str) -> None:
        """
        Send message via TCP

        Args:
            message: Formatted syslog message
        """
        if not self.socket:
            self._connect_tcp()

        try:
            self.socket.sendall(message.encode('utf-8') + b'\n')
        except (socket.error, BrokenPipeError):
            # Reconnect and retry
            logger.warning("TCP connection lost, reconnecting...")
            self._connect_tcp()
            self.socket.sendall(message.encode('utf-8') + b'\n')

    def close(self) -> None:
        """
        Close connection (TCP only)
        """
        if self.socket:
            self.socket.close()
            self.socket = None
            logger.info("Closed Wazuh TCP connection")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create forwarder
    forwarder = WazuhForwarder(
        wazuh_host="localhost",
        wazuh_port=1514,
        protocol="udp"
    )

    # Example DLP event
    test_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_id": "evt-12345",
        "source": "endpoint",
        "user": "john.doe@company.com",
        "classification": {
            "score": 0.92,
            "labels": ["PAN", "HIGH_ENTROPY"],
            "method": "regex+ml"
        },
        "policy": {
            "id": "pol-001",
            "action": "block",
            "severity": "critical"
        },
        "context": {
            "file_path": "/home/user/export.csv",
            "destination": "external-server.com",
            "protocol": "https"
        }
    }

    # Forward event
    success = forwarder.forward_event(test_event)
    print(f"Event forwarded: {success}")

    # Close connection
    forwarder.close()
