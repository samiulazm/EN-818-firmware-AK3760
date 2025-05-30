#!/bin/sh

# === NETWORK CONFIGURATION ===
# Device IP: 192.168.1.150

# Configure network interface
ifconfig eth0 up

ifconfig eth0 192.168.1.150 netmask 255.255.255.0
route add default gw 192.168.1.1


# === WEB INTERFACE ===
echo 'Starting web interface on port 8080...' >> /dev/ttySAK0
/usr/bin/start_web.sh &


# === DEBUG MODE ENABLED ===
echo 'Debug mode active' >> /dev/ttySAK0
export DEBUG=1
export VERBOSE=1

# Start system monitoring
dmesg >> /tmp/boot.log &
ps aux >> /tmp/processes.log &


busybox app >> /dev/ttySAK0
busybox reboot -f
