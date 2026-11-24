"""Injectable HTTPS JSON transport; no secrets in exception messages."""
import json, urllib.request, urllib.parse
class JsonTransport:
    def get(self, url, headers=None, params=None):
        if urllib.parse.urlsplit(url).scheme != 'https':
            raise ValueError('HTTPS required')
        if params:
            url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={'Accept':'application/json', **(headers or {})})
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = response.read(5_000_001)
            if len(payload)>5_000_000: raise ValueError('response too large')
            return json.loads(payload)
