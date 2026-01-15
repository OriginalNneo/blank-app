import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
from typing import Optional, Dict, Any
from app.utils.config import get_google_sheets_url, get_google_service_account_file
import os

class GoogleSheetsDB:
    def __init__(self):
        self.gc = None
        self.spreadsheet = None
        self.initialized = False
        self.error_message = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize Google Sheets connection"""
        try:
            # Get path to the Google service account JSON file
            # Try multiple possible locations
            possible_paths = [
                "/Users/nathanielneo/Desktop/Projects/TGYN_Admin/tgyn-admin-1452dbad90f6.json",  # Absolute path (updated)
                "/Users/nathanielneo/Desktop/TGYN_Admin/tgyn-admin-1452dbad90f6.json",  # Legacy path
                "./tgyn-admin-1452dbad90f6.json",  # Relative to current directory
                "../tgyn-admin-1452dbad90f6.json",  # Relative to backend directory
                "../../tgyn-admin-1452dbad90f6.json",  # From backend/app/services
            ]

            creds_file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    creds_file_path = path
                    print(f"Found Google service account file at: {path}")
                    break

            if not creds_file_path:
                error_msg = f"Google service account JSON file not found. Searched in: {', '.join(possible_paths)}"
                print(f"ERROR: {error_msg}")
                self.error_message = error_msg
                return

            # Load credentials from JSON file
            with open(creds_file_path, 'r') as f:
                creds_dict = json.load(f)

            creds = Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )

            self.gc = gspread.authorize(creds)
            print("Google Sheets client authorized successfully")

            # Get spreadsheet URL from configuration
            spreadsheet_url = get_google_sheets_url()
            if not spreadsheet_url:
                error_msg = "Google Sheets URL not configured. Please set it in config.json or GOOGLE_SPREADSHEET_URL environment variable."
                print(f"ERROR: {error_msg}")
                self.error_message = error_msg
                return

            self.spreadsheet = self.gc.open_by_url(spreadsheet_url)
            self.initialized = True
            print(f"Google Sheets connection established successfully. Spreadsheet: {self.spreadsheet.title}")

        except Exception as e:
            error_msg = f"Failed to initialize Google Sheets connection: {e}"
            print(f"ERROR: {error_msg}")
            self.error_message = error_msg
            import traceback
            traceback.print_exc()

    def get_users_df(self) -> pd.DataFrame:
        """Get users data from Google Sheets"""
        if not self.initialized:
            print("Warning: Cannot get users data - Google Sheets not initialized")
            return pd.DataFrame()
        try:
            worksheet = self.spreadsheet.worksheet("Users")
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error getting users data: {e}")
            return pd.DataFrame()

    def get_worksheet_data(self, worksheet_name: str) -> pd.DataFrame:
        """Get data from a specific worksheet"""
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error getting {worksheet_name} data: {e}")
            return pd.DataFrame()

    def save_worksheet_data(self, worksheet_name: str, df: pd.DataFrame) -> bool:
        """Save DataFrame to a specific worksheet"""
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            # Clear existing data
            worksheet.clear()
            # Convert DataFrame to list of lists
            data = [df.columns.tolist()] + df.values.tolist()
            worksheet.update(data)
            return True
        except Exception as e:
            print(f"Error saving {worksheet_name} data: {e}")
            return False

    def create_worksheet_if_not_exists(self, worksheet_name: str, headers: list) -> bool:
        """Create worksheet if it doesn't exist"""
        try:
            # Check if worksheet exists
            try:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                # Create new worksheet
                worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=26)
                # Add headers
                worksheet.update([headers])
            return True
        except Exception as e:
            print(f"Error creating worksheet {worksheet_name}: {e}")
            return False

# Global database instance
db = GoogleSheetsDB()

async def init_db():
    """Initialize database connection"""
    global db
    try:
        if not db.initialized:
            print("=" * 60)
            print("WARNING: Google Sheets connection not initialized!")
            if db.error_message:
                print(f"Error: {db.error_message}")
            print("\nTo fix this, ensure you have:")
            print("1. Google service account JSON file: tgyn-admin-1452dbad90f6.json")
            print("2. config.json with 'apis.google_sheets.spreadsheet_url' configured")
            print("   OR set GOOGLE_SPREADSHEET_URL environment variable")
            print("=" * 60)
            return

        # Test connection by getting users
        users_df = db.get_users_df()
        print(f"Database initialized. Found {len(users_df)} users.")

        # Create necessary worksheets if they don't exist
        db.create_worksheet_if_not_exists("Users", ["username", "password", "role", "email"])
        db.create_worksheet_if_not_exists("Events", ["id", "name", "date", "type", "created_by", "created_at"])
        db.create_worksheet_if_not_exists("Budgets", ["event_id", "income_data", "expense_data", "created_at"])
        db.create_worksheet_if_not_exists("SOAs", ["event_id", "income_data", "expense_data", "receipts", "created_at"])
        print("Required worksheets verified/created successfully.")

    except Exception as e:
        print(f"Failed to initialize database: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise - allow server to start even if DB init fails

def get_db() -> GoogleSheetsDB:
    """Dependency to get database instance"""
    return db