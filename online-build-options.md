# Online Build Services for Python-to-Android

## GitHub Actions (FREE)
Create `.github/workflows/build.yml`:

```yaml
name: Build Android APK
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        sudo apt update
        sudo apt install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
        pip3 install --upgrade buildozer
        pip3 install --upgrade cython
    
    - name: Build APK
      run: |
        cd taxi-driver-python
        buildozer android debug
    
    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: taxi-driver-app
        path: taxi-driver-python/bin/*.apk
```

## Replit (ONLINE)
1. Go to https://replit.com
2. Create new Python project
3. Upload your code
4. Install buildozer in the shell
5. Run buildozer commands

## Google Colab (FREE)
```python
# Install buildozer
!apt update
!apt install -y git zip unzip openjdk-8-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
!pip install buildozer cython

# Upload your code and run
!buildozer android debug
```
