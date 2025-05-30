# EN-818/EN-818T Firmware Modification Guide

## Overview
This guide provides step-by-step instructions for safely modifying the EBKN EN-818/EN-818T biometric access control device firmware.

**Device Specifications:**
- Model: EN-818 / EN-818T
- Chip: AK3760 (ANYKA A60 series)
- Architecture: ARM 32-bit
- Features: Fingerprint + Password + Card authentication
- Display: 2.4" TFT Color Screen
- Communication: TCP/IP, Wiegand, RS485

## ⚠️ CRITICAL SAFETY WARNINGS

1. **BRICK RISK**: Incorrect firmware modification can permanently damage your device
2. **BACKUP REQUIRED**: Always maintain original firmware backup
3. **RECOVERY METHOD**: Ensure you have JTAG or serial console access for recovery
4. **TEST DEVICE**: Use non-production device for initial testing
5. **POWER STABILITY**: Ensure stable power during firmware operations

## Prerequisites

### Required Tools
```bash
# Install required tools on Ubuntu/Debian
sudo apt update
sudo apt install binwalk squashfs-tools python3 python3-pip

# For firmware flashing (device-specific)
# You may need manufacturer's flashing tool or universal tools like:
# - OpenOCD (for JTAG)
# - tftp (for network flashing)
# - Custom ANYKA flashing tools
```

### Required Files
- Original firmware file: `a60.bin`
- Modification scripts (provided in this workspace)
- Backup storage location

## Step 1: Backup Original Firmware

```bash
# Create backup directory
mkdir -p backup_firmware
cp a60.bin backup_firmware/original_a60.bin

# Calculate hash for verification
sha256sum a60.bin > backup_firmware/original_hash.txt

# Document device information
echo "Device: EBKN EN-818/EN-818T" > backup_firmware/device_info.txt
echo "Date: $(date)" >> backup_firmware/device_info.txt
echo "Original firmware: a60.bin" >> backup_firmware/device_info.txt
```

## Step 2: Extract Firmware

```bash
# Extract firmware components
binwalk -e --preserve-symlinks a60.bin

# Or use the automated script
python3 firmware_analyzer.py
```

## Step 3: Analyze Firmware Structure

```bash
# Run comprehensive analysis
python3 firmware_analyzer.py

# Review generated reports
cat firmware_analysis_summary.md
```

## Step 4: Plan Your Modifications

### Common Modification Goals:

#### A. Enable Debug Mode
- Add debug logging
- Enable verbose output
- Create system monitoring

#### B. Network Configuration
- Set DHCP IP address
- Configure TCP/IP settings

#### C. Authentication Enhancements
- Modify fingerprint sensitivity
- Add custom authentication logic
- Implement logging

#### D. Display Customization
- Change boot messages
- Modify display settings
- Add custom information

## Step 5: Apply Modifications

### Method A: Automated Modification (Recommended)

```bash
# Run the EN-818 specific modifier
python3 en818_modifier.py
```

This will automatically:
- Create backups
- Extract firmware
- Apply common modifications
- Repack filesystem
- Generate modified firmware

### Method B: Manual Modification

#### 1. Create Modification Environment
```bash
# Copy extracted files to working directory
cp -r _a60.bin _a60_modified
cd _a60_modified/squashfs-root
```

#### 2. Modify Configuration
```bash
# Edit main configuration file
nano usr/config.txt

# Example modifications:
# Change device name
sed -i 's/serial=A60-0001/serial=EN818-MOD-001/' usr/config.txt

# Enable debug mode
echo "debug_mode=1" >> usr/config.txt
echo "verbose_logging=1" >> usr/config.txt
```

#### 3. Modify Startup Script
```bash
# Edit startup script
nano etc/run_app.sh

# Add custom initialization
# (See example in en818_modifier.py)
```

#### 4. Add Custom Scripts
```bash
# Create custom authentication handler
cat > usr/bin/custom_auth.sh << 'EOF'
#!/bin/sh
# Custom authentication logic
echo "Custom auth: $1 $2 $3" >> /tmp/auth.log
EOF

chmod +x usr/bin/custom_auth.sh
```

## Step 6: Repack Firmware

### Repack SquashFS
```bash
cd /home/samz/Videos/test\ reverse

# Create new SquashFS filesystem
mksquashfs _a60_modified/squashfs-root _a60_modified/modified.squashfs \
    -comp lzma -b 65536 -no-xattrs
```

### Rebuild Complete Firmware
```bash
# This requires careful offset management
# Use the firmware_modifier.py script for safe rebuilding
python3 firmware_modifier.py
```

## Step 7: Validate Modified Firmware

### File Integrity Check
```bash
# Check SquashFS integrity
unsquashfs -l _a60_modified/modified.squashfs

# Verify critical files exist
ls -la _a60_modified/squashfs-root/usr/config.txt
ls -la _a60_modified/squashfs-root/etc/run_app.sh
```

### Configuration Validation
```bash
# Check configuration syntax
grep -v "^#" _a60_modified/squashfs-root/usr/config.txt | grep "="

# Verify scripts are executable
find _a60_modified/squashfs-root -name "*.sh" -exec ls -la {} \;
```

## Step 8: Flash Modified Firmware

### ⚠️ CRITICAL: Test Environment First

**NEVER flash modified firmware to production device without testing!**

### Flashing Methods

#### Method A: TFTP Network Flashing (If Supported)
```bash
# Set up TFTP server
sudo apt install tftpd-hpa

# Copy modified firmware to TFTP directory
sudo cp modified_a60.bin /var/lib/tftpboot/

# Device must be in recovery mode and configured for TFTP
# Specific procedure varies by device
```

#### Method B: Serial Console Flashing
```bash
# Connect serial console to device
# Interrupt boot process
# Use device-specific flashing commands
```

#### Method C: JTAG Flashing
```bash
# Requires JTAG connection and OpenOCD setup
# Device-specific configuration needed
```

#### Method D: Manufacturer Tools
- Check for ANYKA-specific flashing tools
- May require special USB connection or mode

## Step 9: Testing Modified Firmware

### Initial Boot Test
1. Monitor serial console output
2. Check for error messages
3. Verify system starts correctly

### Functionality Testing
1. **Authentication Systems**
   - Test fingerprint reader
   - Test password input
   - Test card reader (if applicable)

2. **Network Connectivity**
   - Verify IP configuration
   - Test TCP/IP communication
   - Check web interface (if added)

3. **Display Functions**
   - Verify display works
   - Check menu navigation
   - Test user interface

4. **I/O Functions**
   - Test Wiegand output
   - Test RS485 communication
   - Verify alarm I/O

### Debug Information
```bash
# Check system logs (via serial console)
dmesg
cat /tmp/auth.log
ps aux
free -h
df -h
```

## Step 10: Deployment

### Pre-deployment Checklist
- [ ] All functions tested and working
- [ ] Performance acceptable
- [ ] Security features intact
- [ ] Backup firmware available
- [ ] Recovery method available
- [ ] Documentation updated

### Deployment Process
1. Schedule maintenance window
2. Prepare rollback plan
3. Flash modified firmware
4. Verify functionality
5. Monitor for issues
6. Document changes

## Common Modifications Examples


### 2. Custom Authentication Logging
```bash
# Redirect auth events to custom handler
echo 'auth_handler="/usr/bin/custom_auth.sh"' >> usr/config.txt
```

### 4. Display Customization
```bash
# Change boot message
echo 'boot_message="Custom EN-818 Firmware"' >> usr/config.txt
```

## Troubleshooting

### Common Issues

#### 1. Device Won't Boot
- **Cause**: Corrupted filesystem or configuration
- **Solution**: Flash original firmware, check modifications

#### 2. Authentication Not Working
- **Cause**: Modified authentication settings
- **Solution**: Verify configuration, check hardware connections

#### 3. Network Issues
- **Cause**: Incorrect network configuration
- **Solution**: Check IP settings, verify network hardware

#### 4. Display Problems
- **Cause**: Display driver issues or configuration
- **Solution**: Verify display settings, check connections

### Recovery Procedures

#### Method 1: Serial Console Recovery
```bash
# Interrupt boot process
# Load original firmware via TFTP or USB
```

#### Method 2: JTAG Recovery
```bash
# Connect JTAG interface
# Flash original firmware directly to flash memory
```

#### Method 3: Hardware Recovery
- Some devices have hardware recovery modes
- Check manufacturer documentation

## Security Considerations

### Firmware Security
- Modified firmware may have different security properties
- Test thoroughly for vulnerabilities
- Consider impact on authentication security

### Access Control
- Ensure modifications don't bypass security features
- Verify authentication still works correctly
- Test all access control functions

### Network Security
- Modified network settings may affect security
- Ensure proper firewall configuration
- Test network communication security

## Legal and Warranty Notes

### Important Disclaimers
- Firmware modification may void warranty
- Ensure compliance with local regulations
- Consider intellectual property implications
- Use only for authorized devices you own

### Best Practices
- Document all modifications
- Maintain version control
- Test thoroughly before deployment
- Have rollback procedures ready

## Conclusion

This guide provides a comprehensive approach to safely modifying EN-818/EN-818T firmware. Always prioritize safety, testing, and maintaining recovery options.

For additional support or device-specific procedures, consult:
- Device manufacturer documentation
- Hardware service manuals
- Community forums and resources
- Professional firmware modification services

Remember: "With great power comes great responsibility" - firmware modification can enhance your device but requires careful attention to detail and safety procedures.
