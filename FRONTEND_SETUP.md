# Frontend Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
The `.env` file has been created for you with the deployed backend URL:
```
VITE_API_URL=https://pharmgpt-backend.onrender.com/api/v1
```

### 3. Start Development Server
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### 4. Login
Use your credentials to log in. If you don't have an account:
- Register a new account, or
- Use admin credentials (check with your team)

## Troubleshooting

### "Failed to load conversations" Error

This error occurs when:

1. **Frontend dev server needs restart** - After creating/updating `.env`:
   ```bash
   # Stop the dev server (Ctrl+C)
   npm run dev
   ```

2. **Not logged in** - Clear your browser's local storage and log in again:
   - Open DevTools (F12)
   - Go to Application > Local Storage
   - Clear `pharmgpt_token` and `pharmgpt_refresh_token`
   - Refresh and log in

3. **Backend is down** - Check backend status:
   ```bash
   curl https://pharmgpt-backend.onrender.com/health
   ```
   Should return: `{"status":"healthy",...}`

4. **CORS issue** - The backend should allow your origin. Check backend logs on Render.

### Network Error

If you see "Network error. Please check your connection":

1. **Check backend is running**:
   ```bash
   curl https://pharmgpt-backend.onrender.com/health
   ```

2. **Check your internet connection**

3. **Check browser console** (F12) for detailed error messages

4. **Verify API URL** in `.env` file:
   ```
   VITE_API_URL=https://pharmgpt-backend.onrender.com/api/v1
   ```

### Backend Waking Up (Render Free Tier)

If using Render's free tier, the backend spins down after inactivity:
- First request may take 30-60 seconds
- You'll see "Backend is waking up" message
- Subsequent requests will be fast

## Development Options

### Option 1: Use Deployed Backend (Recommended)
- Already configured in `.env`
- No local backend setup needed
- Shared with team

### Option 2: Run Backend Locally
1. Update `.env`:
   ```
   VITE_API_URL=http://localhost:8000/api/v1
   ```

2. Start backend:
   ```bash
   cd backend
   python main.py
   ```

3. Restart frontend dev server

## Environment Variables

### Required
- `VITE_API_URL` - Backend API URL

### Optional
- `VITE_APP_NAME` - Application name (default: PharmGPT)
- `VITE_APP_VERSION` - Version number
- `VITE_ENABLE_DEBUG` - Enable debug mode (true/false)
- `VITE_ENABLE_ANALYTICS` - Enable analytics (true/false)

## Build for Production

```bash
npm run build
```

Output will be in `dist/` directory.

## Deploy to Netlify

1. Push changes to GitHub
2. Netlify will auto-deploy
3. Set environment variables in Netlify dashboard:
   - `VITE_API_URL=https://pharmgpt-backend.onrender.com/api/v1`

## Common Commands

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Type check
npm run type-check
```
