import os
import json
import re
import time
import requests
import streamlit as st

# Configure Streamlit Page
st.set_page_config(
    page_title="Mahammad - Cyber & Bug Bounty Tutor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean, warm paper & sage green UI
st.markdown("""
<style>
    :root {
        --bg-main: #FAF6EE;
        --surface: #FFFDF9;
        --bg-secondary: #F2ECE1;
        --text-primary: #232621;
        --text-secondary: #5C6258;
        --border-color: #E3DDD1;
        --accent: #2F6F5E;
        --accent-hover: #24574A;
        --user-bubble-bg: #EBF3EE;
        --user-bubble-text: #1B3B32;
        --user-bubble-border: #C6DDD0;
        --code-bg: #F3EFE6;
        --code-border: #D6CFC2;
        --inline-code-bg: #EAE4D7;
        --status-success-text: #2B6E44;
        --status-success-bg: #EDF7F0;
        --status-warning-text: #9A5B13;
        --status-warning-bg: #FDF5E7;
        --status-error-text: #A63A3A;
        --status-error-bg: #FBECEC;
    }

    /* Main Application Canvas */
    .stApp {
        background-color: var(--bg-main) !important;
        color: var(--text-primary) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Charter", "Georgia", serif, sans-serif !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: var(--surface) !important;
        border-right: 1px solid var(--border-color) !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] * {
        color: var(--text-primary);
    }
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] p.caption {
        color: var(--text-secondary) !important;
    }

    /* Headers and Text */
    .main-title {
        font-size: 1.95rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.01em;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 0.95rem;
        color: var(--text-secondary);
        margin-bottom: 1.25rem;
        line-height: 1.5;
    }
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }
    p, span, label {
        color: var(--text-primary);
    }
    .stCaption, p.caption, small {
        color: var(--text-secondary) !important;
    }

    /* User Message Bubble */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
    [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]),
    .stChatMessage[data-testid*="user"] {
        background-color: var(--user-bubble-bg) !important;
        color: var(--user-bubble-text) !important;
        border: 1px solid var(--user-bubble-border) !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        margin-bottom: 12px !important;
        box-shadow: none !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p,
    .stChatMessage[data-testid*="user"] p {
        color: var(--user-bubble-text) !important;
    }

    /* Assistant Message Bubble */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
    [data-testid="stChatMessage"]:has([aria-label="Chat message from assistant"]),
    .stChatMessage[data-testid*="assistant"] {
        background-color: var(--surface) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        box-shadow: none !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) p,
    .stChatMessage[data-testid*="assistant"] p {
        color: var(--text-primary) !important;
    }

    /* Code Blocks */
    pre, code, .stCodeBlock {
        background-color: var(--code-bg) !important;
        color: #1F241E !important;
        border: 1px solid var(--code-border) !important;
        border-radius: 6px !important;
    }
    code:not(pre code) {
        background-color: var(--inline-code-bg) !important;
        color: #1F241E !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        border: 1px solid var(--code-border) !important;
        font-size: 0.88em !important;
    }

    /* Primary Accent Buttons */
    button[kind="primary"], .stButton > button[kind="primary"] {
        background-color: var(--accent) !important;
        color: #FFFDF9 !important;
        border: 1px solid var(--accent) !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        transition: background-color 0.15s ease-in-out !important;
        box-shadow: none !important;
    }
    button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {
        background-color: var(--accent-hover) !important;
        border-color: var(--accent-hover) !important;
        color: #FFFFFF !important;
    }

    /* Secondary Buttons */
    .stButton > button:not([kind="primary"]) {
        background-color: var(--surface) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        box-shadow: none !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background-color: var(--bg-secondary) !important;
        border-color: var(--border-color) !important;
        color: var(--text-primary) !important;
    }

    /* Form Inputs and Select Boxes */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    textarea.stTextArea {
        background-color: var(--surface) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        color: var(--text-primary) !important;
        box-shadow: none !important;
    }
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    textarea.stTextArea:focus {
        border-color: var(--accent) !important;
    }

    /* Chat Input Area */
    [data-testid="stChatInput"] {
        background-color: var(--surface) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] textarea {
        color: var(--text-primary) !important;
        background-color: transparent !important;
    }

    /* Badges */
    .badge-privacy {
        display: inline-block;
        background-color: var(--bg-secondary);
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 0.78rem;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .badge-rag {
        display: inline-block;
        background-color: #EBF3EE;
        color: #1B3B32;
        border: 1px solid #C6DDD0;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 0.78rem;
        font-weight: 500;
        margin-bottom: 8px;
    }

    /* Custom Cards */
    .quiz-card {
        background-color: var(--surface);
        border: 1px solid var(--border-color);
        padding: 16px 18px;
        border-radius: 8px;
        margin-bottom: 14px;
        box-shadow: none !important;
    }
    .quiz-explanation {
        background-color: var(--bg-secondary);
        border-left: 3px solid var(--accent);
        border-radius: 4px;
        padding: 10px 14px;
        margin-top: 10px;
        font-size: 0.92rem;
        color: var(--text-primary);
    }
    .note-card {
        background-color: var(--surface);
        border: 1px solid var(--border-color);
        border-left: 3px solid var(--accent);
        padding: 14px 16px;
        border-radius: 6px;
        margin-bottom: 12px;
        box-shadow: none !important;
    }
    .mistake-card {
        background-color: var(--surface);
        border: 1px solid var(--border-color);
        border-left: 3px solid var(--status-error-text);
        padding: 14px 16px;
        border-radius: 6px;
        margin-bottom: 12px;
        box-shadow: none !important;
    }
    .hint-card {
        background-color: var(--status-warning-bg);
        border: 1px solid var(--border-color);
        border-left: 3px solid var(--status-warning-text);
        padding: 10px 14px;
        border-radius: 6px;
        margin-top: 8px;
        font-size: 0.92rem;
        color: var(--text-primary);
    }

    /* Alerts / Notifications */
    .stAlert {
        border-radius: 6px !important;
        box-shadow: none !important;
        border: 1px solid var(--border-color) !important;
        background-color: var(--surface) !important;
    }

    /* Dividers */
    hr {
        border-color: var(--border-color) !important;
        margin: 1.2rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)


# --- Model Detection & Ollama Communication ---

def check_ollama_running(ollama_host="http://localhost:11434"):
    try:
        res = requests.get(f"{ollama_host}/api/tags", timeout=3)
        return res.status_code == 200
    except Exception:
        return False


def get_available_models(ollama_host="http://localhost:11434"):
    """
    Auto-detects installed Ollama models and prioritizes fast & educational models.
    """
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=3)
        if response.status_code == 200:
            data = response.json()
            models = [m.get("name") for m in data.get("models", []) if "name" in m]
            
            # Prioritization order: fast lightweight models first for instant responses
            priority_order = [
                "qwen2.5:1.5b", "llama3.2:1b", "qwen2.5:3b", "llama3.2:3b",
                "deepseek-r1:1.5b", "gemma3", "gemma2",
                "deepseek-coder", "llama3.1", "llama3", "mistral"
            ]
            
            def get_sort_key(model_name):
                base_name = model_name.split(":")[0].lower()
                for i, pref in enumerate(priority_order):
                    if pref in model_name.lower():
                        return i
                return len(priority_order) + 1

            sorted_models = sorted(models, key=get_sort_key)
            return sorted_models
    except Exception:
        pass
    return []


def stream_ollama_response(model: str, prompt: str, system_prompt: str, ollama_host="http://localhost:11434", temperature=0.6):
    """
    Streams response token-by-token with hardware-optimized parameters for maximum speed on CPU.
    """
    url = f"{ollama_host}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": True,
        "options": {
            "temperature": max(0.2, min(temperature, 0.7)),
            "num_ctx": 1024,      # Optimized to avoid slow CPU KV-cache creation
            "num_predict": 280,   # Concise, fast pedagogical guidance
            "top_k": 40,
            "top_p": 0.9
        }
    }
    try:
        with requests.post(url, json=payload, stream=True, timeout=90) as res:
            if res.status_code != 200:
                try:
                    err_detail = res.json().get("error", f"Status {res.status_code}")
                except Exception:
                    err_detail = f"Status {res.status_code}"
                yield f"⚠️ **Ollama Xətası:** {err_detail}\n\n*Terminalda `ollama pull {model}` əmrini yoxlayın.*"
                return

            for line in res.iter_lines(decode_unicode=True):
                if line:
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done", False):
                            break
                    except Exception:
                        continue
    except requests.exceptions.ConnectionError:
        yield "⚠️ **Əlaqə qurula bilmədi:** Ollama serveri işləmir. Zəhmət olmasa terminalda `ollama serve` başladın."
    except Exception as e:
        yield f"⚠️ **Xəta:** {str(e)}"


def query_ollama_sync(model: str, prompt: str, system_prompt: str, ollama_host="http://localhost:11434", temperature=0.3):
    """
    Synchronous request for structured outputs like Quiz JSON with fast parameters.
    """
    url = f"{ollama_host}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_ctx": 1024,
            "num_predict": 350,
            "top_k": 40,
            "top_p": 0.9
        }
    }
    try:
        res = requests.post(url, json=payload, timeout=60)
        if res.status_code == 200:
            return res.json().get("response", "").strip()
        else:
            try:
                err = res.json().get("error", f"Status {res.status_code}")
            except Exception:
                err = f"Status {res.status_code}"
            return f"Error: {err}"
    except Exception as e:
        return f"Error: {str(e)}"


# --- RAG: Document Extraction & Context Search ---

def extract_text_from_upload(uploaded_file):
    """
    Extracts text from PDF, TXT, or MD files without problematic C DLLs.
    """
    filename = uploaded_file.name.lower()
    if filename.endswith(".txt") or filename.endswith(".md"):
        try:
            return uploaded_file.read().decode("utf-8", errors="ignore")
        except Exception as e:
            return f"Xəta: Fayl oxunmadı ({str(e)})"
    elif filename.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(uploaded_file)
            text_pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_pages.append(f"[Səhifə {i+1}]\n{page_text}")
            return "\n\n".join(text_pages)
        except ImportError:
            return "PDF_IMPORT_ERROR"
        except Exception as e:
            return f"Xəta: PDF oxuna bilmədi ({str(e)})"
    return ""


def retrieve_relevant_context(document_text: str, query: str, max_chars=1200) -> str:
    """
    Retrieves the most relevant chunks matching query keywords.
    """
    if not document_text or not query:
        return ""
    
    raw_chunks = re.split(r"\n\s*\n", document_text)
    chunks = [c.strip() for c in raw_chunks if len(c.strip()) > 30]
    
    if not chunks:
        return document_text[:max_chars]
        
    query_words = set(re.findall(r"\w+", query.lower()))
    
    scored_chunks = []
    for chunk in chunks:
        chunk_words = set(re.findall(r"\w+", chunk.lower()))
        score = len(query_words.intersection(chunk_words))
        scored_chunks.append((score, chunk))
        
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    selected = []
    total_len = 0
    for score, chunk in scored_chunks:
        if total_len + len(chunk) <= max_chars:
            selected.append(chunk)
            total_len += len(chunk)
        if len(selected) >= 4:
            break
            
    if not selected:
        return document_text[:max_chars]
        
    return "\n\n---\n\n".join(selected)


def get_all_user_context() -> str:
    """
    Combines uploaded files and manually saved local notes into one unified text stream.
    """
    all_pieces = []
    if st.session_state.get("document_text"):
        doc_name = st.session_state.get("current_doc_name", "Fayl")
        all_pieces.append(f"=== SƏNƏD: {doc_name} ===\n" + st.session_state.document_text)

    for note in st.session_state.get("local_notes", []):
        all_pieces.append(f"=== ŞƏXSİ QEYD: {note.get('title', 'Başlıqsız')} ===\n" + note.get('content', ''))

    return "\n\n".join(all_pieces)


# --- Interactive Challenge Engine ("Məni Sına") ---

def generate_challenge(topic: str, subject: str, level: str, doc_context: str, model: str, ollama_active: bool):
    """
    Generates a realistic Bug Bounty / Cybersecurity challenge scenario with 3 staged hints.
    """
    system_prompt = f"""You are Mahammad Cyber & Bug Bounty Trainer. Generate a hands-on cybersecurity challenge on '{subject}' (topic: '{topic}') suitable for {level} level.
Follow this EXACT JSON structure strictly:
{{
  "title": "Short descriptive challenge title",
  "scenario": "A realistic bug bounty context (e.g. target endpoint, architecture, feature).",
  "request_or_code": "An HTTP request or source code snippet containing the flaw.",
  "objective": "The specific task for the student (e.g. identify the flaw, how to test/bypass).",
  "hint1": "Gentle nudge: which parameter or header to investigate.",
  "hint2": "Stronger clue: the logic flaw mechanism or encoding trick.",
  "hint3": "Nearly direct clue: how to construct the proof of concept.",
  "correct_solution": "The actual vulnerability explanation and root cause remediation."
}}
Output ONLY the JSON object inside ```json ``` block."""

    prompt = f"Target topic: {topic}. Context from notes: {doc_context[:600] if doc_context else 'None'}. Generate a realistic challenge."
    
    if ollama_active:
        raw_res = query_ollama_sync(model, prompt, system_prompt, temperature=0.4)
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw_res, re.DOTALL | re.IGNORECASE)
        json_str = match.group(1).strip() if match else raw_res
        json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict) and "title" in parsed:
                return parsed
        except Exception:
            pass

    # Dynamic fallback scenarios based on topic keywords
    top_lower = topic.lower()
    if "sql" in top_lower:
        return {
            "title": f"'{topic}' üzrə SQL Injection & Filter Bypass Ssenarisi",
            "scenario": "Bug bounty proqramında hədəf e-ticarət platformasının məhsul axtarış filtridir. Backend istifadəçi girişini birbaşa SQL sorğusuna birləşdirir.",
            "request_or_code": "GET /api/v1/products?category=books' AND 1=1-- HTTP/1.1\nHost: target-store.com\nUser-Agent: Mozilla/5.0...\nAccept: application/json",
            "objective": "Bu filtrdə boolean-based və ya error-based SQL Injection zəifliyini necə təsdiqləyərdiniz? Hansı sorğu fərqi aşkara çıxarar?",
            "hint1": "Tək dırnaq (') və ya ikili dırnaq (\") işarələrinin server cavabında status kodunu və ya məhsul sayını dəyişib-dəyişmədiyinə bax.",
            "hint2": "' AND 1=1-- (həqiqi) və ' AND 1=2-- (yalan) şərtlərini müqayisə edərək fərqli HTTP cavabları axtar.",
            "hint3": "Verilənlər bazasının versiyasını oxumaq üçün UNION SELECT NULL, version()-- payload-unu sına.",
            "correct_solution": "Zəiflik: SQL Injection (CWE-89). Backend istifadəçi girişini parametrizasiya olunmamış sətir birləşməsi ilə icra edir. Həll: Mütləq Prepared Statements (Parametrləşdirilmiş sorğular) istifadə edilməlidir."
        }
    elif "ssrf" in top_lower:
        return {
            "title": f"'{topic}' üzrə Server-Side Request Forgery (SSRF) Ssenarisi",
            "scenario": "Hədəf veb-saytda istifadəçilərin xarici URL-dən profil şəkli yükləməsi üçün 'Avatar Import' funksionallığı mövcuddur.",
            "request_or_code": "POST /profile/avatar/fetch HTTP/1.1\nHost: internal-portal.org\nContent-Type: application/json\n\n{\n  \"image_url\": \"http://public-img.com/avatar.png\"\n}",
            "objective": "Bu funksionallıq vasitəsilə daxili şəbəkəyə (cloud metadata və ya localhost xidmətlərinə) daxil olma riskini necə yoxlayardınız?",
            "hint1": "'image_url' parametrinə daxili loopback və ya bulud metadata ünvanlarını verərək serverin necə davrandığını izlə.",
            "hint2": "AWS/GCP mühitində 169.254.169.254 ünvanına və ya daxili 127.0.0.1:8080 portuna sorğu göndər.",
            "hint3": "DNS Rebinding və ya URL parser fərqlərindən (məs: http://127.0.0.1 və ya http://2130706433) istifadə edərək filtri keç.",
            "correct_solution": "Zəiflik: SSRF (CWE-918). Server daxili şəbəkə ünvanlarını bloklamadan xarici URL-ə birbaşa HTTP sorğusu atır. Həll: Daxili IP diapazonlarını (127.0.0.0/8, 10.0.0.0/8, 169.254.0.0/16) sərt bloklayan ağ siyahı (whitelist) və DNS yoxlaması tətbiq olunmalıdır."
        }
    elif "xss" in top_lower:
        return {
            "title": f"'{topic}' üzrə Stored XSS & DOM Təhlili",
            "scenario": "Hədəf layihədə müştəri rəyləri (Feedback) bölməsi var. Daxil edilən rəy moderator panelində və ictimai səhifədə əks olunur.",
            "request_or_code": "POST /feedback/submit HTTP/1.1\nHost: target-app.com\nContent-Type: application/x-www-form-urlencoded\n\ncomment=Great+service!&author=GuestUser",
            "objective": "HTML və JavaScript filtrlərini necə test edərdiniz? Cookie oğurlanmasının qarşısını hansı bayraq alır?",
            "hint1": "Mətn daxilində < və > işarələrinin HTML entity kimi kodlaşdırılıb-kodlaşdırılmadığını yoxla.",
            "hint2": "<img src=x onerror=alert(1)> kimi hadisə idarəediciləri (event handlers) olan etiketləri sına.",
            "hint3": "Sessiya oğurluğundan qorunmaq üçün cookie başlıqlarında HttpOnly bayrağının olub-olmadığını yoxla.",
            "correct_solution": "Zəiflik: Stored XSS (CWE-79). Daxil olan məlumatlar DOM-a çıxarılarkən kontekstual HTML kodlaşdırmasından keçirilmir. Həll: Kontekstdən asılı çıxış kodlaşdırması və güclü CSP (Content Security Policy) tətbiq olunmalıdır."
        }
    else:
        return {
            "title": f"'{topic}' üzrə Praktiki API Pentest & IDOR Ssenarisi",
            "scenario": f"Hədəf tətbiq '{subject}' sahəsində istifadəçi profil yeniləmə API xidmətidir. İstifadəçi öz məlumatlarını yeniləyərkən backend aşağıdakı JSON sorğusunu qəbul edir.",
            "request_or_code": "PUT /api/v2/users/me/profile HTTP/1.1\nHost: target-shop.com\nAuthorization: Bearer eyJhbGci...\nContent-Type: application/json\n\n{\n  \"username\": \"test_hunter\",\n  \"email\": \"hunter@mail.com\",\n  \"role\": \"member\",\n  \"account_id\": 10842\n}",
            "objective": f"Bu sorğuda Mass Assignment və ya IDOR/İmtiyaz Artırma riskini necə test edərdin? Hansı parametr şübhəlidir?",
            "hint1": "Sorğunun bədənindəki (body) istifadəçi tərəfindən göndərilməməli olan inzibati sahələrə diqqət yetir.",
            "hint2": "'role' və ya 'account_id' parametrlərini 'admin' və ya başqa istifadəçi ID-si ilə dəyişib cavab statusunu və hüquqları yoxla.",
            "hint3": "Əgər backend parametrləri 'whitelist' etmirsə, 'role': 'admin' göndərərək imtiyaz artıra bilərsən.",
            "correct_solution": "Bu zəiflik Mass Assignment (CWE-915) və ya IDOR-dur. Backend istifadəçidən gələn JSON sahələrini birbaşa DB modelinə kopyalayır. Həll: Server tərəfdə ciddi DTO və parametr ağ siyahısı (whitelist) tətbiq olunmalıdır."
        }


def evaluate_student_challenge(scenario: dict, student_answer: str, model: str, ollama_active: bool):
    """
    Evaluates student's answer gently and decides if it's correct or has a mistake.
    """
    if ollama_active and len(student_answer.strip()) > 3:
        eval_prompt = f"""Tələbənin kibertəhlükəsizlik ssenarisinə verdiyi cavabı qiymətləndir.
Düzgün zəiflik/həll: {scenario.get('correct_solution')}
Tələbənin cavabı: {student_answer}

Pedaqoji qaydalar:
- Düzgündürsə: Təbrik et, təhlilindəki güclü məqamı qeyd et.
- Səhvdirsə: Əsla tənqid etmə, səhvini yumşaq izah et və düzgün məntiqi göstər.
Format:
QƏRAR: [DÜZGÜN və ya SƏHV]
İzah: ..."""
        res = query_ollama_sync(model, eval_prompt, "You are a supportive cyber security evaluator.", temperature=0.3)
        if res and not res.startswith("Error"):
            is_correct = "DÜZGÜN" in res.upper()
            return is_correct, res

    # Offline / fast fallback evaluation based on scenario concepts
    ans_lower = student_answer.lower()
    sol_lower = scenario.get("correct_solution", "").lower()
    
    sol_keywords = [w for w in re.findall(r"\w{4,}", sol_lower) if w not in {"olan", "üçün", "edir", "kimi", "belə", "buna", "tərəf", "olar"}]
    matches = [w for w in sol_keywords if w in ans_lower]
    sec_matches = [w for w in ["role", "admin", "mass assignment", "idor", "privilege", "imtiyaz", "sqli", "injection", "union", "ssrf", "internal", "169.254", "metadata", "xss", "script", "jwt", "alg", "none", "bypass", "auth", "token", "parametr"] if w in ans_lower]

    if len(matches) >= 2 or len(sec_matches) >= 2:
        found_kw = sec_matches[0] if sec_matches else matches[0]
        return True, f"🎉 **Əla Təhlil!** Düzgün istiqamətdəsən. Arqumentindəki '{found_kw}' məntiqi zəifliyin əsas kök səbəbinə tam uyğun gəlir. Metodologiyanı dəqiq qurdun!"
    else:
        return False, f"🤔 **Yaxşı cəhddir, lakin əsas boşluq fərqli parametr və ya təhlükəsizlik məntiqindədir.** Ssenaridəki sorğunun strukturu və verilən ipuclarına yenidən diqqət yetirərək cavabını dəqiqləşdirə bilərsən."


def stream_fallback_explanation(topic: str, subject: str, level: str, has_doc=False):
    """
    Simulated streaming explanation demonstrating Cybersecurity & Bug Bounty tutor pedagogy when Ollama is offline.
    """
    source_info = " (Təhlükəsizlik sənədi və qeydlər əsasında)" if has_doc else ""
    full_text = f"""Salam! **{topic}** mövzusuna{source_info} birlikdə baxaq ({subject}). Bir mentor kimi birbaşa hazır exploit və ya həlli verməyəcəyəm — gəl zəifliyin mexanizmini və ovlama metodologiyasını addım-addım birlikdə açaq!

💡 **Zəifliyin Əsas Məntiqi ({level} səviyyəsi):**
{topic} — adətən tətbiqin istifadəçidən gələn parametrləri yetərincə təhlükəsizlik filtrindən keçirməməsi və ya icazə mexanizminin (access control) düzgün qurulmaması nəticəsində meydana çıxır. Əsas məqsəd bu zəifliyin hansı məntiqi zəncirdə baş verdiyini və arxasında duran səbəbi (root cause) dərk etməkdir.

🤔 **Sənə İstiqamətləndirici Sualım:**
Səncə, **{topic}** zəifliyini aşkar edərkən ilkin olaraq HTTP sorğusunda hansı parametrə, başlıqlara (headers) və ya istifadəçi girişinə diqqət yetirməliyik? Sənin ilk addımın nə olardı?

*(Fikrini aşağıdakı çatda yaz, birlikdə analiz edib növbəti addıma keçək!)*

---
🎯 **Təhlükəsizlik Yoxlaması (Mini-Test):**
1. {topic} zəifliyini test edərkən ən vacib etik qayda nədir?
   - A) Birbaşa icazəsiz hücum edib sistemə ziyan vurmaq
   - B) Yalnız ayrılmış scope daxilində proof-of-concept (PoC) hazırlayaraq məsuliyyətli şəkildə bildirmək"""

    for word in full_text.split(" "):
        yield word + " "
        time.sleep(0.015)


def generate_fallback_demo_quiz(topic: str, subject: str, level: str, count: int):
    return [
        {
            "question": f"'{topic}' zəifliyi ({subject}) aşkar edilərkən ilk atılmalı ən düzgün addım hansıdır?",
            "options": [
                f"A) Zəifliyin təsir dərəcəsini anlamaq və minimal zərərlə PoC hazırlamaq",
                "B) Bütün verilənlər bazasını dərhal silmək",
                "C) Sistemi ictimaiyyətə açıqlayıb şirkətə şantaj etmək",
                "D) Heç bir qeydiyyat aparmadan növbəti hədəfə keçmək"
            ],
            "answer": "A",
            "explanation": f"Bug bounty metodologiyasında əsas prinsip minimal təsirlə zəifliyin mövcudluğunu sübut etmək (PoC) və hesabat tərtib etməkdir."
        },
        {
            "question": f"{topic} zəifliyinin qarşısını almaq üçün ən effektiv remediasiya hansıdır?",
            "options": [
                "A) Server tərəfdə ciddi giriş validasiyası və ən az imtiyaz (least privilege) prinsipi",
                "B) Yalnız müştəri (frontend/JavaScript) tərəfdə yoxlama aparmaq",
                "C) Xəta mesajlarını gizlətməklə problemi həll olunmuş saymaq",
                "D) Bütün şifrələmə protokollarını ləğv etmək"
            ],
            "answer": "A",
            "explanation": "Kibertəhlükəsizlikdə təhlükəsizlik heç vaxt yalnız müştəri tərəfə etibar edilə bilməz; server tərəfli validasiya və ən az imtiyaz prinsipi mütləqdir."
        },
        {
            "question": f"Bug bounty ovunda {topic} üzrə təqdim edilən hesabatda hansı hissə ən həlledici hesab olunur?",
            "options": [
                "A) Addım-addım təkrarlana bilən aydın reproduksiya (Steps to Reproduce)",
                "B) Mətnin uzunluğu və qəliz terminlərin sayı",
                "C) Avtomatlaşdırılmış skanerin xam çıxışı",
                "D) Təxmini fərziyyələr"
            ],
            "answer": "A",
            "explanation": "Triajerlərin və şirkət mühəndislərinin zəifliyi təsdiqləməsi üçün aydın, addım-addım reproduksiya (Steps to Reproduce) ən vacib şərtdir."
        }
    ][:count]


# --- System Prompt Builders ---

def build_system_prompt(education_level: str, subject: str, mode: str, has_doc=False) -> str:
    level_descriptions = {
        "Beginner (Yeni Başlayan - Əsaslar)": "fundamental web & network concepts, basic HTTP methods, intuitive analogies, friendly, encouraging tone without confusing jargon.",
        "Junior Bug Hunter (Praktik Zəiflik Ovçusu)": "practical vulnerability identification, understanding request/response cycles, manual inspection, Burp Suite workflows, common bug bounty patterns.",
        "Senior Pentester (Qabaqcıl Təhlükəsizlik Mühəndisi)": "in-depth vulnerability mechanics, business logic bypasses, defense evasion, nuanced edge cases, chaining bugs, remediation architecture.",
        "Expert / Red Teamer (Dərin Tədqiqat & Exploit)": "source code audit, exploit development, kernel/memory bypass, zero-day research mindset, complex chained infrastructure attack paths."
    }

    selected_level_desc = level_descriptions.get(education_level, "appropriate security expertise level.")
    
    rag_instruction = ""
    if has_doc:
        rag_instruction = "\n- TƏDQİQAT/DƏRSLİK İNTEQRASİYASI: Tələbə təhlükəsizlik sənədi/hədəf scope/metodologiya materialı yükləyib. İzahlarını və tövsiyələrini birbaşa bu materiala əsaslandır və dərslikdəki faktlara istinad et."

    if mode == "Explain a Topic":
        return f"""Sən "Mahammad Cyber & Bug Bounty Tutor" — kibertəhlükəsizlik, etik hakerlik və bug bounty sahəsində ixtisaslaşmış təcrübəli bələdçi və mentiorsan.
İxtisas sahən: {subject}
Tələbənin təcrübə səviyyəsi: {education_level} ({selected_level_desc})
Dil: İstifadəçinin müraciət etdiyi dildə (əsasən səlis Azərbaycan dilində, yaxud ingiliscə soruşarsa İngilis dilində) cavab ver.

MÜTLƏQ ƏMƏL ETMƏLİ OLDUĞUN 4 ƏSAS PEDAQOJİ QAYDA:

1. 🚫 QƏTİ QADAĞANDIR: BİRBAŞA HAZIR EXPLOIT/HƏLLİ VƏ YA PAYLOAD-U VERMƏK!
   - Şagird hədəf, zəiflik və ya məsələ soruşduqda dərhal hazır payload və ya exploit kodunu vermə.
   - Əvvəlcə zəifliyin kök səbəbini (root-cause) və arxasında duran təhlükəsizlik məntiqini 2-3 cümlə ilə qısa, aydın izah et.
   - Dərhal sonra şagirdə istiqamətləndirici bir sual verərək növbəti addımı onun özünün düşünməsini tələb et.

2. 🌟 SƏLİS, ETİK VƏ TƏŞVİQEDİCİ MENTOR TONU:
   - Şagirdlə səbirli, etik prinsiplərə sadiq, həvəsləndirici və təşviqedici tonda danış ("Əla müşahidədir!", "Bu parametr həqiqətən şübhəlidir, gəl addım-addım yoxlayaq").

3. 🤝 SƏHV FƏRZİYYƏLƏRDƏ YUMŞAQ İSTİQAMƏTLƏNDİRMƏ VƏ YENİ İPUCU (HINT):
   - Əgər şagird yanlış yanaşma təklif edərsə, onu əsla tənqid etmə.
   - Nə üçün həmin yanaşmanın bu ssenaridə işləməyəcəyini yumşaq şəkildə izah et və düzgün yola çıxması üçün yeni, aydın bir İPUCU təqdim et.

4. 🎯 MÖVZUNUN YEKUNUNDA 1-2 TEST / QƏRAR SUALI:
   - Mövzu və ya zəiflik aydınlaşdıqda, öyrənilənləri möhkəmləndirmək üçün ən sonda mütləq "🎯 Təhlükəsizlik Yoxlaması (Mini-Test)" başlığı altında 1-2 kiçik yoxlama sualı təqdim et.
{rag_instruction}

Kod nümunələrini, HTTP sorğu/cavablarını və payload strukturunu təmiz kod bloklarında tərtib et."""

    else:
        return f"""You are Mahammad Cyber & Bug Bounty Tutor, an expert cybersecurity examiner for {subject} at the {education_level} level ({selected_level_desc}).{rag_instruction}
Generate interactive Multiple Choice Questions (MCQs) in JSON format adhering strictly to this schema:
[
  {{
    "question": "Question text here",
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "answer": "A",
    "explanation": "Detailed explanation of why the correct option is right."
  }}
]
Output ONLY valid JSON inside a ```json ``` code block."""


def parse_quiz_json(response_text: str):
    if not response_text:
        return None
        
    # Clean markdown code blocks
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
    if match:
        json_str = match.group(1).strip()
    else:
        start = response_text.find("[")
        end = response_text.rfind("]")
        if start != -1 and end != -1:
            json_str = response_text[start:end+1]
        else:
            json_str = response_text

    json_str = re.sub(r",\s*([\]}])", r"\1", json_str)

    try:
        data = json.loads(json_str)
        if isinstance(data, list) and len(data) > 0:
            return data
    except Exception:
        pass

    # Resilient fallback regex parser if JSON syntax was damaged
    try:
        items = []
        q_blocks = re.split(r"(?:Question|Sual)\s*\d*[:.]?", response_text, flags=re.IGNORECASE)
        for block in q_blocks[1:]:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue
            question = lines[0]
            options = [l for l in lines[1:] if re.match(r"^[A-D]\)", l, re.IGNORECASE)]
            if len(options) >= 2:
                items.append({
                    "question": question,
                    "options": options[:4],
                    "answer": "A",
                    "explanation": "Bu sual tətbiq tərəfindən formatlaşdırılmışdır."
                })
        if items:
            return items
    except Exception:
        pass

    return None


# --- Initialize Session State ---

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

if "document_text" not in st.session_state:
    st.session_state.document_text = None

if "current_doc_name" not in st.session_state:
    st.session_state.current_doc_name = None

# Feature 1: Local Notes & Writeups
if "local_notes" not in st.session_state:
    st.session_state.local_notes = []

# Feature 3: Study Notes & Notebook
if "study_notes" not in st.session_state:
    st.session_state.study_notes = []

# Feature 3: Mistake Notebook (Səhv Dəftəri)
if "mistake_book" not in st.session_state:
    st.session_state.mistake_book = []

# Feature 2: Interactive Challenge ("Məni Sına")
if "current_challenge" not in st.session_state:
    st.session_state.current_challenge = None

if "challenge_hints_shown" not in st.session_state:
    st.session_state.challenge_hints_shown = 0

if "challenge_feedback" not in st.session_state:
    st.session_state.challenge_feedback = None


# --- Sidebar Navigation & Settings ---

ollama_active = check_ollama_running()
available_models = get_available_models() if ollama_active else []

with st.sidebar:
    st.title("🛡️ Mahammad Cyber Tutor")
    st.markdown('<span class="badge-privacy">🔒 100% Private & Offline</span>', unsafe_allow_html=True)
    st.caption("Kibertəhlükəsizlik və Bug Bounty üzrə yerli süni intellekt mentoru.")

    if ollama_active and available_models:
        st.success(f"🟢 Ollama Aktiv ({len(available_models)} model)")
    elif ollama_active and not available_models:
        st.warning("🟡 Ollama Aktivdir, lakin model endirilməyib!")
        st.caption("Terminalda `ollama pull qwen2.5:1.5b` yazın.")
    else:
        st.info("💡 Offline Rejim (Simulyasiya Aktivdir)")
        st.caption("Ollama xidməti tapılmadıqda tətbiq daxili interaktiv təhlil bazası ilə sürətli işləyir.")

    st.divider()
    
    # Feature 1: Lokal fayl/qeyd əlavə etmə
    st.subheader("📚 Şəxsi Materiallar & Qeydlər")
    uploaded_doc = st.file_uploader(
        "Material yükləyin (.pdf, .txt, .md)",
        type=["pdf", "txt", "md"],
        help="Yüklədiyiniz fayldakı məlumatlar və ya qaydalar əsasında AI tədris aparacaq."
    )
    if uploaded_doc is not None:
        if (st.session_state.current_doc_name != uploaded_doc.name):
            with st.spinner("Sənəd oxunur..."):
                doc_text = extract_text_from_upload(uploaded_doc)
                if doc_text == "PDF_IMPORT_ERROR":
                    st.error("PDF oxumaq üçün terminalda `python -m pip install pypdf` quraşdırın.")
                    st.session_state.document_text = None
                elif doc_text.startswith("Xəta"):
                    st.error(doc_text)
                    st.session_state.document_text = None
                else:
                    st.session_state.document_text = doc_text
                    st.session_state.current_doc_name = uploaded_doc.name
                    word_cnt = len(doc_text.split())
                    st.success(f"✅ '{uploaded_doc.name}' yükləndi (~{word_cnt} söz)")
    
    if st.session_state.document_text:
        word_cnt = len(st.session_state.document_text.split())
        st.caption(f"📄 Aktiv Fayl: **{st.session_state.current_doc_name}** ({word_cnt} söz)")
        if st.button("🗑️ Faylı çıxar", key="remove_uploaded_file", use_container_width=True):
            st.session_state.document_text = None
            st.session_state.current_doc_name = None
            st.rerun()

    # Manual Note / Writeup input expander
    with st.expander("➕ Yeni Qeyd / Writeup Əlavə Et"):
        note_title_input = st.text_input("Qeyd Başlığı", placeholder="Məs: Hədəf XSS Qaydaları və ya Recon qeydi")
        note_content_input = st.text_area("Məzmun / Writeup / Scope", placeholder="Öyrəndiyiniz və ya tədqiq etdiyiniz detalları daxil edin...", height=100)
        if st.button("💾 Qeydi Yadda Saxla", use_container_width=True):
            if note_content_input.strip():
                st.session_state.local_notes.append({
                    "title": note_title_input.strip() or f"Qeyd #{len(st.session_state.local_notes)+1}",
                    "content": note_content_input.strip(),
                    "date": time.strftime("%Y-%m-%d %H:%M")
                })
                st.success("Qeyd materiallara əlavə edildi!")
                st.rerun()
            else:
                st.warning("Qeyd məzmunu boş ola bilməz.")

    if st.session_state.local_notes:
        st.caption(f"📝 Yaddaşda **{len(st.session_state.local_notes)}** şəxsi qeyd var.")
        for idx_n, note_item in enumerate(st.session_state.local_notes):
            col_n1, col_n2 = st.columns([4, 1])
            with col_n1:
                st.write(f"• **{note_item['title']}**")
            with col_n2:
                if st.button("❌", key=f"del_note_{idx_n}", help="Qeydi sil"):
                    st.session_state.local_notes.pop(idx_n)
                    st.rerun()

    st.divider()
    st.subheader("⚙️ Tənzimləmələr")

    mode = st.radio(
        "Təlim Rejimi",
        [
            "📖 Zəiflik İzahı (Sokrat Mentoru)",
            "🎯 Məni Sına (Aktiv Məşq & İpucu)",
            "📝 Təhlükəsizlik Testi (MCQ Quiz)",
            "📓 Konspekt & Səhv Dəftəri"
        ],
        index=0
    )

    education_level = st.selectbox(
        "Təcrübə Səviyyəsi",
        [
            "Beginner (Yeni Başlayan - Əsaslar)",
            "Junior Bug Hunter (Praktik Zəiflik Ovçusu)",
            "Senior Pentester (Qabaqcıl Təhlükəsizlik Mühəndisi)",
            "Expert / Red Teamer (Dərin Tədqiqat & Exploit)"
        ],
        index=1
    )

    subject = st.selectbox(
        "Kibertəhlükəsizlik Sahəsi",
        [
            "Web App Security & OWASP Top 10",
            "Bug Bounty Metodologiyası & Recon (OSINT)",
            "XSS, CSRF & Client-Side Hücumlar",
            "SQL Injection & Verilənlər Bazası Zəiflikləri",
            "Broken Access Control & IDOR",
            "Authentication & Session Flaws (JWT, OAuth)",
            "Server-Side Zəifliklər (SSRF, RCE, File Upload)",
            "API Security & GraphQL Zəiflikləri",
            "Network Pentesting & Port Analizi",
            "Privilege Escalation (Linux/Windows)",
            "Etik Hakerlik & Peşəkar Bug Bounty Hesabatı"
        ],
        index=0
    )

    st.divider()
    st.subheader("🤖 Süni İntellekt Modeli")

    if ollama_active and available_models:
        selected_model = st.selectbox("Seçilmiş Model", available_models, index=0)
    else:
        selected_model = "Offline Simulation Preview"
        st.text_input("Aktiv Rejim", value=selected_model, disabled=True)

    temperature = st.slider("Yaradıcılıq Dərəcəsi", min_value=0.1, max_value=1.0, value=0.6, step=0.05)

    st.divider()
    if st.button("🔄 Bütün Söhbəti Sıfırla (Reset)", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.quiz_data = None
        st.session_state.quiz_submitted = False
        st.session_state.user_answers = {}
        st.session_state.current_challenge = None
        st.session_state.challenge_hints_shown = 0
        st.session_state.challenge_feedback = None
        st.rerun()


# --- Main App Interface ---

st.markdown('<div class="main-title">🛡️ Mahammad Cyber & Bug Bounty Tutor</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-title">Sahə: <b>{subject}</b> | Səviyyə: <b>{education_level}</b> | Model: <b>{selected_model}</b></div>',
    unsafe_allow_html=True
)

all_context_text = get_all_user_context()
has_user_materials = bool(all_context_text.strip())

if has_user_materials:
    mat_summary = []
    if st.session_state.get("document_text"):
        mat_summary.append(f"Fayl: {st.session_state.current_doc_name}")
    if st.session_state.get("local_notes"):
        mat_summary.append(f"{len(st.session_state.local_notes)} qeyd")
    st.markdown(f'<span class="badge-rag">📚 Şəxsi Materiallar İnteqrasiya Edilib: <b>{", ".join(mat_summary)}</b></span>', unsafe_allow_html=True)


# ----------------- MODE 1: EXPLAIN A TOPIC (SOCRATIC MENTOR) -----------------
if "Zəiflik İzahı" in mode:
    if has_user_materials:
        st.info("🧑‍🏫 **Cyber Mentor**: Şəxsi materiallarınız və qeydləriniz əsasında təhlil aparılır. Sualınızı və ya fərziyyənizi yazın.")
    else:
        st.info(f"🧑‍🏫 **Cyber Mentor**: **{subject}** üzrə sualını, ssenarini və ya fərziyyəni yaz. Birbaşa hazır exploit vermək əvəzinə, addım-addım düşünməyinə kömək edəcək.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input(f"{subject} üzrə sualını, ssenarini və ya fərziyyəni yaz...")
    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            system_prompt = build_system_prompt(education_level, subject, "Explain a Topic", has_doc=has_user_materials)

            doc_context_str = ""
            if has_user_materials:
                relevant_snippet = retrieve_relevant_context(all_context_text, user_query)
                doc_context_str = f"--- ŞƏXSİ MATERİAL VƏ QEYDLƏRDƏN MÜVAFİQ HİSSƏLƏR ---\n{relevant_snippet}\n---------------------------------\n\n"

            history_turns = st.session_state.chat_history[:-1]
            context_list = []
            for prev in history_turns[-3:]:
                snip = prev['content'][:200].strip()
                context_list.append(f"{prev['role'].capitalize()}: {snip}")
            context = "\n".join(context_list)
                
            if context:
                full_prompt = f"{doc_context_str}Son Dialoq:\n{context}\n\nTələbə: {user_query}\n\nMentor kimi qısa və aydın bələdçilik et, birbaşa hazır exploit vermə."
            else:
                full_prompt = f"{doc_context_str}Tələbə: {user_query}\n\nMentor kimi qısa və aydın bələdçilik et, birbaşa hazır exploit vermə."

            if ollama_active and available_models:
                response_stream = stream_ollama_response(selected_model, full_prompt, system_prompt, temperature=temperature)
            else:
                response_stream = stream_fallback_explanation(user_query, subject, education_level, has_doc=has_user_materials)

            message_placeholder = st.empty()
            full_response = ""
            chunk_count = 0
            for chunk in response_stream:
                full_response += chunk
                chunk_count += 1
                if chunk_count % 3 == 0 or "\n" in chunk:
                    message_placeholder.markdown(full_response + "▌")
            
            if not full_response.strip():
                full_response = "⚠️ Model cavab vermədi. Zəhmət olmasa terminalda `ollama serve` işlədiyini və modelin endirildiyini yoxlayın."
            message_placeholder.markdown(full_response)

        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
        st.rerun()

    # Save last assistant response to Study Notes
    if st.session_state.chat_history:
        last_ai_msgs = [m["content"] for m in st.session_state.chat_history if m["role"] == "assistant"]
        if last_ai_msgs:
            last_text = last_ai_msgs[-1]
            col_save1, col_save2 = st.columns([3, 1])
            with col_save2:
                if st.button("📌 Son İzahı Konspektə Saxla", use_container_width=True):
                    st.session_state.study_notes.append({
                        "title": f"{subject} İzahı - {time.strftime('%H:%M')}",
                        "content": last_text,
                        "date": time.strftime("%Y-%m-%d %H:%M")
                    })
                    st.success("İzah Konspektə əlavə edildi!")


# ----------------- MODE 2: MƏNİ SINA (AKTİV MƏŞQ & İPUCU MƏNTİQİ) -----------------
elif "Məni Sına" in mode:
    st.subheader("🎯 Məni Sına: Praktiki Təhlükəsizlik Məşqi & İpucu Məntiqi")
    st.caption("Passiv oxumaqdan aktiv analizə keçin. Mentor sizə real ssenari və ya kod təqdim edir; zəifliyi tapmaq üçün mərhələli ipuclarından istifadə edin.")

    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        challenge_topic = st.text_input(
            "Təlim Mövzusu / Zəiflik Növü",
            value=subject,
            key="challenge_topic_input",
            placeholder="məs: IDOR və Mass Assignment, SQL Injection, SSRF, JWT bypass..."
        )
    with col_t2:
        st.write("")
        st.write("")
        start_btn = st.button("🚀 Yeni Ssenari Başlat", type="primary", use_container_width=True)

    if start_btn:
        with st.spinner("Realist ssenari və laboratoriya tapşırığı hazırlanır..."):
            doc_ctx = all_context_text[:800] if has_user_materials else ""
            scenario = generate_challenge(challenge_topic, subject, education_level, doc_ctx, selected_model, ollama_active)
            st.session_state.current_challenge = scenario
            st.session_state.challenge_hints_shown = 0
            st.session_state.challenge_feedback = None
            st.rerun()

    if st.session_state.current_challenge:
        ch = st.session_state.current_challenge
        st.markdown("---")
        st.markdown(f"### 🛡️ Tapşırıq: {ch.get('title', 'Təhlükəsizlik Ssenarisi')}")
        
        st.info(f"**📋 Ssenari:**\n\n{ch.get('scenario', '')}")

        req_code = ch.get("request_or_code", "")
        if req_code:
            st.markdown("**💻 Təhlil Ediləcək Sorğu / Kod:**")
            st.code(req_code, language="http" if "HTTP" in req_code else "python")

        st.warning(f"**🎯 Sənin Hədəfin:** {ch.get('objective', '')}")

        # Progressive Hint Mechanism (Feature 2)
        st.markdown("#### 💡 Pilləli İpucu Sistemi")
        hints = [ch.get("hint1"), ch.get("hint2"), ch.get("hint3")]
        hints_unlocked = st.session_state.challenge_hints_shown

        for h_idx in range(hints_unlocked):
            if h_idx < len(hints) and hints[h_idx]:
                st.markdown(f"""
                <div class="hint-card">
                    <b>💡 İpucu {h_idx+1}:</b> {hints[h_idx]}
                </div>
                """, unsafe_allow_html=True)

        col_h1, col_h2 = st.columns([2, 2])
        with col_h1:
            if hints_unlocked < 3:
                if st.button(f"💡 Növbəti İpucunu Aç ({hints_unlocked+1}/3)", use_container_width=True):
                    st.session_state.challenge_hints_shown += 1
                    st.rerun()
            else:
                st.caption("Bütün 3 ipucu açıldı.")

        st.markdown("---")
        st.markdown("#### ✍️ Sənin Təhlilin / Həll Yanaşman")
        student_ans = st.text_area(
            "Zəifliyin növünü, hansı parametr/başlığın şübhəli olduğunu və necə istismar/yoxlama edəcəyini qeyd et:",
            placeholder="Məs: Burada 'account_id' və ya 'role' parametri manipulasiya oluna bilər, çünki backend...",
            height=110,
            key="challenge_student_answer"
        )

        col_sub1, col_sub2 = st.columns([2, 2])
        with col_sub1:
            if st.button("📤 Cavabımı Yoxla", type="primary", use_container_width=True):
                if not student_ans.strip():
                    st.warning("Zəhmət olmasa əvvəlcə təhlilinizi yazın.")
                else:
                    with st.spinner("Mentor cavabınızı təhlil edir..."):
                        is_corr, fb = evaluate_student_challenge(ch, student_ans, selected_model, ollama_active)
                        st.session_state.challenge_feedback = {
                            "is_correct": is_corr,
                            "feedback": fb,
                            "student_ans": student_ans
                        }
                        # If mistake, automatically log into Mistake Notebook (Feature 3)!
                        if not is_corr:
                            st.session_state.mistake_book.append({
                                "topic": ch.get("title", challenge_topic),
                                "question": ch.get("objective", "Ssenari Təhlili"),
                                "wrong_answer": student_ans,
                                "correct_reason": ch.get("correct_solution", "Düzgün yanaşma"),
                                "date": time.strftime("%Y-%m-%d %H:%M")
                            })
                        st.rerun()

        if st.session_state.challenge_feedback:
            cf = st.session_state.challenge_feedback
            st.markdown("---")
            st.markdown("#### 🧑‍🏫 Mentor Qiymətləndirməsi")
            if cf["is_correct"]:
                st.success(cf["feedback"])
                if st.button("📌 Bu Uğurlu Təhlili Konspektə Saxla"):
                    st.session_state.study_notes.append({
                        "title": f"Məşq Uğuru: {ch.get('title')}",
                        "content": f"**Ssenari:** {ch.get('scenario')}\n\n**Mənim Həllim:** {cf['student_ans']}\n\n**İzah:** {ch.get('correct_solution')}",
                        "date": time.strftime("%Y-%m-%d %H:%M")
                    })
                    st.success("Konspektə yazıldı!")
            else:
                st.warning(cf["feedback"])
                st.caption("📕 *Bu səhv təhlil təkrar nəzərdən keçirilməsi üçün avtomatik olaraq **'Səhv Dəftəri'** bölməsinə əlavə olundu.*")

            with st.expander("📖 Rəsmi Zəiflik İzahı və Remediasiya (Həll)"):
                st.markdown(f"**Doğru Zəiflik & İzah:**\n\n{ch.get('correct_solution')}")


# ----------------- MODE 3: GENERATE A QUIZ (MCQ) -----------------
elif "Təhlükəsizlik Testi" in mode:
    if has_user_materials:
        st.info("📝 Şəxsi materiallarınıza və qeydlərinizə əsasən çoxseçimli (MCQ) təhlükəsizlik testi hazırlayın.")
    else:
        st.info("📝 Mövzunu daxil edərək çoxseçimli (MCQ) təhlükəsizlik testi yaradın.")

    col1, col2 = st.columns([3, 1])
    with col1:
        quiz_topic = st.text_input(
            "Test Mövzusu",
            placeholder=f"məsələn: 'IDOR zəiflikləri və bypass' və ya 'SQLi Triage' və ya 'SSRF Metodologiyası'...",
            key="quiz_topic_input"
        )
    with col2:
        num_questions = st.selectbox("Sual Sayı", [3, 5], index=0)

    if st.button("🚀 Test Yarat", type="primary"):
        if not quiz_topic.strip():
            st.warning("Zəhmət olmasa mövzunu daxil edin.")
        else:
            with st.spinner(f"'{quiz_topic}' mövzusunda test hazırlanır..."):
                system_prompt = build_system_prompt(education_level, subject, "Generate a Quiz", has_doc=has_user_materials)
                doc_context_str = ""
                if has_user_materials:
                    relevant_snippet = retrieve_relevant_context(all_context_text, quiz_topic, max_chars=1200)
                    doc_context_str = f"--- DƏRSLİK VƏ QEYDLƏRDƏN HİSSƏLƏR ---\n{relevant_snippet}\n-------------------------\n\n"

                prompt = f"{doc_context_str}Generate {num_questions} multiple-choice questions on '{quiz_topic}'. Output ONLY strict JSON."

                if ollama_active and available_models:
                    raw_response = query_ollama_sync(selected_model, prompt, system_prompt, temperature=temperature)
                    parsed_quiz = parse_quiz_json(raw_response)
                else:
                    parsed_quiz = None

                if not parsed_quiz:
                    parsed_quiz = generate_fallback_demo_quiz(quiz_topic, subject, education_level, num_questions)

                st.session_state.quiz_data = parsed_quiz
                st.session_state.quiz_submitted = False
                st.session_state.user_answers = {}
                st.session_state.quiz_topic = quiz_topic
                st.success("Test uğurla yaradıldı! Aşağıdakı sualları cavablandırın.")

    if st.session_state.quiz_data:
        st.divider()
        st.subheader(f"📝 Test: {st.session_state.get('quiz_topic', 'Mövzu')} ({education_level} Səviyyəsi)")

        with st.form("quiz_form"):
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Sual {i+1}: {q.get('question')}**")
                options = q.get("options", [])
                
                user_choice = st.radio(
                    f"Cavabınızı seçin ({i+1}):",
                    options,
                    key=f"q_{i}",
                    index=None
                )
                st.session_state.user_answers[i] = user_choice
                st.markdown("---")

            submit_quiz = st.form_submit_button("✅ Testi Təqdim Et və Nəticəni Gör", type="primary")

        if submit_quiz:
            st.session_state.quiz_submitted = True
            # Automatically log wrong answers into Mistake Notebook
            for i, q in enumerate(st.session_state.quiz_data):
                chosen = st.session_state.user_answers.get(i)
                correct_letter = q.get("answer", "").strip().upper()
                chosen_letter = chosen.strip()[:1].upper() if chosen else ""
                if chosen_letter != correct_letter:
                    st.session_state.mistake_book.append({
                        "topic": st.session_state.get("quiz_topic", subject),
                        "question": q.get("question"),
                        "wrong_answer": chosen or "Cavab verilməyib",
                        "correct_reason": f"Düzgün variant {correct_letter}: {q.get('explanation', '')}",
                        "date": time.strftime("%Y-%m-%d %H:%M")
                    })

        if st.session_state.quiz_submitted:
            correct_count = 0
            total_questions = len(st.session_state.quiz_data)

            st.subheader("📊 Nəticələr")

            for i, q in enumerate(st.session_state.quiz_data):
                chosen = st.session_state.user_answers.get(i)
                correct_letter = q.get("answer", "").strip().upper()
                chosen_letter = chosen.strip()[:1].upper() if chosen else ""
                is_correct = (chosen_letter == correct_letter)
                if is_correct:
                    correct_count += 1
                    status_badge = '<span style="color:#2B6E44; font-weight:600;">✅ Düzgün!</span>'
                else:
                    status_badge = f'<span style="color:#A63A3A; font-weight:600;">❌ Səhv.</span> <span style="color:#5C6258;">(Seçiminiz: {chosen or "Seçilməyib"}, Doğru: Variant {correct_letter})</span>'

                st.markdown(f"""
                <div class="quiz-card">
                    <h4>Sual {i+1}: {q.get('question')}</h4>
                    <p>{status_badge}</p>
                    <div class="quiz-explanation">
                        <b>İzah:</b> {q.get('explanation', 'İzah təqdim edilməyib.')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            score_percent = int((correct_count / total_questions) * 100)
            if score_percent >= 80:
                st.balloons()
                st.success(f"🎉 Əla Nəticə! Balınız: {correct_count}/{total_questions} ({score_percent}%)")
            elif score_percent >= 50:
                st.info(f"👍 Yaxşı Cəhd! Balınız: {correct_count}/{total_questions} ({score_percent}%)")
            else:
                st.warning(f"📚 Mövzunu təkrar oxumaq tövsiyə olunur! Balınız: {correct_count}/{total_questions} ({score_percent}%)")

            if correct_count < total_questions:
                st.caption("📕 *Səhv cavablandırılan suallar avtomatik olaraq **'Səhv Dəftəri'** bölməsinə əlavə olundu.*")


# ----------------- MODE 4: KONSPEKT & SƏHV DƏFTƏRİ -----------------
elif "Konspekt" in mode:
    st.subheader("📓 Dərs Konspekti və Səhv Dəftəri")
    st.caption("Öyrəndiklərinizin və etdiyiniz səhvlərin itməməsi üçün şəxsi tədris jurnalı. Buradan qeydlərinizi oxuya, səhvlərinizi təkrarlaya və `.md` faylı kimi endirə bilərsiniz.")

    tab_konspekt, tab_mistakes = st.tabs(["📚 Dərs Konspekti (Study Notes)", f"📕 Səhv Dəftəri ({len(st.session_state.mistake_book)})"])

    with tab_konspekt:
        with st.expander("➕ Şəxsi Konspekt / Qeyd Əlavə Et"):
            new_title = st.text_input("Mövzu / Başlıq", placeholder="Məs: IDOR Triage Qaydaları", key="new_study_title")
            new_body = st.text_area("Konspekt Məzmunu", placeholder="Öyrəndiyiniz əsas dərsləri, payload nümunələrini qeyd edin...", height=120, key="new_study_body")
            if st.button("💾 Konspektə Əlavə Et", key="btn_add_study"):
                if new_body.strip():
                    st.session_state.study_notes.append({
                        "title": new_title.strip() or f"Konspekt #{len(st.session_state.study_notes)+1}",
                        "content": new_body.strip(),
                        "date": time.strftime("%Y-%m-%d %H:%M")
                    })
                    st.success("Konspekt saxlanıldı!")
                    st.rerun()
                else:
                    st.warning("Məzmun boş ola bilməz.")

        if not st.session_state.study_notes:
            st.info("💡 Hələlik heç bir konspekt saxlanılmayıb. 'Zəiflik İzahı' və ya 'Məni Sına' bölmələrindəki 'Konspektə Saxla' düymələri ilə və ya yuxarıdakı form ilə vacib məqamları burada toplaya bilərsiniz.")
        else:
            for idx_s, snote in enumerate(st.session_state.study_notes):
                col_s1, col_s2 = st.columns([5, 1])
                with col_s1:
                    st.markdown(f"""
                    <div class="note-card">
                        <h4>📌 {snote.get('title')}</h4>
                        <small style="color:var(--text-secondary);">{snote.get('date', '')}</small>
                        <div style="margin-top:8px; white-space: pre-wrap;">{snote.get('content')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_s2:
                    if st.button("🗑️ Sil", key=f"del_study_{idx_s}", help="Bu konspekti sil"):
                        st.session_state.study_notes.pop(idx_s)
                        st.rerun()

    with tab_mistakes:
        if not st.session_state.mistake_book:
            st.success("🎉 Əla! Səhv dəftəriniz boşdur. 'Məni Sına' və ya 'Test' bölmələrində yanlış cavab verdikdə mentor həmin sualları təkrar etmək üçün avtomatik bura toplayacaq.")
        else:
            col_m_all1, col_m_all2 = st.columns([4, 1])
            with col_m_all2:
                if st.button("🗑️ Hamısını Təmizlə", key="clear_all_mistakes", use_container_width=True):
                    st.session_state.mistake_book = []
                    st.rerun()

            for idx_m, mist in enumerate(st.session_state.mistake_book):
                col_m1, col_m2 = st.columns([5, 1])
                with col_m1:
                    st.markdown(f"""
                    <div class="mistake-card">
                        <h4>⚠️ Mövzu: {mist.get('topic')}</h4>
                        <small style="color:var(--text-secondary);">{mist.get('date', '')}</small>
                        <p style="margin-top:6px;"><b>Sual / Ssenari:</b> {mist.get('question')}</p>
                        <p style="color:var(--status-error-text);"><b>Mənim Yanlış Yanaşmam:</b> {mist.get('wrong_answer')}</p>
                        <div class="quiz-explanation">
                            <b>💡 Düzgün Məntiq / Mentor İzahı:</b><br/>{mist.get('correct_reason')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_m2:
                    if st.button("✅ Öyrəndim", key=f"done_mistake_{idx_m}", help="Bu səhvi öyrəndim, siyahıdan çıxar"):
                        st.session_state.mistake_book.pop(idx_m)
                        st.rerun()

    # Markdown Export
    st.divider()
    st.markdown("#### 💾 Oflayn Saxlama və İxrac (Export)")
    
    export_lines = [
        f"# Mahammad AI Tutor - Kibertəhlükəsizlik Konspekti",
        f"**Tarix:** {time.strftime('%Y-%m-%d %H:%M')}",
        f"**Sahə:** {subject} | **Təcrübə Səviyyəsi:** {education_level}\n",
        "---",
        "## 📚 Dərs Konspektləri\n"
    ]
    if st.session_state.study_notes:
        for sn in st.session_state.study_notes:
            export_lines.append(f"### 📌 {sn.get('title')} ({sn.get('date')})")
            export_lines.append(f"{sn.get('content')}\n")
    else:
        export_lines.append("*Konspekt yoxdur.*\n")

    export_lines.append("---")
    export_lines.append("## 📕 Səhv Dəftəri (Düzəldilməli Məqamlar)\n")
    if st.session_state.mistake_book:
        for mb in st.session_state.mistake_book:
            export_lines.append(f"### ⚠️ {mb.get('topic')} ({mb.get('date')})")
            export_lines.append(f"- **Sual / Ssenari:** {mb.get('question')}")
            export_lines.append(f"- **Səhv Cavabım:** {mb.get('wrong_answer')}")
            export_lines.append(f"- **Düzgün Məntiq:** {mb.get('correct_reason')}\n")
    else:
        export_lines.append("*Səhv dəftəri boşdur.*\n")

    md_content = "\n".join(export_lines)
    st.download_button(
        label="📥 Konspekt və Səhv Dəftərini Yüklə (.md)",
        data=md_content,
        file_name=f"kiber_konspekt_{time.strftime('%Y%m%d')}.md",
        mime="text/markdown",
        use_container_width=True
    )
