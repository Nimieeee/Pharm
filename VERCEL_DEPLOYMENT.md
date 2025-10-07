# Vercel Deployment Guide

This guide covers deploying the PharmGPT frontend to Vercel.

## Prerequisites

- Vercel account (sign up at https://vercel.com)
- Vercel CLI (optional): `npm i -g vercel`
- Backend API deployed and accessible

## Quick Deploy

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Connect Repository**
   - Go to https://vercel.com/new
   - Import your Git repository
   - Select the `frontend` directory as the root directory

2. **Configure Project**
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

3. **Set Environment Variables**
   
   Add these in the Vercel dashboard under Settings → Environment Variables:
   
   **Production:**
   ```
   VITE_API_URL=https://pharmgpt-backend.onrender.com/api/v1
   VITE_APP_NAME=PharmGPT
   VITE_APP_VERSION=2.0.0
   VITE_ENABLE_ANALYTICS=false
   VITE_ENABLE_DEBUG=false
   ```
   
   **Preview (optional):**
   ```
   VITE_API_URL=https://pharmgpt-backend-staging.onrender.com/api/v1
   VITE_APP_NAME=PharmGPT
   VITE_APP_VERSION=2.0.0
   VITE_ENABLE_ANALYTICS=false
   VITE_ENABLE_DEBUG=true
   ```

4. **Deploy**
   - Click "Deploy"
   - Vercel will automatically build and deploy your application

### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy from Frontend Directory**
   ```bash
   cd frontend
   vercel
   ```

4. **Follow the prompts:**
   - Set up and deploy? Yes
   - Which scope? Select your account/team
   - Link to existing project? No (first time) or Yes (subsequent deploys)
   - What's your project's name? pharmgpt-frontend
   - In which directory is your code located? ./
   - Want to override settings? No (vercel.json will be used)

5. **Set Environment Variables**
   ```bash
   vercel env add VITE_API_URL production
   # Enter: https://pharmgpt-backend.onrender.com/api/v1
   
   vercel env add VITE_APP_NAME production
   # Enter: PharmGPT
   
   vercel env add VITE_APP_VERSION production
   # Enter: 2.0.0
   ```

6. **Deploy to Production**
   ```bash
   vercel --prod
   ```

## Configuration Details

### vercel.json

The `frontend/vercel.json` file configures:
- Build settings (Vite framework)
- SPA routing (all routes → index.html)
- Cache headers for static assets
- Security headers (X-Frame-Options, CSP, etc.)

### Environment Variables

All environment variables must be prefixed with `VITE_` to be accessible in the frontend:

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `https://your-backend.onrender.com/api/v1` |
| `VITE_APP_NAME` | Application name | `PharmGPT` |
| `VITE_APP_VERSION` | Application version | `2.0.0` |
| `VITE_ENABLE_ANALYTICS` | Enable analytics | `false` |
| `VITE_ENABLE_DEBUG` | Enable debug mode | `false` |

## Custom Domain

1. Go to your project in Vercel dashboard
2. Navigate to Settings → Domains
3. Add your custom domain
4. Follow DNS configuration instructions
5. Vercel automatically provisions SSL certificates

## Automatic Deployments

Vercel automatically deploys:
- **Production**: Pushes to `main` branch
- **Preview**: Pull requests and other branches

Configure branch settings in Settings → Git.

## Backend CORS Configuration

Ensure your backend allows requests from your Vercel domain:

```python
# backend/app/core/config.py
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://your-app.vercel.app",
    "https://your-custom-domain.com"
]
```

## Monitoring & Logs

- **Deployment Logs**: Available in Vercel dashboard for each deployment
- **Runtime Logs**: View in Vercel dashboard → Logs
- **Analytics**: Enable Vercel Analytics in Settings → Analytics

## Rollback

To rollback to a previous deployment:
1. Go to Deployments in Vercel dashboard
2. Find the deployment you want to restore
3. Click "..." → "Promote to Production"

## Troubleshooting

### Build Fails

- Check build logs in Vercel dashboard
- Verify all dependencies are in `package.json`
- Ensure Node.js version compatibility (18+)

### Environment Variables Not Working

- Ensure variables are prefixed with `VITE_`
- Redeploy after adding/changing environment variables
- Check variable scope (Production/Preview/Development)

### API Connection Issues

- Verify `VITE_API_URL` is correct
- Check backend CORS configuration
- Ensure backend is accessible from Vercel's network

### 404 on Routes

- Verify `vercel.json` rewrites configuration
- Check that SPA routing is properly configured

## Migration from Netlify

If migrating from Netlify:

1. Deploy to Vercel first (don't delete Netlify yet)
2. Test thoroughly on Vercel preview URL
3. Update DNS to point to Vercel (if using custom domain)
4. Monitor for 24-48 hours
5. Archive or delete Netlify deployment

## Cost Considerations

Vercel Free Tier includes:
- Unlimited deployments
- 100 GB bandwidth/month
- Automatic HTTPS
- Preview deployments

For production apps with higher traffic, consider Vercel Pro.

## Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vite on Vercel](https://vercel.com/docs/frameworks/vite)
- [Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Custom Domains](https://vercel.com/docs/concepts/projects/domains)
