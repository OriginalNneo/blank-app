# 🎯 TGYN Admin Portal

A professional 3-layer web application for Teck Ghee Youth Network administration, featuring budget planning, statement of accounts generation, and AI-powered receipt processing.

## 🏗️ Architecture

- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python
- **Database**: Google Sheets API
- **AI Processing**: Google Gemini for receipt analysis
- **Notifications**: Telegram Bot integration

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Google Cloud service account with Sheets API access
- Telegram Bot token
- Google Gemini API key

### Installation

1. **Clone and setup backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Setup frontend:**
   ```bash
   cd frontend
   npm install
   ```

3. **Configure APIs:**
   - Edit `config.json` with your API credentials
   - Ensure Google service account JSON file is in the root directory

### Running the Application

1. **Start the backend:**
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## ⚙️ Configuration

All API configurations are centralized in `config.json`:

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
  }
}
```

## 🎨 Customization

### Theme Configuration

Modify colors, fonts, and visual appearance by editing the `theme` section in `config.json`. Changes are applied automatically to the frontend.

### API Configuration

Update API keys and credentials in the `apis` section of `config.json`. The backend automatically reloads configuration changes.

## 📋 Features

- **User Authentication**: JWT-based login with Google Sheets user database
- **Budget Planning**: Create professional Excel budget templates
- **SOA Generation**: Generate Statement of Accounts with variance analysis
- **Receipt Processing**: AI-powered receipt image analysis using Google Gemini
- **Telegram Integration**: Send documents and create approval polls
- **Responsive Design**: Professional UI with customizable themes

## 🔒 Security

- API keys are stored securely in configuration files
- JWT tokens for session management
- CORS protection on API endpoints
- Input validation and sanitization

## 📚 API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the terms specified in the LICENSE file.
