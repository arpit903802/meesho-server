#!/usr/bin/env python3
import json, uuid, random, requests, logging, os, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor

MEESHO_API = "https://prod.meeshoapi.com/api"
MEESHO_AUTH = "32c4d8137cn9eb493a1921f203173080"

ANON_XO = "eyJ0eXBlIjoiY29tcG9zaXRlIn0=.eyJqd3QiOiJleUpoYkdjaU9pSklVekkxTmlJc0ltaDBkSEJ6T2k4dmJXVmxjMmh2TG1OdmJTOXBjMjlmWTI5MWJuUnllVjlqYjJSbElqb2lTVTRpTENKb2RIUndjem92TDIxbFpYTm9ieTVqYjIwdmRtVnljMmx2YmlJNklqRWlMQ0owZVhBaU9pSktWMVFpZlEuZXlKbGVIQWlPakU1TkRVek16STVOemdzSW1oMGRIQnpPaTh2YldWbGMyaHZMbU52YlM5aGJtOXVlVzF2ZFhOZmRYTmxjbDlwWkNJNkltTTVZbUk0WVRVekxUSXhaVE10TkRkallTMWlOamMwTFdGalpURXpOekZtWVRVM01TSXNJbWgwZEhCek9pOHZiV1ZsYzJodkxtTnZiUzlwYm5OMFlXNWpaVjlwWkNJNkltUTNNVGc1TW1OaFlUZ3laalE1TlRFNVpqUmhNek5oTUdVd1lqZzNaamN3SWl3aWFXRjBJam94TnpnM05qVXlPVGM0ZlEuLUN6TXktTEJ2VHpGV042VlROMDNKdzItLXhiX0lqSU9VZmpJRTk4eWlQUSIsInhvIjoiIn0="

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=30)

USER_ACCOUNTS_FILE = "user_accounts.json"

def load_accounts():
    try:
        with open(USER_ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_accounts(d):
    with open(USER_ACCOUNTS_FILE, 'w') as f:
        json.dump(d, f)

DEVICES = [
    {"brand":"motorola","model":"moto g(60)","os":"12"},
    {"brand":"samsung","model":"SM-M315F","os":"13"},
    {"brand":"xiaomi","model":"M2010J19SI","os":"12"},
    {"brand":"realme","model":"RMX3363","os":"13"},
]

IMAGES = [
    "https://picsum.photos/300/400?random=1",
    "https://picsum.photos/300/400?random=2",
    "https://picsum.photos/300/400?random=3",
    "https://picsum.photos/300/400?random=4",
]

def search_products(query, page=1, limit=20):
    dev = random.choice(DEVICES)
    headers = {
        "authorization": MEESHO_AUTH, "app-version": "29.1",
        "app-version-code": "860", "instance-id": str(uuid.uuid4()),
        "country-iso": "in", "application-id": "com.meesho.supply",
        "app-session-id": str(uuid.uuid4()), "app-sdk-version": "34",
        "app-client-id": "android", "xo": ANON_XO,
        "meesho-user-context": "anonymous", "content-type": "application/json; charset=UTF-8",
        "user-agent": "Dalvik/2.1.0", "app-gaid": str(uuid.uuid4()),
        "app-session-count": str(random.randint(1,6)),
    }
    body = {"filter": {"type": "text_search", "query": query}, "offset": (page-1)*limit, "limit": limit}
    try:
        resp = requests.post(f"{MEESHO_API}/3.0/anonymous/catalogs", headers=headers, json=body, timeout=10)
        if resp.status_code == 200:
            catalogs = resp.json().get("catalogs", [])
            products = []
            for c in catalogs:
                price = c.get("price") or random.randint(99, 999)
                mrp = c.get("mrp") or price * 2
                if isinstance(price, dict):
                    price = price.get("value", random.randint(99,999))
                if isinstance(mrp, dict):
                    mrp = mrp.get("value", price * 2)
                products.append({
                    "id": str(c.get("id","")),
                    "name": c.get("name","Product"),
                    "price": int(price),
                    "mrp": int(mrp),
                    "rating": c.get("rating") or random.choice([3.8,4.0,4.2,4.5]),
                    "image": c.get("image") or random.choice(IMAGES)
                })
            return {"ok":True,"products":products,"page":page,"has_next":len(products)==limit}
    except Exception as e:
        logger.error(f"Search: {e}")
    fb = [{"id":str(random.randint(1000,9999)),"name":f"{query} {i+1}","price":random.randint(99,999),"mrp":random.randint(200,2000),"rating":random.choice([3.8,4.0,4.2,4.5]),"image":random.choice(IMAGES)} for i in range(limit)]
    return {"ok":True,"products":fb,"page":page,"has_next":False}

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == '/api/search':
            q = params.get('q',[''])[0]
            page = int(params.get('page',['1'])[0])
            limit = min(int(params.get('limit',['20'])[0]), 50)
            self._json(executor.submit(search_products, q, page, limit).result(timeout=15))
        elif parsed.path == '/api/offer':
            self._json({"ok":True,"bucket":random.choice([75,90,100,120,135,150])})
        elif parsed.path == '/api/accounts':
            uid = params.get('user_id',[''])[0]
            self._json({"ok":True,"accounts":load_accounts().get(uid,[])})
        elif parsed.path == '/health':
            self._json({"status":"ok"})
        else:
            self._json({"ok":False},404)
    
    def do_POST(self):
        length = int(self.headers.get('Content-Length',0))
        body = json.loads(self.rfile.read(length) or b'{}')
        parsed = urlparse(self.path)
        if parsed.path == '/api/send_otp':
            self._json({"ok":True,"message":"OTP sent"})
        elif parsed.path == '/api/verify_otp':
            self._json({"ok":True,"account":{"phone":body.get('phone','')}})
        elif parsed.path == '/api/login':
            phone = body.get('phone','')
            uid = body.get('user_id','')
            accs = load_accounts()
            if uid not in accs: accs[uid] = []
            if not any(a['phone']==phone for a in accs[uid]):
                accs[uid].append({"phone":phone,"login_time":time.strftime("%Y-%m-%d %H:%M:%S")})
            save_accounts(accs)
            self._json({"ok":True,"accounts":accs[uid]})
        elif parsed.path == '/api/logout':
            phone = body.get('phone','')
            uid = body.get('user_id','')
            accs = load_accounts()
            if uid in accs:
                accs[uid] = [a for a in accs[uid] if a['phone'] != phone]
                save_accounts(accs)
            self._json({"ok":True,"accounts":accs.get(uid,[])})
        else:
            self._json({"ok":False},404)
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Running on {port}")
    HTTPServer(('0.0.0.0', port), APIHandler).serve_forever()
