# Deploying to Hugging Face Spaces

This guide explains how to deploy your PharmGPT backend to Hugging Face Spaces using the free Docker tier (16GB RAM).

## 1. Prepare Your Files

The essential files have been prepared in `deployment/huggingface/`.

You need to upload these files to your Hugging Face Space along with your source code.

## 2. Directory Structure

Hugging Face expects the `Dockerfile` to be at the **root** of your Space's repository.

Since your project has a `backend/` folder, you cannot simply connect your Git repo directly unless you restructure it.

**Recommended Method: Manual Upload (Easiest)**

1.  Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces).
    *   **Name:** `pharmgpt-backend`
    *   **SDK:** `Docker`
    *   **Visibility:** `Public` (needed for free tier access)

2.  Clone the Space to your computer locally:
    ```bash
    git clone https://huggingface.co/spaces/YOUR_USERNAME/pharmgpt-backend
    cd pharmgpt-backend
    ```

3.  Copy the following files/folders from your project into this new folder:
    *   Copy `deployment/huggingface/Dockerfile` -> to root `Dockerfile`
    *   Copy `deployment/huggingface/README.md` -> to root `README.md`
    *   Copy `backend/requirements.txt` -> to root `requirements.txt`
    *   Copy `backend/main.py` -> to root `main.py`
    *   Copy `backend/app` folder -> to root `app/`

    *Configuration Check:*
    Your folder should look like this:
    ```
    pharmgpt-backend/
    ├── Dockerfile
    ├── README.md
    ├── requirements.txt
    ├── main.py
    └── app/
        ├── __init__.py
        ├── api/
        ├── core/
        └── ...
    ```

4.  Push the files to Hugging Face:
    ```bash
    git add .
    git commit -m "Initial deploy"
    git push
    ```

## 3. Configure Secrets

Go to your Space's **Settings** tab -> **Variables and secrets**.

Add these **Repository secrets**:

| Name | Description |
|------|-------------|
| `SUPABASE_URL` | From your Supabase Dashboard |
| `SUPABASE_ANON_KEY` | From your Supabase Dashboard |
| `SUPABASE_SERVICE_ROLE_KEY` | From your Supabase Dashboard |
| `MISTRAL_API_KEY` | From Mistral AI Console |
| `JWT_SECRET` | Generate one: `openssl rand -hex 32` |

## 4. Keep It Alive (Anti-Sleep)

Free Spaces sleep after 48 hours.

1.  Use **UptimeRobot** (free).
2.  Create a new HTTP(s) Monitor.
3.  URL: `https://YOUR_USERNAME-pharmgpt-backend.hf.space/health`
4.  Interval: 5 minutes.

This keeps your backend active permanently for free.
