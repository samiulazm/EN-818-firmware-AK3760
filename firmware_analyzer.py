#!/usr/bin/env python3
"""
EN-818/EN-818T Firmware Analysis and Preparation
===============================================

This script analyzes the extracted EN-818/EN-818T firmware and prepares
it for safe modification by identifying key components and dependencies.
"""

import os
import json
import subprocess
from pathlib import Path

class FirmwareAnalyzer:
    def __init__(self, extract_dir="_a60.bin"):
        self.extract_dir = extract_dir
        self.squashfs_root = f"{extract_dir}/squashfs-root"
        self.analysis_report = {}
        
    def analyze_filesystem_structure(self):
        """Analyze the extracted filesystem structure"""
        print("📁 Analyzing filesystem structure...")
        
        structure = {}
        
        if os.path.exists(self.squashfs_root):
            for root, dirs, files in os.walk(self.squashfs_root):
                rel_path = os.path.relpath(root, self.squashfs_root)
                if rel_path == ".":
                    rel_path = "/"
                
                structure[rel_path] = {
                    "directories": dirs,
                    "files": files,
                    "file_count": len(files),
                    "dir_count": len(dirs)
                }
        
        self.analysis_report["filesystem"] = structure
        print(f"   Found {len(structure)} directories")
        
    def analyze_configuration_files(self):
        """Analyze configuration files"""
        print("⚙️  Analyzing configuration files...")
        
        config_files = [
            "usr/config.txt",
            "etc/inittab",
            "etc/rcS",
            "etc/run_app.sh",
            "etc/passwd",
            "etc/group",
            "etc/fstab"
        ]
        
        configs = {}
        
        for config_file in config_files:
            full_path = f"{self.squashfs_root}/{config_file}"
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    configs[config_file] = {
                        "exists": True,
                        "size": len(content),
                        "lines": len(content.split('\n')),
                        "content_preview": content[:200] + "..." if len(content) > 200 else content
                    }
                except Exception as e:
                    configs[config_file] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                configs[config_file] = {"exists": False}
        
        self.analysis_report["configurations"] = configs
        print(f"   Analyzed {len([c for c in configs.values() if c['exists']])} config files")
        
    def analyze_device_settings(self):
        """Extract and analyze device-specific settings"""
        print("🔧 Analyzing device settings...")
        
        config_path = f"{self.squashfs_root}/usr/config.txt"
        device_settings = {}
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        device_settings[key] = value
        
        # Categorize settings
        categorized = {
            "device_info": {},
            "authentication": {},
            "network": {},
            "system": {},
            "unknown": {}
        }
        
        # Device information
        device_keys = ['product_name', 'serial', 'firmware_name', 'fw_file_name']
        auth_keys = ['rs485_fp_reader', 'face_engine_threshold', 'keyboard']
        network_keys = ['xml_download', 'tcp_port']
        system_keys = ['status_led', 'sensor_led_on_level', 'use_reopen', 'fail_log']
        
        for key, value in device_settings.items():
            if key in device_keys:
                categorized["device_info"][key] = value
            elif key in auth_keys:
                categorized["authentication"][key] = value
            elif key in network_keys:
                categorized["network"][key] = value
            elif key in system_keys:
                categorized["system"][key] = value
            else:
                categorized["unknown"][key] = value
        
        self.analysis_report["device_settings"] = categorized
        print(f"   Found {len(device_settings)} device settings")
        
    def analyze_binaries(self):
        """Analyze binary files and executables"""
        print("🔍 Analyzing binary files...")
        
        bin_dirs = ["bin", "sbin", "usr/bin", "usr/sbin"]
        binaries = {}
        
        for bin_dir in bin_dirs:
            full_dir = f"{self.squashfs_root}/{bin_dir}"
            if os.path.exists(full_dir):
                binaries[bin_dir] = []
                
                for item in os.listdir(full_dir):
                    item_path = f"{full_dir}/{item}"
                    if os.path.isfile(item_path):
                        # Check if executable
                        is_exec = os.access(item_path, os.X_OK)
                        
                        # Get file info
                        stat = os.stat(item_path)
                        
                        # Try to get file type
                        try:
                            result = subprocess.run(['file', item_path], 
                                                  capture_output=True, text=True)
                            file_type = result.stdout.strip()
                        except:
                            file_type = "unknown"
                        
                        binaries[bin_dir].append({
                            "name": item,
                            "size": stat.st_size,
                            "executable": is_exec,
                            "type": file_type
                        })
        
        self.analysis_report["binaries"] = binaries
        total_bins = sum(len(bins) for bins in binaries.values())
        print(f"   Found {total_bins} binary files")
        
    def identify_modification_points(self):
        """Identify safe modification points"""
        print("🎯 Identifying modification points...")
        
        modification_points = {
            "safe_to_modify": [],
            "risky_to_modify": [],
            "do_not_modify": []
        }
        
        # Safe to modify
        safe_files = [
            "usr/config.txt",
            "etc/run_app.sh",
            "etc/rcS",
            "etc/passwd",
            "etc/group"
        ]
        
        # Risky to modify
        risky_files = [
            "bin/busybox",
            "sbin/init",
            "lib/*"
        ]
        
        # Do not modify
        critical_files = [
            "init",
            "linuxrc"
        ]
        
        for file_path in safe_files:
            if os.path.exists(f"{self.squashfs_root}/{file_path}"):
                modification_points["safe_to_modify"].append(file_path)
        
        modification_points["recommendations"] = [
            "Modify usr/config.txt for device settings",
            "Add custom scripts to etc/ directory", 
            "Modify etc/run_app.sh for startup customization",
            "Add custom binaries to usr/bin/",
            "Avoid modifying core system files",
            "Always backup before modifying"
        ]
        
        self.analysis_report["modification_points"] = modification_points
        print(f"   Identified {len(modification_points['safe_to_modify'])} safe modification points")
        
    def analyze_security_features(self):
        """Analyze security features and potential vulnerabilities"""
        print("🔒 Analyzing security features...")
        
        security_analysis = {
            "authentication_methods": [],
            "network_security": [],
            "file_permissions": {},
            "potential_issues": []
        }
        
        # Check authentication methods from config
        device_settings = self.analysis_report.get("device_settings", {})
        auth_settings = device_settings.get("authentication", {})
        
        if auth_settings.get("rs485_fp_reader") == "1":
            security_analysis["authentication_methods"].append("Fingerprint (RS485)")
        
        if "keyboard" in auth_settings:
            security_analysis["authentication_methods"].append("Keyboard/Password")
            
        # Check for default passwords
        passwd_path = f"{self.squashfs_root}/etc/passwd"
        if os.path.exists(passwd_path):
            with open(passwd_path, 'r') as f:
                passwd_content = f.read()
                if "root::0:0" in passwd_content:
                    security_analysis["potential_issues"].append("Root account with no password")
        
        # Check file permissions on critical files
        critical_files = ["etc/passwd", "etc/shadow", "usr/config.txt"]
        for file_path in critical_files:
            full_path = f"{self.squashfs_root}/{file_path}"
            if os.path.exists(full_path):
                stat = os.stat(full_path)
                permissions = oct(stat.st_mode)[-3:]
                security_analysis["file_permissions"][file_path] = permissions
        
        self.analysis_report["security"] = security_analysis
        print(f"   Found {len(security_analysis['authentication_methods'])} authentication methods")
        
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("📝 Generating analysis report...")
        
        # Run all analysis functions
        self.analyze_filesystem_structure()
        self.analyze_configuration_files()
        self.analyze_device_settings()
        self.analyze_binaries()
        self.identify_modification_points()
        self.analyze_security_features()
        
        # Save detailed report
        with open("firmware_analysis_report.json", "w") as f:
            json.dump(self.analysis_report, f, indent=2)
        
        # Generate summary report
        self.generate_summary_report()
        
        print("✅ Analysis complete!")
        print("   📄 Detailed report: firmware_analysis_report.json")
        print("   📋 Summary report: firmware_analysis_summary.md")
        
    def generate_summary_report(self):
        """Generate human-readable summary report"""
        
        summary = f"""# EN-818/EN-818T Firmware Analysis Summary

## Device Information
- **Product**: {self.analysis_report['device_settings']['device_info'].get('product_name', 'Unknown')}
- **Serial**: {self.analysis_report['device_settings']['device_info'].get('serial', 'Unknown')}
- **Firmware**: {self.analysis_report['device_settings']['device_info'].get('firmware_name', 'Unknown')}

## Filesystem Overview
- **Total Directories**: {len(self.analysis_report['filesystem'])}
- **Key Components**: bin/, etc/, usr/, lib/

## Authentication Features
"""
        
        auth_methods = self.analysis_report['security']['authentication_methods']
        for method in auth_methods:
            summary += f"- {method}\n"
        
        summary += f"""
## Safe Modification Points
"""
        
        safe_mods = self.analysis_report['modification_points']['safe_to_modify']
        for mod_point in safe_mods:
            summary += f"- {mod_point}\n"
        
        summary += f"""
## Recommendations
"""
        
        recommendations = self.analysis_report['modification_points']['recommendations']
        for rec in recommendations:
            summary += f"- {rec}\n"
        
        summary += f"""
## Security Considerations
"""
        
        issues = self.analysis_report['security']['potential_issues']
        if issues:
            for issue in issues:
                summary += f"- ⚠️  {issue}\n"
        else:
            summary += "- No major security issues identified\n"
        
        summary += f"""
## Next Steps for Modification
1. Create backup of original firmware
2. Test modifications on development device first
3. Focus on safe modification points
4. Validate all changes before deployment
5. Maintain recovery method (JTAG/serial)
"""
        
        with open("firmware_analysis_summary.md", "w") as f:
            f.write(summary)

def main():
    """Main analysis function"""
    print("=" * 70)
    print("EN-818/EN-818T Firmware Analysis Tool")
    print("=" * 70)
    print()
    
    analyzer = FirmwareAnalyzer()
    
    # Check if firmware is extracted
    if not os.path.exists(analyzer.squashfs_root):
        print("❌ Firmware not extracted yet!")
        print("   Please run binwalk extraction first:")
        print("   binwalk -e a60.bin")
        return
    
    # Generate comprehensive analysis
    analyzer.generate_report()
    
    print()
    print("🎯 Ready for firmware modification!")
    print("   Use the generated reports to plan your modifications safely.")

if __name__ == "__main__":
    main()
