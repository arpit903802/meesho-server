import json, random, requests, os, time, uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

MEESHO_API = "https://prod.meeshoapi.com/api"
MEESHO_AUTH = "32c4d8137cn9eb493a1921f203173080"
ANON_XO = "eyJ0eXBlIjoiY29tcG9zaXRlIn0=.eyJqd3QiOiJleUpoYkdjaU9pSklVekkxTmlJc0ltaDBkSEJ6T2k4dmJXVmxjMmh2TG1OdmJTOXBjMjlmWTI5MWJuUnllVjlqYjJSbElqb2lTVTRpTENKb2RIUndjem92TDIxbFpYTm9ieTVqYjIwdmRtVnljMmx2YmlJNklqRWlMQ0owZVhBaU9pSktWMVFpZlEuZXlKbGVIQWlPakU1TkRVek16STVOemdzSW1oMGRIQnpPaTh2YldWbGMyaHZMbU52YlM5aGJtOXVlVzF2ZFhOZmRYTmxjbDlwWkNJNkltTTVZbUk0WVRVekxUSXhaVE10TkRkallTMWlOamMwTFdGalpURXpOekZtWVRVM01TSXNJbWgwZEhCek9pOHZiV1ZsYzJodkxtTnZiUzlwYm5OMFlXNWpaVjlwWkNJNkltUTNNVGc1TW1OaFlUZ3laalE1TlRFNVpqUmhNek5oTUdVd1lqZzNaamN3SWl3aWFXRjBJam94TnpnM05qVXlPVGM0ZlEuLUN6TXktTEJ2VHpGV042VlROMDNKdzItLXhiX0lqSU9VZmpJRTk4eWlQUSIsInhvIjoiIn0="

OTP_SESSIONS = {}
IMAGES = ["https://picsum.photos/300/400?1","https://picsum.photos/300/400?2","https://picsum.photos/300/400?3","https://picsum.photos/300/400?4"]

def search(query, page=1):
    headers = {
        "authorization": MEESHO_AUTH, "app-version": "29.1",
        "app-version-code": "860", "instance-id": str(uuid.uuid4()),
        "country-iso": "in", "application-id": "com.meesho.supply",
        "app-session-id": str(uuid.uuid4()), "app-sdk-version": "34",
        "app-client-id": "android", "xo": ANON_XO,
        "meesho-user-context": "anonymous", "content-type": "application/json",
        "user-agent": "Dalvik/2.1.0", "app-gaid": str(uuid.uuid4()), "app-session-count": "1"
    }
    body = {"filter": {"type": "text_search", "query": query}, "offset": (page-1)*20, "limit": 20}
    try:
        r = requests.post(f"{MEESHO_API}/3.0/anonymous/catalogs", headers=headers, json=body, timeout=10)
        if r.status_code == 200:
            products = []
            for c in r.json().get("catalogs", []):
                p = c.get("price") or random.randint(99,999)
                m = c.get("mrp") or p*2
                if isinstance(p, dict): p = random.randint(99,999)
                if isinstance(m, dict): m = p*2
                products.append({"id": str(c.get("id","")), "name": c.get("name","Product"), "price": int(p), "mrp": int(m), "rating": c.get("rating") or 4.0, "image": c.get("image") or random.choice(IMAGES)})
            return {"ok": True, "products": products, "has_next": len(products)==20}
    except: pass
    fb = [{"id": str(i), "name": f"{query} {i}", "price": random.randint(99,999), "mrp": random.randint(200,2000), "rating": 4.0, "image": random.choice(IMAGES)} for i in range(20)]
    return {"ok": True, "products": fb, "has_next": False}

def send_otp(phone, user_id):
    ts_id = f"{uuid.uuid4()}-{int(time.time()*1000)}"
    in_id = f"{uuid.uuid4()}-{int(time.time()*1000)}"
    try:
        sr = requests.get("https://user-auth.otpless.app/v2/state", params={
            "origin":"https://otpless.com","version":"V3","tsId":ts_id,"inId":in_id,
            "isHeadless":"true","platform":"android","isLoginPage":"false",
            "packageName":"com.meesho.supply","appId":"XN07RN1IQC548C9YK5I4",
            "loginUri":"otpless.xn07rn1iqc548c9yk5i4://otpless",
            "deviceInfo":json.dumps({"platform":"android","vendor":"motorola","language":"en-IN","screenWidth":1080,"screenHeight":2225,"timezoneOffset":330,"cpuArchitecture":"aarch64"})
        }, timeout=10)
        if sr.status_code != 200: return {"ok":False,"message":"State failed"}
        state = sr.json().get("state")
        if not state: return {"ok":False,"message":"No state"}
        
        di = {"platform":"android","vendor":"motorola","language":"en-IN","screenWidth":1080,"screenHeight":2225,"timezoneOffset":330,"cpuArchitecture":"aarch64"}
        ib = {
            "selectedCountryCode":"+91","mobile":f"91{phone}","silentAuthEnabled":False,
            "hasWhatsapp":"false","deliveryChannel":"SMS",
            "metadata":json.dumps({"appInfo":json.dumps({"platform":"android","manufacturer":"motorola","androidVersion":"31","packageName":"com.meesho.supply","model":"moto g(60)","appSignature":"oBcOM6bXKNcqouiPFcR1ur60Z6myTuVIDNSNWuKOlzU","sdkVersion":"1.3.3"}),"deviceInfo":json.dumps(di),"deviceIdInfo":json.dumps({"androidId":"aa5e8c37ca4077f7","gaid":str(uuid.uuid4())})}),
            "triggerWebauthn":False,"telephonyInfo":{"isMobileDataOn":False,"hasReadPhoneStatePermission":False},
            "clientMetaData":json.dumps({"tid":str(uuid.uuid4())[:16]}),
            "asId":"","isViSnaWhitelisted":True,"isAirtelSnaWhitelisted":True,
            "isAutoIntent":True,"origin":"https://otpless.com","version":"V4",
            "tsId":ts_id,"inId":in_id,"deviceInfo":json.dumps(di),
            "loginUri":"otpless.xn07rn1iqc548c9yk5i4://otpless",
            "appId":"XN07RN1IQC548C9YK5I4","isHeadless":True,
            "packageName":"com.meesho.supply","package":"com.meesho.supply",
            "otpHash":"oBcOM6bXKNc","platform":"HEADLESS"
        }
        ir = requests.post(f"https://user-auth.otpless.app/v3/lp/user/transaction/intent/{state}", headers={"user-agent":"okhttp/4.9.0","content-type":"application/json"}, json=ib, timeout=15)
        if ir.status_code != 200: return {"ok":False,"message":"Intent failed"}
        leap = ir.json().get("quantumLeap", {})
        if not leap.get("uid") or not leap.get("channelAuthToken"): return {"ok":False,"message":"No leap"}
        
        OTP_SESSIONS[phone] = {"state":state,"uid":leap["uid"],"token":leap["channelAuthToken"],"as_id":leap.get("asId",""),"ts_id":ts_id,"in_id":in_id,"user_id":user_id}
        return {"ok":True,"message":"OTP sent"}
    except Exception as e:
        return {"ok":False,"message":str(e)}

def verify_otp(phone, otp):
    s = OTP_SESSIONS.get(phone)
    if not s: return {"ok":False,"message":"OTP pehle bhejo"}
    try:
        ob = {
            "selectedCountryCode":"91","mobile":phone,"otp":otp,"value":f"91{phone}",
            "isOTPAutoRead":"false","uid":s["uid"],"token":s["token"],"asId":s["as_id"],
            "origin":"https://otpless.com","version":"V4","tsId":s["ts_id"],"inId":s["in_id"],
            "deviceInfo":json.dumps({"platform":"android","vendor":"motorola","language":"en-IN","screenWidth":1080,"screenHeight":2225,"timezoneOffset":330,"cpuArchitecture":"aarch64"}),
            "loginUri":"otpless.xn07rn1iqc548c9yk5i4://otpless",
            "appId":"XN07RN1IQC548C9YK5I4","isHeadless":True,
            "packageName":"com.meesho.supply","package":"com.meesho.supply",
            "otpHash":"oBcOM6bXKNc","platform":"HEADLESS"
        }
        vr = requests.post(f"https://user-auth.otpless.app/v3/lp/user/transaction/otp/{s['state']}", headers={"user-agent":"okhttp/4.9.0","content-type":"application/json"}, json=ob, timeout=15)
        if vr.status_code != 200: return {"ok":False,"message":"OTP galat hai"}
        del OTP_SESSIONS[phone]
        return {"ok":True,"account":{"phone":phone}}
    except Exception as e:
        return {"ok":False,"message":str(e)}

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urlparse(self.path)
        q = parse_qs(p.query)
        if p.path == '/api/search':
            self._j(search(q.get('q',[''])[0], int(q.get('page',['1'])[0])))
        elif p.path == '/api/offer':
            self._j({"ok":True,"bucket":random.choice([75,90,100,120,135,150])})
        elif p.path == '/health':
            self._j({"status":"ok"})
        else:
            self._j({"ok":False},404)
    def do_POST(self):
        l = int(self.headers.get('Content-Length',0))
        b = json.loads(self.rfile.read(l) or b'{}')
        p = urlparse(self.path)
        if p.path == '/api/send_otp':
            self._j(send_otp(b.get('phone',''), b.get('user_id','')))
        elif p.path == '/api/verify_otp':
            self._j(verify_otp(b.get('phone',''), b.get('otp','')))
        else:
            self._j({"ok":False},404)
    def _j(self, d, s=200):
        self.send_response(s)
        self.send_header('Content-Type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps(d).encode())
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), H).serve_forever()
