"""Live certificate observation using verified TLS, no vendor API required."""
import socket, ssl
from datetime import datetime, timezone
from ..core import Signal
class TLSCollector:
    source='TLS'
    def __init__(self,host,port=443,application='default'):
        self.host=host; self.port=port; self.application=application
    def collect(self):
        now=datetime.now(timezone.utc)
        with socket.create_connection((self.host,self.port),timeout=10) as sock:
            with ssl.create_default_context().wrap_socket(sock,server_hostname=self.host) as tls:
                expiry=datetime.fromtimestamp(ssl.cert_time_to_seconds(tls.getpeercert()['notAfter']),timezone.utc)
        days=(expiry-now).days
        return [Signal(self.source,self.application,self.host,'certificate_days_remaining',days,'days','critical' if days<7 else 'warning' if days<30 else 'healthy',now.isoformat())]
