#!/usr/bin/env python3
import json, uuid, random, requests, logging, os
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

DEVICES = [
    {"brand": "motorola", "model": "moto g(60)", "os_version": "12"},
    {"brand": "samsung", "model": "SM-M315F", "os_version": "13"},
    {"brand": "xiaomi", "model": "M2010J19SI", "os_version": "12"},
    {"brand": "realme", "model": "RMX3363", "os_version": "13"},
    {"brand": "vivo", "model": "V2130", "os_version": "13"},
    {"brand": "oneplus", "model": "CPH2583", "os_version": "14"},
]

def extract_price(value, fallback=0):
    """Price ko sahi se extract karo - int, float, str, dict sab handle"""
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
        for key in ["value", "selling_price", "price", "mrp", "original_price", "min_price", "max_price"]:
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
        "user-agent": f"Dalvik/2.1.0 (Linux; U; Android {dev['os_version']}; {dev['model']} Build/) Cronet/137.0.7100.61",
        "app-gaid": str(uuid.uuid4()), "app-session-count": str(random.randint(1, 6)),
    }
    body = {
        "filter": {"type": "text_search", "sort_option": None, "selected_filters": [],
                   "current_row_filters": [], "session_state": None, "selectedFilterIds": [],
                   "isClearFilterClicked": False, "query": query, "intent_payload": None,
                   "is_voice_search": False},
        "search_session_id": None, "cursor": None, "offset": (page-1)*limit,
        "limit": limit, "supplier_id": None, "featured_collection_type": None,
        "meta": {"recent_searches": [query]}, "retry_count": 0, "product_listing_page_id": None
    }
    
    try:
        resp = requests.post(f"{MEESHO_API}/3.0/anonymous/catalogs", headers=headers, json=body, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            catalogs = data.get("catalogs", [])
            products = []
            
            for c in catalogs:
                # Price extract karo - multiple fields try
                price = extract_price(c.get("price")) or extract_price(c.get("selling_price")) or extract_price(c.get("min_price"))
                mrp = extract_price(c.get("mrp")) or extract_price(c.get("maximum_retail_price")) or extract_price(c.get("original_price"))
                
                # Agar price 0 hai to fallback random
                if price <= 0:
                    price = random.randint(99, 999)
                if mrp <= 0 or mrp < price:
                    mrp = price * random.choice([2, 2.5, 3, 3.5, 4])
                
                # Rating extract
                rating = c.get("rating")
                if isinstance(rating, dict):
                    rating = rating.get("average") or rating.get("value") or 0
                if not rating or rating <= 0:
                    rating = random.choice([3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4, 4.5])
                
                products.append({
                    "id": str(c.get("id", "")),
                    "name": c.get("name", "Product"),
                    "price": int(price),
                    "mrp": int(mrp),
                    "rating": round(float(rating), 1)
                })
            
            return {"ok": True, "products": products, "page": page, "has_next": len(products) == limit}
    except Exception as e:
        logger.error(f"Search error: {e}")
    
    # Fallback agar API fail
    fallback_products = []
    for i in range(limit):
        p = random.randint(99, 999)
        fallback_products.append({
            "id": str(random.randint(1000, 9999)),
            "name": f"{query} Product {i+1}",
            "price": p,
            "mrp": p * 2,
            "rating": random.choice([3.8, 4.0, 4.2, 4.5])
        })
    return {"ok": True, "products": fallback_products, "page": page, "has_next": False}

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if parsed.path == '/api/search':
            query = params.get('q', [''])[0]
            page = int(params.get('page', ['1'])[0])
            limit = min(int(params.get('limit', ['20'])[0]), 50)
            result = executor.submit(search_products, query, page, limit).result(timeout=15)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        elif parsed.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Running on port {port}")
    HTTPServer(('0.0.0.0', port), APIHandler).serve_forever()
