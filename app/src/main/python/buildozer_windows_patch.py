#!/usr/bin/env python3
"""
Experimental buildozer Windows workaround
This patches the android target to work on Windows (experimental)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def patch_buildozer_for_windows():
    """Patch buildozer to work on Windows"""
    
    # Find buildozer installation
    import buildozer
    buildozer_path = Path(buildozer.__file__).parent
    android_target_path = buildozer_path / "targets" / "android.py"
    
    print(f"Buildozer path: {buildozer_path}")
    print(f"Android target: {android_target_path}")
    
    # Create backup
    backup_path = android_target_path.with_suffix(".py.backup")
    if not backup_path.exists():
        shutil.copy2(android_target_path, backup_path)
        print(f"Created backup: {backup_path}")
    
    # Read original file
    with open(android_target_path, 'r') as f:
        content = f.read()
    
    # Patch the Windows check
    if "raise NotImplementedError('Windows platform not yet working for Android')" in content:
        print("Patching Windows check...")
        
        # Replace the check with a warning instead of error
        patched_content = content.replace(
            "raise NotImplementedError('Windows platform not yet working for Android')",
            "# WARNING: Windows support is experimental\n    print('WARNING: Building on Windows is experimental!')"
        )
        
        # Write patched file
        with open(android_target_path, 'w') as f:
            f.write(patched_content)
        
        print("✅ Buildozer patched for Windows!")
        return True
    else:
        print("❌ Windows check not found - already patched?")
        return False

def restore_buildozer():
    """Restore original buildozer"""
    import buildozer
    buildozer_path = Path(buildozer.__file__).parent
    android_target_path = buildozer_path / "targets" / "android.py"
    backup_path = android_target_path.with_suffix(".py.backup")
    
    if backup_path.exists():
        shutil.copy2(backup_path, android_target_path)
        print("✅ Buildozer restored from backup")
        return True
    else:
        print("❌ No backup found")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_buildozer()
    else:
        patch_buildozer_for_windows()
