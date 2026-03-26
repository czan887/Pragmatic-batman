#!/bin/bash
# Twitter Bot v2.0 - Firewall Setup Script
# Configures UFW firewall to only allow VPN access

set -e

echo "=== Twitter Bot Firewall Setup ==="
echo "This script configures UFW to only allow access from VPN network"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./setup_firewall.sh)"
    exit 1
fi

# Reset UFW to defaults
echo "Resetting UFW to defaults..."
ufw --force reset

# Default policies
echo "Setting default policies..."
ufw default deny incoming
ufw default allow outgoing

# Allow WireGuard VPN (adjust port if needed)
echo "Allowing WireGuard VPN traffic..."
ufw allow 51820/udp comment 'WireGuard VPN'

# Allow SSH only from VPN network (adjust IP range for your VPN)
echo "Allowing SSH from VPN network only..."
ufw allow from 10.8.0.0/24 to any port 22 proto tcp comment 'SSH via VPN'

# Allow web app only from VPN network
echo "Allowing web app from VPN network only..."
ufw allow from 10.8.0.0/24 to any port 8080 proto tcp comment 'Twitter Bot Web App via VPN'

# Allow localhost connections (for internal communication)
ufw allow from 127.0.0.1 to any comment 'Localhost'

# Enable UFW
echo "Enabling UFW..."
ufw --force enable

# Show status
echo ""
echo "=== Firewall Status ==="
ufw status verbose

echo ""
echo "=== Setup Complete ==="
echo "The Twitter Bot is now only accessible via VPN."
echo "Make sure your VPN client is connected before accessing the web interface."
echo ""
echo "To access the dashboard: https://10.8.0.1:8080 (adjust IP for your VPN)"
