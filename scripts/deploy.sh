#!/bin/bash
# Quick Deployment Commands for Raspberry Pi
# Copy and paste these commands in sequence

# ===== STEP 1: SYSTEM UPDATE =====
sudo apt-get update && sudo apt-get upgrade -y

# ===== STEP 2: INSTALL DEPENDENCIES =====
sudo apt-get install -y python3 python3-pip python3-venv git wget curl
sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2

# ===== STEP 3: INSTALL MONGODB =====
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# ===== STEP 4: CLONE REPOSITORY =====
cd ~
git clone https://github.com/gagan114662/behance.git
cd behance

# ===== STEP 5: SETUP PYTHON ENVIRONMENT =====
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium

# ===== STEP 6: CONFIGURE ENVIRONMENT =====
cp .env.example .env
# Edit .env with your credentials:
nano .env

# ===== STEP 7: CREATE DIRECTORIES =====
mkdir -p logs behance_images pinterest_images

# ===== STEP 8: TEST SCRAPERS =====
# Test Behance
python3 scripts/scrape_behance.py --search "logo" --max 2

# Test Pinterest (replace with your credentials)
python3 scripts/scrape_pinterest.py \
  --username sangichandresh \
  --email "gagan@getfoolish.com" \
  --password "vandanchopra@114" \
  --max-boards 1 \
  --max-pins 10

# ===== STEP 9: SETUP CRON JOB =====
cat > ~/behance/run_scraper.sh << 'SCRIPT'
#!/bin/bash
cd /home/pi/behance
source venv/bin/activate
python3 scripts/cron_scraper.py
exit 0
SCRIPT

chmod +x ~/behance/run_scraper.sh

# Add to crontab (run daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/pi/behance/run_scraper.sh >> /home/pi/behance/logs/cron.log 2>&1") | crontab -

# ===== STEP 10: VERIFY =====
echo "===== VERIFICATION ====="
echo "Python version:"
python3 --version
echo ""
echo "MongoDB status:"
mongosh --eval "db.adminCommand('ping')"
echo ""
echo "Cron jobs:"
crontab -l
echo ""
echo "✅ Deployment complete!"
