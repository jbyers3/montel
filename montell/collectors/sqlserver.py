from .base import RestCollector

class SQLServerCollector(RestCollector):
    """Adapter slot for SQL Server. Override fetch/headers/normalize for the native API."""
    source = 'SQL Server'
