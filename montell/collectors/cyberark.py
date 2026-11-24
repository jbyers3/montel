from .base import RestCollector

class CyberArkCollector(RestCollector):
    """Adapter slot for CyberArk. Override fetch/headers/normalize for the native API."""
    source = 'CyberArk'
