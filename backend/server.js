const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const https = require('https');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { OAuth2Client } = require('google-auth-library');
const sqlite3 = require('sqlite3').verbose();

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'mahammad-offline-ai-ultra-secure-key-2026';
const GOOGLE_CLIENT_ID = '427833067127-jaq0aob8eismkafbitvj70a56padb7l2.apps.googleusercontent.com';
const ADMIN_SECRET_KEY = process.env.ADMIN_KEY || 'admin12345';
const DEFAULT_GEMINI_KEY = process.env.GEMINI_API_KEY || '';
const DB_FILE = path.join(__dirname, 'database.sqlite');
const LEGACY_USERS_FILE = path.join(__dirname, 'users.json');

const googleClient = new OAuth2Client(GOOGLE_CLIENT_ID);

// Middleware
app.use(cors());
app.use(express.json());

// Frontend fayllarını statik olaraq təqdim et
app.use(express.static(path.join(__dirname, '..')));

// ==========================================
// SQLITE VERİLƏNLƏR BAZASI VƏ MİQRASİYA
// ==========================================
const db = new sqlite3.Database(DB_FILE, (err) => {
    if (err) {
        console.error('[Xəta] SQLite bazasına qoşularkən xəta:', err.message);
    } else {
        console.log('[✓] SQLite verilənlər bazası hazırdır:', DB_FILE);
    }
});

db.serialize(() => {
    db.run(`
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
    `);

    // Təhlükəsiz ALTER TABLE miqrasiyası
    const migrations = [
        "ALTER TABLE users ADD COLUMN avatar TEXT",
        "ALTER TABLE users ADD COLUMN bio TEXT",
        "ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'email'"
    ];

    migrations.forEach((sql) => {
        db.run(sql, () => {});
    });

    // Əgər baza boşdursa və köhnə users.json varsa, köçür
    db.get("SELECT COUNT(*) as count FROM users", (err, row) => {
        if (!err && row && row.count === 0 && fs.existsSync(LEGACY_USERS_FILE)) {
            try {
                const legacy = JSON.parse(fs.readFileSync(LEGACY_USERS_FILE, 'utf8') || '[]');
                if (legacy.length > 0) {
                    const stmt = db.prepare(`
                        INSERT OR IGNORE INTO users (id, name, email, password_hash, avatar, bio, auth_provider, createdAt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    `);
                    legacy.forEach(u => {
                        stmt.run(
                            u.id || ('usr_' + Date.now().toString(36)),
                            u.name,
                            u.email,
                            u.passwordHash || null,
                            u.avatar || null,
                            u.bio || '',
                            u.auth_provider || 'email',
                            u.createdAt || new Date().toISOString()
                        );
                    });
                    stmt.finalize();
                }
            } catch (e) {}
        }
    });
});

// Promisified DB metodları
function dbGet(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
}

function dbAll(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) reject(err);
            else resolve(rows);
        });
    });
}

function dbRun(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function (err) {
            if (err) reject(err);
            else resolve(this);
        });
    });
}

// Token doğrulama middleware
function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ error: 'Giriş icazəsi yoxdur. Zəhmət olmasa daxil olun.' });
    }

    jwt.verify(token, JWT_SECRET, (err, userPayload) => {
        if (err) {
            return res.status(403).json({ error: 'Sessiyanızın vaxtı bitib və ya token yanlışdır.' });
        }
        req.user = userPayload;
        next();
    });
}

// Admin yoxlama middleware
function authenticateAdmin(req, res, next) {
    const adminKey = req.headers['x-admin-key'] || req.query.admin_key;
    if (adminKey && adminKey === ADMIN_SECRET_KEY) {
        return next();
    }
    return res.status(403).json({ error: 'Admin icazəsi yoxdur. Yanlış açar.' });
}

// ==========================================
// CHAT API: GEMINI INTEGRATION
// ==========================================
app.post('/api/chat', async (req, res) => {
    try {
        const { provider, model, messages, systemPrompt, apiKey } = req.body;

        if (provider !== 'gemini') {
            return res.status(400).json({ error: 'Yalnız "gemini" provayderi server üzərindən qəbul edilir. Lokal Ollama üçün birbaşa brauzerdən localhost:11434 istifadə olunur.' });
        }

        const effectiveKey = apiKey || process.env.GEMINI_API_KEY || DEFAULT_GEMINI_KEY;

        if (!effectiveKey) {
            return res.status(400).json({
                error: 'Gemini API açarı tapılmadı! Zəhmət olmasa Google AI Studio-dan (https://aistudio.google.com) pulsuz API açarı əldə edərək interfeysdə daxil edin və ya serverdə GEMINI_API_KEY mühit dəyişənini təyin edin.'
            });
        }

        // Gemini üçün mesajları formatla
        const formattedContents = [];
        if (Array.isArray(messages)) {
            messages.forEach(msg => {
                const role = msg.role === 'assistant' ? 'model' : (msg.role === 'system' ? 'user' : msg.role);
                formattedContents.push({
                    role: role,
                    parts: [{ text: msg.content || '' }]
                });
            });
        }

        const requestBody = {
            contents: formattedContents.length > 0 ? formattedContents : [{ role: 'user', parts: [{ text: 'Salam' }] }],
            generationConfig: {
                temperature: 0.7,
                maxOutputTokens: 2048
            }
        };

        if (systemPrompt) {
            requestBody.system_instruction = {
                parts: [{ text: systemPrompt }]
            };
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

        const apiReq = https.request(options, (apiRes) => {
            let data = '';
            apiRes.on('data', chunk => data += chunk);
            apiRes.on('end', () => {
                try {
                    const result = JSON.parse(data);
                    if (result.error) {
                        return res.status(apiRes.statusCode || 400).json({
                            error: `Gemini API Xətası: ${result.error.message || 'Açar etibarsızdır və ya kvota bitib.'}`
                        });
                    }

                    const candidate = result.candidates && result.candidates[0];
                    const replyText = candidate?.content?.parts?.[0]?.text || 'Cavab alına bilmədi.';

                    return res.json({
                        reply: replyText,
                        model: targetModel,
                        provider: 'gemini'
                    });
                } catch (parseErr) {
                    return res.status(500).json({ error: 'Gemini cavabı emal edilərkən xəta baş verdi.' });
                }
            });
        });

        apiReq.on('error', (err) => {
            return res.status(500).json({ error: 'Gemini serverinə qoşularkən xəta: ' + err.message });
        });

        apiReq.write(postData);
        apiReq.end();
    } catch (err) {
        console.error('[Xəta] Chat API:', err);
        return res.status(500).json({ error: 'Server daxili xətası baş verdi.' });
    }
});

// ==========================================
// AUTH & GOOGLE API ENDPOINT-LƏR
// ==========================================

// 1. Qeydiyyat (POST /api/register)
app.post('/api/register', async (req, res) => {
    try {
        const { name, email, password } = req.body;

        if (!name || !email || !password) {
            return res.status(400).json({ error: 'Ad, email və şifrə daxil edilməlidir.' });
        }

        const normalizedEmail = email.trim().toLowerCase();
        if (password.length < 6) {
            return res.status(400).json({ error: 'Şifrə minimum 6 simvol olmalıdır.' });
        }

        const existing = await dbGet("SELECT id FROM users WHERE email = ?", [normalizedEmail]);
        if (existing) {
            return res.status(400).json({ error: 'Bu email artıq qeydiyyatdan keçib.' });
        }

        const salt = await bcrypt.genSalt(10);
        const passwordHash = await bcrypt.hash(password, salt);
        const userId = 'usr_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 4);
        const createdAt = new Date().toISOString();

        await dbRun(`
            INSERT INTO users (id, name, email, password_hash, avatar, bio, auth_provider, createdAt)
            VALUES (?, ?, ?, ?, ?, ?, 'email', ?)
        `, [userId, name.trim(), normalizedEmail, passwordHash, null, '', createdAt]);

        const token = jwt.sign(
            { id: userId, name: name.trim(), email: normalizedEmail },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        return res.status(201).json({
            message: 'Qeydiyyat uğurla tamamlandı!',
            token,
            user: { id: userId, name: name.trim(), email: normalizedEmail, avatar: null, auth_provider: 'email' }
        });
    } catch (err) {
        return res.status(500).json({ error: 'Daxili server xətası baş verdi.' });
    }
});

// 2. Giriş (POST /api/login)
app.post('/api/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        if (!email || !password) {
            return res.status(400).json({ error: 'Email və şifrə daxil edilməlidir.' });
        }

        const normalizedEmail = email.trim().toLowerCase();
        const user = await dbGet("SELECT * FROM users WHERE email = ?", [normalizedEmail]);

        if (!user) {
            return res.status(401).json({ error: 'Email və ya şifrə yanlışdır.' });
        }

        if (!user.password_hash && user.auth_provider === 'google') {
            return res.status(400).json({ error: 'Bu hesaba Google ilə daxil olunub. Google düyməsindən istifadə edin.' });
        }

        const isMatch = await bcrypt.compare(password, user.password_hash);
        if (!isMatch) {
            return res.status(401).json({ error: 'Email və ya şifrə yanlışdır.' });
        }

        const token = jwt.sign(
            { id: user.id, name: user.name, email: user.email },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        return res.json({
            message: 'Uğurla daxil oldunuz!',
            token,
            user: { id: user.id, name: user.name, email: user.email, avatar: user.avatar, auth_provider: user.auth_provider }
        });
    } catch (err) {
        return res.status(500).json({ error: 'Daxili server xətası baş verdi.' });
    }
});

// 3. Google ilə Daxil Ol (POST /api/auth/google)
app.post('/api/auth/google', async (req, res) => {
    try {
        const { credential } = req.body;
        if (!credential) {
            return res.status(400).json({ error: 'Google credential tələb olunur.' });
        }

        const ticket = await googleClient.verifyIdToken({
            idToken: credential,
            audience: GOOGLE_CLIENT_ID
        });

        const payload = ticket.getPayload();
        const email = (payload.email || '').trim().toLowerCase();
        const name = payload.name || 'Google İstifadəçisi';
        const picture = payload.picture || null;

        if (!email) {
            return res.status(400).json({ error: 'Google hesabından email alına bilmədi.' });
        }

        let user = await dbGet("SELECT * FROM users WHERE email = ?", [email]);

        if (!user) {
            const userId = 'usr_g_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 4);
            const createdAt = new Date().toISOString();

            await dbRun(`
                INSERT INTO users (id, name, email, password_hash, avatar, bio, auth_provider, createdAt)
                VALUES (?, ?, ?, NULL, ?, '', 'google', ?)
            `, [userId, name, email, picture, createdAt]);

            user = { id: userId, name, email, avatar: picture, auth_provider: 'google', createdAt };
        } else {
            if (picture && (!user.avatar || user.avatar !== picture)) {
                await dbRun("UPDATE users SET avatar = ? WHERE id = ?", [picture, user.id]);
                user.avatar = picture;
            }
        }

        const token = jwt.sign(
            { id: user.id, name: user.name, email: user.email },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        return res.json({
            message: 'Google ilə uğurla daxil oldunuz!',
            token,
            user: {
                id: user.id,
                name: user.name,
                email: user.email,
                avatar: user.avatar,
                auth_provider: user.auth_provider || 'google'
            }
        });
    } catch (err) {
        return res.status(401).json({ error: 'Google tokeni doğrulanmadı: ' + err.message });
    }
});

// 4. GET /api/me
app.get('/api/me', authenticateToken, async (req, res) => {
    try {
        const user = await dbGet("SELECT id, name, email, avatar, bio, auth_provider, createdAt FROM users WHERE id = ?", [req.user.id]);
        if (!user) return res.status(404).json({ error: 'İstifadəçi tapılmadı.' });
        return res.json({ user });
    } catch (err) {
        return res.status(500).json({ error: 'Məlumat alınarkən xəta baş verdi.' });
    }
});

// 5. GET /api/profile
app.get('/api/profile', authenticateToken, async (req, res) => {
    try {
        const user = await dbGet("SELECT id, name, email, avatar, bio, auth_provider, createdAt FROM users WHERE id = ?", [req.user.id]);
        if (!user) return res.status(404).json({ error: 'İstifadəçi tapılmadı.' });
        return res.json({ user });
    } catch (err) {
        return res.status(500).json({ error: 'Profil məlumatı alınmadı.' });
    }
});

// 6. PUT /api/profile
app.put('/api/profile', authenticateToken, async (req, res) => {
    try {
        const { name, bio, avatar, oldPassword, newPassword } = req.body;
        const user = await dbGet("SELECT * FROM users WHERE id = ?", [req.user.id]);

        if (!user) return res.status(404).json({ error: 'İstifadəçi tapılmadı.' });

        const newName = name ? name.trim() : user.name;
        const newBio = bio !== undefined ? bio.trim() : (user.bio || '');
        const newAvatar = avatar !== undefined ? avatar.trim() : (user.avatar || null);

        let newPasswordHash = user.password_hash;
        if (newPassword) {
            if (user.auth_provider === 'google') {
                return res.status(400).json({ error: 'Google ilə daxil olmuş hesabların şifrəsi dəyişdirilə bilməz.' });
            }
            if (!oldPassword) {
                return res.status(400).json({ error: 'Şifrəni dəyişmək üçün köhnə şifrənizi daxil edin.' });
            }
            const isMatch = await bcrypt.compare(oldPassword, user.password_hash);
            if (!isMatch) {
                return res.status(400).json({ error: 'Köhnə şifrəniz yanlışdır.' });
            }
            if (newPassword.length < 6) {
                return res.status(400).json({ error: 'Yeni şifrə minimum 6 simvol olmalıdır.' });
            }
            const salt = await bcrypt.genSalt(10);
            newPasswordHash = await bcrypt.hash(newPassword, salt);
        }

        await dbRun(`
            UPDATE users 
            SET name = ?, bio = ?, avatar = ?, password_hash = ?
            WHERE id = ?
        `, [newName, newBio, newAvatar, newPasswordHash, user.id]);

        return res.json({
            message: 'Profiliniz uğurla yeniləndi!',
            user: {
                id: user.id,
                name: newName,
                email: user.email,
                avatar: newAvatar,
                bio: newBio,
                auth_provider: user.auth_provider,
                createdAt: user.createdAt
            }
        });
    } catch (err) {
        return res.status(500).json({ error: 'Profil yenilənərkən xəta baş verdi.' });
    }
});

// 7. GET /api/admin/users
app.get('/api/admin/users', authenticateAdmin, async (req, res) => {
    try {
        const users = await dbAll(`
            SELECT id, name, email, avatar, bio, auth_provider, createdAt 
            FROM users 
            ORDER BY rowid DESC
        `);
        return res.json({ users });
    } catch (err) {
        return res.status(500).json({ error: 'İstifadəçi siyahısı alınmadı.' });
    }
});

// 8. DELETE /api/admin/users/:id
app.delete('/api/admin/users/:id', authenticateAdmin, async (req, res) => {
    try {
        const { id } = req.params;
        const result = await dbRun("DELETE FROM users WHERE id = ?", [id]);
        if (result.changes === 0) {
            return res.status(404).json({ error: 'İstifadəçi tapılmadı.' });
        }
        return res.json({ message: 'İstifadəçi uğurla silindi.' });
    } catch (err) {
        return res.status(500).json({ error: 'İstifadəçi silinərkən xəta baş verdi.' });
    }
});

app.listen(PORT, () => {
    console.log(`=======================================================`);
    console.log(`🛡️  MAHAMMAD OFFLINE AI & GEMINI CHAT BACKEND`);
    console.log(`👉 Server ünvanı: http://localhost:${PORT}`);
    console.log(`👉 Veb sayt:      http://localhost:${PORT}/index.html`);
    console.log(`👉 Admin Panel:   http://localhost:${PORT}/admin.html`);
    console.log(`=======================================================`);
});
