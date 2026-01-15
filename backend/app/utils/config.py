import json
import os
from typing import Dict, Any, Optional
from decouple import config as decouple_config

class ConfigManager:
    """Centralized configuration manager for the TGYN Admin Portal"""

    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None
        self._load_config()

    def _load_config(self):
        """Load configuration from config.json file"""
        config_paths = [
            "/Users/nathanielneo/Desktop/Projects/TGYN_Admin/config.json",  # Absolute path (updated)
            "/Users/nathanielneo/Desktop/TGYN_Admin/config.json",  # Legacy path
            "./config.json",  # Relative to current directory
            "../config.json",  # Relative to backend directory
            "../../config.json",  # From backend/app/utils
        ]

        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        self._config = json.load(f)
                    print(f"Configuration loaded from: {path}")
                    return
                except Exception as e:
                    print(f"Error loading config from {path}: {e}")
                    continue

        # Fallback to individual JSON files if unified config not found
        print("Unified config.json not found, falling back to individual API files")
        self._config = self._load_individual_configs()

        # Fallback to environment variables if all else fails
        if not self._config:
            print("No configuration files found, using environment variables")
            self._config = self._load_from_env()

    def _load_individual_configs(self) -> Dict[str, Any]:
        """Load configuration from individual JSON files (backward compatibility)"""
        config = {"apis": {}, "theme": {}, "app": {}}

        # Load Google service account
        service_account_paths = [
            "/Users/nathanielneo/Desktop/Projects/TGYN_Admin/tgyn-admin-1452dbad90f6.json",
            "/Users/nathanielneo/Desktop/TGYN_Admin/tgyn-admin-1452dbad90f6.json",
        ]
        for path in service_account_paths:
            try:
                if os.path.exists(path):
                    config["apis"]["google_sheets"] = {"service_account_file": "tgyn-admin-1452dbad90f6.json"}
                    break
            except:
                pass

        # Load Telegram config
        try:
            with open("/Users/nathanielneo/Desktop/TGYN_Admin/Telegram_api.json", 'r') as f:
                config["apis"]["telegram"] = json.load(f)
        except:
            pass

        # Load Gemini config
        try:
            with open("/Users/nathanielneo/Desktop/TGYN_Admin/Gemini_api.json", 'r') as f:
                config["apis"]["gemini"] = json.load(f)
        except:
            pass

        # Load theme config
        try:
            with open("/Users/nathanielneo/Desktop/TGYN_Admin/theme_config.json", 'r') as f:
                theme_data = json.load(f)
                config["theme"] = theme_data.get("theme", {})
        except:
            pass

        return config

    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables (fallback)"""
        return {
            "apis": {
                "telegram": {
                    "token": decouple_config("TELEGRAM_TOKEN", default=""),
                    "group_id": decouple_config("TELEGRAM_GROUP_ID", default="")
                },
                "gemini": {
                    "api_key": decouple_config("GEMINI_API_KEY", default="")
                },
                "google_sheets": {
                    "spreadsheet_url": decouple_config("GOOGLE_SPREADSHEET_URL", default="")
                }
            },
            "theme": {
                "primaryColor": "#00C2FF",
                "backgroundColor": "#F5F7FA",
                "secondaryBackgroundColor": "#FFFFFF",
                "textColor": "#1A202C",
                "accentColor": "#FF6B6B",
                "font": "Poppins"
            },
            "app": {
                "name": "TGYN Admin Portal",
                "version": "1.0.0"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key (e.g., 'apis.telegram.token')"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self._config.get(section, {}) if self._config else {}

    def get_apis(self) -> Dict[str, Any]:
        """Get API configurations"""
        return self.get_section("apis")

    def get_theme(self) -> Dict[str, Any]:
        """Get theme configuration"""
        return self.get_section("theme")

    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration"""
        return self.get_section("app")

# Global configuration instance
config_manager = ConfigManager()

# Convenience functions
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value"""
    return config_manager.get(key, default)

def get_telegram_token() -> str:
    """Get Telegram bot token"""
    return get_config("apis.telegram.token", "")

def get_telegram_group_id() -> str:
    """Get Telegram group ID"""
    return get_config("apis.telegram.group_id", "")

def get_gemini_api_key() -> str:
    """Get Gemini API key"""
    return get_config("apis.gemini.api_key", "")

def get_google_sheets_url() -> str:
    """Get Google Sheets URL"""
    return get_config("apis.google_sheets.spreadsheet_url", "")

def get_google_service_account_file() -> str:
    """Get Google service account file path"""
    filename = get_config("apis.google_sheets.service_account_file", "tgyn-admin-1452dbad90f6.json")
    # Try multiple possible locations
    possible_paths = [
        os.path.join("/Users/nathanielneo/Desktop/Projects/TGYN_Admin", filename),
        os.path.join("/Users/nathanielneo/Desktop/TGYN_Admin", filename),
        filename,  # Current directory
        os.path.join("..", filename),  # Parent directory
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    # Return the first path as default (will be checked by caller)
    return possible_paths[0]

def get_members_sheets_url() -> str:
    """Get Google Sheets URL for members"""
    return get_config("apis.google_sheets.members", "")

def get_attendance_sheets_url() -> str:
    """Get Google Sheets URL for attendance"""
    return get_config("apis.google_sheets.attendance", "")