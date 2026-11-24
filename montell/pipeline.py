"""Collect independently so one vendor failure cannot stop others."""
from datetime import datetime, timezone
from .config import VendorConfig
from .collectors.ciphertrust import CipherTrustCollector
from .collectors.norton import NortonCollector
from .collectors.cyberark import CyberArkCollector
from .collectors.dynatrace import DynatraceCollector
from .collectors.cloudwatch import CloudWatchCollector
from .collectors.sqlserver import SQLServerCollector
from .collectors.tls import TLSCollector
import os
REGISTRY={'CIPHERTRUST':CipherTrustCollector,'NORTON':NortonCollector,'CYBERARK':CyberArkCollector,'DYNATRACE':DynatraceCollector,'CLOUDWATCH':CloudWatchCollector,'SQLSERVER':SQLServerCollector}
def configured_collectors():
    result=[]
    for prefix, cls in REGISTRY.items():
        if os.getenv(prefix+'_ENABLED')=='1': result.append(cls(VendorConfig.from_env(prefix)))
    if os.getenv('TLS_ENABLED')=='1': result.append(TLSCollector(os.environ['TLS_HOST'],int(os.getenv('TLS_PORT','443')),os.getenv('TLS_APPLICATION','default')))
    return result
class Pipeline:
    def __init__(self,store,collectors): self.store=store; self.collectors=collectors; self.status=[]
    def run(self):
        results=[]
        for c in self.collectors:
            name=getattr(c,'source',type(c).__name__); now=datetime.now(timezone.utc).isoformat()
            try:
                signals=c.collect(); self.store.ingest(signals)
                results.append({'source':name,'state':'ok','count':len(signals),'checked_at':now})
            except Exception as e:
                results.append({'source':name,'state':'error','error_type':type(e).__name__,'checked_at':now})
        self.status=results; return results
