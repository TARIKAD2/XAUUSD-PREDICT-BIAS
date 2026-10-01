import sys, time, httpx, os
os.environ['PYTHONPATH']='backend'
# give server a moment to start
time.sleep(3)
base='http://127.0.0.1:8000'
endpoints=[
    '/docs',
    '/openapi.json',
    '/api/health',
    '/api/market',
    '/api/market/XAUUSD',
    '/api/news',
    '/api/economic-events',
    '/api/predictions',
    '/api/predictions/XAUUSD',
    '/api/model-performance',
]
for ep in endpoints:
    try:
        r=httpx.get(base+ep, timeout=10.0)
        print(f"{ep} -> {r.status_code}")
        if r.status_code==200 and ep.startswith('/api/') and not ep in ['/api/health']:
            # print a short snippet of json (first 100 chars)
            try:
                txt=r.text.replace('\n','')
                print('  payload:', txt[:100])
            except Exception:
                pass
    except Exception as e:
        print(f"{ep} -> ERROR {e}")

