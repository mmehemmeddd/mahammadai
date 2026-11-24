@echo off
chcp 65001 >nul
title Mahammad Offline AI - Ağıllı Başladıcı və Quraşdırıcı
color 0a
cls

echo ================================================================
echo       🛡️  MAHAMMAD OFLAYN AI SİSTEMİ - AĞILLI BAŞLADICI  🛡️
echo ================================================================
echo [Məlumat] Bu skript brauzer inteqrasiyasını və oflayn AI modelini qurur.
echo.

:: 1. Sistemdə Ollama mühərriki yoxlanılır
echo [*] 1/3: Sistemdə Ollama mühərriki yoxlanılır...
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    color 0c
    echo.
    echo ================================================================
    echo [X] XƏTA: Kompüterinizdə Ollama tapılmadı!
    echo ================================================================
    echo Oflayn modelin işləməsi üçün Ollama quraşdırılmalıdır.
    echo Rəsmi yükləmə səhifəsi brauzerinizdə açılır...
    echo.
    timeout /t 2 >nul
    start https://ollama.com/download/windows
    echo Zəhmət olmasa Ollamanı qurduqdan sonra bu faylı yenidən açın.
    echo ================================================================
    pause
    exit /b 1
)
echo [✓] Ollama mühərriki aktivdir!

:: 2. Veb Brauzer və Netlify ilə əlaqə üçün CORS konfiqurasiyası
echo [*] 2/3: Brauzerlə əlaqə üçün CORS icazələri sazlanır (OLLAMA_ORIGINS)...
setx OLLAMA_ORIGINS "*" >nul 2>nul
set OLLAMA_ORIGINS=*
echo [✓] CORS icazəsi uğurla aktivləşdirildi (*).

:: 3. Model Seçimi
echo.
echo ================================================================
echo        🤖 ZƏHMƏT OLMASA İSTİFADƏ EDƏCƏYİNİZ MODELİ SEÇİN
echo ================================================================
echo   [1] Sürətli / Yüngül      (qwen2.5:3b)       - 4-8 GB RAM üçün ideal
echo   [2] Balanslı / Standart    (llama3.1:8b)      - 8-16 GB RAM üçün əla
echo   [3] Kodlaşdırma Eksperti   (qwen2.5-coder:7b) - Proqramlaşdırma və Kiber Analiz
echo   [4] Mahammad Xüsusi Model  (mahammad)         - Xüsusi Lokal Model
echo ================================================================
set /p MODEL_CHOICE="Seçiminizi daxil edin [1, 2, 3 və ya 4] (Standart 1): "

set TARGET_MODEL=qwen2.5:3b
if "%MODEL_CHOICE%"=="1" set TARGET_MODEL=qwen2.5:3b
if "%MODEL_CHOICE%"=="2" set TARGET_MODEL=llama3.1:8b
if "%MODEL_CHOICE%"=="3" set TARGET_MODEL=qwen2.5-coder:7b
if "%MODEL_CHOICE%"=="4" set TARGET_MODEL=mahammad

echo.
echo [*] 3/3: Seçilmiş model yoxlanılır və yüklənir: %TARGET_MODEL%...
echo (Əgər model kompüterinizdə yoxdursa, avtomatik endiriləcək)
echo.

ollama pull %TARGET_MODEL%

echo.
echo ================================================================
echo   ✓ Model hazırdır! Canlı terminal söhbəti başladılır.
echo   ℹ️ Veb səhifədəki "AI Chat" bölməsi də indi canlı qoşulacaq!
echo   Çıxmaq üçün '/bye' yazıb Enter basın.
echo ================================================================
echo.

ollama run %TARGET_MODEL%

if %errorlevel% neq 0 (
    color 0e
    echo.
    echo [!] Model işə salına bilmədi. Yerli modelləriniz:
    ollama list
    echo.
    echo Əgər 'mahammad' modeli üçün Modelfile tələb olunursa:
    echo    ollama create mahammad -f Modelfile
    echo.
    pause
)
