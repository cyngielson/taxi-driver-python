# Taxi Driver App - Android APK

Python-based taxi driver application compiled to Android APK using GitHub Codespaces.

## 🚗 Features
- Driver registration and login
- Trip management (accept/decline rides)
- Real-time location tracking
- Trip history
- Earnings tracking
- Modern UI with Kivy framework

## 📱 Compilation Options

This project includes multiple compilation methods:

### 1. GitHub Codespaces (Recommended)
Compile in cloud using Linux environment:
- See [CODESPACES-SETUP.md](CODESPACES-SETUP.md) for detailed instructions
- Uses buildozer with Python 3.8 for maximum compatibility
- No local setup required

### 2. IntelliJ IDEA + Chaquopy
Local compilation using Android Studio/IntelliJ IDEA:
- See [GOTOWE-INTELLIJ.md](GOTOWE-INTELLIJ.md) for setup instructions
- Uses Chaquopy plugin for Python-to-APK compilation
- Requires Python 3.8-3.12 compatibility

## 🚀 Quick Start (GitHub Codespaces)

1. **Fork/Clone this repository**
2. **Create Codespace**:
   - Click "Code" → "Codespaces" → "Create codespace"
   - Wait for environment setup (3-5 minutes)
3. **Compile APK**:
   ```bash
   cd /workspaces/taxi-driver-python
   buildozer android debug
   ```
4. **Download APK**:
   - Find APK in `bin/` folder
   - Download via VS Code file explorer

## 📁 Project Structure

```
taxi-driver-python/
├── .devcontainer/          # Codespaces configuration
├── app/                    # Android app configuration
│   ├── build.gradle        # Chaquopy configuration
│   └── src/main/python/    # Python source code
├── screens/                # UI screens
├── services/               # API services
├── components/             # UI components
├── buildozer.spec          # Buildozer configuration
└── requirements.txt        # Python dependencies
```

## 🛠 Technical Details

- **Language**: Python 3.8+ with Kivy
- **Android compilation**: Buildozer + python-for-android
- **Target API**: Android API 30 (Android 11)
- **Architecture**: ARM64 (arm64-v8a)
- **Dependencies**: requests, kivy, kivymd

## 💡 Why GitHub Codespaces?

- **Cross-platform**: Works on Windows, Mac, Linux
- **No setup**: Pre-configured environment
- **Fast compilation**: Powerful cloud servers
- **Consistent results**: Same environment every time

## 📋 Requirements

- GitHub account
- Internet connection
- Web browser (for Codespaces)

## 🔧 Troubleshooting

If compilation fails:
1. Check Python version (must be 3.8-3.12)
2. Verify all dependencies in requirements.txt
3. Check buildozer.spec configuration
4. See logs in `.buildozer/android/platform/` for details

## 📄 License

MIT License - see LICENSE file for details
