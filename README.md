# Behance & Pinterest Image Scraper

A production-ready web scraper for Behance projects and Pinterest boards with browser automation, MongoDB storage, and autonomous operation.

## Features

- **Dual Platform Support**: Scrape both Behance projects and Pinterest boards
- **Browser Automation**: Playwright with stealth mode for realistic browsing
- **Pinterest Authentication**: Google OAuth login with cookie persistence
- **MongoDB Storage**: Flexible schema for projects, boards, pins, and images
- **Image Pipeline**: Concurrent downloads with organized folder structure
- **Autonomous Operation**: Cron job support for scheduled scraping
- **CLI Interface**: Easy-to-use command-line tools

## Project Structure

```
behance/
├── scripts/              # Executable scripts
│   ├── scrape_behance.py    # Behance scraper CLI
│   ├── scrape_pinterest.py  # Pinterest scraper CLI
│   ├── cron_scraper.py      # Autonomous cron job
│   └── deploy.sh            # Deployment script
├── src/                  # Core library
│   ├── auth/                # Pinterest authentication
│   ├── browser/             # Playwright automation
│   ├── extractors/          # Data extraction logic
│   ├── models/              # Pydantic data models
│   └── storage/             # MongoDB & image pipeline
├── docs/                 # Documentation
│   └── DEPLOYMENT.md        # Raspberry Pi deployment guide
├── behance_images/       # Behance downloads (gitignored)
├── pinterest_images/     # Pinterest downloads (gitignored)
├── .env.example         # Environment template
├── docker-compose.yml   # MongoDB container
└── requirements.txt     # Python dependencies
```

## Installation

### Quick Start

```bash
# Clone repository
git clone https://github.com/gagan114662/behance.git
cd behance

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Setup environment
cp .env.example .env

# Start MongoDB (Docker)
docker-compose up -d
```

### Manual MongoDB Installation

```bash
# macOS
brew install mongodb-community

# Ubuntu/Debian
sudo apt-get install mongodb-org

# Start MongoDB
mongod --dbpath ./data
```

## Usage

### Scrape Behance

```bash
# Search for projects
python3 scripts/scrape_behance.py --search "logo design" --max 20

# Scrape user's projects
python3 scripts/scrape_behance.py --user adobe --max 10

# Scrape trending projects
python3 scripts/scrape_behance.py --trending --max 15
```

### Scrape Pinterest

```bash
# Scrape all boards from a profile
python3 scripts/scrape_pinterest.py --username sangichandresh

# With authentication (recommended)
python3 scripts/scrape_pinterest.py \
  --username sangichandresh \
  --email your@email.com \
  --password yourpassword

# Use saved cookies
python3 scripts/scrape_pinterest.py \
  --username sangichandresh \
  --cookies-path ./pinterest_cookies.json

# Limit boards and pins
python3 scripts/scrape_pinterest.py \
  --username sangichandresh \
  --max-boards 5 \
  --max-pins 100
```

### Autonomous Operation

```bash
# Run both scrapers
python3 scripts/cron_scraper.py

# Setup cron job (runs daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * cd $(pwd) && python3 scripts/cron_scraper.py >> logs/cron.log 2>&1") | crontab -
```

## Configuration

Edit `scripts/cron_scraper.py` to configure autonomous scraping:

```python
self.config = {
    'behance': {
        'urls': [
            'https://www.behance.net/search/projects?search=branding',
            'https://www.behance.net/search/projects?search=logo',
        ],
        'max_projects': 5,
    },
    'pinterest': {
        'username': 'your_username',
        'email': 'your@email.com',
        'password': 'your_password',
        'max_pins': 10000,
    }
}
```

## Deployment

### Raspberry Pi Deployment

See comprehensive deployment guide: **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**

Quick deployment:
```bash
bash scripts/deploy.sh
```

## Output Structure

### Behance Images
```
behance_images/
└── [Owner] - [Project Title]/
    ├── image_001.jpg
    ├── image_002.jpg
    └── ...
```

### Pinterest Images
```
pinterest_images/
└── [username]/
    ├── [Board Name 1]/
    │   ├── image_001.jpg
    │   └── ...
    ├── [Board Name 2]/
    │   └── ...
    └── ...
```

## Development

### Project is organized for clarity and maintainability:

- **scripts/** - All executable entry points
- **src/** - Reusable library code
- **docs/** - Documentation
- Clean separation of concerns
- Type hints with Pydantic models
- Async/await throughout

### MongoDB Collections

**Behance:**
- `behance_projects` - Project metadata
- `behance_users` - User profiles
- `behance_images` - Image references

**Pinterest:**
- `pinterest_profiles` - Profile data
- `pinterest_boards` - Board information
- `pinterest_pins` - Pin metadata

## Troubleshooting

### Pinterest Login Issues
If authentication fails:
1. Use `--no-headless` to see the browser
2. Try direct login instead of Google OAuth
3. Check for captchas
4. Verify credentials are correct

### Memory Issues on Raspberry Pi
- Reduce `max_projects` and `max_pins` in config
- Run scrapers sequentially instead of parallel
- Increase swap space

### Browser Issues
```bash
# Reinstall Playwright
playwright install chromium
playwright install-deps chromium
```

## License

MIT
