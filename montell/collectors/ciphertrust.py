from .base import RestCollector

class CipherTrustCollector(RestCollector):
    """Adapter slot for CipherTrust. Override fetch/headers/normalize for the native API."""
    source = 'CipherTrust'
