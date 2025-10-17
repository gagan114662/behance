# Cron Job Setup Instructions

This guide explains how to set up automated scraping using the cron job script.

## Prerequisites

1. Ensure all dependencies are installed:
```bash
pip3 install -r requirements.txt
playwright install chromium
```

2. Ensure MongoDB is running:
```bash
# Check if MongoDB is running
mongosh --eval "db.adminCommand('ping')"
```

3. Ensure Pinterest cookies are saved:
```bash
# Run Pinterest scraper once manually to save cookies
python3 scrape_pinterest_images.py \
  --username sangichandresh \
  --email "gagan@getfoolish.com" \
  --password "vandanchopra@114" \
  --max-boards 1 \
  --no-headless
```

## Setup Cron Job

### 1. Create logs directory
```bash
cd /Users/gaganarora/Desktop/gagan_projects/behance
mkdir -p logs
```

### 2. Make cron script executable
```bash
chmod +x cron_scraper.py
```

### 3. Edit crontab
```bash
crontab -e
```

### 4. Add cron job entry

Choose one of the following schedules:

#### Option A: Run daily at 2 AM
```cron
0 2 * * * cd /Users/gaganarora/Desktop/gagan_projects/behance && /usr/bin/python3 cron_scraper.py >> logs/cron.log 2>&1
```

#### Option B: Run every 6 hours
```cron
0 */6 * * * cd /Users/gaganarora/Desktop/gagan_projects/behance && /usr/bin/python3 cron_scraper.py >> logs/cron.log 2>&1
```

#### Option C: Run every Monday at 3 AM
```cron
0 3 * * 1 cd /Users/gaganarora/Desktop/gagan_projects/behance && /usr/bin/python3 cron_scraper.py >> logs/cron.log 2>&1
```

#### Option D: Run weekly on Sunday at midnight
```cron
0 0 * * 0 cd /Users/gaganarora/Desktop/gagan_projects/behance && /usr/bin/python3 cron_scraper.py >> logs/cron.log 2>&1
```

### 5. Verify cron job is scheduled
```bash
crontab -l
```

## Configuration

Edit `cron_scraper.py` to customize:

### Behance Configuration
```python
'behance': {
    'urls': [
        'https://www.behance.net/search/projects?search=magenta',
        'https://www.behance.net/search/projects?search=branding',
        # Add more search URLs here
    ],
    'mongodb_url': 'mongodb://localhost:27017',
    'database': 'behance_crawler',
    'output_dir': './behance_images',
    'max_projects': 5,  # Adjust this value
}
```

### Pinterest Configuration
```python
'pinterest': {
    'username': 'sangichandresh',  # Change to your Pinterest username
    'mongodb_url': 'mongodb://localhost:27017',
    'database': 'pinterest_crawler',
    'output_dir': './pinterest_images',
    'cookies_path': './pinterest_cookies.json',
    'email': 'gagan@getfoolish.com',  # Your Google email
    'password': 'vandanchopra@114',   # Your Google password
    'max_pins': 10000,  # Maximum pins per board
}
```

## Monitoring

### View logs
```bash
# View real-time logs
tail -f logs/cron.log

# View last 100 lines
tail -100 logs/cron.log

# Search for errors
grep "ERROR\|❌" logs/cron.log
```

### Check scraper status
```bash
# Check if scraper is currently running
ps aux | grep cron_scraper.py

# Check last run status
tail -20 logs/cron.log
```

### Monitor database
```bash
# Check Behance data
mongosh behance_crawler --eval "db.projects.countDocuments({})"

# Check Pinterest data
mongosh pinterest_crawler --eval "db.pinterest_boards.countDocuments({})"
mongosh pinterest_crawler --eval "db.pinterest_pins.countDocuments({})"
```

### Monitor disk usage
```bash
# Check image directories
du -sh behance_images/
du -sh pinterest_images/
```

## Troubleshooting

### Cron job not running

1. Check cron service is running (macOS):
```bash
sudo launchctl list | grep cron
```

2. Check permissions:
```bash
ls -la cron_scraper.py
```

3. Test script manually:
```bash
cd /Users/gaganarora/Desktop/gagan_projects/behance
python3 cron_scraper.py
```

### Authentication failures

1. Re-login to Pinterest manually to refresh cookies:
```bash
python3 scrape_pinterest_images.py \
  --username sangichandresh \
  --email "gagan@getfoolish.com" \
  --password "vandanchopra@114" \
  --max-boards 1 \
  --no-headless
```

2. Check cookie file exists:
```bash
ls -la pinterest_cookies.json
```

### MongoDB connection errors

1. Ensure MongoDB is running:
```bash
brew services list | grep mongodb
# or
mongosh --eval "db.adminCommand('ping')"
```

2. Restart MongoDB if needed:
```bash
brew services restart mongodb-community
```

### Disk space issues

1. Check available space:
```bash
df -h
```

2. Clean up old images if needed:
```bash
# Archive old images
tar -czf behance_images_$(date +%Y%m%d).tar.gz behance_images/
tar -czf pinterest_images_$(date +%Y%m%d).tar.gz pinterest_images/

# Remove originals after verification
rm -rf behance_images/
rm -rf pinterest_images/
```

## Log Rotation

To prevent logs from growing too large, set up log rotation:

### Create logrotate config
```bash
cat > /usr/local/etc/logrotate.d/behance_scraper << EOF
/Users/gaganarora/Desktop/gagan_projects/behance/logs/*.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
EOF
```

## Notifications (Optional)

### Email notifications on errors

Add to cron_scraper.py:
```python
import smtplib
from email.mime.text import MIMEText

def send_error_email(error_msg):
    msg = MIMEText(f"Scraper error: {error_msg}")
    msg['Subject'] = 'Scraper Error Alert'
    msg['From'] = 'your-email@gmail.com'
    msg['To'] = 'your-email@gmail.com'

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('your-email@gmail.com', 'your-app-password')
        smtp.send_message(msg)
```

## Best Practices

1. **Start with a conservative schedule** (e.g., weekly) and adjust based on needs
2. **Monitor disk usage** regularly
3. **Check logs** periodically for errors
4. **Keep credentials secure** - consider using environment variables
5. **Backup data** regularly
6. **Test changes** manually before updating cron job

## Security Recommendations

1. **Protect credentials**:
```bash
# Use environment variables instead of hardcoding
export PINTEREST_EMAIL="your-email@gmail.com"
export PINTEREST_PASSWORD="your-password"
```

2. **Restrict file permissions**:
```bash
chmod 600 cron_scraper.py
chmod 600 pinterest_cookies.json
```

3. **Regular updates**:
```bash
# Keep dependencies updated
pip3 install --upgrade -r requirements.txt
playwright install --force chromium
```
