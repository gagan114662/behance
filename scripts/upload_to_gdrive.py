#!/usr/bin/env python3
"""Upload Pinterest images to Google Drive.

This script uploads all Pinterest images to Google Drive, maintaining the folder structure.
It uses OAuth 2.0 for authentication.

Setup:
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable Google Drive API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials.json and place in project root
6. Run this script: python3 scripts/upload_to_gdrive.py

The script will open a browser for first-time authentication.
Credentials are saved to gdrive_token.json for future use.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Scopes for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveUploader:
    """Upload files to Google Drive maintaining folder structure."""

    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'gdrive_token.json'):
        """Initialize uploader with credentials.

        Args:
            credentials_file: Path to OAuth credentials JSON file
            token_file: Path to save/load access token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.folder_cache = {}

    def authenticate(self):
        """Authenticate with Google Drive API."""
        creds = None

        # Check if token file exists
        if os.path.exists(self.token_file):
            print(f"📂 Loading credentials from {self.token_file}")
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"\n❌ ERROR: {self.credentials_file} not found!")
                    print("\n📋 Setup Instructions:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a project and enable Google Drive API")
                    print("3. Create OAuth 2.0 credentials (Desktop app)")
                    print("4. Download as credentials.json")
                    print("5. Place credentials.json in project root")
                    print()
                    sys.exit(1)

                print("🔐 Opening browser for authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            print(f"💾 Credentials saved to {self.token_file}")

        self.service = build('drive', 'v3', credentials=creds)
        print("✅ Authenticated with Google Drive")

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Create a folder in Google Drive.

        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)

        Returns:
            Created folder ID
        """
        # Check cache first
        cache_key = f"{parent_id}:{name}"
        if cache_key in self.folder_cache:
            return self.folder_cache[cache_key]

        # Check if folder already exists
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        try:
            results = self.service.files().list(q=query, fields='files(id, name)').execute()
            items = results.get('files', [])

            if items:
                folder_id = items[0]['id']
                self.folder_cache[cache_key] = folder_id
                return folder_id
        except HttpError as e:
            print(f"⚠️  Error checking folder: {e}")

        # Create new folder
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]

        try:
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
            self.folder_cache[cache_key] = folder_id
            print(f"  📁 Created folder: {name}")
            return folder_id
        except HttpError as e:
            print(f"❌ Error creating folder '{name}': {e}")
            raise

    def upload_file(self, file_path: Path, parent_id: Optional[str] = None) -> Optional[str]:
        """Upload a file to Google Drive.

        Args:
            file_path: Path to file
            parent_id: Parent folder ID (None for root)

        Returns:
            Uploaded file ID or None if failed
        """
        file_metadata = {'name': file_path.name}
        if parent_id:
            file_metadata['parents'] = [parent_id]

        try:
            media = MediaFileUpload(str(file_path), resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            return file.get('id')
        except HttpError as e:
            print(f"  ❌ Error uploading {file_path.name}: {e}")
            return None

    def upload_directory(self, local_path: Path, parent_id: Optional[str] = None, root_folder_name: str = None):
        """Upload entire directory to Google Drive recursively.

        Args:
            local_path: Local directory path
            parent_id: Parent folder ID in Google Drive
            root_folder_name: Name for root folder (defaults to directory name)
        """
        if not local_path.exists():
            print(f"❌ Directory not found: {local_path}")
            return

        # Create root folder
        folder_name = root_folder_name or local_path.name
        current_folder_id = self.create_folder(folder_name, parent_id)

        # Track statistics
        stats = {'folders': 0, 'files': 0, 'failed': 0, 'skipped': 0}

        def process_directory(dir_path: Path, folder_id: str, depth: int = 0):
            """Process directory recursively."""
            indent = "  " * depth

            try:
                items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            except PermissionError:
                print(f"{indent}⚠️  Permission denied: {dir_path.name}")
                return

            for item in items:
                # Skip hidden files and __pycache__
                if item.name.startswith('.') or item.name == '__pycache__':
                    stats['skipped'] += 1
                    continue

                if item.is_dir():
                    print(f"{indent}📁 {item.name}/")
                    sub_folder_id = self.create_folder(item.name, folder_id)
                    stats['folders'] += 1
                    process_directory(item, sub_folder_id, depth + 1)
                else:
                    # Upload file
                    print(f"{indent}  📄 {item.name}...", end=' ')
                    file_id = self.upload_file(item, folder_id)
                    if file_id:
                        print("✅")
                        stats['files'] += 1
                    else:
                        print("❌")
                        stats['failed'] += 1

        print(f"\n📤 Uploading: {local_path}")
        print(f"📁 To Google Drive folder: {folder_name}")
        print("="*60)

        process_directory(local_path, current_folder_id)

        print("\n" + "="*60)
        print("📊 Upload Summary:")
        print(f"  📁 Folders created: {stats['folders']}")
        print(f"  📄 Files uploaded: {stats['files']}")
        print(f"  ❌ Failed: {stats['failed']}")
        print(f"  ⏭️  Skipped: {stats['skipped']}")
        print("="*60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Upload Pinterest images to Google Drive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Setup:
  1. Go to https://console.cloud.google.com/
  2. Create project and enable Google Drive API
  3. Create OAuth 2.0 credentials (Desktop app)
  4. Download as credentials.json
  5. Place in project root

Examples:
  # Upload Pinterest images
  python3 scripts/upload_to_gdrive.py

  # Upload specific directory
  python3 scripts/upload_to_gdrive.py --dir ./my_images

  # Custom folder name on Google Drive
  python3 scripts/upload_to_gdrive.py --folder-name "My Pinterest Collection"
        """
    )

    parser.add_argument(
        '--dir',
        default='./pinterest_images',
        help='Directory to upload (default: ./pinterest_images)'
    )
    parser.add_argument(
        '--folder-name',
        default='Pinterest Images',
        help='Name for root folder on Google Drive (default: Pinterest Images)'
    )
    parser.add_argument(
        '--credentials',
        default='credentials.json',
        help='Path to OAuth credentials file (default: credentials.json)'
    )

    args = parser.parse_args()

    # Initialize uploader
    uploader = GoogleDriveUploader(credentials_file=args.credentials)

    try:
        # Authenticate
        uploader.authenticate()

        # Upload directory
        upload_path = Path(args.dir)
        uploader.upload_directory(upload_path, root_folder_name=args.folder_name)

        print("\n✅ Upload complete!")
        print("📱 View your files at: https://drive.google.com/drive/my-drive")

    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
