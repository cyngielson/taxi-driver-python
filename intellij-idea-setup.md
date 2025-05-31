# IntelliJ IDEA + Android Plugin Setup Guide

## Tak! IntelliJ IDEA może skompilować aplikację Android z Pythonem!

## Metody kompilacji w IntelliJ IDEA:

### **Metoda 1: IntelliJ IDEA + Android Plugin + Chaquopy (ZALECANA)**

#### 1. Instalacja
- Pobierz IntelliJ IDEA Community/Ultimate
- Zainstaluj plugin "Android" w Settings > Plugins
- Zainstaluj Android SDK przez IDEA

#### 2. Nowy projekt Android
```
File > New > Project > Android > Empty Activity
- Language: Kotlin
- Minimum SDK: API 21
- Package name: com.taxidriver.app
```

#### 3. Konfiguracja build.gradle (app level)
```gradle
plugins {
    id 'com.android.application'
    id 'kotlin-android'
    id 'com.chaquo.python'
}

android {
    namespace 'com.taxidriver.app'
    compileSdk 34

    defaultConfig {
        applicationId "com.taxidriver.app"
        minSdk 21
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
    
    sourceSets {
        main {
            python.srcDirs = ["src/main/python"]
        }
    }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.11.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
}

chaquopy {
    defaultConfig {
        version "3.8"
        pip {
            install "kivy==2.1.0"
            install "kivymd==1.1.1"
            install "requests"
            install "plyer"
            install "pillow"
            install "certifi"
        }
    }
}
```

#### 4. Konfiguracja build.gradle (project level)
```gradle
buildscript {
    dependencies {
        classpath 'com.android.tools.build:gradle:8.2.0'
        classpath 'org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.20'
        classpath 'com.chaquo.python:gradle:15.0.1'
    }
}
```

### **Metoda 2: IntelliJ IDEA + Kivy Buildozer w Docker**

#### Docker Compose setup:
```yaml
version: '3.8'
services:
  buildozer:
    image: kivy/buildozer
    volumes:
      - .:/app
    working_dir: /app
    command: buildozer android debug
```

### **Metoda 3: IntelliJ IDEA + BeeWare (Python to Android)**

#### Instalacja BeeWare:
```bash
pip install briefcase
briefcase new
# Konfiguruj dla Android
briefcase build android
briefcase package android
```

## Kompilacja w IntelliJ IDEA:

### Opcja A: Gradle Build
```bash
# W terminalu IntelliJ IDEA:
./gradlew assembleDebug
```

### Opcja B: Build Menu
```
Build > Build Bundle(s) / APK(s) > Build APK(s)
```

### Opcja C: Run Configuration
```
Run > Edit Configurations > Add New > Android App
Target: USB Device/Emulator
Module: app
```

## Struktura folderów w IntelliJ:
```
taxi-driver-android/
├── app/
│   ├── src/main/
│   │   ├── java/com/taxidriver/app/  # Kotlin/Java
│   │   ├── python/                   # Python files (Kivy app)
│   │   │   ├── main.py
│   │   │   ├── screens/
│   │   │   ├── services/
│   │   │   └── components/
│   │   ├── res/                      # Android resources
│   │   └── AndroidManifest.xml
│   └── build.gradle
├── build.gradle
└── settings.gradle
```

## Zalety IntelliJ IDEA:
✅ Pełne wsparcie dla Android + Python
✅ Debugging Python i Kotlin w jednym IDE
✅ Git integration
✅ Refactoring tools
✅ Code completion
✅ Gradle integration
✅ Device manager
✅ APK Analyzer

## Następne kroki:
1. Zainstaluj IntelliJ IDEA Ultimate (ma lepsze wsparcie Android)
2. Skonfiguruję projekt dla Twojej aplikacji
3. Skopiuję wszystkie pliki Python
4. Zbuduję APK

Czy chcesz, żebym utworzył kompletny projekt IntelliJ IDEA dla Twojej aplikacji taxi-driver-python?
