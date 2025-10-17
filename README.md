# Behance & Pinterest Image Scraper

A lightweight web scraper for Behance projects and Pinterest boards with browser automation, local storage, and Google Drive upload.

## Features

- **Dual Platform Support**: Scrape both Behance projects and Pinterest boards
- **Browser Automation**: Playwright with stealth mode for realistic browsing
- **Pinterest Authentication**: Google OAuth login with cookie persistence
- **Local Storage**: Images saved to organized local folders
- **Google Drive Upload**: One-command upload to your Google Drive
- **No Database Required**: Simple, lightweight, file-based storage
- **CLI Interface**: Easy-to-use command-line tools

## Project Structure

```
behance/
├── scripts/                  # Executable scripts
│   ├── scrape_behance.py        # Behance scraper
│   ├── scrape_pinterest.py      # Pinterest scraper
│   ├── upload_to_gdrive.py      # Upload to Google Drive
│   └── deploy.sh                # Deployment script
├── src/                      # Core library
│   ├── auth/                    # Pinterest authentication
│   ├── browser/                 # Playwright automation
│   ├── extractors/              # Data extraction logic
│   └── models/                  # Pydantic data models
├── docs/                     # Documentation
│   ├── DEPLOYMENT.md            # Raspberry Pi deployment guide
│   └── GOOGLE_DRIVE_SETUP.md    # Google Drive upload setup
├── behance_images/           # Behance downloads (gitignored)
├── pinterest_images/         # Pinterest downloads (gitignored)
└── requirements.txt          # Python dependencies
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
```

## Usage

### 1. Scrape Pinterest Images

```bash
# Scrape all boards from a profile
python3 scripts/scrape_pinterest.py --username sangichandresh

# With authentication (recommended for private boards)
python3 scripts/scrape_pinterest.py \
  --username sangichandresh \
  --email your@email.com \
  --password yourpassword

# Use saved cookies
python3 scripts/scrape_pinterest.py \
  --username sangichandresh \
  --cookies-path ./pinterest_cookies.json
```

### 2. Upload to Google Drive

```bash
# Upload all Pinterest images to Google Drive
python3 scripts/upload_to_gdrive.py

# First time: Browser will open for Google authentication
# Future runs: Uses saved token automatically
```

**Setup Google Drive (first time only):**
See detailed guide: **[docs/GOOGLE_DRIVE_SETUP.md](docs/GOOGLE_DRIVE_SETUP.md)**

Quick steps:
1. Go to https://console.cloud.google.com/
2. Enable Google Drive API
3. Create OAuth Desktop credentials
4. Download as `credentials.json`
5. Run the uploader script

### 3. Scrape Behance (Optional)

```bash
# Search for projects
python3 scripts/scrape_behance.py --search "logo design" --max 20

# Scrape user's projects
python3 scripts/scrape_behance.py --user adobe --max 10
```

## Output Structure

### Pinterest Images
```
pinterest_images/
└── [username]/
    ├── [Board Name 1]/
    │   ├── image_001.jpg
    │   ├── image_002.jpg
    │   └── ...
    ├── [Board Name 2]/
    │   └── ...
    └── ...
```

### Behance Images
```
behance_images/
└── [Owner] - [Project Title]/
    ├── image_001.jpg
    ├── image_002.jpg
    └── ...
```

## Google Drive Upload

The uploader script:
- ✅ Maintains folder structure
- ✅ Shows real-time progress
- ✅ Resumes from interruptions
- ✅ Supports any directory
- ✅ Secure OAuth authentication

**Example:**
```bash
# Upload Pinterest images (default)
python3 scripts/upload_to_gdrive.py

# Upload Behance images
python3 scripts/upload_to_gdrive.py --dir ./behance_images

# Custom folder name on Google Drive
python3 scripts/upload_to_gdrive.py --folder-name "My Collection"
```

View uploaded files: https://drive.google.com/drive/my-drive

## Troubleshooting

### Pinterest Login Issues
If authentication fails:
1. Use `--no-headless` to see the browser
2. Try direct login instead of Google OAuth
3. Check for captchas
4. Verify credentials are correct

### Google Drive Upload Issues
- **"credentials.json not found"**: Download OAuth credentials from Google Cloud Console
- **"Access blocked"**: Click "Advanced" → "Go to app (unsafe)" - your personal app is safe
- **Upload timeout**: Check internet connection, script will resume from where it stopped

### Browser Issues
```bash
# Reinstall Playwright
playwright install chromium
playwright install-deps chromium
```

## Why No Database?

This scraper is designed to be **simple and lightweight**:
- No MongoDB or database installation required
- Images saved directly to folders
- Easy to backup - just copy the folders
- Upload anywhere - Google Drive, Dropbox, etc.
- Perfect for Raspberry Pi deployment

## Raspberry Pi Deployment

See comprehensive deployment guide: **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**

Quick deployment:
```bash
bash scripts/deploy.sh
```

## Development

### Clean Architecture:
- **scripts/** - All executable entry points
- **src/** - Reusable library code
- **docs/** - Documentation
- Type hints with Pydantic models
- Async/await throughout
- No database dependencies

## License

MIT
