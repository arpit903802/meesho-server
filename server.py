#!/usr/bin/env python3
import json, uuid, random, requests, logging, os, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor

MEESHO_API = "https://prod.meeshoapi.com/api"
MEESHO_AUTH = "32c4d8137cn9eb493a1921f203173080"
APP_VERSION = "29.1"
APP_VERSION_CODE = "860"

ANON_XO = "eyJ0eXBlIjoiY29tcG9zaXRlIn0=.eyJqd3QiOiJleUpoYkdjaU9pSklVekkxTmlJc0ltaDBkSEJ6T2k4dmJXVmxjMmh2TG1OdmJTOXBjMjlmWTI5MWJuUnllVjlqYjJSbElqb2lTVTRpTENKb2RIUndjem92TDIxbFpYTm9ieTVqYjIwdmRtVnljMmx2YmlJNklqRWlMQ0owZVhBaU9pSktWMVFpZlEuZXlKbGVIQWlPakU1TkRVek16STVOemdzSW1oMGRIQnpPaTh2YldWbGMyaHZMbU52YlM5aGJtOXVlVzF2ZFhOZmRYTmxjbDlwWkNJNkltTTVZbUk0WVRVekxUSXhaVE10TkRkallTMWlOamMwTFdGalpURXpOekZtWVRVM01TSXNJbWgwZEhCek9pOHZiV1ZsYzJodkxtTnZiUzlwYm5OMFlXNWpaVjlwWkNJNkltUTNNVGc1TW1OaFlUZ3laalE1TlRFNVpqUmhNek5oTUdVd1lqZzNaamN3SWl3aWFXRjBJam94TnpnM05qVXlPVGM0ZlEuLUN6TXktTEJ2VHpGV042VlROMDNKdzItLXhiX0lqSU9VZmpJRTk4eWlQUSIsInhvIjoiIn0="

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=50)

USER_ACCOUNTS_FILE = "user_accounts.json"

def load_user_accounts():
    try:
        with open(USER_ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_user_accounts(accounts):
    with open(USER_ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f)

DEVICES = [
    {"brand": "motorola", "model": "moto g(60)", "os_version": "12"},
    {"brand": "samsung", "model": "SM-M315F", "os_version": "13"},
    {"brand": "xiaomi", "model": "M2010J19SI", "os_version": "12"},
    {"brand": "realme", "model": "RMX3363", "os_version": "13"},
    {"brand": "vivo", "model": "V2130", "os_version": "13"},
    {"brand": "oneplus", "model": "CPH2583", "os_version": "14"},
]

PRODUCT_IMAGES = [
    "https://picsum.photos/300/400?random=1",
    "https://picsum.photos/300/400?random=2",
    "https://picsum.photos/300/400?random=3",
    "https://picsum.photos/300/400?random=4",
    "https://picsum.photos/300/400?random=5",
]

def extract_price(value, fallback=0):
    if value is None:
        return fallback
    if isinstance(value, (int, float)):
        return value if value > 0 else fallback
    if isinstance(value, str):
        try:
            return float(value.replace("₹", "").replace(",", "").strip())
        except:
            return fallback
    if isinstance(value, dict):
        for key in ["value", "selling_price", "price", "mrp", "original_price"]:
            if value.get(key):
                return extract_price(value[key], fallback)
        return fallback
    return fallback

def search_products(query, page=1, limit=20):
    dev = random.choice(DEVICES)
    headers = {
        "authorization": MEESHO_AUTH, "app-version": APP_VERSION,
        "app-version-code": APP_VERSION_CODE, "instance-id": str(uuid.uuid4()),
        "country-iso": "in", "application-id": "com.meesho.supply",
        "app-session-id": str(uuid.uuid4()), "app-sdk-version": "34",
        "app-client-id": "android", "xo": ANON_XO,
        "meesho-user-context": "anonymous", "content-type": "application/json; charset=UTF-8",
        "user-agent": "Dalvik/2.1.0 (Linux; U; Android 12; moto g(60) Build/) Cronet",
        "app-gaid": str(uuid.uuid4()), "app-session-count": str(random.randint(1, 6)),
    }
    body = {"filter": {"type": "text_search", "query": query}, "offset": (page-1)*limit, "limit": limit}
    try:
        resp = requests.post(f"{MEESHO_API}/3.0/anonymous/catalogs", headers=headers, json=body, timeout=10)
        if resp.status_code == 200:
            catalogs = resp.json().get("catalogs", [])
            products = []
            for c in catalogs:
                price = extract_price(c.get("price")) or extract_price(c.get("selling_price")) or random.randint(99, 999)
                mrp = extract_price(c.get("mrp")) or extract_price(c.get("maximum_retail_price")) or price * 2
                rating = c.get("rating") or random.choice([3.8, 4.0, 4.2, 4.5])
                image = c.get("image") or c.get("image_url") or random.choice(PRODUCT_IMAGES)
                products.append({"id": str(c.get("id", "")), "name": c.get("name", "Product"), "price": int(price), "mrp": int(mrp), "rating": round(float(rating), 1), "image": str(image)})
            return {"ok": True, "products": products, "page": page, "has_next": len(products) == limit}
    except Exception as e:
        logger.error(f"Search: {e}")
    fallback = []
    for i in range(limit):
        p = random.randint(99, 999)
        fallback.append({"id": str(random.randint(1000,9999)), "name": f"{query} {i+1}", "price": p, "mrp": p*2, "rating": random.choice([3.8,4.0,4.2,4.5]), "image": random.choice(PRODUCT_IMAGES)})
    return {"ok": True, "products": fallback, "page": page, "has_next": False}

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if parsed.path == '/api/search':
            query = params.get('q', [''])[0]
            page = int(params.get('page', ['1'])[0])
            limit = min(int(params.get('limit', ['20'])[0]), 50)
            result = executor.submit(search_products, query, page, limit).result(timeout=15)
            self._json(result)
        
        elif parsed.path == '/api/offer':
            dev = random.choice(DEVICES)
            bucket = random.choice([75, 90, 100, 120, 135, 150])
            self._json({"ok": True, "bucket": bucket, "device": dev["model"]})
        
        elif parsed.path == '/api/accounts':
            user_id = params.get('user_id', [''])[0]
            self._json({"ok": True, "accounts": load_user_accounts().get(user_id, [])})
        
        elif parsed.path == '/health':
            self._json({"status": "ok"})
        
        else:
            self._json({"ok": False}, 404)
    
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length) or b'{}')
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/login':
            phone = body.get('phone', '')
            user_id = body.get('user_id', '')
            accounts = load_user_accounts()
            if user_id not in accounts:
                accounts[user_id] = []
            if not any(a['phone'] == phone for a in accounts[user_id]):
                accounts[user_id].append({"phone": phone, "login_time": time.strftime("%Y-%m-%d %H:%M:%S")})
            save_user_accounts(accounts)
            self._json({"ok": True, "accounts": accounts[user_id]})
        
        elif parsed.path == '/api/logout':
            user_id = body.get('user_id', '')
            phone = body.get('phone', '')
            accounts = load_user_accounts()
            if user_id in accounts:
                accounts[user_id] = [a for a in accounts[user_id] if a['phone'] != phone]
                save_user_accounts(accounts)
            self._json({"ok": True, "accounts": accounts.get(user_id, [])})
        
        else:
            self._json({"ok": False}, 404)
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Running on port {port}")
    HTTPServer(('0.0.0.0', port), APIHandler).serve_forever()
