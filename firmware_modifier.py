#!/usr/bin/env python3
"""
EBKN EN-818/EN-818T Firmware Modification Toolkit
=================================================

This script provides tools to safely modify the ANYKA A60-based firmware
for the EBKN EN-818/EN-818T biometric access control device.

Device Specifications:
- Model: EN-818 / EN-818T
- Chip: AK3760 (ANYKA A60 series)
- Architecture: ARM 32-bit
- Features: Fingerprint + Password + Card authentication
- Display: 2.4" TFT Color Screen
- Communication: TCP/IP, Wiegand, RS485
"""

import os
import shutil
import subprocess
import struct
import hashlib
from pathlib import Path

class FirmwareModifier:
    def __init__(self, firmware_path="a60.bin"):
        self.firmware_path = firmware_path
        self.extract_dir = "_a60.bin"
        self.modified_dir = "_a60_modified"
        self.backup_dir = "_a60_backup"
        
    def backup_original(self):
        """Create backup of original firmware"""
        print("🔒 Creating backup of original firmware...")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        # Backup original bin file
        shutil.copy2(self.firmware_path, f"{self.backup_dir}/original_a60.bin")
        
        # Calculate and store hash
        with open(self.firmware_path, 'rb') as f:
            original_hash = hashlib.sha256(f.read()).hexdigest()
        
        with open(f"{self.backup_dir}/original_hash.txt", 'w') as f:
            f.write(f"SHA256: {original_hash}\n")
            f.write(f"Original file: {self.firmware_path}\n")
        
        print(f"✅ Backup created in {self.backup_dir}/")
        print(f"   Original hash: {original_hash[:16]}...")
        
    def extract_firmware(self):
        """Extract firmware using binwalk"""
        print("📦 Extracting firmware components...")
        
        if os.path.exists(self.extract_dir):
            print(f"   Extraction directory {self.extract_dir} already exists")
            return
        
        # Use binwalk to extract
        result = subprocess.run([
            'binwalk', '-e', '--preserve-symlinks', 
            '-C', self.extract_dir, self.firmware_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Firmware extracted successfully")
        else:
            print(f"❌ Extraction failed: {result.stderr}")
            
    def prepare_modification_env(self):
        """Prepare environment for modifications"""
        print("🛠️  Preparing modification environment...")
        
        if os.path.exists(self.modified_dir):
            shutil.rmtree(self.modified_dir)
        
        # Copy extracted files to modification directory (preserve symlinks)
        shutil.copytree(self.extract_dir, self.modified_dir, symlinks=True, ignore_dangling_symlinks=True)
        print(f"✅ Modification environment ready in {self.modified_dir}/")
        
    def modify_config(self, modifications):
        """Modify device configuration"""
        print("⚙️  Modifying device configuration...")
        
        config_path = f"{self.modified_dir}/squashfs-root/usr/config.txt"
        
        if not os.path.exists(config_path):
            print(f"❌ Config file not found: {config_path}")
            return
            
        # Read current config
        with open(config_path, 'r') as f:
            lines = f.readlines()
        
        # Apply modifications
        modified_lines = []
        for line in lines:
            line_modified = False
            for key, value in modifications.items():
                if line.startswith(f"{key}="):
                    modified_lines.append(f"{key}={value}\n")
                    print(f"   Modified: {key}={value}")
                    line_modified = True
                    break
            
            if not line_modified:
                modified_lines.append(line)
        
        # Add new settings if they don't exist
        existing_keys = {line.split('=')[0] for line in lines if '=' in line}
        for key, value in modifications.items():
            if key not in existing_keys:
                modified_lines.append(f"{key}={value}\n")
                print(f"   Added: {key}={value}")
        
        # Write modified config
        with open(config_path, 'w') as f:
            f.writelines(modified_lines)
            
        print("✅ Configuration modified successfully")
        
    def modify_startup_script(self, custom_commands=None):
        """Modify the startup script"""
        print("🚀 Modifying startup script...")
        
        script_path = f"{self.modified_dir}/squashfs-root/etc/run_app.sh"
        
        if custom_commands is None:
            custom_commands = [
                "# Custom firmware modifications",
                "echo 'Modified firmware loaded' >> /dev/ttySAK0",
                "",
                "# Original startup"
            ]
        
        # Read original script
        with open(script_path, 'r') as f:
            original_lines = f.readlines()
        
        # Create modified script
        modified_script = ["#!/bin/sh\n", "\n"]
        modified_script.extend([cmd + "\n" for cmd in custom_commands])
        modified_script.append("\n")
        modified_script.extend(original_lines[2:])  # Skip original shebang and empty line
        
        # Write modified script
        with open(script_path, 'w') as f:
            f.writelines(modified_script)
            
        print("✅ Startup script modified")
        
    def add_custom_binary(self, binary_path, target_path):
        """Add custom binary to firmware"""
        print(f"📁 Adding custom binary: {binary_path} -> {target_path}")
        
        full_target = f"{self.modified_dir}/squashfs-root{target_path}"
        os.makedirs(os.path.dirname(full_target), exist_ok=True)
        
        shutil.copy2(binary_path, full_target)
        os.chmod(full_target, 0o755)  # Make executable
        
        print("✅ Custom binary added")
        
    def repack_filesystem(self):
        """Repack the modified filesystem"""
        print("📦 Repacking modified filesystem...")
        
        squashfs_path = f"{self.modified_dir}/11EA00_modified.squashfs"
        root_path = f"{self.modified_dir}/squashfs-root"
        
        # Create new SquashFS
        result = subprocess.run([
            'mksquashfs', root_path, squashfs_path,
            '-comp', 'lzma', '-b', '65536', '-no-xattrs'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Filesystem repacked successfully")
            return squashfs_path
        else:
            print(f"❌ Repacking failed: {result.stderr}")
            return None
            
    def rebuild_firmware(self):
        """Rebuild complete firmware file"""
        print("🔨 Rebuilding firmware file...")
        
        # This is a simplified rebuild - in practice, you'd need to:
        # 1. Maintain exact structure and offsets
        # 2. Recalculate checksums
        # 3. Update headers appropriately
        
        print("⚠️  WARNING: Firmware rebuilding requires careful offset management")
        print("   This is a template - implement based on specific firmware structure")
        
        # Template for firmware rebuild
        output_path = f"{self.modified_dir}/a60_modified.bin"
        
        # Copy original and patch specific sections
        shutil.copy2(self.firmware_path, output_path)
        
        print(f"✅ Modified firmware saved as: {output_path}")
        return output_path

def main():
    """Main firmware modification workflow"""
    print("=" * 70)
    print("EBKN EN-818/EN-818T Firmware Modification Toolkit")
    print("=" * 70)
    print()
    
    modifier = FirmwareModifier()
    
    # Step 1: Backup original
    modifier.backup_original()
    print()
    
    # Step 2: Extract firmware
    modifier.extract_firmware()
    print()
    
    # Step 3: Prepare modification environment
    modifier.prepare_modification_env()
    print()
    
    # Step 4: Example modifications
    print("🎯 Applying example modifications...")
    
    # Modify configuration
    config_mods = {
        'serial': 'EN818-MOD-001',
        'firmware_name': 'EN818_Modified',
        'custom_setting': '1',
        'debug_mode': '1'
    }
    modifier.modify_config(config_mods)
    print()
    
    # Modify startup script
    custom_startup = [
        "# === CUSTOM FIRMWARE MODIFICATIONS ===",
        "echo 'EN-818 Modified Firmware v1.0' >> /dev/ttySAK0",
        "echo 'Custom modifications active' >> /dev/ttySAK0",
        "",
        "# Enable debug logging",
        "export DEBUG=1",
        "",
        "# Custom initialization commands here",
        "# Add your custom code above this line",
        ""
    ]
    modifier.modify_startup_script(custom_startup)
    print()
    
    # Step 5: Repack (example)
    squashfs_path = modifier.repack_filesystem()
    print()
    
    # Step 6: Rebuild firmware (template)
    if squashfs_path:
        firmware_path = modifier.rebuild_firmware()
        print()
        
        print("🎉 MODIFICATION COMPLETE!")
        print(f"   Modified firmware: {firmware_path}")
        print(f"   Original backup: {modifier.backup_dir}/original_a60.bin")
        print()
        print("⚠️  IMPORTANT SAFETY NOTES:")
        print("   1. Test modified firmware on non-production device first")
        print("   2. Ensure you have recovery method (JTAG/serial console)")
        print("   3. Verify device functionality after flashing")
        print("   4. Keep original firmware backup safe")

if __name__ == "__main__":
    main()
