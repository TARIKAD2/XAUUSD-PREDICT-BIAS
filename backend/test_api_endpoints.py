import sys, time, httpx, os
sys.path.append('backend')
# Give server a moment to start
time.sleep(5)
base = 'http://127.0.0.1:8000'
endpoints = ['/docs', '/openapi.json', '/api/health']
for ep in endpoints:
    url = base + ep
    try:
        r = httpx.get(url, timeout=10.0)
        print(f'{ep} -> {r.status_code}')
        if r.status_code == 200 and ep == '/api/health':
            print('Health payload:', r.json())
    except Exception as e:
        print(f'{ep} -> ERROR {e}')

