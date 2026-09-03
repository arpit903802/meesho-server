#!/usr/bin/env python3
import json, uuid, random, requests, logging, os, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor

MEESHO_API = "https://prod.meeshoapi.com/api"
MEESHO_AUTH = "32c4d8137cn9eb493a1921f203173080"
APP_VERSION = "29.1"
APP_VERSION_CODE = "860"

OTPLESS_APP_ID = "XN07RN1IQC548C9YK5I4"
OTPLESS_LOGIN_URI = "otpless.xn07rn1iqc548c9yk5i4://otpless"

ANON_XO = "eyJ0eXBlIjoiY29tcG9zaXRlIn0=.eyJqd3QiOiJleUpoYkdjaU9pSklVekkxTmlJc0ltaDBkSEJ6T2k4dmJXVmxjMmh2TG1OdmJTOXBjMjlmWTI5MWJuUnllVjlqYjJSbElqb2lTVTRpTENKb2RIUndjem92TDIxbFpYTm9ieTVqYjIwdmRtVnljMmx2YmlJNklqRWlMQ0owZVhBaU9pSktWMVFpZlEuZXlKbGVIQWlPakU1TkRVek16STVOemdzSW1oMGRIQnpPaTh2YldWbGMyaHZMbU52YlM5aGJtOXVlVzF2ZFhOZmRYTmxjbDlwWkNJNkltTTVZbUk0WVRVekxUSXhaVE10TkRkallTMWlOamMwTFdGalpURXpOekZtWVRVM01TSXNJbWgwZEhCek9pOHZiV1ZsYzJodkxtTnZiUzlwYm5OMFlXNWpaVjlwWkNJNkltUTNNVGc1TW1OaFlUZ3laalE1TlRFNVpqUmhNek5oTUdVd1lqZzNaamN3SWl3aWFXRjBJam94TnpnM05qVXlPVGM0ZlEuLUN6TXktTEJ2VHpGV042VlROMDNKdzItLXhiX0lqSU9VZmpJRTk4eWlQUSIsInhvIjoiIn0="

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=30)

ACCOUNTS_FILE = "accounts.json"
OTP_FILE = "otp_sessions.json"
ORDERS_FILE = "orders.json"

def load_json(f, d):
    try:
        with open(f, 'r') as fh:
            return json.load(fh)
    except:
        return d

def save_json(f, d):
    with open(f, 'w') as fh:
        json.dump(d, fh)

DEVICES = [{"brand":"motorola","model":"moto g(60)","os":"12"},{"brand":"samsung","model":"SM-M315F","os":"13"},{"brand":"xiaomi","model":"M2010J19SI","os":"12"},{"brand":"realme","model":"RMX3363","os":"13"}]
IMAGES = ["https://picsum.photos/300/400?random=1","https://picsum.photos/300/400?random=2","https://picsum.photos/300/400?random=3"]

def search_products(query, page=1, limit=20):
    dev = random.choice(DEVICES)
    headers = {
        "authorization": MEESHO_AUTH, "app-version": APP_VERSION,
        "app-version-code": APP_VERSION_CODE, "instance-id": str(uuid.uuid4()),
        "country-iso":"in","application-id":"com.meesho.supply",
        "app-session-id":str(uuid.uuid4()),"app-sdk-version":"34",
        "app-client-id":"android","xo":ANON_XO,
        "meesho-user-context":"anonymous","content-type":"application/json; charset=UTF-8",
        "user-agent":"Dalvik/2.1.0","app-gaid":str(uuid.uuid4()),
        "app-session-count":str(random.randint(1,6)),
    }
    body = {"filter":{"type":"text_search","query":query},"offset":(page-1)*limit,"limit":limit}
    try:
        resp = requests.post(f"{MEESHO_API}/3.0/anonymous/catalogs", headers=headers, json=body, timeout=10)
        if resp.status_code == 200:
            catalogs = resp.json().get("catalogs",[])
            products = []
            for c in catalogs:
                price = c.get("price") or random.randint(99,999)
                mrp = c.get("mrp") or price*2
                if isinstance(price,dict): price = price.get("value", random.randint(99,999))
                if isinstance(mrp,dict): mrp = mrp.get("value", price*2)
                products.append({"id":str(c.get("id","")),"name":c.get("name","Product"),"price":int(price),"mrp":int(mrp),"rating":c.get("rating") or random.choice([3.8,4.0,4.2,4.5]),"image":c.get("image") or random.choice(IMAGES)})
            return {"ok":True,"products":products,"page":page,"has_next":len(products)==limit}
    except: pass
    fb = [{"id":str(random.randint(1000,9999)),"name":f"{query} {i+1}","price":random.randint(99,999),"mrp":random.randint(200,2000),"rating":random.choice([3.8,4.0,4.2,4.5]),"image":random.choice(IMAGES)} for i in range(limit)]
    return {"ok":True,"products":fb,"page":page,"has_next":False}

# ============ REAL OTPLESS (No Cryptography) ============

def send_otp_real(phone, user_id):
    ts_id = f"{uuid.uuid4()}-{int(time.time()*1000)}"
    in_id = f"{uuid.uuid4()}-{int(time.time()*1000)}"
    
    try:
        # Step 1: Get state
        state_resp = requests.get(
            "https://user-auth.otpless.app/v2/state",
            params={
                "origin":"https://otpless.com","version":"V3",
                "tsId":ts_id,"inId":in_id,"isHeadless":"true",
                "platform":"android","isLoginPage":"false",
                "packageName":"com.meesho.supply",
                "appId":OTPLESS_APP_ID,
                "loginUri":OTPLESS_LOGIN_URI,
                "deviceInfo":json.dumps({"platform":"android","vendor":"motorola","language":"en-IN","screenWidth":1080,"screenHeight":2225,"timezoneOffset":330,"cpuArchitecture":"aarch64"})
            }, timeout=10
        )
        
        if state_resp.status_code != 200:
            return {"ok":False,"message":"State failed: HTTP "+str(state_resp.status_code)}
        
        state = state_resp.json().get("state")
        if not state:
            return {"ok":False,"message":"No state in response"}
        
        # Step 2: Send OTP intent
        device_info = {"platform":"android","vendor":"motorola","language":"en-IN","screenWidth":1080,"screenHeight":2225,"timezoneOffset":330,"cpuArchitecture":"aarch64"}
        
        intent_body = {
            "selectedCountryCode":"+91","mobile":f"91{phone}",
            "silentAuthEnabled":False,"hasWhatsapp":"false","deliveryChannel":"SMS",
            "metadata":json.dumps({
                "appInfo":json.dumps({"platform":"android","manufacturer":"motorola","androidVersion":"31","packageName":"com.meesho.supply","model":"moto g(60)","appSignature":"oBcOM6bXKNcqouiPFcR1ur60Z6myTuVIDNSNWuKOlzU","sdkVersion":"1.3.3"}),
                "deviceInfo":json.dumps(device_info),
                "deviceIdInfo":json.dumps({"androidId":"aa5e8c37ca4077f7","gaid":str(uuid.uuid4())})
            }),
            "triggerWebauthn":False,
            "telephonyInfo":{"isMobileDataOn":False,"hasReadPhoneStatePermission":False},
            "clientMetaData":json.dumps({"tid":str(uuid.uuid4())[:16]}),
            "asId":"","isViSnaWhitelisted":True,"isAirtelSnaWhitelisted":True,
            "isAutoIntent":True,"origin":"https://otpless.com","version":"V4",
            "tsId":ts_id,"inId":in_id,
            "deviceInfo":json.dumps(device_info),
            "loginUri":OTPLESS_LOGIN_URI,
            "appId":OTPLESS_APP_ID,"isHeadless":True,
            "packageName":"com.meesho.supply","package":"com.meesho.supply",
            "otpHash":"oBcOM6bXKNc","platform":"HEADLESS"
        }
        
        intent_resp = requests.post(
            f"https://user-auth.otpless.app/v3/lp/user/transaction/intent/{state}",
            headers={"user-agent":"okhttp/4.9.0","content-type":"application/json"},
            json=intent_body, timeout=15
        )
        
        if intent_resp.status_code != 200:
            return {"ok":False,"message":"Intent failed: HTTP "+str(intent_resp.status_code)}
        
        data = intent_resp.json()
        leap = data.get("quantumLeap", {})
        
        if not leap.get("uid") or not leap.get("channelAuthToken"):
            return {"ok":False,"message":"No leap data. Response: "+str(data)[:200]}
        
        # Save session
        sessions = load_json(OTP_FILE, {})
        sessions[phone] = {
            "state":state,
            "uid":leap["uid"],
            "token":leap["channelAuthToken"],
            "as_id":leap.get("asId",""),
            "ts_id":ts_id,
            "in_id":in_id,
            "user_id":user_id
        }
        save_json(OTP_FILE, sessions)
        
        return {"ok":True,"message":"OTP sent to +91"+phone}
    
    except Exception as e:
        return {"ok":False,"message":"Error: "+str(e)}

def verify_otp_real(phone, otp):
    sessions = load_json(OTP_FILE, {})
    session = sessions.get(phone)
    
    if not session:
        return {"ok":False,"message":"OTP pehle bhejo"}
    
    try:
        otp_body = {
            "selectedCountryCode":"91","mobile":phone,"otp":otp,
            "value":f"91{phone}","isOTPAutoRead":"false",
            "uid":session["uid"],"token":session["token"],
            "asId":session["as_id"],"origin":"https://otpless.com",
            "version":"V4","tsId":session["ts_id"],"inId":session["in_id"],
            "deviceInfo":json.dumps({"platform":"android","vendor":"motorola","language":"en-IN","screenWidth":1080,"screenHeight":2225,"timezoneOffset":330,"cpuArchitecture":"aarch64"}),
            "loginUri":OTPLESS_LOGIN_URI,
            "appId":OTPLESS_APP_ID,"isHeadless":True,
            "packageName":"com.meesho.supply","package":"com.meesho.supply",
            "otpHash":"oBcOM6bXKNc","platform":"HEADLESS"
        }
        
        verify_resp = requests.post(
            f"https://user-auth.otpless.app/v3/lp/user/transaction/otp/{session['state']}",
            headers={"user-agent":"okhttp/4.9.0","content-type":"application/json"},
            json=otp_body, timeout=15
        )
        
        if verify_resp.status_code != 200:
            return {"ok":False,"message":"OTP verify failed: HTTP "+str(verify_resp.status_code)}
        
        data = verify_resp.json()
        
        # Save account
        accs = load_json(ACCOUNTS_FILE, {})
        uid = session.get("user_id","default")
        if uid not in accs: accs[uid] = []
        if not any(a["phone"]==phone for a in accs[uid]):
            accs[uid].append({"phone":phone,"login_time":time.strftime("%Y-%m-%d %H:%M:%S")})
        save_json(ACCOUNTS_FILE, accs)
        
        # Clean session
        del sessions[phone]
        save_json(OTP_FILE, sessions)
        
        return {"ok":True,"account":{"phone":phone,"verified":True}}
    
    except Exception as e:
        return {"ok":False,"message":"Verify error: "+str(e)}

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == '/api/search':
            q = params.get('q',[''])[0]
            page = int(params.get('page',['1'])[0])
            limit = min(int(params.get('limit',['20'])[0]), 50)
            self._json(executor.submit(search_products,q,page,limit).result(timeout=15))
        elif parsed.path == '/api/offer':
            self._json({"ok":True,"bucket":random.choice([75,90,100,120,135,150])})
        elif parsed.path == '/api/accounts':
            uid = params.get('user_id',[''])[0]
            self._json({"ok":True,"accounts":load_json(ACCOUNTS_FILE,{}).get(uid,[])})
        elif parsed.path == '/api/orders':
            phone = params.get('phone',[''])[0]
            orders = [o for o in load_json(ORDERS_FILE,[]) if o.get('phone')==phone]
            self._json({"ok":True,"orders":orders})
        elif parsed.path == '/health':
            self._json({"status":"ok"})
        else:
            self._json({"ok":False},404)
    
    def do_POST(self):
        length = int(self.headers.get('Content-Length',0))
        body = json.loads(self.rfile.read(length) or b'{}')
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/send_otp':
            self._json(send_otp_real(body.get('phone',''), body.get('user_id','')))
        
        elif parsed.path == '/api/verify_otp':
            self._json(verify_otp_real(body.get('phone',''), body.get('otp','')))
        
        elif parsed.path == '/api/order':
            orders = load_json(ORDERS_FILE, [])
            orders.append(body)
            save_json(ORDERS_FILE, orders)
            self._json({"ok":True,"order":body})
        
        elif parsed.path == '/api/logout':
            uid = body.get('user_id','')
            phone = body.get('phone','')
            accs = load_json(ACCOUNTS_FILE, {})
            if uid in accs:
                accs[uid] = [a for a in accs[uid] if a['phone']!=phone]
                save_json(ACCOUNTS_FILE, accs)
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
