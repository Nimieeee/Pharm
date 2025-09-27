# 🔑 Mistral API Setup Guide

## Getting Your Mistral API Key

1. **Visit Mistral AI Console**
   - Go to: https://console.mistral.ai/
   - Sign up for an account or log in

2. **Create API Key**
   - Navigate to "API Keys" section
   - Click "Create new key"
   - Give it a name (e.g., "PharmGPT")
   - Copy the generated API key

3. **Set Up API Key**

   ### Option A: Environment Variable (Recommended)
   ```bash
   export MISTRAL_API_KEY="your_actual_api_key_here"
   ```

   ### Option B: Streamlit Secrets
   Create `.streamlit/secrets.toml`:
   ```toml
   MISTRAL_API_KEY = "your_actual_api_key_here"
   ```

   ### Option C: .env File
   Create `.env` file:
   ```
   MISTRAL_API_KEY=your_actual_api_key_here
   ```

## API Key Format

Mistral API keys typically:
- Start with specific prefixes
- Are longer than 30 characters
- Contain alphanumeric characters

## Testing Your Setup

1. Set your API key using one of the methods above
2. Run the app: `streamlit run simple_app.py`
3. Check the sidebar for "✅ Ready for pharmacology queries"
4. Try asking a test question

## Troubleshooting

- **401 Unauthorized**: API key is invalid or missing
- **429 Rate Limited**: You've exceeded your usage limits
- **400 Bad Request**: Message format issue (contact support)

## Pricing

Check current Mistral AI pricing at: https://mistral.ai/technology/#pricing

The app uses `mistral-small-latest` model with up to 10,000 tokens per response.