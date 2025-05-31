#!/bin/bash

# 🚀 Auto-build script for GitHub Codespaces
# This script automatically compiles the taxi driver app

echo "🚕 Starting Taxi Driver App Compilation in Codespaces..."
echo "=================================================="

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -qq

# Install build dependencies
echo "🔧 Installing build dependencies..."
sudo apt-get install -y build-essential git unzip python3-dev \
    libffi-dev libssl-dev libbz2-dev libncurses5-dev \
    libncursesw5-dev libreadline-dev libsqlite3-dev \
    libgdbm-dev libdb5.3-dev liblzma-dev tk-dev

# Install Python packages
echo "🐍 Installing Python packages..."
pip install --upgrade pip
pip install buildozer python-for-android cython

# Setup Android SDK (if not already done)
echo "📱 Setting up Android environment..."
export ANDROID_HOME=$HOME/android-sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf .buildozer/
rm -rf bin/

# Start buildozer compilation
echo "🚀 Starting APK compilation..."
buildozer android debug

# Check if APK was created
if [ -f "bin/*.apk" ]; then
    echo "✅ SUCCESS! APK compiled successfully!"
    echo "📁 APK location: $(ls bin/*.apk)"
    ls -la bin/
else
    echo "❌ FAILED! APK compilation failed."
    echo "📋 Check logs above for errors."
fi

echo "=================================================="
echo "🏁 Compilation finished!"
