# Streamlit Secrets Setup Guide

## Overview
The authentication system uses Streamlit's built-in secrets management instead of environment variables. This is more secure and integrates better with Streamlit Cloud deployments.

## Local Development Setup

### 1. Create Secrets Directory
```bash
mkdir -p .streamlit
```

### 2. Create Secrets File
```bash
cp secrets.toml.example .streamlit/secrets.toml
```

### 3. Configure Your Secrets
Edit `.streamlit/secrets.toml` with your actual Supabase credentials:

```toml
# Supabase Configuration
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your_anon_key_here"
SUPABASE_SERVICE_KEY = "your_service_key_here"

# Groq API Configuration (for later tasks)
GROQ_API_KEY = "your_groq_api_key"
GROQ_FAST_MODEL = "gemma2-9b-it"
GROQ_PREMIUM_MODEL = "qwen/qwen3-32b"
```

### 4. Add to .gitignore
Make sure `.streamlit/secrets.toml` is in your `.gitignore`:
```
.streamlit/secrets.toml
```

## Streamlit Cloud Setup

### 1. Deploy Your App
Push your code to GitHub and connect it to Streamlit Cloud.

### 2. Configure Secrets
1. Go to your app in Streamlit Cloud
2. Click on "Settings" 
3. Go to the "Secrets" tab
4. Paste your secrets in TOML format:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your_anon_key_here"
SUPABASE_SERVICE_KEY = "your_service_key_here"
GROQ_API_KEY = "your_groq_api_key"
GROQ_FAST_MODEL = "gemma2-9b-it"
GROQ_PREMIUM_MODEL = "qwen/qwen3-32b"
```

### 3. Save and Redeploy
Click "Save" and your app will automatically redeploy with the new secrets.

## Getting Supabase Credentials

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Sign up/in and create a new project
3. Wait for the project to be set up

### 2. Get Your Credentials
1. Go to Settings → API
2. Copy your Project URL (SUPABASE_URL)
3. Copy your anon/public key (SUPABASE_ANON_KEY)
4. Copy your service_role key (SUPABASE_SERVICE_KEY)

### 3. Enable Authentication
1. Go to Authentication → Settings
2. Configure your authentication providers
3. Set up email confirmation if needed

## Testing Your Setup

Run the structure test to verify everything is working:
```bash
python test_auth_mock.py
```

Then test the actual app:
```bash
streamlit run auth_app.py
```

## Security Notes

- Never commit secrets to version control
- Use different credentials for development and production
- Regularly rotate your API keys
- The service key has admin privileges - handle with care

## Troubleshooting

### "No secrets found" Error
- Make sure `.streamlit/secrets.toml` exists in your project root
- Check that the file has the correct TOML format
- Verify file permissions allow reading

### "KeyError" for Missing Secrets
- Check that all required secrets are defined in your secrets.toml
- Verify the secret names match exactly (case-sensitive)
- Make sure there are no typos in the secret keys

### Supabase Connection Errors
- Verify your SUPABASE_URL is correct and includes https://
- Check that your SUPABASE_ANON_KEY is valid
- Ensure your Supabase project is active and not paused