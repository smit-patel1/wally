#!/bin/bash
# Fix Livox MID360 network configuration
# This script makes the eno1 static IP persistent across reboots.
# Run with: sudo bash ~/fix_livox_network.sh

set -e

# Create persistent NetworkManager connection
nmcli con delete eno1 2>/dev/null || true
nmcli con add type ethernet ifname eno1 con-name "livox-lidar" \
    ipv4.method manual \
    ipv4.addresses 192.168.1.5/24 \
    connection.autoconnect yes \
    ipv6.method disabled

# Ensure it's active
nmcli con up livox-lidar

echo "Done. eno1 is now configured with persistent static IP 192.168.1.5/24"
echo "This configuration will survive reboots."
