from .base import RestCollector

class CloudWatchCollector(RestCollector):
    """Adapter slot for CloudWatch. Override fetch/headers/normalize for the native API."""
    source = 'CloudWatch'
