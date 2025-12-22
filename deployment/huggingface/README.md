---
title: PharmGPT Backend
emoji: 💊
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# PharmGPT Backend on Hugging Face Spaces

This Space hosts the FastAPI backend for PharmGPT.

## Configuration

To run this backend, you must configure the following Secrets in the Settings tab:

### 1. Database (Supabase)
- `SUPABASE_URL`: Your Supabase Project URL
- `SUPABASE_ANON_KEY`: Your Supabase Anonymous Key
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase Service Role Key (Required for RAG)

### 2. AI Models
- `MISTRAL_API_KEY`: Your Mistral AI API Key

### 3. Security
- `JWT_SECRET`: A secure random string for token generation (32+ chars)
- `ADMIN_PASSWORD`: Password for the admin account (optional, defaults to admin123)

### 4. Optional
- `TAVILY_API_KEY`: For web search capabilities
- `SERP_API_KEY`: For Google Scholar search
- `GROQ_API_KEY`: For faster inference (optional)

## Connecting Frontend

Your frontend should point to the direct URL of this Space:
`https://huggingface.co/spaces/YOUR_USERNAME/pharmgpt-backend`
(Usually formatted as `https://YOUR_USERNAME-pharmgpt-backend.hf.space/api/v1`)
