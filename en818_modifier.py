#!/usr/bin/env python3
"""
EN-818/EN-818T Specific Modifications
====================================

This script provides specific modifications for the EBKN EN-818/EN-818T
biometric access control device firmware.
"""

import os
import json
from firmware_modifier import FirmwareModifier

class EN818Modifier(FirmwareModifier):
    """EN-818 specific firmware modifications"""
    
    def __init__(self):
        super().__init__()
        self.device_model = "EN-818/EN-818T"
        
    def enable_debug_mode(self):
        """Enable comprehensive debug mode"""
        print("🐛 Enabling debug mode...")
        
        debug_config = {
            'debug_mode': '1',
            'verbose_logging': '1',
            'console_output': '1',
            'fail_log': '1',
            'system_log': '1'
        }
        
        self.modify_config(debug_config)
        
        # Add debug startup commands
        debug_commands = [
            "# === DEBUG MODE ENABLED ===",
            "echo 'Debug mode active' >> /dev/ttySAK0",
            "export DEBUG=1",
            "export VERBOSE=1",
            "",
            "# Start system monitoring",
            "dmesg >> /tmp/boot.log &",
            "ps aux >> /tmp/processes.log &",
            ""
        ]
        
        self.modify_startup_script(debug_commands)
        
    def modify_authentication_settings(self, settings):
        """Modify authentication-related settings"""
        print("🔐 Modifying authentication settings...")
        
        auth_config = {}
        
        # Fingerprint settings
        if 'fingerprint_enabled' in settings:
            auth_config['rs485_fp_reader'] = '1' if settings['fingerprint_enabled'] else '0'
            
        if 'fingerprint_threshold' in settings:
            auth_config['face_engine_threshold'] = str(settings['fingerprint_threshold'])
            
        # Card reader settings
        if 'card_enabled' in settings:
            auth_config['card_reader'] = '1' if settings['card_enabled'] else '0'
            
        # Password settings
        if 'password_complexity' in settings:
            auth_config['password_min_length'] = str(settings['password_complexity'])
            
        # Timeout settings
        if 'auth_timeout' in settings:
            auth_config['auth_timeout'] = str(settings['auth_timeout'])
            
        self.modify_config(auth_config)
        
    def modify_network_settings(self, network_config):
        """Modify TCP/IP network settings"""
        print("🌐 Modifying network settings...")
        
        net_config = {}
        
        if 'dhcp_enabled' in network_config:
            net_config['use_dhcp'] = '1' if network_config['dhcp_enabled'] else '0'
            
        if 'static_ip' in network_config:
            net_config['static_ip'] = network_config['static_ip']
            
        if 'subnet_mask' in network_config:
            net_config['subnet_mask'] = network_config['subnet_mask']
            
        if 'gateway' in network_config:
            net_config['gateway'] = network_config['gateway']
            
        if 'dns_server' in network_config:
            net_config['dns_server'] = network_config['dns_server']
            
        # TCP port settings
        if 'tcp_port' in network_config:
            net_config['tcp_port'] = str(network_config['tcp_port'])
            
        self.modify_config(net_config)
        
        # Add network initialization to startup
        network_commands = [
            "# === NETWORK CONFIGURATION ===",
            f"# Device IP: {network_config.get('static_ip', 'DHCP')}",
            "",
            "# Configure network interface",
            "ifconfig eth0 up",
            ""
        ]
        
        if not network_config.get('dhcp_enabled', True):
            ip = network_config.get('static_ip', '192.168.1.100')
            mask = network_config.get('subnet_mask', '255.255.255.0')
            gw = network_config.get('gateway', '192.168.1.1')
            
            network_commands.extend([
                f"ifconfig eth0 {ip} netmask {mask}",
                f"route add default gw {gw}",
                ""
            ])
        else:
            network_commands.extend([
                "udhcpc -i eth0 &",
                ""
            ])
            
        self.modify_startup_script(network_commands)
        
    def modify_display_settings(self, display_config):
        """Modify 2.4" TFT display settings"""
        print("🖥️  Modifying display settings...")
        
        display_settings = {}
        
        if 'brightness' in display_config:
            display_settings['lcd_brightness'] = str(display_config['brightness'])
            
        if 'contrast' in display_config:
            display_settings['lcd_contrast'] = str(display_config['contrast'])
            
        if 'timeout' in display_config:
            display_settings['lcd_timeout'] = str(display_config['timeout'])
            
        if 'language' in display_config:
            display_settings['display_language'] = display_config['language']
            
        self.modify_config(display_settings)
        
    def add_custom_authentication_script(self):
        """Add custom authentication verification script"""
        print("🔒 Adding custom authentication script...")
        
        auth_script = '''#!/bin/sh
# Custom Authentication Handler for EN-818/EN-818T
# This script is called during authentication events

USER_ID=$1
AUTH_TYPE=$2  # finger, card, password
AUTH_RESULT=$3  # success, fail

LOG_FILE="/tmp/auth.log"
echo "$(date): User $USER_ID - $AUTH_TYPE - $AUTH_RESULT" >> $LOG_FILE

case $AUTH_RESULT in
    "success")
        echo "Access granted to user $USER_ID via $AUTH_TYPE" >> /dev/ttySAK0
        # Custom success actions here
        ;;
    "fail")
        echo "Access denied for user $USER_ID via $AUTH_TYPE" >> /dev/ttySAK0
        # Custom failure actions here
        ;;
esac

# Return result to main application
exit 0
'''
        
        script_path = "/usr/bin/custom_auth.sh"
        full_path = f"{self.modified_dir}/squashfs-root{script_path}"
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(auth_script)
        os.chmod(full_path, 0o755)
        
        # Update config to use custom script
        self.modify_config({'custom_auth_handler': script_path})
        
    def add_web_interface(self):
        """Add simple web interface for remote management"""
        print("🌐 Adding web interface...")
        
        # Simple HTTP server script
        web_script = '''#!/bin/sh
# Simple web interface for EN-818/EN-818T
# Provides basic status and configuration via HTTP

WEB_ROOT="/tmp/www"
mkdir -p $WEB_ROOT

# Create simple status page
cat > $WEB_ROOT/index.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>EN-818 Status</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>EBKN EN-818/EN-818T Status</h1>
    <h2>System Information</h2>
    <p>Uptime: $(uptime)</p>
    <p>Memory: $(free -h)</p>
    <p>Storage: $(df -h)</p>
    
    <h2>Device Status</h2>
    <p>Fingerprint Reader: Active</p>
    <p>Network: Connected</p>
    <p>Display: Online</p>
    
    <h2>Recent Authentication Events</h2>
    <pre>$(tail -10 /tmp/auth.log 2>/dev/null || echo "No events logged")</pre>
</body>
</html>
EOF

# Start simple HTTP server on port 8080
busybox httpd -p 8080 -h $WEB_ROOT
'''
        
        web_path = "/usr/bin/start_web.sh"
        full_path = f"{self.modified_dir}/squashfs-root{web_path}"
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(web_script)
        os.chmod(full_path, 0o755)
        
        # Add to startup
        web_commands = [
            "# === WEB INTERFACE ===",
            "echo 'Starting web interface on port 8080...' >> /dev/ttySAK0",
            "/usr/bin/start_web.sh &",
            ""
        ]
        
        self.modify_startup_script(web_commands)

def create_modification_profile():
    """Create a modification profile for EN-818/EN-818T"""
    
    profile = {
        "device": "EBKN EN-818/EN-818T",
        "modifications": {
            "debug_mode": True,
            "web_interface": True,
            "custom_auth": True,
            
            "authentication": {
                "fingerprint_enabled": True,
                "fingerprint_threshold": 3,
                "card_enabled": True,
                "password_complexity": 6,
                "auth_timeout": 30
            },
            
            "network": {
                "dhcp_enabled": False,
                "static_ip": "192.168.1.150",
                "subnet_mask": "255.255.255.0",
                "gateway": "192.168.1.1",
                "dns_server": "8.8.8.8",
                "tcp_port": 4370
            },
            
            "display": {
                "brightness": 80,
                "contrast": 70,
                "timeout": 60,
                "language": "en"
            },
            
            "custom_config": {
                "device_name": "EN818-Modified",
                "admin_password": "admin123",
                "max_users": 2000,
                "backup_enabled": True
            }
        }
    }
    
    with open("en818_modification_profile.json", "w") as f:
        json.dump(profile, f, indent=2)
        
    print("📋 Modification profile created: en818_modification_profile.json")
    return profile

def apply_modifications():
    """Apply all modifications to EN-818/EN-818T firmware"""
    
    print("=" * 70)
    print("EN-818/EN-818T Firmware Modification Script")
    print("=" * 70)
    print()
    
    # Create modification profile
    profile = create_modification_profile()
    
    # Initialize modifier
    modifier = EN818Modifier()
    
    # Backup and extract
    modifier.backup_original()
    modifier.extract_firmware()
    modifier.prepare_modification_env()
    
    print("🎯 Applying EN-818/EN-818T specific modifications...")
    print()
    
    # Apply modifications based on profile
    mods = profile["modifications"]
    
    if mods["debug_mode"]:
        modifier.enable_debug_mode()
        print()
        
    if mods["custom_auth"]:
        modifier.add_custom_authentication_script()
        print()
        
    if mods["web_interface"]:
        modifier.add_web_interface()
        print()
        
    # Apply settings
    modifier.modify_authentication_settings(mods["authentication"])
    print()
    
    modifier.modify_network_settings(mods["network"])
    print()
    
    modifier.modify_display_settings(mods["display"])
    print()
    
    # Apply custom config
    modifier.modify_config(mods["custom_config"])
    print()
    
    # Repack and rebuild
    modifier.repack_filesystem()
    modifier.rebuild_firmware()
    
    print("🎉 EN-818/EN-818T firmware modification complete!")
    print()
    print("📝 Summary of modifications:")
    print("   ✅ Debug mode enabled")
    print("   ✅ Custom authentication handler added")
    print("   ✅ Web interface added (port 8080)")
    print("   ✅ Network settings configured")
    print("   ✅ Display settings optimized")
    print("   ✅ Custom configuration applied")
    print()
    print("⚠️  Next steps:")
    print("   1. Test modified firmware on development device")
    print("   2. Verify all functions work correctly")
    print("   3. Flash to target device using appropriate tool")
    print("   4. Test biometric authentication functions")
    print("   5. Verify network connectivity and web interface")

if __name__ == "__main__":
    apply_modifications()
