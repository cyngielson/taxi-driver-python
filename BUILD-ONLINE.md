# 🚕 Online Build - Kompilacja APK w Chmurze

## Opcja 1: GitHub Codespaces (NAJLEPSZE!)

### Krok 1: Przygotuj repozytorium
```bash
# Skopiuj projekt do GitHub repo lub użyj GitHub Desktop
```

### Krok 2: Otwórz w Codespaces
1. Idź na github.com/twój-repo
2. Kliknij **Code** → **Codespaces** → **Create codespace**
3. Poczekaj na uruchomienie (Linux Ubuntu z Pythonem)

### Krok 3: Zainstaluj buildozer
```bash
sudo apt update
sudo apt install -y git zip unzip python3-pip
pip3 install buildozer
sudo apt install -y openjdk-8-jdk
```

### Krok 4: Kompiluj APK
```bash
cd taxi-driver-python
buildozer android debug
```

## Opcja 2: Replit (SZYBKIE!)

1. Idź na **replit.com**
2. **Create Repl** → **Import from GitHub**
3. Wklej link do repo lub upload pliki
4. W terminalu:
```bash
pip install buildozer
buildozer android debug
```

## Opcja 3: Google Colab (BEZPŁATNE!)

1. Idź na **colab.research.google.com**
2. **New notebook**
3. Upload pliki projektu
4. W komórce:
```python
!apt update
!apt install -y openjdk-8-jdk
!pip install buildozer
!cd taxi-driver-python && buildozer android debug
```

## Opcja 4: Docker przez Google Cloud Shell

1. Idź na **shell.cloud.google.com**
2. Upload pliki projektu
3. Uruchom:
```bash
docker run --rm -v $PWD/taxi-driver-python:/app kivy/buildozer android debug
```

## Który wybierasz?

**POLECAM: GitHub Codespaces** - masz 60h/miesiąc za darmo!

---
**Status:** GOTOWE DO UŻYCIA! 🎉
