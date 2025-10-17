# Google Drive Upload Setup

This guide shows you how to upload your Pinterest images to Google Drive.

## Quick Start (5 minutes)

### Step 1: Get Google Drive API Credentials

1. **Go to Google Cloud Console**: https://console.cloud.google.com/

2. **Create a New Project** (or select existing):
   - Click "Select a project" at the top
   - Click "NEW PROJECT"
   - Name it "Pinterest Scraper" or anything you want
   - Click "CREATE"

3. **Enable Google Drive API**:
   - Go to: https://console.cloud.google.com/apis/library/drive.googleapis.com
   - Click "ENABLE"

4. **Create OAuth Credentials**:
   - Go to: https://console.cloud.google.com/apis/credentials
   - Click "CREATE CREDENTIALS" → "OAuth client ID"
   - If prompted, configure OAuth consent screen:
     - User Type: "External"
     - App name: "Pinterest Scraper"
     - User support email: your email
     - Developer email: your email
     - Click "SAVE AND CONTINUE" through all steps
   - Back to Create OAuth client ID:
     - Application type: "Desktop app"
     - Name: "Pinterest Uploader"
     - Click "CREATE"

5. **Download Credentials**:
   - Click the ⬇️ download icon for your OAuth client
   - Rename the downloaded file to `credentials.json`
   - Move it to your project root folder (where README.md is)

### Step 2: Upload Your Images

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the uploader
python3 scripts/upload_to_gdrive.py
```

**What happens:**
1. A browser window will open
2. Sign in with your Google account
3. Click "Allow" when asked for Drive access
4. The upload will start automatically
5. All 2,314 Pinterest images (40MB) will be uploaded

### Step 3: View Your Files

Go to: https://drive.google.com/drive/my-drive

You'll see a folder called "Pinterest Images" with all your boards inside!

---

## Troubleshooting

### "credentials.json not found"
- Make sure you downloaded the file from Google Cloud Console
- Rename it to exactly `credentials.json`
- Place it in the project root (same folder as README.md)

### "Access blocked: This app hasn't been verified"
This is normal for personal projects! Click "Advanced" → "Go to [App Name] (unsafe)"

Your app is safe - Google just shows this for apps that aren't publicly verified.

### "The redirect URI in the request does not match"
This happens if you selected "Web application" instead of "Desktop app" when creating credentials.

Solution: Delete the OAuth client in Google Cloud Console and create a new one with type "Desktop app".

### Upload Failed / Timeout
- Check your internet connection
- Try again - the script will skip already uploaded files

---

## Advanced Options

### Upload Different Directory

```bash
python3 scripts/upload_to_gdrive.py --dir ./behance_images
```

### Custom Folder Name

```bash
python3 scripts/upload_to_gdrive.py --folder-name "My Collection"
```

### Use Different Credentials File

```bash
python3 scripts/upload_to_gdrive.py --credentials ./my_creds.json
```

---

## How It Works

1. **First Run**: Opens browser for OAuth authentication
2. **Saves Token**: Stores `gdrive_token.json` for future use
3. **Creates Folders**: Mirrors your local folder structure
4. **Uploads Files**: Recursively uploads all images
5. **Tracks Progress**: Shows real-time upload status

## Security

- **OAuth Tokens**: Stored locally in `gdrive_token.json`
- **Your Data**: Only you have access to your Google Drive
- **Credentials**: Never shared or uploaded anywhere

---

## Need Help?

The uploader script includes detailed help:
```bash
python3 scripts/upload_to_gdrive.py --help
```
