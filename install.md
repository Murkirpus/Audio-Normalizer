# 🚀 Быстрая установка Audio Normalizer

## Для нетерпеливых (5 минут)

### Windows 10/11

**1. Установите Python** (2 минуты)
```
Скачайте: https://www.python.org/downloads/
✅ Обязательно отметьте "Add Python to PATH"!
```

**2. Установите FFmpeg** (3 минуты)
```
Скачайте: https://www.gyan.dev/ffmpeg/builds/
Выберите: ffmpeg-release-essentials.zip
Распакуйте в: C:\ffmpeg
```

Добавьте в PATH:
1. `Win + Pause` → "Дополнительные параметры системы"
2. "Переменные среды" → "Path" → "Изменить"
3. "Создать" → Добавьте: `C:\ffmpeg\bin`
4. ОК везде
5. **Перезапустите командную строку!**

**3. Проверьте установку**
```bash
python --version
ffmpeg -version
```
Если обе команды показывают версии - всё готово! ✅

**4. Запустите программу**
```bash
python audio_normalizer.py
```

---

### Linux (Ubuntu/Debian)

```bash
# Установка всего за 30 секунд
sudo apt update
sudo apt install python3 python3-pip python3-tk ffmpeg

# Проверка
python3 --version
ffmpeg -version

# Запуск
python3 audio_normalizer.py
```

---

### macOS

```bash
# Установите Homebrew (если нет)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установка
brew install python3 ffmpeg

# Проверка
python3 --version
ffmpeg -version

# Запуск
python3 audio_normalizer.py
```

---

## ⚠️ Частые ошибки

### "ffmpeg не найден"
- Проверьте установку: `ffmpeg -version`
- Перезапустите командную строку
- Убедитесь что `C:\ffmpeg\bin` добавлен в PATH

### "Python не распознается"
- Переустановите Python с галочкой "Add to PATH"
- Или используйте полный путь: `C:\Users\ВашеИмя\AppData\Local\Programs\Python\Python3XX\python.exe`

### "No module named 'tkinter'"
```bash
# Linux
sudo apt install python3-tk

# macOS
brew install python-tk
```

---

## 📖 Полная документация

См. файл `README.md` для подробного описания всех функций.

---

## 🎯 Первый запуск (Quickstart)

1. Запустите программу
2. Нажмите "Добавить файлы" - выберите MP3/MP4
3. Нажмите "Выбрать" возле "Выходная папка"
4. Оставьте настройки по умолчанию:
   - Целевой уровень: `-16 dB`
   - Режим: `Normal`
5. Нажмите большую зелёную кнопку "Нормализовать файлы"
6. Готово! ✅

**Совет:** Для музыки попробуйте режим "Music" с уровнем `-14 dB`

---

## 💾 Создание EXE файла (Windows, опционально)

Если хотите запускать программу без командной строки:

```bash
# Установите PyInstaller
pip install pyinstaller

# Создайте EXE
pyinstaller --onefile --windowed --name="AudioNormalizer" audio_normalizer.py

# EXE будет в папке dist\AudioNormalizer.exe
```

Теперь можно запускать двойным кликом! 🎉

---

**Возникли проблемы?** → Смотрите раздел "Решение проблем" в `README.md`

**Всё работает?** → Приятного использования! 🎵
