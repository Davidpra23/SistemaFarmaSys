import requests
import re
import json
import time

BASE = 'http://127.0.0.1:5000'

import requests
import re
import json
import time

BASE = 'http://127.0.0.1:5000'

s = requests.Session()

def get_with_retries(url, max_retries=10, delay=0.5):
    for i in range(max_retries):
        try:
            r = s.get(url)
            return r
        except requests.exceptions.RequestException:
            time.sleep(delay)
    raise RuntimeError(f'Failed to connect to {url} after {max_retries} retries')

print('Waiting for server...')
get_with_retries(BASE + '/login', max_retries=20, delay=0.5)

# Login
login_url = BASE + '/login'
print('Logging in...')
r = s.post(login_url, data={'username': 'admin', 'password': '123'}, allow_redirects=True)
print('Login status:', r.status_code)
if r.status_code not in (200, 302):
    print('Login failed or unexpected status')
    print(r.text[:800])
    exit(1)

# Get sales page to extract INIT_PRODUCTS
print('Fetching /sales to extract products...')
r = get_with_retries(BASE + '/sales')
if r.status_code != 200:
    print('/sales returned', r.status_code)
    print(r.text[:800])
    exit(1)

m = re.search(r'window\.INIT_PRODUCTS\s*=\s*(\[.*?\]);', r.text, re.S)
if not m:
    print('Could not find window.INIT_PRODUCTS in /sales HTML. Showing snippet:')
    print(r.text[:1200])
    exit(1)

products_json = m.group(1)
products = json.loads(products_json)
print('Found', len(products), 'products')
if not products:
    print('No products to use for checkout')
    exit(1)

p = products[0]
items = [{'id': p['id'], 'name': p['name'], 'price': p['price'], 'qty': 1}]

print('Posting checkout for', items)
r = s.post(BASE + '/api/checkout', json={'items': items})
print('Checkout status:', r.status_code)
print('Response body:', r.text)

if r.status_code == 200:
    data = r.json()
    rid = data.get('receipt_id')
    if rid:
        print('Receipt id:', rid)
        # Fetch receipt page
        rr = s.get(f'{BASE}/receipt/{rid}')
        print('/receipt status:', rr.status_code)
        print('Receipt page snippet:')
        print(rr.text[:800])

print('Done')
