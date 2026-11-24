from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import sqlite3, json
from typing import Protocol

@dataclass(frozen=True)
class Signal:
    source: str
    application: str
    resource: str
    metric: str
    value: float | str
    unit: str
    status: str
    observed_at: str
    def __post_init__(self):
        if self.status not in {'healthy','warning','critical','unknown'}:
            raise ValueError('invalid status')

class Collector(Protocol):
    def collect(self) -> list[Signal]: ...

class DemoCollector:
    """Synthetic portfolio fixtures, never connections to real services."""
    def collect(self):
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            ('CipherTrust','demo-db','encryption_status','protected','','healthy'),
            ('TLS','demo-api','certificate_days_remaining',18,'days','warning'),
            ('Norton/Symantec','demo-host','endpoint_protection','active','','healthy'),
            ('Norton/Symantec','demo-host','definitions_age',1,'days','healthy'),
            ('CyberArk','demo-service-account','rotation_age',42,'days','warning'),
            ('Dynatrace','demo-api','response_p95',820,'ms','warning'),
            ('Dynatrace','demo-api','error_rate',0.4,'%','healthy'),
            ('CloudWatch','demo-instance','cpu_utilization',71,'%','warning'),
            ('CloudWatch','demo-volume','read_latency',24,'ms','warning'),
            ('SQL Server','demo_catalog','database_state','ONLINE','','healthy'),
            ('SQL Server','demo_orders','database_state','ONLINE','','healthy'),
            ('SQL Server','query-hash-demo-01','expensive_query_cpu',3100,'ms','warning'),
            ('SQL Server','query-hash-demo-02','long_running_query',95,'s','critical'),
        ]
        return [Signal(s,'demo-commerce',r,m,v,u,h,now) for s,r,m,v,u,h in rows]

class Store:
    def __init__(self,path):
        self.path=Path(path)
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS samples (id INTEGER PRIMARY KEY, source TEXT, application TEXT, resource TEXT, metric TEXT, observed_at TEXT, payload TEXT)')
            db.execute('CREATE INDEX IF NOT EXISTS signal_lookup ON samples(application,source,resource,metric,id)')
    def ingest(self,signals):
        with sqlite3.connect(self.path) as db:
            db.executemany('INSERT INTO samples(source,application,resource,metric,observed_at,payload) VALUES (?,?,?,?,?,?)',[(s.source,s.application,s.resource,s.metric,s.observed_at,json.dumps(asdict(s))) for s in signals])
    def latest(self):
        with sqlite3.connect(self.path) as db:
            rows=db.execute('SELECT payload FROM samples WHERE id IN (SELECT max(id) FROM samples GROUP BY application,source,resource,metric) ORDER BY source,resource,metric').fetchall()
        return [json.loads(r[0]) for r in rows]
