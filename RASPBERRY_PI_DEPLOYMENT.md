# Raspberry Pi Deployment Guide

**TESTED ON:** Raspberry Pi 4 Model B (4GB RAM), Raspberry Pi OS (64-bit)  
**PYTHON VERSION:** 3.9 or higher required  
**ESTIMATED SETUP TIME:** 30-45 minutes

---

## ⚠️ PREREQUISITES

Before starting, ensure your Raspberry Pi has:
- **Raspberry Pi OS (64-bit)** installed (Bullseye or newer)
- **At least 4GB RAM** (8GB recommended for heavy scraping)
- **At least 32GB SD card** (64GB+ recommended for storing images)
- **Stable internet connection**
- **SSH access** (if deploying remotely)

---

## 📋 STEP 1: SYSTEM PREPARATION

### 1.1 Update System
```bash
# Update package lists
sudo apt-get update

# Upgrade existing packages (this may take 10-15 minutes)
sudo apt-get upgrade -y

# Reboot if kernel was updated
sudo reboot
```

**WAIT:** After reboot, SSH back in and continue.

### 1.2 Install System Dependencies
```bash
# Install Python 3.9+ and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Verify Python version (must be 3.9 or higher)
python3 --version

# Install MongoDB dependencies
sudo apt-get install -y wget curl gnupg software-properties-common

# Install git
sudo apt-get install -y git

# Install Playwright system dependencies
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2

# Verify installations
which python3 && which pip3 && which git && echo "✅ All system dependencies installed"
```

**EXPECTED OUTPUT:** Should see paths to python3, pip3, and git, followed by "✅ All system dependencies installed"

---

## 📋 STEP 2: INSTALL MONGODB

### 2.1 Install MongoDB on Raspberry Pi
```bash
# Add MongoDB repository key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Add MongoDB repository (for Debian/Ubuntu ARM64)
echo "deb [ arch=arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update package lists
sudo apt-get update

# Install MongoDB
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod

# Enable MongoDB to start on boot
sudo systemctl enable mongod

# Verify MongoDB is running
sudo systemctl status mongod

# Test MongoDB connection
mongosh --eval "db.adminCommand('ping')"
```

**EXPECTED OUTPUT:** Last command should print `{ ok: 1 }`

**TROUBLESHOOTING:**
- If `mongodb-org` is not available for ARM64, use Docker method instead (see Alternative Method below)

### 2.2 Alternative: MongoDB via Docker (If Step 2.1 fails)
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
exit
# SSH back in

# Install Docker Compose
sudo apt-get install -y docker-compose

# Verify Docker is running
docker --version && docker-compose --version
```

**NOTE:** If using Docker, skip step 2.1 and use docker-compose in Step 4.

---

## 📋 STEP 3: CLONE REPOSITORY

### 3.1 Clone from GitHub
```bash
# Navigate to home directory
cd ~

# Clone repository
git clone https://github.com/gagan114662/behance.git

# Navigate to project directory
cd behance

# Verify files are present
ls -la

# Check current branch
git branch
```

**EXPECTED OUTPUT:** Should see all project files including `scrape_behance_images.py`, `scrape_pinterest_images.py`, `cron_scraper.py`

---

## 📋 STEP 4: SETUP PYTHON ENVIRONMENT

### 4.1 Create Virtual Environment
```bash
# Ensure you're in the behance directory
cd ~/behance

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (prompt should show (venv))
which python
```

**EXPECTED OUTPUT:** `/home/pi/behance/venv/bin/python`

### 4.2 Install Python Dependencies
```bash
# Upgrade pip (important!)
pip install --upgrade pip

# Install all requirements (this will take 5-10 minutes)
pip install -r requirements.txt

# Verify installations
pip list | grep -E "playwright|pymongo|pydantic|aiohttp"
```

**EXPECTED OUTPUT:** Should see playwright, pymongo, pydantic, aiohttp in the list

### 4.3 Install Playwright Browsers
```bash
# Install Chromium browser for Playwright (this will take 5-10 minutes)
playwright install chromium

# Install system dependencies for Playwright
playwright install-deps chromium

# Verify installation
playwright --version
```

**EXPECTED OUTPUT:** `Version 1.x.x`

**TROUBLESHOOTING:**
- If playwright install fails with "unsupported platform", you may need to build from source or use a different browser. Contact me if this happens.

---

## 📋 STEP 5: CONFIGURE ENVIRONMENT

### 5.1 Create Environment File
```bash
# Copy example environment file
cp .env.example .env

# Edit environment file
nano .env
```

**ADD THE FOLLOWING:**
```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
BEHANCE_DATABASE=behance_crawler
PINTEREST_DATABASE=pinterest_crawler

# Pinterest Authentication
PINTEREST_EMAIL=gagan@getfoolish.com
PINTEREST_PASSWORD=vandanchopra@114
PINTEREST_COOKIES_PATH=./pinterest_cookies.json

# Scraping Configuration
HEADLESS=true
MAX_PROJECTS=10
MAX_PINS_PER_BOARD=10000

# Output Directories
BEHANCE_OUTPUT_DIR=./behance_images
PINTEREST_OUTPUT_DIR=./pinterest_images

# Cron Configuration
CRON_SCHEDULE=daily
CRON_TIME=02:00
```

**SAVE AND EXIT:** Press `Ctrl+X`, then `Y`, then `Enter`

### 5.2 Create Required Directories
```bash
# Create logs directory
mkdir -p logs

# Create output directories
mkdir -p behance_images pinterest_images

# Verify directories
ls -la | grep -E "logs|behance_images|pinterest_images"
```

---

## 📋 STEP 6: START MONGODB (If not using Docker)

### 6.1 Verify MongoDB is Running
```bash
# Check MongoDB status
sudo systemctl status mongod

# If not running, start it
sudo systemctl start mongod

# Test connection
mongosh --eval "db.adminCommand('ping')"
```

**EXPECTED OUTPUT:** `{ ok: 1 }`

### 6.2 Alternative: Start MongoDB via Docker
```bash
# If you installed Docker in Step 2.2, use this instead:
cd ~/behance
docker-compose up -d

# Verify MongoDB container is running
docker ps | grep mongodb

# Test connection
docker exec behance_mongodb mongosh --eval "db.adminCommand('ping')"
```

---

## 📋 STEP 7: TEST THE SCRAPERS

### 7.1 Test Behance Scraper
```bash
# Ensure virtual environment is activated
source ~/behance/venv/bin/activate

# Navigate to project directory
cd ~/behance

# Run Behance scraper with small test
python3 scrape_behance_images.py --search "logo" --max 2
```

**EXPECTED OUTPUT:**
```
🔧 Setting up scraper...
✅ Connected to MongoDB: behance_crawler
✅ Browser launched
🔍 Searching for: 'logo'
📋 Found 25 project links
📦 [1/2] Processing: ...
  📝 Project: ...
  🖼️  Found XX images
  ✅ Downloaded XX/XX images
...
✅ Cleanup complete
```

**TROUBLESHOOTING:**
- If MongoDB connection fails: Check `sudo systemctl status mongod`
- If browser fails: Check `playwright install chromium` was successful
- If timeout errors: Your Pi might be slow, increase timeout in code or try with `--max 1`

### 7.2 Test Pinterest Scraper
```bash
# Run Pinterest scraper with authentication
python3 scrape_pinterest_images.py \
  --username sangichandresh \
  --email "gagan@getfoolish.com" \
  --password "vandanchopra@114" \
  --max-boards 1 \
  --max-pins 10 \
  --no-headless
```

**EXPECTED OUTPUT:**
```
🔧 Setting up Pinterest scraper...
✅ Connected to MongoDB: pinterest_crawler
✅ Browser launched
🔐 Logging into Pinterest with Google...
  ✅ Google login successful!
✅ Saved cookies to: ./pinterest_cookies.json
...
✅ Cleanup complete
```

**IMPORTANT:** After first successful login, cookies are saved to `pinterest_cookies.json` and you won't need to login again.

### 7.3 Test Cron Job Script
```bash
# Run cron script manually to test (this will take 5-10 minutes)
python3 cron_scraper.py 2>&1 | tee logs/manual_test.log

# Check the log
tail -50 logs/manual_test.log
```

**EXPECTED OUTPUT:** Should see both Behance and Pinterest scrapers running successfully

---

## 📋 STEP 8: SETUP CRON JOB FOR AUTOMATION

### 8.1 Create Cron Wrapper Script
```bash
# Create wrapper script
cat > ~/behance/run_scraper.sh << 'SCRIPT_EOF'
#!/bin/bash

# Activate virtual environment
cd /home/pi/behance
source venv/bin/activate

# Run scraper
python3 cron_scraper.py

# Exit
exit 0
SCRIPT_EOF

# Make executable
chmod +x ~/behance/run_scraper.sh

# Test the wrapper
./run_scraper.sh 2>&1 | head -20
```

### 8.2 Setup Crontab
```bash
# Open crontab editor
crontab -e

# If asked to choose editor, select nano (option 1)
```

**ADD ONE OF THESE LINES:**

**Option A: Run daily at 2 AM**
```cron
0 2 * * * /home/pi/behance/run_scraper.sh >> /home/pi/behance/logs/cron.log 2>&1
```

**Option B: Run every 6 hours**
```cron
0 */6 * * * /home/pi/behance/run_scraper.sh >> /home/pi/behance/logs/cron.log 2>&1
```

**Option C: Run weekly on Sunday at midnight**
```cron
0 0 * * 0 /home/pi/behance/run_scraper.sh >> /home/pi/behance/logs/cron.log 2>&1
```

**SAVE AND EXIT:** Press `Ctrl+X`, then `Y`, then `Enter`

### 8.3 Verify Cron Job
```bash
# List crontab
crontab -l

# Check cron service is running
sudo systemctl status cron

# Force run to test (wait 1-2 minutes for cron to execute)
# Note: Cron jobs run in background, check logs to see output
sleep 120 && tail -50 logs/cron.log
```

---

## 📋 STEP 9: MONITORING AND MAINTENANCE

### 9.1 Check Logs
```bash
# View real-time logs
tail -f ~/behance/logs/cron.log

# View last 100 lines
tail -100 ~/behance/logs/cron.log

# Search for errors
grep -i "error\|failed" ~/behance/logs/cron.log

# Check log file size
du -h ~/behance/logs/cron.log
```

### 9.2 Check MongoDB Data
```bash
# Check Behance database
mongosh behance_crawler --eval "
  print('Projects:', db.projects.countDocuments({}));
  print('Images:', db.images.countDocuments({}));
"

# Check Pinterest database  
mongosh pinterest_crawler --eval "
  print('Profiles:', db.pinterest_profiles.countDocuments({}));
  print('Boards:', db.pinterest_boards.countDocuments({}));
  print('Pins:', db.pinterest_pins.countDocuments({}));
"
```

### 9.3 Check Disk Usage
```bash
# Check image directories
du -sh ~/behance/behance_images
du -sh ~/behance/pinterest_images

# Check total project size
du -sh ~/behance

# Check available disk space
df -h
```

### 9.4 Check System Resources
```bash
# Check memory usage
free -h

# Check CPU usage
top -bn1 | head -20

# Check running processes
ps aux | grep python

# Check MongoDB status
sudo systemctl status mongod
```

---

## 📋 STEP 10: TROUBLESHOOTING

### Common Issues and Solutions

#### Issue 1: MongoDB Connection Failed
```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod

# Check MongoDB logs
sudo tail -50 /var/log/mongodb/mongod.log
```

#### Issue 2: Playwright Browser Not Found
```bash
# Reinstall Playwright browsers
source ~/behance/venv/bin/activate
playwright install --force chromium
playwright install-deps chromium
```

#### Issue 3: Pinterest Login Fails
```bash
# Delete old cookies and re-authenticate
rm ~/behance/pinterest_cookies.json

# Run with visible browser to debug
python3 scrape_pinterest_images.py \
  --username sangichandresh \
  --email "gagan@getfoolish.com" \
  --password "vandanchopra@114" \
  --max-boards 1 \
  --no-headless
```

#### Issue 4: Out of Memory
```bash
# Check memory
free -h

# Increase swap size (Raspberry Pi OS)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Reboot
sudo reboot
```

#### Issue 5: Disk Space Full
```bash
# Check space
df -h

# Clean up old images (CAREFUL!)
# Move to external drive or delete old downloads
rm -rf ~/behance/behance_images_old
rm -rf ~/behance/pinterest_images_old

# Compress old images
tar -czf ~/behance_images_backup_$(date +%Y%m%d).tar.gz ~/behance/behance_images
tar -czf ~/pinterest_images_backup_$(date +%Y%m%d).tar.gz ~/behance/pinterest_images

# Move compressed files to external drive
# Then delete originals
```

#### Issue 6: Cron Job Not Running
```bash
# Check cron service
sudo systemctl status cron

# Restart cron
sudo systemctl restart cron

# Check system logs
grep CRON /var/log/syslog | tail -20

# Test wrapper script manually
cd ~/behance
./run_scraper.sh
```

---

## 📋 STEP 11: UPDATING THE CODE

### 11.1 Pull Latest Changes from GitHub
```bash
# Navigate to project
cd ~/behance

# Stash any local changes
git stash

# Pull latest code
git pull origin main

# Reactivate virtual environment
source venv/bin/activate

# Reinstall dependencies (in case they changed)
pip install -r requirements.txt

# Test updated code
python3 scrape_behance_images.py --search "test" --max 1
```

### 11.2 Rollback if Something Breaks
```bash
# View commit history
cd ~/behance
git log --oneline

# Rollback to previous commit (replace COMMIT_HASH)
git reset --hard COMMIT_HASH

# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📋 STEP 12: BACKUPS

### 12.1 Backup MongoDB Data
```bash
# Create backup directory
mkdir -p ~/behance_backups

# Backup Behance database
mongodump --db behance_crawler --out ~/behance_backups/behance_$(date +%Y%m%d)

# Backup Pinterest database
mongodump --db pinterest_crawler --out ~/behance_backups/pinterest_$(date +%Y%m%d)

# Compress backups
cd ~/behance_backups
tar -czf mongodb_backup_$(date +%Y%m%d).tar.gz *_$(date +%Y%m%d)

# Copy to external drive or cloud storage
# Example: rsync to remote server
# rsync -avz ~/behance_backups/ user@backup-server:/backups/
```

### 12.2 Restore from Backup
```bash
# Extract backup
cd ~/behance_backups
tar -xzf mongodb_backup_YYYYMMDD.tar.gz

# Restore Behance database
mongorestore --db behance_crawler ~/behance_backups/behance_YYYYMMDD/behance_crawler

# Restore Pinterest database
mongorestore --db pinterest_crawler ~/behance_backups/pinterest_YYYYMMDD/pinterest_crawler
```

---

## 📋 PERFORMANCE OPTIMIZATION FOR RASPBERRY PI

### Recommended Settings for Raspberry Pi 4 (4GB RAM)

**Edit cron_scraper.py configuration:**
```python
'behance': {
    'max_projects': 3,  # Lower for Pi (default was 5)
},
'pinterest': {
    'max_pins': 5000,  # Lower for Pi (default was 10000)
}
```

**Increase timeout for slower Pi:**
```python
# In scrape_behance_images.py and scrape_pinterest_images.py
timeout=60000  # Change from 30000 to 60000 (60 seconds)
```

**Run scrapers sequentially (not parallel):**
```bash
# Instead of running cron_scraper.py, run individually:
python3 scrape_behance_images.py --search "design" --max 3
python3 scrape_pinterest_images.py --username sangichandresh --max-boards 10
```

---

## ✅ VERIFICATION CHECKLIST

Before considering deployment complete, verify:

- [ ] Python 3.9+ installed: `python3 --version`
- [ ] MongoDB running: `mongosh --eval "db.adminCommand('ping')"`
- [ ] Virtual environment created: `ls ~/behance/venv`
- [ ] Dependencies installed: `pip list | grep playwright`
- [ ] Playwright browsers installed: `playwright --version`
- [ ] Environment variables configured: `cat ~/behance/.env`
- [ ] Behance scraper works: `python3 scrape_behance_images.py --search "test" --max 1`
- [ ] Pinterest scraper works: `python3 scrape_pinterest_images.py --username sangichandresh --max-boards 1`
- [ ] Cron job configured: `crontab -l`
- [ ] Logs directory created: `ls ~/behance/logs`
- [ ] MongoDB has data: `mongosh behance_crawler --eval "db.projects.countDocuments({})"`

---

## 📞 SUPPORT

If you encounter issues not covered in this guide:

1. Check logs: `tail -100 ~/behance/logs/cron.log`
2. Check MongoDB: `mongosh --eval "db.adminCommand('ping')"`
3. Check system resources: `free -h && df -h`
4. Check GitHub Issues: https://github.com/gagan114662/behance/issues
5. Test on desktop first to isolate Raspberry Pi-specific issues

---

## 📊 EXPECTED PERFORMANCE

**Raspberry Pi 4 (4GB RAM):**
- Behance: ~2-3 minutes per project (depends on image count)
- Pinterest: ~30-60 seconds per board (depends on pin count)
- Full Pinterest scrape (35 boards): ~30-60 minutes
- Memory usage: 500MB-1.5GB
- CPU usage: 60-80% during active scraping

**Storage Estimates:**
- Behance projects: ~10-50MB per project
- Pinterest boards: ~5-20MB per board
- MongoDB database: ~100-500MB after heavy usage
- Logs: ~1-5MB per day

---

## 🔐 SECURITY NOTES

1. **Credentials stored in .env are NOT encrypted** - ensure proper file permissions:
   ```bash
   chmod 600 ~/behance/.env
   chmod 600 ~/behance/pinterest_cookies.json
   ```

2. **MongoDB is exposed on port 27017** - if your Pi is accessible from internet, secure it:
   ```bash
   # Edit MongoDB config
   sudo nano /etc/mongod.conf
   # Change bindIp from 0.0.0.0 to 127.0.0.1
   sudo systemctl restart mongod
   ```

3. **Regular security updates:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

---

**DEPLOYMENT COMPLETED** ✅

Once all steps are verified, the scraper will run automatically according to your cron schedule.
