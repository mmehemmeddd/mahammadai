# Mahammad Quraşdırma Təlimatı / Installation Guide

## 1. Tələblər (Prerequisites)
- Python 3.8 və ya daha yeni versiya
- Ollama (yerli süni intellekt modellərini işə salmaq üçün: https://ollama.com)

## 2. Asılılıqların quraşdırılması (Dependencies)
Layihə qovluğuna daxil olun və kitabxanaları quraşdırın:
```bash
pip install -r requirements.txt
```

## 3. Ollama Modelinin Seçilməsi və Endirilməsi
Ollama serverinin işlədiyindən əmin olun (`ollama serve`). Sonra ehtiyacınıza uyğun modeli yükləyin:
- Ümumi təhsil üçün:
  ```bash
  ollama pull gemma3
  ```
- Proqramlaşdırma və texniki fənlər üçün:
  ```bash
  ollama pull deepseek-coder
  ```
- Alternativ model:
  ```bash
  ollama pull llama3
  ```

## 4. Tətbiqi Başlatmaq (Run Application)
Streamlit interfeysini başladın:
```bash
streamlit run app.py
```
Brauzeriniz avtomatik olaraq `http://localhost:8501` səhifəsini açacaq.
