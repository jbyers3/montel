"""Native CloudWatch metrics using the Lambda execution role; no access keys."""
from datetime import datetime, timedelta, timezone
from ..core import Signal

class NativeCloudWatchCollector:
    source = 'CloudWatch'
    def __init__(self, config, client=None):
        self.config, self.client = config, client

    def collect(self):
        if self.client is None:
            import boto3
            self.client = boto3.client('cloudwatch', region_name=self.config.get('region'))
        now = datetime.now(timezone.utc)
        result = []
        for metric in self.config['metrics']:
            period = int(metric.get('period', 300))
            stat = metric.get('statistic', 'Average')
            response = self.client.get_metric_statistics(Namespace=metric['namespace'], MetricName=metric['name'], Dimensions=metric.get('dimensions', []), StartTime=now-timedelta(seconds=period*3), EndTime=now, Period=period, Statistics=[stat])
            points = response.get('Datapoints', [])
            if not points:
                value, unit, status, observed = 'no data', '', 'unknown', now
            else:
                p = max(points, key=lambda row: row['Timestamp'])
                value, unit, observed = float(p[stat]), p.get('Unit', ''), p['Timestamp']
                critical, warning = metric.get('critical_above'), metric.get('warning_above')
                status = 'critical' if critical is not None and value >= critical else 'warning' if warning is not None and value >= warning else 'healthy' if warning is not None or critical is not None else 'unknown'
            result.append(Signal(self.source,self.config.get('application','default'),metric['resource'],metric['name'],value,unit,status,observed.isoformat()))
        return result
