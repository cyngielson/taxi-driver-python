#!/bin/bash

echo "🚀 Instalowanie buildozer i narzędzi do kompilacji Android..."

# Aktualizacja systemu
sudo apt-get update

# Instalacja podstawowych narzędzi
sudo apt-get install -y \
    build-essential \
    git \
    unzip \
    python3-dev \
    python3-pip \
    openjdk-17-jdk \
    gradle \
    cmake \
    ninja-build \
    autotools-dev \
    autoconf \
    automake \
    libtool

# Aktualizacja pip
pip3 install --upgrade pip setuptools wheel

# Instalacja buildozer i python-for-android
pip3 install --upgrade \
    buildozer \
    python-for-android \
    cython \
    kivy[base] \
    kivymd

# Sprawdzenie instalacji
echo "📦 Sprawdzanie instalacji..."
python3 --version
pip3 --version
buildozer --version
java -version
gradle --version

echo "✅ Instalacja zakończona!"
echo "🔧 Uruchom: buildozer android debug"
