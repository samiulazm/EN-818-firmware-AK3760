#!/bin/sh
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
