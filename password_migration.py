#!/usr/bin/env python3
"""
Password Migration Helper for TGYN Admin Portal

This script helps migrate plain text passwords to properly hashed passwords
for better security in the Google Sheets database.
"""

import os
import json
import pandas as pd
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def load_service_account():
    """Load Google service account credentials"""
    possible_paths = [
        "/Users/nathanielneo/Desktop/TGYN_Admin/tgyn-admin-1452dbad90f6.json",
        "./tgyn-admin-1452dbad90f6.json",
        "../tgyn-admin-1452dbad90f6.json",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    return None

def get_spreadsheet_url():
    """Get spreadsheet URL from config or environment"""
    config_paths = [
        "/Users/nathanielneo/Desktop/TGYN_Admin/config.json",
        "./config.json",
        "../config.json",
    ]

    for path in config_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                config = json.load(f)
                return config.get("apis", {}).get("google_sheets", {}).get("spreadsheet_url")

    # Fallback to environment
    return os.getenv("GOOGLE_SPREADSHEET_URL")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def migrate_passwords():
    """Migrate plain text passwords to hashed passwords"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        print("🔐 TGYN Admin Portal - Password Migration Tool")
        print("=" * 50)

        # Load credentials
        creds_data = load_service_account()
        if not creds_data:
            print("❌ Google service account credentials not found!")
            return

        # Setup Google Sheets connection
        creds = Credentials.from_service_account_info(
            creds_data,
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )

        gc = gspread.authorize(creds)
        spreadsheet_url = get_spreadsheet_url()

        if not spreadsheet_url:
            print("❌ Spreadsheet URL not found in config!")
            return

        # Open spreadsheet and get Users worksheet
        sh = gc.open_by_url(spreadsheet_url)
        try:
            worksheet = sh.worksheet("Users")
        except gspread.exceptions.WorksheetNotFound:
            print("❌ Users worksheet not found in spreadsheet!")
            return

        # Get all user data
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        if df.empty:
            print("❌ No users found in the Users worksheet!")
            return

        print(f"📊 Found {len(df)} users in the database")
        print("\n🔍 Checking password formats...")

        # Check which passwords need migration
        passwords_to_migrate = []
        for idx, row in df.iterrows():
            username = row.get('username', '')
            password = str(row.get('password', '')).strip()

            if not password:
                print(f"⚠️  User '{username}' has no password!")
                continue

            # Check if password is already hashed (bcrypt hashes start with $2b$)
            if password.startswith('$2b$') or password.startswith('$2a$'):
                print(f"✅ User '{username}' already has hashed password")
            else:
                passwords_to_migrate.append((idx, username, password))

        if not passwords_to_migrate:
            print("\n🎉 All passwords are already properly hashed!")
            return

        print(f"\n🔄 Found {len(passwords_to_migrate)} passwords to migrate:")
        for _, username, _ in passwords_to_migrate:
            print(f"   - {username}")

        # Ask for confirmation
        print("\n⚠️  This will permanently hash the passwords!")
        print("   Make sure you have backups and inform users to use password reset if needed.")

        response = input("\nDo you want to proceed? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Migration cancelled.")
            return

        # Perform migration
        print("\n🔄 Migrating passwords...")

        updated_count = 0
        for idx, username, plain_password in passwords_to_migrate:
            try:
                hashed_password = hash_password(plain_password)

                # Update the worksheet (note: gspread uses 1-based indexing)
                worksheet.update_cell(idx + 2, df.columns.get_loc('password') + 1, hashed_password)

                print(f"✅ Migrated password for user '{username}'")
                updated_count += 1

            except Exception as e:
                print(f"❌ Failed to migrate password for user '{username}': {e}")

        print(f"\n🎉 Migration complete! Updated {updated_count} passwords.")

        print("\n📝 Next steps:")
        print("   1. Test login with existing credentials")
        print("   2. If login fails, users may need to reset passwords")
        print("   3. Consider implementing password reset functionality")

    except ImportError as e:
        print(f"❌ Missing required packages: {e}")
        print("   Install with: pip install gspread google-auth pandas passlib")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_passwords()