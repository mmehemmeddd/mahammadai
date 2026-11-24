# 🛡️ Mahammad Cyber & Bug Bounty Tutor

Tamamilə oflayn və məxfi işləyən, **Kibertəhlükəsizlik və Bug Bounty** sahəsinə ixtisaslaşdırılmış interaktiv Sokratik Süni İntellekt Mentoru.

---

## 🌟 Əsas Funksiyalar və Yeniliklər

### 1. 📚 Lokal Fayl və Şəxsi Qeydlər Əlavə Etmə (Öz Materialı Üzərindən Tədris)
- **Fayl Dəstəyi**: `.txt`, `.md`, və `.pdf` sənədlərini (hədəf scope, pentest hesabatları, metodologiyalar) yükləyərək AI-a təqdim edə bilərsiniz.
- **Şəxsi Qeyd & Writeup Daxiletmə**: Yan paneldə "➕ Yeni Qeyd / Writeup Əlavə Et" bölməsindən öz şəxsi araşdırma qeydlərinizi yadda saxlayın; AI dərhal bu qeydləri təhlil edib cavablarına daxil edir.
- Bütün materiallar lokal yaddaşda qalır, heç bir xarici serverə göndərilmir.

### 2. 🎯 "Məni Sına" + Pilləli İpucu Məntiqi (Aktiv Praktiki Məşq)
- Passiv mətn oxumaqdan aktiv zəiflik ovuna keçid!
- Mentor sizə real bug bounty laboratoriya ssenariləri və zəif HTTP sorğuları/kod parçaları təqdim edir.
- **3-Mərhələli İpucu Sistemi**:
  - 💡 *İpucu 1:* İstiqamətləndirici ilkin işarə (hansı başlıq/parametrə baxmalı).
  - 💡 *İpucu 2:* Məntiqi boşluğun işləmə mexanizmi.
  - 💡 *İpucu 3:* Zəifliyi təsdiqləmək üçün konkret addım və PoC istiqaməti.
- Tələbə öz təhlilini yazdıqdan sonra mentor onu dəyərləndirir, düzgün yanaşmanı tərifləyir, səhv olduqda isə yumşaq şəkildə izah edir və avtomatik olaraq **Səhv Dəftəri**nə qeyd edir.

### 3. 📓 Dərs Konspekti və Səhv Dəftəri (Öyrənilənlərin İtməməsi)
- **📚 Dərs Konspekti (Study Notes)**: Mentor izahlarının və ya laboratoriya həllərinin altındakı "📌 Konspektə Saxla" düyməsi ilə vacib nəticələri bir toxunuşla qeyd edin. İstənilən vaxt əllə yeni qeyd əlavə edə bilərsiniz.
- **📕 Səhv Dəftəri (Mistake Notebook)**: "Məni Sına" və ya "Test" bölməsində etdiyiniz yanlış cavablar avtomatik olaraq bura yazılır. Zəif tərəflərinizi təkrarladıqdan sonra "✅ Öyrəndim" düyməsi ilə silə bilərsiniz.
- **💾 Markdown İxracı (.md Download)**: Tək düymə ilə bütün konspektinizi və səhv dəftərinizi formatlanmış `kiber_konspekt.md` faylı kimi endirib arxivləşdirin.

### 4. 🧑‍🏫 Sokratik Tədris Metodologiyası
- **Qəti Qayda:** Birbaşa hazır exploit və ya həll vermir.
- Zəifliyin kök səbəbini (root cause) izah edir və tələbəyə istiqamətləndirici sual verərək addım-addım düşünməyə sövq edir.
- Sonda bilikləri yoxlamaq üçün 1-2 kiçik yoxlama sualı verir.

### 5. 🎨 İsti Kağız & Sakit Adaçayı Yaşılı Dizayn (Paper & Sage Green)
- Göz yormayan, kitabxana/dəftər sakitliyində təmiz interfeys:
  - Əsas fon: `#FAF6EE` (isti krem kağız)
  - Kart və panellər: `#FFFDF9`
  - Vurğu və düymələr: `#2F6F5E` (adaçayı yaşılı)
  - Yazı rəngi: `#232621` (yumşaq zeytun-şifer)

---

## ⚡ Tez Başlama (Oflayn İşə Salma)

### 1. Asılılıqlar
```powershell
python -m pip install streamlit requests pypdf
```

### 2. Tətbiqi Başlatmaq
```powershell
cd C:\Users\ilqar\.gemini\antigravity\scratch\mahammad
python -m streamlit run app.py
```

### 3. Sürətli Model Tövsiyəsi (Ollama)
CPU-da dərhal, saniyəlik cavablar almaq üçün yüngül və sürətli model tövsiyə olunur:
```powershell
ollama pull qwen2.5:1.5b
```
*(Əgər `gemma3` modeliniz varsa, tətbiq onu avtomatik aşkar edir və CPU üçün optimallaşdırılmış parametrlərlə işlədir).*
