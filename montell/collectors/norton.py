from .base import RestCollector

class NortonCollector(RestCollector):
    """Adapter slot for Norton/Symantec. Override fetch/headers/normalize for the native API."""
    source = 'Norton/Symantec'
