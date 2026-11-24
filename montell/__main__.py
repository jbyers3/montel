import argparse,json,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from .core import Store,DemoCollector
from .pipeline import Pipeline,configured_collectors
PAGE=Path(__file__).with_name('dashboard.html')
def main():
    p=argparse.ArgumentParser(description='Montell observability service')
    p.add_argument('--db'); p.add_argument('--port',type=int,default=8080); p.add_argument('--mode',choices=['demo','live'],default='demo'); p.add_argument('--interval',type=int,default=60); p.add_argument('--once',action='store_true')
    a=p.parse_args(); store=Store(a.db or f'montell-{a.mode}.sqlite3'); collectors=[DemoCollector()] if a.mode=='demo' else configured_collectors()
    if not collectors: p.error('No live collectors enabled')
    if a.interval<1: p.error('Interval must be positive')
    pipeline=Pipeline(store,collectors); pipeline.run()
    if a.once: print(json.dumps(pipeline.status)); return int(any(x['state']=='error' for x in pipeline.status))
    stop=threading.Event()
    def poll():
        while not stop.wait(a.interval): pipeline.run()
    threading.Thread(target=poll,daemon=True).start()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path=='/': data=PAGE.read_bytes(); mime='text/html; charset=utf-8'
            elif self.path=='/api/signals': data=json.dumps(store.latest()).encode(); mime='application/json'
            elif self.path=='/api/collectors': data=json.dumps({'mode':a.mode,'collectors':pipeline.status}).encode(); mime='application/json'
            else: self.send_error(404); return
            self.send_response(200); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
    print(f'Montell {a.mode}: http://127.0.0.1:{a.port}')
    try: ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
    finally: stop.set()
if __name__=='__main__': raise SystemExit(main())
