# Android Studio + Chaquopy Setup Guide

## Overview
Since buildozer doesn't work on Windows, we can use Android Studio with Chaquopy to compile the Python app.

## Steps:

### 1. Install Android Studio
- Download from: https://developer.android.com/studio
- Install with Android SDK

### 2. Create New Android Project
```bash
# Create new project with:
# - Language: Kotlin
# - Minimum SDK: API 21
# - Template: Empty Activity
```

### 3. Add Chaquopy Plugin
Add to `app/build.gradle`:
```gradle
plugins {
    id 'com.android.application'
    id 'kotlin-android'
    id 'com.chaquo.python'
}

android {
    compileSdkVersion 34
    defaultConfig {
        applicationId "com.taxidriver.app"
        minSdkVersion 21
        targetSdkVersion 34
        versionCode 1
        versionName "1.0"
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
}

chaquopy {
    defaultConfig {
        pip {
            install "kivy==2.1.0"
            install "kivymd==1.1.1"
            install "requests"
            install "plyer"
        }
    }
}
```

### 4. Add Python Files
Copy all Python files to: `app/src/main/python/`

### 5. Build APK
```bash
./gradlew assembleDebug
```

## Alternative: Use Docker

If you have Docker Desktop:
```bash
docker run --rm -v %cd%:/app kivy/buildozer android debug
```
