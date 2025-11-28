# SNMP Monitoring Server Setup Guide

## 📋 Overview

This guide walks through setting up the SNMP monitoring server to monitor your GNS3 network simulation.

**Server Details:**
- **IP Address:** 192.168.254.100/24
- **Gateway:** 192.168.254.1
- **OS:** Ubuntu 22.04 LTS
- **Connected to:** SERVER-SW port Ethernet0/1
- **VLAN:** 99 (Management)

---

## 🖥️ Step 1: Configure Server Network

### Ubuntu Network Configuration

```bash
# Check interface name
ip addr show

# Common names: eth0, ens3, ens33, ens160
# We'll use ens3 for this example
```

### Configure Static IP with Netplan

```bash
# Edit netplan configuration
sudo nano /etc/netplan/01-netcfg.yaml
```

**Configuration File:**
```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    ens3:  # Change to your interface name
      addresses:
        - 192.168.254.100/24
      routes:
        - to: default
          via: 192.168.254.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
        search:
          - school.edu
```

**Apply Configuration:**
```bash
# Test configuration
sudo netplan try

# If successful, apply permanently
sudo netplan apply

# Verify configuration
ip addr show ens3
ip route show
```

**Expected Output:**
```bash
ens3: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 192.168.254.100/24 brd 192.168.254.255 scope global ens3

default via 192.168.254.1 dev ens3 proto static
```

---

## 🔍 Step 2: Test Network Connectivity

### Ping Gateway and Devices

```bash
# Test gateway (MAIN-RTR)
ping -c 4 192.168.254.1

# Test core switch
ping -c 4 192.168.254.10

# Test all switches
for ip in 192.168.254.{1,10,20,25,30,31,32,40}; do
    echo "Testing $ip..."
    ping -c 2 $ip
done
```

**Expected Output:**
```
64 bytes from 192.168.254.1: icmp_seq=1 ttl=255 time=1.23 ms
64 bytes from 192.168.254.1: icmp_seq=2 ttl=255 time=1.45 ms
```

### Test DNS Resolution

```bash
# Test internet connectivity
ping -c 4 8.8.8.8

# Test DNS
ping -c 4 google.com
```

---

## 📦 Step 3: Install SNMP Tools

### Install SNMP Utilities

```bash
# Update package list
sudo apt update

# Install SNMP client tools
sudo apt install -y snmp snmp-mibs-downloader

# Download Cisco MIBs (optional)
sudo download-mibs
```

### Configure SNMP to Use MIBs

```bash
# Edit snmp.conf
sudo nano /etc/snmp/snmp.conf
```

**Comment out this line:**
```bash
# Original:
mibs :

# Change to (add # at the beginning):
# mibs :
```

**Save and exit** (Ctrl+O, Enter, Ctrl+X)

---

## 🧪 Step 4: Test SNMP Connectivity

### Test Router SNMP

```bash
# Test system information
snmpwalk -v2c -c public 192.168.254.1 system

# Expected output:
SNMPv2-MIB::sysDescr.0 = STRING: Cisco IOS Software, 3700 Software...
SNMPv2-MIB::sysObjectID.0 = OID: SNMPv2-SMI::enterprises.9.1.122
SNMPv2-MIB::sysUpTime.0 = Timeticks: (123456) 0:20:34.56
SNMPv2-MIB::sysContact.0 = STRING: IT Department - it@school.edu
SNMPv2-MIB::sysName.0 = STRING: MAIN-RTR
SNMPv2-MIB::sysLocation.0 = STRING: Server Room - Main Router...
```

### Test CPU and Memory OIDs

```bash
# Test CPU on router
snmpget -v2c -c public 192.168.254.1 1.3.6.1.4.1.9.9.109.1.1.1.1.8.1

# Expected:
SNMPv2-SMI::enterprises.9.9.109.1.1.1.1.8.1 = Gauge32: 5

# Test memory on router
snmpwalk -v2c -c public 192.168.254.1 1.3.6.1.4.1.9.9.48.1.1.1
```

### Test Switch SNMP

```bash
# Test IOSvL2 switch (CORE-SW)
snmpget -v2c -c public 192.168.254.10 1.3.6.1.2.1.1.5.0

# Expected:
SNMPv2-MIB::sysName.0 = STRING: CORE-SW

# Test IOU L2 switch (LAB-SW2)
snmpget -v2c -c public 192.168.254.31 1.3.6.1.2.1.1.5.0

# Expected:
SNMPv2-MIB::sysName.0 = STRING: LAB-SW2
```

### Test All Devices

```bash
# Quick test script
for ip in 192.168.254.{1,10,20,25,30,31,32,40}; do
    hostname=$(snmpget -v2c -c public -Oqv $ip 1.3.6.1.2.1.1.5.0 2>/dev/null)
    echo "$ip - $hostname"
done
```

**Expected Output:**
```
192.168.254.1 - MAIN-RTR
192.168.254.10 - CORE-SW
192.168.254.20 - ADMIN-SW
192.168.254.25 - SERVER-SW
192.168.254.30 - LAB-SW1
192.168.254.31 - LAB-SW2
192.168.254.32 - LAB-SW3
192.168.254.40 - LIB-SW
```

---

## 🐍 Step 5: Install SNMP Monitoring Application

### Clone Repository

```bash
# Install git if not already installed
sudo apt install -y git

# Clone the SNMP monitoring repository
cd ~
git clone https://github.com/wharizmarzuki/SNMP-Monitoring.git
cd SNMP-Monitoring
```

### Run Setup Script

```bash
# Make setup script executable
chmod +x setup.sh

# Run interactive setup
./setup.sh
```

**Setup Wizard Prompts:**
```
Enter network range for discovery (CIDR notation):
> 192.168.254.0/24

Enter SNMP community string:
> public

Enter polling interval in seconds:
> 60

Enter SMTP server (leave blank to skip email):
> [Press Enter to skip]

Enable Redis caching? (y/n):
> n
```

### Manual Installation (Alternative)

```bash
# Install Python 3.12
sudo apt install -y python3.12 python3.12-venv python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Backend setup
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install --legacy-peer-deps

# Create backend .env file
cd ../backend
cp .env.example .env
nano .env
```

**Edit .env file:**
```bash
# Network Discovery
DISCOVERY_NETWORK=192.168.254.0/24

# SNMP Configuration
SNMP_COMMUNITY=public
SNMP_TIMEOUT=10
SNMP_RETRIES=3

# Polling
POLLING_INTERVAL=60

# Database
DATABASE_URL=sqlite:///./monitoring.db

# JWT (generate secure key)
JWT_SECRET=your-secret-key-here
```

---

## 🚀 Step 6: Start SNMP Monitoring Services

### Start Backend

```bash
# Terminal 1 - Backend
cd ~/SNMP-Monitoring/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Start Frontend

```bash
# Terminal 2 - Frontend
cd ~/SNMP-Monitoring/frontend
npm run dev

# Expected output:
> frontend@0.1.0 dev
> next dev
  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
  - Network:      http://192.168.254.100:3000
```

### Using the Start Script (Recommended)

```bash
# Use the provided start script
cd ~/SNMP-Monitoring
./start-dev.sh

# This starts both backend and frontend
# Logs to: logs/backend.log and logs/frontend.log
```

---

## 🔍 Step 7: Initial Device Discovery

### Access Web Interface

```bash
# From GNS3 host machine, open browser:
http://192.168.254.100:3000

# Default login (if prompted):
# Username: admin
# Password: (set during setup)
```

### Run Network Discovery

1. **Navigate to Settings** (⚙️ icon)
2. **Scroll to "Network Discovery" section**
3. **Enter parameters:**
   - Network IP: `192.168.254.0`
   - Subnet: `24`
4. **Click "Run Discovery"**

**CLI Alternative:**
```bash
# Using curl to trigger discovery
curl -X GET "http://192.168.254.100:8000/api/v1/device/discover?network=192.168.254.0&subnet=24"
```

**Expected Discovery Results:**
```json
{
  "total_scanned": 254,
  "devices_found": 8,
  "devices": [
    {"ip": "192.168.254.1", "hostname": "MAIN-RTR", "vendor": "Cisco"},
    {"ip": "192.168.254.10", "hostname": "CORE-SW", "vendor": "Cisco"},
    {"ip": "192.168.254.20", "hostname": "ADMIN-SW", "vendor": "Cisco"},
    ...
  ]
}
```

---

## 📊 Step 8: Verify Monitoring

### Check Dashboard

```bash
# Navigate to: http://192.168.254.100:3000/dashboard

# You should see:
# - Total Devices: 8
# - Devices Up: 8
# - Devices Down: 0
# - Top 5 Devices by Priority
```

### Verify Device Metrics

1. **Click on any device** (e.g., MAIN-RTR)
2. **Check metrics:**
   - CPU Utilization: 5-15%
   - Memory Usage: 30-50%
   - Uptime: Active time
   - Interface Statistics

### Check Polling Logs

```bash
# View backend logs
tail -f ~/SNMP-Monitoring/logs/backend.log

# Should see polling messages every 60 seconds:
INFO: Polling device MAIN-RTR (192.168.254.1)
INFO: Successfully polled MAIN-RTR - CPU: 8%, Memory: 42%
INFO: Polling device CORE-SW (192.168.254.10)
...
```

---

## ⚙️ Step 9: Configure Device Priorities

### Set Device Priorities via Web UI

1. **Go to Devices page**
2. **For each device, click Edit**
3. **Set priorities:**
   - MAIN-RTR: Priority 1 (Critical)
   - CORE-SW: Priority 1 (Critical)
   - SERVER-SW: Priority 1 (Critical)
   - ADMIN-SW: Priority 2 (High)
   - LAB-SW1: Priority 2 (High)
   - LAB-SW2: Priority 3 (Medium)
   - LAB-SW3: Priority 3 (Medium)
   - LIB-SW: Priority 3 (Medium)

### Set Priorities via API

```bash
# Update MAIN-RTR priority
curl -X PUT "http://192.168.254.100:8000/api/v1/device/1" \
  -H "Content-Type: application/json" \
  -d '{"priority": 1}'

# Update CORE-SW priority
curl -X PUT "http://192.168.254.100:8000/api/v1/device/2" \
  -H "Content-Type: application/json" \
  -d '{"priority": 1}'
```

---

## 🧪 Step 10: Test Alert System

### Configure Alert Thresholds

```bash
# Set low CPU threshold to test alerts
# Edit device → CPU Threshold: 5%

# This should trigger alert when CPU > 5%
```

### Trigger Test Alert

```bash
# On MAIN-RTR console in GNS3
MAIN-RTR# configure terminal
MAIN-RTR(config)# do show processes cpu
# This generates CPU load

# Check alerts in web UI
# Navigate to: Alerts page
# Should see new alert for MAIN-RTR
```

---

## 📊 Step 11: Database Verification

### Check Database

```bash
# View database
cd ~/SNMP-Monitoring/backend
sqlite3 monitoring.db

# SQL commands:
.tables
SELECT * FROM devices;
SELECT * FROM device_metrics LIMIT 10;
.quit
```

**Expected Tables:**
```
devices
device_metrics
interface_metrics
users
application_settings
alert_recipients
```

---

## 🔐 Step 12: Security Hardening (Optional)

### Configure Firewall

```bash
# Allow SNMP monitoring traffic
sudo ufw allow 8000/tcp comment 'SNMP Backend API'
sudo ufw allow 3000/tcp comment 'SNMP Frontend'
sudo ufw allow from 192.168.254.0/24 comment 'Management VLAN'

# Enable firewall
sudo ufw enable
```

### Change SNMP Community String (Production)

**On all network devices:**
```cisco
# Remove old community
no snmp-server community public RO

# Add secure community
snmp-server community Secur3C0mmun1ty RO
```

**Update server .env:**
```bash
nano ~/SNMP-Monitoring/backend/.env

# Change:
SNMP_COMMUNITY=Secur3C0mmun1ty
```

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Server has IP 192.168.254.100/24
- [ ] Can ping all 8 network devices
- [ ] SNMP queries work on all devices
- [ ] All 8 devices discovered successfully
- [ ] Backend running on port 8000
- [ ] Frontend accessible on port 3000
- [ ] Dashboard shows all devices
- [ ] Polling occurs every 60 seconds
- [ ] Device priorities are set correctly
- [ ] Top 5 devices display correctly

---

## 🐛 Troubleshooting

### No Devices Discovered

```bash
# Test SNMP manually
snmpwalk -v2c -c public 192.168.254.1 system

# Check network connectivity
ping 192.168.254.1

# Verify .env configuration
cat ~/SNMP-Monitoring/backend/.env | grep DISCOVERY
```

### Backend Won't Start

```bash
# Check Python version
python3 --version  # Should be 3.12+

# Check dependencies
cd ~/SNMP-Monitoring/backend
source venv/bin/activate
pip install -r requirements.txt

# Check for port conflicts
sudo netstat -tlnp | grep 8000
```

### No Metrics Showing

```bash
# Check polling service is running
# Look for polling logs
tail -f ~/SNMP-Monitoring/logs/backend.log | grep -i poll

# Manually trigger poll
curl http://192.168.254.100:8000/api/v1/device/poll
```

---

## 📚 Next Steps

- **Configure Email Alerts** → Edit backend/.env SMTP settings
- **Run Tests** → See [testing/snmp-verification.md](../testing/snmp-verification.md)
- **Explore Dashboard Features** → Device details, alerts, reports

---

**SNMP Monitoring Server Setup Complete!** 🎉

Your network simulation is now fully monitored via SNMP.
