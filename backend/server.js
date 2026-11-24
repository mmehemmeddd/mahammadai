const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'mahammad-offline-ai-ultra-secure-key-2026';
const USERS_FILE = path.join(__dirname, 'users.json');

// Middleware
app.use(cors());
app.use(express.json());

// Frontend fayllarını (index.html, qurasdir.bat və s.) statik olaraq təqdim et
app.use(express.static(path.join(__dirname, '..')));

// Köməkçi funksiyalar: users.json oxu və yaz
function readUsers() {
    try {
        if (!fs.existsSync(USERS_FILE)) {
            fs.writeFileSync(USERS_FILE, '[]', 'utf8');
            return [];
        }
        const data = fs.readFileSync(USERS_FILE, 'utf8');
        return JSON.parse(data || '[]');
    } catch (err) {
        console.error('[Xəta] users.json oxunarkən xəta:', err.message);
        return [];
    }
}

function saveUsers(users) {
    try {
        fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2), 'utf8');
        return true;
    } catch (err) {
        console.error('[Xəta] users.json yazılarkən xəta:', err.message);
        return false;
    }
}

// Token doğrulama middleware
function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1]; // "Bearer <TOKEN>"

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

// ==========================================
// API ENDPOINT-LƏR
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

        const users = readUsers();

        // Emailin mövcudluğunu yoxla
        const existingUser = users.find(u => u.email === normalizedEmail);
        if (existingUser) {
            return res.status(400).json({ error: 'Bu email artıq qeydiyyatdan keçib.' });
        }

        // Şifrəni bcrypt ilə hash-lə
        const salt = await bcrypt.genSalt(10);
        const passwordHash = await bcrypt.hash(password, salt);

        const newUser = {
            id: 'usr_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5),
            name: name.trim(),
            email: normalizedEmail,
            passwordHash,
            createdAt: new Date().toISOString()
        };

        users.push(newUser);
        saveUsers(users);

        // JWT Token yarat
        const token = jwt.sign(
            { id: newUser.id, name: newUser.name, email: newUser.email },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        return res.status(201).json({
            message: 'Qeydiyyat uğurla tamamlandı!',
            token,
            user: {
                id: newUser.id,
                name: newUser.name,
                email: newUser.email,
                createdAt: newUser.createdAt
            }
        });
    } catch (err) {
        console.error('[Xəta] Register API:', err);
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
        const users = readUsers();

        const user = users.find(u => u.email === normalizedEmail);
        if (!user) {
            return res.status(401).json({ error: 'Email və ya şifrə yanlışdır.' });
        }

        // Şifrəni yoxla
        const isMatch = await bcrypt.compare(password, user.passwordHash);
        if (!isMatch) {
            return res.status(401).json({ error: 'Email və ya şifrə yanlışdır.' });
        }

        // JWT Token yarat
        const token = jwt.sign(
            { id: user.id, name: user.name, email: user.email },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        return res.json({
            message: 'Uğurla daxil oldunuz!',
            token,
            user: {
                id: user.id,
                name: user.name,
                email: user.email,
                createdAt: user.createdAt
            }
        });
    } catch (err) {
        console.error('[Xəta] Login API:', err);
        return res.status(500).json({ error: 'Daxili server xətası baş verdi.' });
    }
});

// 3. Cari İstifadəçi Məlumatı (GET /api/me)
app.get('/api/me', authenticateToken, (req, res) => {
    const users = readUsers();
    const user = users.find(u => u.id === req.user.id);

    if (!user) {
        return res.status(404).json({ error: 'İstifadəçi tapılmadı.' });
    }

    return res.json({
        user: {
            id: user.id,
            name: user.name,
            email: user.email,
            createdAt: user.createdAt
        }
    });
});

// Serveri başlat
app.listen(PORT, () => {
    console.log(`=======================================================`);
    console.log(`🛡️  MAHAMMAD OFFLINE AI BACKEND AKTİVDİR!`);
    console.log(`👉 Server ünvanı: http://localhost:${PORT}`);
    console.log(`👉 Veb interfeys: http://localhost:${PORT}/index.html`);
    console.log(`=======================================================`);
});
