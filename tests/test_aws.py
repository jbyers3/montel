import unittest
from datetime import datetime, timezone
from montell.aws_backend import AWSStore, build_collectors
from montell.core import DemoCollector

class FakeCloudWatch:
    def get_metric_statistics(self, **kwargs):
        assert kwargs['Namespace']=='AWS/EC2'
        return {'Datapoints':[{'Timestamp':datetime.now(timezone.utc),'Average':81,'Unit':'Percent'}]}

class FakeTable:
    def __init__(self): self.items={}
    def batch_writer(self, **kwargs): return self
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def put_item(self, Item): self.items[(Item['pk'],Item['sk'])]=Item
    def get_item(self,Key): return {'Item':self.items.get((Key['pk'],Key['sk']))}

class AWSTests(unittest.TestCase):
    def test_native_cloudwatch(self):
        c=build_collectors({'CLOUDWATCH':{'enabled':True,'metrics':[{'namespace':'AWS/EC2','name':'CPUUtilization','resource':'demo','warning_above':70}]}},FakeCloudWatch())[0]
        s=c.collect()[0]; self.assertEqual(s.value,81); self.assertEqual(s.status,'warning')
    def test_store_deduplicates_identity_and_separates_mode(self):
        table=FakeTable(); demo=AWSStore(table,'demo'); signals=DemoCollector().collect(); demo.ingest(signals); demo.ingest(signals)
        self.assertEqual(len(table.items),len(signals)); AWSStore(table,'live').ingest(signals); self.assertEqual(len(table.items),2*len(signals))
        demo.record_status([{'state':'ok'}]); self.assertEqual(demo.status(),[{'state':'ok'}])
