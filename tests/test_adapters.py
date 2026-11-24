import tempfile,unittest
from pathlib import Path
from montell.config import VendorConfig
from montell.collectors.dynatrace import DynatraceCollector
from montell.pipeline import Pipeline
from montell.core import Store,DemoCollector
class Fake:
    def get(self,url,headers):
        assert url=='https://demo.invalid/metrics'; assert headers['Authorization']=='Bearer fake'
        return {'items':[{'resource':'app','metric':'latency','value':100,'unit':'ms','status':'healthy'}]}
class Broken:
    def collect(self): raise RuntimeError('secret must not leak')
class AdapterTests(unittest.TestCase):
    def test_transport_injection(self):
        c=DynatraceCollector(VendorConfig('https://demo.invalid','metrics','fake','demo'),Fake()); self.assertEqual(c.collect()[0].value,100)
    def test_failure_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(Path(d)/'data.db'); result=Pipeline(s,[Broken(),DemoCollector()]).run(); self.assertEqual([r['state'] for r in result],['error','ok']); self.assertTrue(s.latest()); self.assertNotIn('secret',str(result))
