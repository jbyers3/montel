"""AWS Lambda entrypoints. SDK clients are injected in unit tests."""
import hashlib
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from .core import DemoCollector
from .config import VendorConfig
from .pipeline import REGISTRY, Pipeline
from .collectors.tls import TLSCollector
from .collectors.aws_cloudwatch import NativeCloudWatchCollector


def _table():
    import boto3
    return boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])


class AWSStore:
    def __init__(self, table, mode):
        self.table, self.mode = table, mode

    def ingest(self, signals):
        with self.table.batch_writer(overwrite_by_pkeys=['pk', 'sk']) as batch:
            for signal in signals:
                payload = asdict(signal)
                identity = json.dumps([signal.source, signal.application, signal.resource, signal.metric], separators=(',', ':'))
                key = hashlib.sha256(identity.encode()).hexdigest()
                batch.put_item(Item={'pk': self.mode + '#signals', 'sk': key, 'payload': json.dumps(payload, allow_nan=False)})

    def record_status(self, status):
        self.table.put_item(Item={'pk': self.mode + '#status', 'sk': 'latest', 'payload': json.dumps(status)})

    def latest(self):
        from boto3.dynamodb.conditions import Key
        options = {'KeyConditionExpression': Key('pk').eq(self.mode + '#signals')}
        rows = []
        while True:
            result = self.table.query(**options)
            rows.extend(json.loads(item['payload']) for item in result['Items'])
            if 'LastEvaluatedKey' not in result:
                return rows
            options['ExclusiveStartKey'] = result['LastEvaluatedKey']

    def status(self):
        item = self.table.get_item(Key={'pk': self.mode + '#status', 'sk': 'latest'}).get('Item')
        return json.loads(item['payload']) if item else []


def build_collectors(config, cloudwatch_client=None):
    collectors = []
    for name, settings in config.items():
        if not settings.get('enabled', False):
            continue
        if name == 'TLS':
            collectors.append(TLSCollector(settings['host'], settings.get('port', 443), settings.get('application', 'default')))
        elif name == 'CLOUDWATCH':
            collectors.append(NativeCloudWatchCollector(settings, cloudwatch_client))
        elif name in REGISTRY:
            collectors.append(REGISTRY[name](VendorConfig(settings['base_url'], settings['path'], settings.get('token', ''), settings.get('application', 'default'))))
        else:
            raise ValueError('unknown collector name')
    return collectors


def collect_handler(event, context):
    mode = os.environ['MONTELL_MODE']
    store = AWSStore(_table(), mode)
    if mode == 'demo':
        collectors = [DemoCollector()]
    else:
        import boto3
        secret = boto3.client('secretsmanager').get_secret_value(SecretId=os.environ['CONFIG_SECRET_ARN'])
        collectors = build_collectors(json.loads(secret['SecretString']))
    if not collectors:
        raise ValueError('no collectors enabled')
    statuses = Pipeline(store, collectors).run()
    store.record_status(statuses)
    # Fail the invocation if any collector failed, for Lambda monitoring.
    if any(row['state'] == 'error' for row in statuses):
        raise RuntimeError('one or more collectors failed; inspect collector status')
    return {'collectors': statuses}


def api_handler(event, context):
    mode = os.environ['MONTELL_MODE']
    store = AWSStore(_table(), mode)
    path = event.get('resource')
    if path == '/api/signals':
        payload = store.latest()
    elif path == '/api/collectors':
        payload = {'mode': mode, 'collectors': store.status()}
    else:
        return {'statusCode': 404, 'body': '{}'}
    return {'statusCode': 200, 'headers': {'Content-Type': 'application/json', 'Cache-Control': 'no-store'}, 'body': json.dumps(payload)}
