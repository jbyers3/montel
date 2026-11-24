"""Each adapter owns request and response mapping; inject a transport for tests."""
from datetime import datetime, timezone
from ..core import Signal
from ..transport import JsonTransport
class RestCollector:
    source = ''
    def __init__(self, config, transport=None):
        self.config=config; self.transport=transport or JsonTransport()
    def fetch(self):
        c=self.config
        if not c.base_url or not c.path: raise ValueError('vendor endpoint not configured')
        return self.transport.get(c.base_url.rstrip('/')+'/'+c.path.lstrip('/'),headers=self.headers())
    def headers(self):
        return {'Authorization':'Bearer '+self.config.token} if self.config.token else {}
    def normalize(self, payload):
        """Default adapter contract, NOT a claim about a native vendor response.
        Override this method to map the vendor's actual response schema.
        """
        rows=payload['items']; now=datetime.now(timezone.utc).isoformat()
        return [Signal(self.source,self.config.application,str(r['resource']),str(r['metric']),r['value'],str(r.get('unit','')),r.get('status','unknown'),r.get('observed_at',now)) for r in rows]
    def collect(self): return self.normalize(self.fetch())
