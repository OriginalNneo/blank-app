# API Configuration Guide

## Overview

This document describes the unified API configuration structure for the TGYN Admin Portal. All API credentials and settings have been consolidated into a single `config.json` file for better organization and management.

## Configuration Structure

The `config.json` file contains all application configuration in a structured format:

```json
{
  "apis": {
    "google_sheets": {
      "spreadsheet_url": "YOUR_SPREADSHEET_URL",
      "service_account_file": "tgyn-admin-1452dbad90f6.json"
    },
    "telegram": {
      "token": "YOUR_BOT_TOKEN",
      "group_id": "YOUR_GROUP_ID"
    },
    "gemini": {
      "api_key": "YOUR_GEMINI_API_KEY"
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
    "version": "1.0.0",
    "description": "Teck Ghee Youth Network Administration Portal"
  }
}
```

## Configuration Sections

### APIs Section

#### Google Sheets API
- **Purpose**: Database operations and user authentication
- **File**: `tgyn-admin-1452dbad90f6.json` (Google service account credentials)
- **URL**: Google Sheets spreadsheet URL for data storage

#### Telegram API
- **Purpose**: Send documents and approval polls to Telegram groups
- **Token**: Bot token from @BotFather
- **Group ID**: Telegram group/chat ID for notifications

#### Gemini API
- **Purpose**: AI-powered receipt image analysis
- **API Key**: Google AI Studio API key

### Theme Section

Contains customizable theme settings for the frontend:
- `primaryColor`: Main brand color
- `backgroundColor`: Page background
- `secondaryBackgroundColor`: Card/component backgrounds
- `textColor`: Primary text color
- `accentColor`: Secondary/accent color
- `font`: Font family (Poppins recommended)

### App Section

Application metadata and settings.

## How to Update Configuration

### Method 1: Direct JSON Editing
1. Open `config.json` in a text editor
2. Modify the desired values
3. Save the file
4. Restart backend services for API changes
5. Refresh frontend for theme changes

### Method 2: Environment Variables (Fallback)
The system falls back to environment variables if `config.json` is not found:
- `GOOGLE_SPREADSHEET_URL`
- `TELEGRAM_TOKEN`
- `TELEGRAM_GROUP_ID`
- `GEMINI_API_KEY`

### Method 3: Individual JSON Files (Legacy)
For backward compatibility, the system can still read from individual files:
- `Gemini_api.json`
- `Telegram_api.json`
- `theme_config.json`

## Security Best Practices

- **Never commit** `config.json` to version control
- Use **environment-specific** configuration files
- **Rotate API keys** regularly
- **Restrict service account permissions** to minimum required
- Use **encrypted storage** for production deployments

## File Locations

- **Main Config**: `/config.json` (root directory)
- **Service Account**: `/tgyn-admin-1452dbad90f6.json` (root directory)
- **Frontend Access**: `/frontend/public/config.json` (copied automatically)

## Migration Notes

The configuration system has been completely migrated from the previous Streamlit-based approach:

- ❌ Old: `.streamlit/secrets.toml` + individual JSON files
- ✅ New: Unified `config.json` with automatic loading

The backend includes backward compatibility for existing individual JSON files during the transition period.

## Backend Configuration

The `.env` file in the `backend/` directory now only contains:
- FastAPI server settings
- Google Sheets URL
- Comments indicating where API keys are loaded from

All sensitive API credentials are loaded directly from the JSON files at runtime.