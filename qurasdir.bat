@echo off
chcp 65001 >nul
title Mahammad Offline AI - Qurasdirici ve Basladici
color 0a
cls

echo ================================================================
echo       🛡️  MAHAMMAD OFLAYN AI SİSTEMİ - BAŞLADICI  🛡️
echo ================================================================
echo [Məlumat] Bu skript 'mahammad' oflayn modelini yoxlayır və başladır.
echo.

:: 1. Sistemdə Ollama mühərriki yoxlanılır
echo [*] 1/2: Sistemdə Ollama yoxlanılır...
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

echo [✓] Ollama sistemi aktivdir!
echo [*] 2/2: 'mahammad' modeli başladılır...
echo.
echo ================================================================
echo   Söhbət başladı! Çıxmaq üçün '/bye' yazıb Enter basın.
echo ================================================================
echo.

ollama run mahammad

if %errorlevel% neq 0 (
    color 0e
    echo.
    echo [!] Model işə düşmədi. Yerli modellər siyahınız:
    ollama list
    echo.
    echo Əgər model hələ yaradılmayıbsa:
    echo    ollama create mahammad -f Modelfile
    echo.
    pause
)
