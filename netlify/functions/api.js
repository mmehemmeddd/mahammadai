const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const https = require('https');

const SECRET_KEY = 'mahammad-offline-ai-netlify-secret-2026';
const GOOGLE_CLIENT_ID = '427833067127-jaq0aob8eismkafbitvj70a56padb7l2.apps.googleusercontent.com';
const ADMIN_SECRET_KEY = process.env.ADMIN_KEY || 'admin12345';
const DEFAULT_GEMINI_KEY = process.env.GEMINI_API_KEY || process.env.gemini || process.env.GEMINI || '';
const USERS_FILE = path.join('/tmp', 'users.json');

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
    } catch (e) {}
}

function hashPassword(password, salt = null) {
    if (!salt) salt = crypto.randomBytes(16).toString('hex');
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

function verifyGoogleToken(idToken) {
    return new Promise((resolve, reject) => {
        const url = `https://oauth2.googleapis.com/tokeninfo?id_token=${encodeURIComponent(idToken)}`;
        https.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(data);
                    if (parsed.error_description || parsed.error) return reject(new Error(parsed.error_description || parsed.error));
                    if (parsed.aud !== GOOGLE_CLIENT_ID) return reject(new Error('Google Client ID uyğun gəlmir.'));
                    resolve(parsed);
                } catch (err) {
                    reject(err);
                }
            });
        }).on('error', reject);
    });
}

function requestGeminiChat(effectiveKey, model, messages, systemPrompt) {
    return new Promise((resolve, reject) => {
        const formattedContents = [];
        if (Array.isArray(messages)) {
            messages.forEach(msg => {
                const role = msg.role === 'assistant' ? 'model' : (msg.role === 'system' ? 'user' : msg.role);
                formattedContents.push({ role, parts: [{ text: msg.content || '' }] });
            });
        }

        const requestBody = {
            contents: formattedContents.length > 0 ? formattedContents : [{ role: 'user', parts: [{ text: 'Salam' }] }],
            generationConfig: { temperature: 0.7, maxOutputTokens: 2048 }
        };

        if (systemPrompt) {
            requestBody.system_instruction = { parts: [{ text: systemPrompt }] };
        }

        const targetModel = model || 'gemini-1.5-flash';
        const postData = JSON.stringify(requestBody);

        const options = {
            hostname: 'generativelanguage.googleapis.com',
            path: `/v1beta/models/${targetModel}:generateContent?key=${effectiveKey}`,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const result = JSON.parse(data);
                    if (result.error) {
                        return reject(new Error(result.error.message || 'Gemini API açarı etibarsızdır.'));
                    }
                    const text = result.candidates?.[0]?.content?.parts?.[0]?.text || 'Cavab alınmadı.';
                    resolve({ reply: text, model: targetModel, provider: 'gemini' });
                } catch (err) {
                    reject(err);
                }
            });
        });

        req.on('error', reject);
        req.write(postData);
        req.end();
    });
}

exports.handler = async (event, context) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-admin-key',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Content-Type': 'application/json; charset=utf-8'
    };

    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    const rawPath = event.path.replace(/\/\.netlify\/functions\/api/, '').replace(/^\/api/, '');
    const pathname = rawPath.replace(/\/$/, '') || '/';
    const authHeader = event.headers.authorization || event.headers.Authorization || '';
    const token = authHeader.replace(/^Bearer\s+/, '').trim();
    const adminKey = event.headers['x-admin-key'] || (event.queryStringParameters && event.queryStringParameters.admin_key);

    let body = {};
    if (['POST', 'PUT'].includes(event.httpMethod)) {
        try {
            body = JSON.parse(event.body || '{}');
        } catch (e) {
            return { statusCode: 400, headers, body: JSON.stringify({ error: 'JSON formatı yanlışdır.' }) };
        }
    }

    // 1. POST /chat (Gemini API)
    if (pathname === '/chat' && event.httpMethod === 'POST') {
        const { provider, model, messages, systemPrompt, apiKey } = body;
        if (provider !== 'gemini') {
            return { statusCode: 400, headers, body: JSON.stringify({ error: 'Yalnız "gemini" provayderi qəbul edilir.' }) };
        }

        const effectiveKey = apiKey || process.env.GEMINI_API_KEY || process.env.gemini || process.env.GEMINI || DEFAULT_GEMINI_KEY;
        if (!effectiveKey) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({
                    error: 'Gemini API açarı tapılmadı! Zəhmət olmasa Google AI Studio-dan pulsuz API açarı əldə edin və daxil edin.'
                })
            };
        }

        try {
            const chatResponse = await requestGeminiChat(effectiveKey, model, messages, systemPrompt);
            return { statusCode: 200, headers, body: JSON.stringify(chatResponse) };
        } catch (err) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: `Gemini API Xətası: ${err.message}` })
            };
        }
    }

    // 2. GET /me & GET /profile
    if ((pathname === '/me' || pathname === '/profile') && event.httpMethod === 'GET') {
        const verified = verifyToken(token);
        if (!verified) return { statusCode: 401, headers, body: JSON.stringify({ error: 'Sessiyanız bitib.' }) };
        const users = readUsers();
        const user = users.find(u => u.id === verified.id);
        if (!user) return { statusCode: 404, headers, body: JSON.stringify({ error: 'İstifadəçi tapılmadı.' }) };
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                user: {
                    id: user.id,
                    name: user.name,
                    email: user.email,
                    avatar: user.avatar || null,
                    bio: user.bio || '',
                    auth_provider: user.auth_provider || 'email',
                    createdAt: user.createdAt || ''
                }
            })
        };
    }

    // 3. PUT /profile
    if (pathname === '/profile' && event.httpMethod === 'PUT') {
        const verified = verifyToken(token);
        if (!verified) return { statusCode: 401, headers, body: JSON.stringify({ error: 'Giriş icazəsi yoxdur.' }) };
        const users = readUsers();
        const userIndex = users.findIndex(u => u.id === verified.id);
        if (userIndex === -1) return { statusCode: 404, headers, body: JSON.stringify({ error: 'İstifadəçi tapılmadı.' }) };

        const user = users[userIndex];
        const newName = body.name ? body.name.trim() : user.name;
        const newBio = body.bio !== undefined ? body.bio.trim() : (user.bio || '');
        const newAvatar = body.avatar !== undefined ? body.avatar.trim() : (user.avatar || null);

        if (body.newPassword) {
            if (user.auth_provider === 'google') {
                return { statusCode: 400, headers, body: JSON.stringify({ error: 'Google hesablarının şifrəsi dəyişdirilə bilməz.' }) };
            }
            if (!body.oldPassword || !verifyPassword(body.oldPassword, user.passwordHash)) {
                return { statusCode: 400, headers, body: JSON.stringify({ error: 'Köhnə şifrəniz yanlışdır.' }) };
            }
            if (body.newPassword.length < 6) {
                return { statusCode: 400, headers, body: JSON.stringify({ error: 'Yeni şifrə minimum 6 simvol olmalıdır.' }) };
            }
            user.passwordHash = hashPassword(body.newPassword);
        }

        user.name = newName;
        user.bio = newBio;
        user.avatar = newAvatar;
        users[userIndex] = user;
        saveUsers(users);

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                message: 'Profiliniz uğurla yeniləndi!',
                user: {
                    id: user.id,
                    name: user.name,
                    email: user.email,
                    avatar: user.avatar,
                    bio: user.bio,
                    auth_provider: user.auth_provider || 'email',
                    createdAt: user.createdAt
                }
            })
        };
    }

    // 4. POST /auth/google
    if (pathname === '/auth/google' && event.httpMethod === 'POST') {
        try {
            const { credential } = body;
            if (!credential) return { statusCode: 400, headers, body: JSON.stringify({ error: 'Google credential tələb olunur.' }) };

            const googleUser = await verifyGoogleToken(credential);
            const email = (googleUser.email || '').trim().toLowerCase();
            const name = googleUser.name || 'Google İstifadəçisi';
            const picture = googleUser.picture || null;

            const users = readUsers();
            let user = users.find(u => u.email === email);

            if (!user) {
                user = {
                    id: 'usr_g_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 4),
                    name,
                    email,
                    passwordHash: null,
                    avatar: picture,
                    bio: '',
                    auth_provider: 'google',
                    createdAt: new Date().toISOString()
                };
                users.push(user);
                saveUsers(users);
            } else {
                if (picture && user.avatar !== picture) {
                    user.avatar = picture;
                    saveUsers(users);
                }
            }

            const token = generateToken(user);
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    message: 'Google ilə uğurla daxil oldunuz!',
                    token,
                    user: { id: user.id, name: user.name, email: user.email, avatar: user.avatar, auth_provider: 'google' }
                })
            };
        } catch (err) {
            return { statusCode: 401, headers, body: JSON.stringify({ error: 'Google tokeni doğrulanmadı: ' + err.message }) };
        }
    }

    // 5. POST /register
    if (pathname === '/register' && event.httpMethod === 'POST') {
        const name = (body.name || '').trim();
        const email = (body.email || '').trim().toLowerCase();
        const password = body.password || '';

        if (!name || !email || !password) return { statusCode: 400, headers, body: JSON.stringify({ error: 'Ad, email və şifrə daxil edilməlidir.' }) };
        if (password.length < 6) return { statusCode: 400, headers, body: JSON.stringify({ error: 'Şifrə minimum 6 simvol olmalıdır.' }) };

        const users = readUsers();
        if (users.some(u => u.email === email)) return { statusCode: 400, headers, body: JSON.stringify({ error: 'Bu email artıq qeydiyyatdan keçib.' }) };

        const newUser = {
            id: 'usr_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 4),
            name,
            email,
            passwordHash: hashPassword(password),
            avatar: null,
            bio: '',
            auth_provider: 'email',
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
                user: { id: newUser.id, name: newUser.name, email: newUser.email, avatar: null, auth_provider: 'email' }
            })
        };
    }

    // 6. POST /login
    if (pathname === '/login' && event.httpMethod === 'POST') {
        const email = (body.email || '').trim().toLowerCase();
        const password = body.password || '';

        if (!email || !password) return { statusCode: 400, headers, body: JSON.stringify({ error: 'Email və şifrə daxil edilməlidir.' }) };

        const users = readUsers();
        const user = users.find(u => u.email === email);

        if (!user) return { statusCode: 401, headers, body: JSON.stringify({ error: 'Email və ya şifrə yanlışdır.' }) };
        if (!user.passwordHash && user.auth_provider === 'google') return { statusCode: 400, headers, body: JSON.stringify({ error: 'Bu hesaba Google ilə daxil olunub.' }) };
        if (!verifyPassword(password, user.passwordHash)) return { statusCode: 401, headers, body: JSON.stringify({ error: 'Email və ya şifrə yanlışdır.' }) };

        const token = generateToken(user);
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                message: 'Uğurla daxil oldunuz!',
                token,
                user: { id: user.id, name: user.name, email: user.email, avatar: user.avatar, auth_provider: user.auth_provider || 'email' }
            })
        };
    }

    // 7. GET /admin/users
    if (pathname === '/admin/users' && event.httpMethod === 'GET') {
        if (adminKey !== ADMIN_SECRET_KEY) return { statusCode: 403, headers, body: JSON.stringify({ error: 'Admin icazəsi yoxdur.' }) };
        const users = readUsers().map(u => ({
            id: u.id,
            name: u.name,
            email: u.email,
            avatar: u.avatar || null,
            bio: u.bio || '',
            auth_provider: u.auth_provider || 'email',
            createdAt: u.createdAt || ''
        }));
        return { statusCode: 200, headers, body: JSON.stringify({ users }) };
    }

    // 8. DELETE /admin/users/:id
    const deleteMatch = pathname.match(/^\/admin\/users\/([^/]+)$/);
    if (deleteMatch && event.httpMethod === 'DELETE') {
        if (adminKey !== ADMIN_SECRET_KEY) return { statusCode: 403, headers, body: JSON.stringify({ error: 'Admin icazəsi yoxdur.' }) };
        const targetId = deleteMatch[1];
        let users = readUsers();
        const initialLen = users.length;
        users = users.filter(u => u.id !== targetId);
        if (users.length === initialLen) return { statusCode: 404, headers, body: JSON.stringify({ error: 'İstifadəçi tapılmadı.' }) };
        saveUsers(users);
        return { statusCode: 200, headers, body: JSON.stringify({ message: 'İstifadəçi uğurla silindi.' }) };
    }

    return { statusCode: 404, headers, body: JSON.stringify({ error: 'Endpoint tapılmadı: ' + pathname }) };
};
