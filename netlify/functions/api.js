const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const SECRET_KEY = 'mahammad-offline-ai-netlify-secret-2026';
const USERS_FILE = path.join('/tmp', 'users.json');

// users.json oxu və yaz
function readUsers() {
    try {
        if (!fs.existsSync(USERS_FILE)) {
            fs.writeFileSync(USERS_FILE, '[]', 'utf8');
            return [];
        }
        const data = fs.readFileSync(USERS_FILE, 'utf8');
        return JSON.parse(data || '[]');
    } catch (e) {
        return [];
    }
}

function saveUsers(users) {
    try {
        fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2), 'utf8');
    } catch (e) {
        console.error('Users write error:', e);
    }
}

// Şifrə Hash-ləmə (PBKDF2 SHA256)
function hashPassword(password, salt = null) {
    if (!salt) {
        salt = crypto.randomBytes(16).toString('hex');
    }
    const hash = crypto.pbkdf2Sync(password, salt, 100000, 32, 'sha256').toString('hex');
    return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
    try {
        const [salt, hash] = stored.split(':');
        const calc = crypto.pbkdf2Sync(password, salt, 100000, 32, 'sha256').toString('hex');
        return crypto.timingSafeEqual(Buffer.from(hash), Buffer.from(calc));
    } catch (e) {
        return false;
    }
}

// Token Yaratma və Doğrulama
function generateToken(user) {
    const payload = {
        id: user.id,
        email: user.email,
        name: user.name,
        exp: Math.floor(Date.now() / 1000) + (7 * 24 * 3600)
    };
    const b64 = Buffer.from(JSON.stringify(payload)).toString('base64url');
    const sig = crypto.createHmac('sha256', SECRET_KEY).update(b64).digest('hex');
    return `${b64}.${sig}`;
}

function verifyToken(token) {
    try {
        const [b64, sig] = token.split('.');
        const expected = crypto.createHmac('sha256', SECRET_KEY).update(b64).digest('hex');
        if (sig !== expected) return null;
        const payload = JSON.parse(Buffer.from(b64, 'base64url').toString('utf8'));
        if (payload.exp < Math.floor(Date.now() / 1000)) return null;
        return payload;
    } catch (e) {
        return null;
    }
}

// Netlify Serverless Handler
exports.handler = async (event, context) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json; charset=utf-8'
    };

    // Preflight OPTIONS
    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    const pathname = event.path.replace(/\/\.netlify\/functions\/api/, '').replace(/^\/api/, '');

    // 1. GET /me
    if (pathname === '/me' && event.httpMethod === 'GET') {
        const auth = event.headers.authorization || event.headers.Authorization || '';
        const token = auth.replace(/^Bearer\s+/, '').trim();
        const verified = verifyToken(token);

        if (!verified) {
            return {
                statusCode: 401,
                headers,
                body: JSON.stringify({ error: 'Sessiyanız bitib və ya daxil olmamısınız.' })
            };
        }

        const users = readUsers();
        const user = users.find(u => u.id === verified.id);

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                user: {
                    id: verified.id,
                    name: verified.name,
                    email: verified.email,
                    createdAt: user ? user.createdAt : ''
                }
            })
        };
    }

    // Yalnız POST metodları üçün body parse
    let body = {};
    if (event.httpMethod === 'POST') {
        try {
            body = JSON.parse(event.body || '{}');
        } catch (e) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'JSON formatı yanlışdır.' })
            };
        }
    }

    // 2. POST /register
    if (pathname === '/register' && event.httpMethod === 'POST') {
        const name = (body.name || '').trim();
        const email = (body.email || '').trim().toLowerCase();
        const password = body.password || '';

        if (!name || !email || !password) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'Ad, email və şifrə daxil edilməlidir.' })
            };
        }

        if (password.length < 6) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'Şifrə minimum 6 simvol olmalıdır.' })
            };
        }

        const users = readUsers();
        if (users.some(u => u.email === email)) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'Bu email artıq qeydiyyatdan keçib.' })
            };
        }

        const newUser = {
            id: 'usr_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 4),
            name,
            email,
            passwordHash: hashPassword(password),
            createdAt: new Date().toISOString()
        };

        users.push(newUser);
        saveUsers(users);

        const token = generateToken(newUser);
        return {
            statusCode: 201,
            headers,
            body: JSON.stringify({
                message: 'Qeydiyyat uğurla tamamlandı!',
                token,
                user: { id: newUser.id, name: newUser.name, email: newUser.email }
            })
        };
    }

    // 3. POST /login
    if (pathname === '/login' && event.httpMethod === 'POST') {
        const email = (body.email || '').trim().toLowerCase();
        const password = body.password || '';

        if (!email || !password) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'Email və şifrə daxil edilməlidir.' })
            };
        }

        const users = readUsers();
        const user = users.find(u => u.email === email);

        if (!user || !verifyPassword(password, user.passwordHash)) {
            return {
                statusCode: 401,
                headers,
                body: JSON.stringify({ error: 'Email və ya şifrə yanlışdır.' })
            };
        }

        const token = generateToken(user);
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                message: 'Uğurla daxil oldunuz!',
                token,
                user: { id: user.id, name: user.name, email: user.email }
            })
        };
    }

    return {
        statusCode: 404,
        headers,
        body: JSON.stringify({ error: 'Endpoint tapılmadı: ' + pathname })
    };
};
