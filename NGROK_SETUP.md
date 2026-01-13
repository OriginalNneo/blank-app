# Ngrok Setup Guide

This guide explains how to configure the TGYN Admin Portal to work with ngrok for external access.

## Prerequisites

1. Install ngrok: https://ngrok.com/download
2. Sign up for a free ngrok account (optional, but recommended)

## Setup Steps

### 1. Start Your Backend Server

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Create ngrok Tunnel for Backend

In a new terminal:

```bash
ngrok http 8000
```

This will give you a URL like: `https://abc123.ngrok.io`

### 3. Configure Backend CORS

Create a `.env` file in the `backend/` directory:

```bash
cd backend
touch .env
```

Add your frontend ngrok URL to the `.env` file:

```env
ALLOWED_ORIGINS=https://your-frontend-ngrok-url.ngrok.io
```

**Note:** If you're also running the frontend through ngrok, use that URL. If not, you can keep localhost:

```env
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://your-frontend-ngrok-url.ngrok.io
```

### 4. Restart Backend Server

After updating the `.env` file, restart your backend server to apply CORS changes.

### 5. Configure Frontend

Create a `.env.local` file in the `frontend/` directory:

```bash
cd frontend
touch .env.local
```

Add your backend ngrok URL:

```env
NEXT_PUBLIC_API_URL=https://your-backend-ngrok-url.ngrok.io
```

**Example:**
```env
NEXT_PUBLIC_API_URL=https://abc123.ngrok.io
```

### 6. Restart Frontend Server

After updating `.env.local`, restart your Next.js dev server:

```bash
npm run dev
```

## Using Both Frontend and Backend with Ngrok

If you want to expose both frontend and backend:

### Frontend Ngrok (Optional)

In a new terminal:

```bash
cd frontend
npm run dev
# Then in another terminal:
ngrok http 3000
```

This gives you a frontend URL like: `https://xyz789.ngrok.io`

### Update Backend CORS

Update `backend/.env`:

```env
ALLOWED_ORIGINS=https://xyz789.ngrok.io
```

### Update Frontend API URL

Update `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=https://abc123.ngrok.io
```

## Quick Reference

### Backend `.env` file:
```env
PORT=8000
ALLOWED_ORIGINS=https://your-frontend-ngrok-url.ngrok.io
SECRET_KEY=your-secret-key-here
```

### Frontend `.env.local` file:
```env
NEXT_PUBLIC_API_URL=https://your-backend-ngrok-url.ngrok.io
```

## Troubleshooting

### CORS Errors

If you see CORS errors:
1. Make sure your backend `.env` has the correct `ALLOWED_ORIGINS` with your frontend URL
2. Restart the backend server after changing `.env`
3. Check that the ngrok URL matches exactly (including `https://`)

### Connection Refused

If you see connection errors:
1. Verify ngrok is running: Check the ngrok dashboard at http://localhost:4040
2. Make sure the backend is running on port 8000
3. Verify `NEXT_PUBLIC_API_URL` in frontend `.env.local` matches your ngrok URL

### Environment Variables Not Loading

- Frontend: Make sure the file is named `.env.local` (not `.env`)
- Backend: Make sure the file is named `.env` in the `backend/` directory
- Restart both servers after creating/updating `.env` files

## Notes

- Ngrok free tier URLs change each time you restart ngrok (unless you have a paid plan)
- Update your `.env` files whenever you get a new ngrok URL
- For production, consider using a static domain or paid ngrok plan
