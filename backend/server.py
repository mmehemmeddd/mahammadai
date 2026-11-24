import os
import json
import time
import hmac
import hashlib
import base64
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

PORT = 3000
SECRET_KEY = b"mahammad-offline-ai-ultra-secure-key-2026"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
USERS_FILE = os.path.join(BASE_DIR, "users.json")

# users.json oxu və yaz
def read_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

# Şifrə Hash-ləmə (Salt + PBKDF2 HMAC SHA256)
def hash_password(password, salt=None):
    if not salt:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"{salt}:{pwd_hash}"

def verify_password(password, stored_hash):
    try:
        salt, pwd_hash = stored_hash.split(":")
        calc_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
        return hmac.compare_digest(pwd_hash, calc_hash)
    except Exception:
        return False

# Sadə və Təhlükəsiz JWT / İmzalanmış Token
def generate_token(user_id, email, name):
    payload = {
        "id": user_id,
        "email": email,
        "name": name,
        "exp": int(time.time()) + (7 * 24 * 3600)
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(SECRET_KEY, payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"

def verify_token(token):
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, signature = parts
        expected_sig = hmac.new(SECRET_KEY, payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

# Xüsusi HTTP Server Handler
class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        
        # 1. GET /api/me
        if parsed.path == "/api/me":
            auth_header = self.headers.get("Authorization", "")
            token = auth_header.replace("Bearer ", "").strip() if "Bearer " in auth_header else ""
            user_data = verify_token(token)
            
            if not user_data:
                return self._send_json(401, {"error": "Giriş icazəsi yoxdur və ya sessiya bitib."})
            
            users = read_users()
            user = next((u for u in users if u["id"] == user_data["id"]), None)
            if not user:
                return self._send_json(404, {"error": "İstifadəçi tapılmadı."})
                
            return self._send_json(200, {
                "user": {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "createdAt": user.get("createdAt", "")
                }
            })
            
        # 2. Ana səhifə yönləndirməsi
        if parsed.path == "/" or parsed.path == "":
            self.path = "/index.html"

        # Digər statik fayllar (index.html, qurasdir.bat və s.)
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        
        try:
            req_data = json.loads(body)
        except Exception:
            return self._send_json(400, {"error": "JSON formatı yanlışdır."})

        # 1. POST /api/register
        if parsed.path == "/api/register":
            name = req_data.get("name", "").strip()
            email = req_data.get("email", "").strip().lower()
            password = req_data.get("password", "")

            if not name or not email or not password:
                return self._send_json(400, {"error": "Ad, email və şifrə daxil edilməlidir."})
            if len(password) < 6:
                return self._send_json(400, {"error": "Şifrə minimum 6 simvol olmalıdır."})

            users = read_users()
            if any(u["email"] == email for u in users):
                return self._send_json(400, {"error": "Bu email artıq qeydiyyatdan keçib."})

            new_user = {
                "id": f"usr_{int(time.time())}_{os.urandom(3).hex()}",
                "name": name,
                "email": email,
                "passwordHash": hash_password(password),
                "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            users.append(new_user)
            save_users(users)

            token = generate_token(new_user["id"], new_user["email"], new_user["name"])
            return self._send_json(201, {
                "message": "Qeydiyyat uğurla tamamlandı!",
                "token": token,
                "user": {
                    "id": new_user["id"],
                    "name": new_user["name"],
                    "email": new_user["email"],
                    "createdAt": new_user["createdAt"]
                }
            })

        # 2. POST /api/login
        if parsed.path == "/api/login":
            email = req_data.get("email", "").strip().lower()
            password = req_data.get("password", "")

            if not email or not password:
                return self._send_json(400, {"error": "Email və şifrə daxil edilməlidir."})

            users = read_users()
            user = next((u for u in users if u["email"] == email), None)

            if not user or not verify_password(password, user["passwordHash"]):
                return self._send_json(401, {"error": "Email və ya şifrə yanlışdır."})

            token = generate_token(user["id"], user["email"], user["name"])
            return self._send_json(200, {
                "message": "Uğurla daxil oldunuz!",
                "token": token,
                "user": {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "createdAt": user.get("createdAt", "")
                }
            })

        return self._send_json(404, {"error": "Endpoint tapılmadı."})

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), AppHandler)
    print("=" * 60)
    print("🛡️  MAHAMMAD OFFLINE AI BACKEND AKTİVDİR! (Python Mühərriki)")
    print(f"👉 Server ünvanı: http://localhost:{PORT}")
    print(f"👉 Veb interfeys: http://localhost:{PORT}/index.html")
    print("👉 Heç bir əlavə quraşdırma tələb olunmur!")
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server dayandırıldı.")
