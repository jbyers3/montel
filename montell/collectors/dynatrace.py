from .base import RestCollector

class DynatraceCollector(RestCollector):
    """Adapter slot for Dynatrace. Override fetch/headers/normalize for the native API."""
    source = 'Dynatrace'
