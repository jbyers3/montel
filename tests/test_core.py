import tempfile, unittest
from pathlib import Path
from montell.core import Store, DemoCollector, Signal
class Tests(unittest.TestCase):
    def test_latest_and_sources(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(Path(d)/'demo.db'); signals=DemoCollector().collect(); store.ingest(signals); store.ingest(signals)
            rows=store.latest(); self.assertEqual(len(rows),len(signals)); self.assertEqual(len({r['source'] for r in rows}),7)
    def test_invalid_status(self):
        with self.assertRaises(ValueError): Signal('x','a','r','m',1,'','bad','now')
    def test_query_categories(self):
        metrics={r.metric for r in DemoCollector().collect()}; self.assertTrue({'database_state','expensive_query_cpu','long_running_query'} <= metrics)
