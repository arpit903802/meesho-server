#!/usr/bin/env python3
import json, uuid, random, requests, logging, os, time, secrets, base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

MEESHO_API = "https://prod.meeshoapi.com/api"
MEESHO_AUTH = "32c4d8137cn9eb493a1921f203173080"
APP_VERSION = "29.1"
APP_VERSION_CODE = "860"

OTPLESS_APP_ID = "XN07RN1IQC548C9YK5I4"
OTPLESS_LOGIN_URI = "otpless.xn07rn1iqc548c9yk5i4://otpless"
OTPLESS_HASH = "oBcOM6bXKNc"
OTPLESS_SIGNATURE = "oBcOM6bXKNcqouiPFcR1ur60Z6myTuVIDNSNWuKOlzU"

ANON_XO = "eyJ0eXBlIjoiY29tcG9zaXRlIn0=.eyJqd3QiOiJleUpoYkdjaU9pSklVekkxTmlJc0ltaDBkSEJ6T2k4dmJXVmxjMmh2TG1OdmJTOXBjMjlmWTI5MWJuUnllVjlqYjJSbElqb2lTVTRpTENKb2RIUndjem92TDIxbFpYTm9ieTVqYjIwdmRtVnljMmx2YmlJNklqRWlMQ0owZVhBaU9pSktWMVFpZlEuZXlKbGVIQWlPakU1TkRVek16STVOemdzSW1oMGRIQnpPaTh2YldWbGMyaHZMbU52YlM5aGJtOXVlVzF2ZFhOZmRYTmxjbDlwWkNJNkltTTVZbUk0WVRVekxUSXhaVE10TkRkallTMWlOamMwTFdGalpURXpOekZtWVRVM01TSXNJbWgwZEhCek9pOHZiV1ZsYzJodkxtTnZiUzlwYm5OMFlXNWpaVjlwWkNJNkltUTNNVGc1TW1OaFlUZ3laalE1TlRFNVpqUmhNek5oTUdVd1lqZzNaamN3SWl3aWFXRjBJam94TnpnM05qVXlPVGM0ZlEuLUN6TXktTEJ2VHpGV042VlROMDNKdzItLXhiX0lqSU9VZmpJRTk4eWlQUSIsInhvIjoiIn0="

MEESHO_RSA_PUBKEY_B64 = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAslmrLKGRzVnAtii3o89yI33FXZoRfBJV89PaCTp9Mxu7FgAaAOtaOnB2xWGG2a6Rz6zRzKPilRdAsm5oBW8mm8Uzvt7mbf7c7pjfBrjNdnKji/9/zM3fpjh364/GwG3OpyYngD49i09ySljA7Elh97Pp+QJH2z25Xv2eRSHJPizgQ8TE1bJkP9fd9JcfpGFyeEJX1bUIbgRlfED2TpJKGeaEfZ9no5+i/rgCaIRO9t86UqgeVJyCyJLnUkrU/ARPj9q/AijJV9kvyPT137UQLO+Cl6nZYOglqGcPnRbGiW6WM7imkSxR2XBn6N4ojf49nJOwnN826hkdH5JaPJ1pAQIDAQAB"

KEY_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=50)

USER_ACCOUNTS_FILE = "user_accounts.json"
OTP_SESSIONS_FILE = "otp_sessions.json"

def load_json_file(f, d):
    try:
        with open(f, 'r') as fh:
            return json.load(fh)
    except:
        return d

def save_json_file(f, d):
    with open(f, 'w') as fh:
        json.dump(d, fh)

def load_user_accounts():
    return load_json_file(USER_ACCOUNTS_FILE, {})

def save_user_accounts(d):
    save_json_file(USER_ACCOUNTS_FILE, d)

def load_otp_sessions():
    return load_json_file(OTP_SESSIONS_FILE, {})

def save_otp_sessions(d):
    save_json_file(OTP_SESSIONS_FILE, d)

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
    if value is None: return fallback
    if isinstance(value, (int, float)): return value if value > 0 else fallback
    if isinstance(value, str):
        try: return float(value.replace("₹","").replace(",","").strip())
        except: return fallback
    if isinstance(value, dict):
        for k in ["value","selling_price","price","mrp"]:
            if value.get(k): return extract_price(value[k], fallback)
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
                price = extract_price(c.get("price")) or random.randint(99,999)
                mrp = extract_price(c.get("mrp")) or price*2
                products.append({"id":str(c.get("id","")),"name":c.get("name","Product"),"price":int(price),"mrp":int(mrp),"rating":c.get("rating") or random.choice([3.8,4.0,4.2,4.5]),"image":c.get("image") or random.choice(PRODUCT_IMAGES)})
            return {"ok":True,"products":products,"page":page,"has_next":len(products)==limit}
    except: pass
    fallback = [{"id":str(random.randint(1000,9999)),"name":f"{query} {i+1}","price":random.randint(99,999),"mrp":random.randint(200,2000),"rating":random.choice([3.8,4.0,4.2,4.5]),"image":random.choice(PRODUCT_IMAGES)} for i in range(limit)]
    return {"ok":True,"products":fallback,"page":page,"has_next":False}

# ============ OTPLESS SEND OTP ============
def send_otp_otpless(phone):
    ts_id = f"{uuid.uuid4()}-{int(time.time()*1000)}"
    in_id = f"{uuid.uuid4()}-{int(time.time()*1000)}"
    
    try:
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
            },
            timeout=10
        )
        if state_resp.status_code != 200:
            return {"ok": False, "message": "State failed"}
        
        state = state_resp.json().get("state")
        if not state:
            return {"ok": False, "message": "No state"}
        
        device_info = {"platform":"android","vendor":"motorola","language":"en-IN","screenWidth":1080,"screenHeight":2225,"timezoneOffset":330,"cpuArchitecture":"aarch64"}
        
        intent_body = {
            "selectedCountryCode":"+91","mobile":f"91{phone}",
            "silentAuthEnabled":False,"hasWhatsapp":"false","deliveryChannel":"SMS",
            "metadata":json.dumps({"appInfo":json.dumps({"platform":"android","manufacturer":"motorola","androidVersion":"31","packageName":"com.meesho.supply","model":"moto g(60)","appSignature":OTPLESS_SIGNATURE,"sdkVersion":"1.3.3"}),"deviceInfo":json.dumps(device_info),"deviceIdInfo":json.dumps({"androidId":"aa5e8c37ca4077f7","gaid":str(uuid.uuid4())})}),
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
            "otpHash":OTPLESS_HASH,"platform":"HEADLESS"
        }
        
        intent_resp = requests.post(
            f"https://user-auth.otpless.app/v3/lp/user/transaction/intent/{state}",
            headers={"user-agent":"okhttp/4.9.0","content-type":"application/json"},
            json=intent_body, timeout=15
        )
        if intent_resp.status_code != 200:
            return {"ok": False, "message": "Intent failed"}
        
        data = intent_resp.json()
        leap = data.get("quantumLeap", {})
        if not leap.get("uid") or not leap.get("channelAuthToken"):
            return {"ok": False, "message": "No leap data"}
        
        session = {
            "state": state,
            "uid": leap["uid"],
            "token": leap["channelAuthToken"],
            "as_id": leap.get("asId", ""),
            "ts_id": ts_id,
            "in_id": in_id,
            "instance_id": uuid.uuid4().hex,
            "phone": phone
        }
        
        # Save session
        sessions = load_otp_sessions()
        sessions[phone] = session
        save_otp_sessions(sessions)
        
        return {"ok": True, "message": "OTP sent", "session": session}
    except Exception as e:
        return {"ok": False, "message": str(e)}

# ============ OTPLESS VERIFY OTP ============
def verify_otp_otpless(phone, otp):
    sessions = load_otp_sessions()
    session = sessions.get(phone)
    if not session:
        return {"ok": False, "message": "No session found. OTP bhejo pehle."}
    
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
            "otpHash":OTPLESS_HASH,"platform":"HEADLESS"
        }
        
        verify_resp = requests.post(
            f"https://user-auth.otpless.app/v3/lp/user/transaction/otp/{session['state']}",
            headers={"user-agent":"okhttp/4.9.0","content-type":"application/json"},
            json=otp_body, timeout=15
        )
        if verify_resp.status_code != 200:
            return {"ok": False, "message": "OTP verify failed"}
        
        data = verify_resp.json()
        one_tap = data.get("oneTap", {})
        token = one_tap.get("token")
        id_token = (one_tap.get("merchantUserInfo", {})).get("idToken")
        
        if not token or not id_token:
            return {"ok": False, "message": "No token"}
        
        key = "".join(secrets.choice(KEY_CHARSET) for _ in range(16))
        iv = os.urandom(12)
        ct = AESGCM(key[:16].encode()).encrypt(iv, id_token.encode(), None)
        encrypted_id_token = base64.b64encode(iv + ct).decode()
        
        pub = serialization.load_der_public_key(base64.b64decode(MEESHO_RSA_PUBKEY_B64))
        encrypted_key = base64.b64encode(pub.encrypt(key.encode(), padding.PKCS1v15())).decode()
        
        login_body = {
            "login_type":"otpless",
            "otpless":{"token":token,"id_token":encrypted_id_token,"aes_key_encrypted":encrypted_key,"version":"v2"},
            "ga_id":str(uuid.uuid4())
        }
        
        dev = random.choice(DEVICES)
        headers = {
            "authorization":MEESHO_AUTH,"app-version":APP_VERSION,
            "app-version-code":APP_VERSION_CODE,"instance-id":session["instance_id"],
            "country-iso":"in","application-id":"com.meesho.supply",
            "app-session-id":str(uuid.uuid4()),"app-sdk-version":"34",
            "app-client-id":"android","xo":ANON_XO,
            "meesho-user-context":"anonymous","content-type":"application/json; charset=UTF-8",
            "user-agent":"Dalvik/2.1.0",
        }
        
        login_resp = requests.post(f"{MEESHO_API}/2.0/user/login", headers=headers, json=login_body, timeout=20)
        if login_resp.status_code != 200:
            return {"ok": False, "message": "Meesho login failed"}
        
        data = login_resp.json()
        user = data.get("user", {})
        xo_data = data.get("xoox", {})
        
        account = {
            "phone": user.get("phone", phone),
            "user_id": user.get("user_id", ""),
            "xo": xo_data.get("xo", ""),
            "is_new": user.get("new", False),
        }
        
        # Save account
        accounts = load_user_accounts()
        user_id = session.get("user_id", "default")
        if user_id not in accounts:
            accounts[user_id] = []
        if not any(a["phone"] == phone for a in accounts[user_id]):
            accounts[user_id].append({"phone": phone, "login_time": time.strftime("%Y-%m-%d %H:%M:%S")})
        save_user_accounts(accounts)
        
        # Clean session
        del sessions[phone]
        save_otp_sessions(sessions)
        
        return {"ok": True, "account": account}
    except Exception as e:
        return {"ok": False, "message": str(e)}

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
            self._json({"ok": True, "bucket": random.choice([75,90,100,120,135,150]), "device": dev["model"]})
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
        
        if parsed.path == '/api/send_otp':
            phone = body.get('phone', '')
            user_id = body.get('user_id', '')
            result = send_otp_otpless(phone)
            if result.get("ok"):
                sessions = load_otp_sessions()
                if phone in sessions:
                    sessions[phone]["user_id"] = user_id
                    save_otp_sessions(sessions)
            self._json(result)
        
        elif parsed.path == '/api/verify_otp':
            phone = body.get('phone', '')
            otp = body.get('otp', '')
            result = verify_otp_otpless(phone, otp)
            self._json(result)
        
        elif parsed.path == '/api/login':
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
    logger.info(f"Running on {port}")
    HTTPServer(('0.0.0.0', port), APIHandler).serve_forever()
