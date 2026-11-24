import os
import json
import time
import hmac
import hashlib
import base64
import sqlite3
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get("PORT", 3000))
SECRET_KEY = b"mahammad-offline-ai-ultra-secure-key-2026"
GOOGLE_CLIENT_ID = "427833067127-jaq0aob8eismkafbitvj70a56padb7l2.apps.googleusercontent.com"
ADMIN_SECRET_KEY = os.environ.get("ADMIN_KEY", "admin12345")
DEFAULT_GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("gemini") or os.environ.get("GEMINI") or ""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DB_FILE = os.path.join(BASE_DIR, "database.sqlite")
LEGACY_USERS_FILE = os.path.join(BASE_DIR, "users.json")

# SQLite Database Sazlaması və Miqrasiya
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            avatar TEXT,
            bio TEXT,
            auth_provider TEXT DEFAULT 'email',
            createdAt TEXT
        )
    """)
    conn.commit()

    # Köhnə users.json varsa və baza boşdursa köçür
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    if count == 0 and os.path.exists(LEGACY_USERS_FILE):
        try:
            with open(LEGACY_USERS_FILE, "r", encoding="utf-8") as f:
                legacy = json.load(f)
                for u in legacy:
                    c.execute("""
                        INSERT OR IGNORE INTO users (id, name, email, password_hash, avatar, bio, auth_provider, createdAt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        u.get("id") or f"usr_{int(time.time())}_{os.urandom(3).hex()}",
                        u.get("name", "İstifadəçi"),
                        u.get("email"),
                        u.get("passwordHash"),
                        u.get("avatar"),
                        u.get("bio", ""),
                        u.get("auth_provider", "email"),
                        u.get("createdAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    ))
            conn.commit()
        except Exception:
            pass
    conn.close()

init_db()

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

# JWT / Token Yaradılması və Doğrulanması
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

# Google ID Token Doğrulaması
def verify_google_token(id_token):
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(id_token)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mahammad-AI-Python"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("error_description") or data.get("error"):
                return None, data.get("error_description") or data.get("error")
            if data.get("aud") != GOOGLE_CLIENT_ID:
                return None, "Google Client ID uyğun gəlmir."
            return data, None
    except Exception as e:
        return None, str(e)

# Gemini API Çağırışı
def call_gemini_api(effective_key, target_model, messages, system_prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={effective_key}"
    
    formatted_contents = []
    if isinstance(messages, list):
        for msg in messages:
            r = msg.get("role", "user")
            role = "model" if r == "assistant" else ("user" if r == "system" else r)
            formatted_contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}]
            })
    
    if not formatted_contents:
        formatted_contents = [{"role": "user", "parts": [{"text": "Salam"}]}]
        
    req_body = {
        "contents": formatted_contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }
    if system_prompt:
        req_body["system_instruction"] = {
            "parts": [{"text": system_prompt}]
        }
        
    data_bytes = json.dumps(req_body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json", "User-Agent": "Mahammad-AI-Python"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if "error" in res_data:
                return None, res_data["error"].get("message", "Açar etibarsızdır və ya kvota bitib.")
            candidates = res_data.get("candidates", [])
            reply_text = "Cavab alına bilmədi."
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts:
                    reply_text = parts[0].get("text", "")
            return reply_text, None
    except urllib.error.HTTPError as e:
        try:
            err_json = json.loads(e.read().decode("utf-8"))
            return None, err_json.get("error", {}).get("message", e.reason)
        except Exception:
            return None, f"HTTP Xətası {e.code}: {e.reason}"
    except Exception as e:
        return None, str(e)

# Xüsusi HTTP Server Handler
class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-admin-key")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-admin-key")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()

    def get_auth_user(self):
        auth_header = self.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip() if "Bearer " in auth_header else ""
        return verify_token(token)

    def check_admin(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        admin_key = self.headers.get("x-admin-key") or (qs.get("admin_key", [None])[0])
        return admin_key == ADMIN_SECRET_KEY

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. GET /api/me
        if path == "/api/me":
            user_data = self.get_auth_user()
            if not user_data:
                return self._send_json(401, {"error": "Giriş icazəsi yoxdur və ya sessiya bitib."})
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id, name, email, avatar, bio, auth_provider, createdAt FROM users WHERE id = ?", (user_data["id"],))
            row = c.fetchone()
            conn.close()
            if not row:
                return self._send_json(404, {"error": "İstifadəçi tapılmadı."})
            return self._send_json(200, {"user": dict(row)})

        # 2. GET /api/profile
        if path == "/api/profile":
            user_data = self.get_auth_user()
            if not user_data:
                return self._send_json(401, {"error": "Giriş icazəsi yoxdur və ya sessiya bitib."})
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id, name, email, avatar, bio, auth_provider, createdAt FROM users WHERE id = ?", (user_data["id"],))
            row = c.fetchone()
            conn.close()
            if not row:
                return self._send_json(404, {"error": "İstifadəçi tapılmadı."})
            return self._send_json(200, {"user": dict(row)})

        # 3. GET /api/admin/stats
        if path == "/api/admin/stats":
            if not self.check_admin():
                return self._send_json(403, {"error": "Admin icazəsi yoxdur."})
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            total = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE auth_provider = 'google'")
            google_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE auth_provider = 'email' OR auth_provider IS NULL")
            email_count = c.fetchone()[0]
            c.execute("SELECT createdAt FROM users ORDER BY createdAt DESC LIMIT 1")
            latest_row = c.fetchone()
            conn.close()
            latest = latest_row[0] if latest_row else None
            return self._send_json(200, {
                "stats": {
                    "totalUsers": total,
                    "googleUsers": google_count,
                    "emailUsers": email_count,
                    "latestRegistration": latest
                }
            })

        # 4. GET /api/admin/users
        if path == "/api/admin/users":
            if not self.check_admin():
                return self._send_json(403, {"error": "Admin icazəsi yoxdur."})
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id, name, email, avatar, bio, auth_provider, createdAt FROM users ORDER BY createdAt DESC")
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            return self._send_json(200, {"users": rows})

        # Ana səhifə yönləndirməsi
        if path == "/" or path == "":
            self.path = "/index.html"

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            req_data = json.loads(body)
        except Exception:
            return self._send_json(400, {"error": "JSON formatı yanlışdır."})

        # 1. POST /api/register
        if path == "/api/register":
            name = req_data.get("name", "").strip()
            email = req_data.get("email", "").strip().lower()
            password = req_data.get("password", "")

            if not name or not email or not password:
                return self._send_json(400, {"error": "Ad, email və şifrə daxil edilməlidir."})
            if len(password) < 6:
                return self._send_json(400, {"error": "Şifrə minimum 6 simvol olmalıdır."})

            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE email = ?", (email,))
            if c.fetchone():
                conn.close()
                return self._send_json(400, {"error": "Bu email artıq qeydiyyatdan keçib."})

            user_id = f"usr_{int(time.time())}_{os.urandom(3).hex()}"
            pwd_hash = hash_password(password)
            created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")

            c.execute("""
                INSERT INTO users (id, name, email, password_hash, avatar, bio, auth_provider, createdAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, name, email, pwd_hash, None, "", "email", created_at))
            conn.commit()
            conn.close()

            token = generate_token(user_id, email, name)
            return self._send_json(201, {
                "message": "Qeydiyyat uğurla tamamlandı!",
                "token": token,
                "user": {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "avatar": None,
                    "bio": "",
                    "auth_provider": "email",
                    "createdAt": created_at
                }
            })

        # 2. POST /api/login
        if path == "/api/login":
            email = req_data.get("email", "").strip().lower()
            password = req_data.get("password", "")

            if not email or not password:
                return self._send_json(400, {"error": "Email və şifrə daxil edilməlidir."})

            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = c.fetchone()
            conn.close()

            if not row or not row["password_hash"] or not verify_password(password, row["password_hash"]):
                return self._send_json(401, {"error": "Email və ya şifrə yanlışdır."})

            token = generate_token(row["id"], row["email"], row["name"])
            return self._send_json(200, {
                "message": "Uğurla daxil oldunuz!",
                "token": token,
                "user": {
                    "id": row["id"],
                    "name": row["name"],
                    "email": row["email"],
                    "avatar": row["avatar"],
                    "bio": row["bio"],
                    "auth_provider": row["auth_provider"],
                    "createdAt": row["createdAt"]
                }
            })

        # 3. POST /api/auth/google
        if path == "/api/auth/google":
            credential = req_data.get("credential")
            if not credential:
                return self._send_json(400, {"error": "Google credential token tələb olunur."})

            payload, err = verify_google_token(credential)
            if err or not payload:
                return self._send_json(400, {"error": f"Google token doğrulanmadı: {err}"})

            email = payload.get("email", "").lower()
            name = payload.get("name") or email.split("@")[0]
            picture = payload.get("picture")

            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = c.fetchone()

            if row:
                user_id = row["id"]
                if not row["avatar"] and picture:
                    c.execute("UPDATE users SET avatar = ? WHERE id = ?", (picture, user_id))
                    conn.commit()
                name = row["name"]
                created_at = row["createdAt"]
                avatar = picture if not row["avatar"] else row["avatar"]
                bio = row["bio"]
                provider = row["auth_provider"]
            else:
                user_id = f"goog_{int(time.time())}_{os.urandom(3).hex()}"
                created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                bio = ""
                provider = "google"
                avatar = picture
                c.execute("""
                    INSERT INTO users (id, name, email, password_hash, avatar, bio, auth_provider, createdAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, name, email, None, avatar, bio, provider, created_at))
                conn.commit()

            conn.close()
            token = generate_token(user_id, email, name)
            return self._send_json(200, {
                "message": "Google ilə uğurla daxil oldunuz!",
                "token": token,
                "user": {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "avatar": avatar,
                    "bio": bio,
                    "auth_provider": provider,
                    "createdAt": created_at
                }
            })

        # 4. POST /api/chat (Gemini API Entegrasiyası)
        if path == "/api/chat":
            provider = req_data.get("provider", "gemini")
            if provider != "gemini":
                return self._send_json(400, {"error": 'Yalnız "gemini" provayderi server üzərindən qəbul edilir. Lokal Ollama üçün birbaşa localhost:11434 istifadə olunur.'})

            model = req_data.get("model") or "gemini-1.5-flash"
            messages = req_data.get("messages", [])
            system_prompt = req_data.get("systemPrompt", "")
            api_key = req_data.get("apiKey") or os.environ.get("GEMINI_API_KEY") or DEFAULT_GEMINI_KEY

            if not api_key:
                return self._send_json(400, {
                    "error": "Gemini API açarı tapılmadı! Zəhmət olmasa Google AI Studio-dan (https://aistudio.google.com) pulsuz API açarı əldə edərək interfeysdə daxil edin və ya serverdə GEMINI_API_KEY mühit dəyişənini təyin edin."
                })

            reply_text, err = call_gemini_api(api_key, model, messages, system_prompt)
            if err:
                return self._send_json(400, {"error": f"Gemini API Xətası: {err}"})

            return self._send_json(200, {
                "reply": reply_text,
                "model": model,
                "provider": "gemini"
            })

        return self._send_json(404, {"error": "Endpoint tapılmadı."})

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. PUT /api/profile
        if path == "/api/profile":
            user_data = self.get_auth_user()
            if not user_data:
                return self._send_json(401, {"error": "Giriş icazəsi yoxdur və ya sessiya bitib."})

            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
            try:
                req_data = json.loads(body)
            except Exception:
                return self._send_json(400, {"error": "JSON formatı yanlışdır."})

            name = req_data.get("name", "").strip()
            avatar = req_data.get("avatar", "").strip()
            bio = req_data.get("bio", "").strip()
            old_pwd = req_data.get("oldPassword")
            new_pwd = req_data.get("newPassword")

            if not name:
                return self._send_json(400, {"error": "Ad boş ola bilməz."})

            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE id = ?", (user_data["id"],))
            user = c.fetchone()

            if not user:
                conn.close()
                return self._send_json(404, {"error": "İstifadəçi tapılmadı."})

            new_password_hash = user["password_hash"]
            if new_pwd:
                if user["auth_provider"] == "google":
                    conn.close()
                    return self._send_json(400, {"error": "Google ilə daxil olan hesabların şifrəsi dəyişdirilə bilməz."})
                if not old_pwd or not verify_password(old_pwd, user["password_hash"]):
                    conn.close()
                    return self._send_json(400, {"error": "Cari (köhnə) şifrə yanlışdır."})
                if len(new_pwd) < 6:
                    conn.close()
                    return self._send_json(400, {"error": "Yeni şifrə minimum 6 simvol olmalıdır."})
                new_password_hash = hash_password(new_pwd)

            c.execute("""
                UPDATE users SET name = ?, avatar = ?, bio = ?, password_hash = ?
                WHERE id = ?
            """, (name, avatar or None, bio, new_password_hash, user_data["id"]))
            conn.commit()

            c.execute("SELECT id, name, email, avatar, bio, auth_provider, createdAt FROM users WHERE id = ?", (user_data["id"],))
            updated_user = dict(c.fetchone())
            conn.close()

            return self._send_json(200, {
                "message": "Profil məlumatları yeniləndi!",
                "user": updated_user
            })

        return self._send_json(404, {"error": "Endpoint tapılmadı."})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # DELETE /api/admin/users/<id>
        if path.startswith("/api/admin/users/"):
            if not self.check_admin():
                return self._send_json(403, {"error": "Admin icazəsi yoxdur."})
            user_id = path.replace("/api/admin/users/", "").strip()
            if not user_id:
                return self._send_json(400, {"error": "İstifadəçi ID göstərilməyib."})
            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            return self._send_json(200, {"message": "İstifadəçi uğurla silindi."})

        return self._send_json(404, {"error": "Endpoint tapılmadı."})

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), AppHandler)
    print("=" * 65)
    print("🛡️  MAHAMMAD OFFLINE AI BACKEND AKTİVDİR! (Python Mühərriki)")
    print(f"👉 Server ünvanı: http://localhost:{PORT}")
    print(f"👉 Veb interfeys: http://localhost:{PORT}/index.html")
    print(f"👉 Admin Panel:   http://localhost:{PORT}/admin.html")
    print("👉 SQLite + Google Auth + Admin + Gemini API Dəstəklənir!")
    print("=" * 65)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server dayandırıldı.")
