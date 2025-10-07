# PharmGPT Deployment Guide

This guide covers deploying the PharmGPT application with a React frontend on Netlify and FastAPI backend on Render.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Netlify       │    │     Render      │    │   Supabase      │
│   (Frontend)    │───▶│   (Backend)     │───▶│   (Database)    │
│   React App     │    │   FastAPI       │    │   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

- GitHub account
- Netlify account
- Render account
- Supabase account
- Mistral AI API key

## Database Setup (Supabase)

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and anon key

### 2. Run Database Migrations

1. Go to SQL Editor in Supabase dashboard
2. Run the migration files in order:
   ```sql
   -- Copy and run backend/migrations/001_add_users_and_support.sql
   -- Copy and run backend/migrations/002_create_admin_user.sql
   ```

### 3. Update Admin User

After running migrations, update the admin user password:

```sql
UPDATE users 
SET password_hash = '$2b$12$your_hashed_password_here'
WHERE email = 'admin@pharmgpt.com';
```

## Backend Deployment (Render)

### 1. Prepare Repository

1. Push your code to GitHub
2. Ensure `backend/` directory contains:
   - `main.py`
   - `requirements.txt`
   - `render.yaml`
   - All application code

### 2. Create Render Service

1. Go to [render.com](https://render.com)
2. Connect your GitHub account
3. Create new "Web Service"
4. Select your repository
5. Configure:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`

### 3. Set Environment Variables

In Render dashboard, add these environment variables:

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SECRET_KEY=your_jwt_secret_key_32_chars_minimum
MISTRAL_API_KEY=your_mistral_api_key
ADMIN_EMAIL=admin@pharmgpt.com
ADMIN_PASSWORD=your_secure_admin_password
DEBUG=false
PORT=8000
ALLOWED_ORIGINS=https://your-netlify-app.netlify.app,http://localhost:3000
```

### 4. Deploy

1. Click "Create Web Service"
2. Wait for deployment to complete
3. Note your Render app URL (e.g., `https://pharmgpt-backend.onrender.com`)

### 5. Test Backend

Visit `https://your-render-app.onrender.com/docs` to verify API is working.

## Frontend Deployment (Netlify)

### 1. Prepare Repository

Ensure `frontend/` directory contains:
- `package.json`
- `netlify.toml`
- All React application code

### 2. Create Netlify Site

1. Go to [netlify.com](https://netlify.com)
2. Connect your GitHub account
3. Click "New site from Git"
4. Select your repository
5. Configure:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`

### 3. Set Environment Variables

In Netlify dashboard, go to Site settings > Environment variables:

```
VITE_API_URL=https://your-render-app.onrender.com/api/v1
VITE_APP_NAME=PharmGPT
VITE_APP_VERSION=2.0.0
```

### 4. Deploy

1. Click "Deploy site"
2. Wait for build to complete
3. Note your Netlify app URL (e.g., `https://pharmgpt.netlify.app`)

### 5. Update Backend CORS

Update your backend's `ALLOWED_ORIGINS` environment variable to include your Netlify URL:

```
ALLOWED_ORIGINS=https://your-netlify-app.netlify.app,http://localhost:3000
```

## Post-Deployment Setup

### 1. Create Admin User

If the migration didn't create the admin user properly:

1. Register a new user through the frontend
2. In Supabase, update that user to be admin:
   ```sql
   UPDATE users 
   SET is_admin = true 
   WHERE email = 'your-admin-email@example.com';
   ```

### 2. Test Complete Flow

1. Visit your Netlify app
2. Register a new user account
3. Login and test chat functionality
4. Login as admin and test admin panel
5. Test document upload
6. Test support form

### 3. Configure Custom Domain (Optional)

#### Netlify:
1. Go to Site settings > Domain management
2. Add custom domain
3. Configure DNS records

#### Render:
1. Go to Settings > Custom Domains
2. Add your API domain
3. Configure DNS records

## Environment-Specific Configurations

### Production
```bash
# Backend
DEBUG=false
ALLOWED_ORIGINS=https://pharmgpt.com,https://www.pharmgpt.com

# Frontend
VITE_API_URL=https://api.pharmgpt.com/api/v1
```

### Staging
```bash
# Backend
DEBUG=true
ALLOWED_ORIGINS=https://staging-pharmgpt.netlify.app

# Frontend
VITE_API_URL=https://staging-pharmgpt-api.onrender.com/api/v1
```

## Monitoring and Maintenance

### Health Checks

- Backend: `https://your-render-app.onrender.com/health`
- Frontend: Monitor through Netlify dashboard

### Logs

- **Render**: View logs in Render dashboard
- **Netlify**: View build and function logs in Netlify dashboard
- **Supabase**: Monitor database performance in Supabase dashboard

### Backups

1. **Database**: Supabase provides automatic backups
2. **Code**: Ensure regular Git commits
3. **Environment Variables**: Document all environment variables

## Troubleshooting

### Common Issues

#### Backend Won't Start
- Check environment variables are set correctly
- Verify Supabase connection
- Check Render logs for errors

#### Frontend Build Fails
- Verify Node.js version (18+)
- Check for TypeScript errors
- Ensure all dependencies are installed

#### CORS Errors
- Verify `ALLOWED_ORIGINS` includes your Netlify URL
- Check that URLs don't have trailing slashes
- Ensure HTTPS is used in production

#### Database Connection Issues
- Verify Supabase URL and key
- Check if database migrations ran successfully
- Ensure database is not paused (free tier)

#### Authentication Issues
- Verify JWT secret key is set
- Check token expiration settings
- Ensure admin user exists and has correct permissions

### Getting Help

1. Check application logs
2. Verify all environment variables
3. Test API endpoints directly
4. Check database connectivity
5. Contact support if issues persist

## Security Considerations

### Production Checklist

- [ ] Use strong JWT secret key (32+ characters)
- [ ] Set secure admin password
- [ ] Enable HTTPS only
- [ ] Configure proper CORS origins
- [ ] Set up rate limiting (recommended)
- [ ] Enable database row-level security
- [ ] Regular security updates
- [ ] Monitor for suspicious activity

### API Keys

- Store all API keys as environment variables
- Never commit API keys to version control
- Rotate keys regularly
- Use different keys for different environments

## Scaling Considerations

### Backend Scaling
- Render auto-scales based on traffic
- Consider upgrading to higher tier for better performance
- Implement caching for frequently accessed data

### Frontend Scaling
- Netlify CDN handles global distribution
- Optimize images and assets
- Implement code splitting for large applications

### Database Scaling
- Monitor Supabase usage and upgrade plan as needed
- Optimize queries and add indexes
- Consider read replicas for high-traffic applications

## Cost Optimization

### Free Tier Limits
- **Render**: 750 hours/month (free tier)
- **Netlify**: 100GB bandwidth/month (free tier)
- **Supabase**: 500MB database, 2GB bandwidth (free tier)

### Optimization Tips
- Use efficient queries to reduce database load
- Optimize images and assets
- Implement proper caching strategies
- Monitor usage and upgrade plans as needed