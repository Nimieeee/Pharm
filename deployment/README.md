# Self-Hosting Guide (Oracle Cloud / VPS)

This guide explains how to deploy your **Backend + Full Supabase Stack** on a VPS (like Oracle Cloud Free Tier).

## 1. Prerequisites

### Server Requirements
*   **Provider:** Oracle Cloud (Always Free Tier highly recommended)
*   **Instance:** **VM.Standard.A1.Flex** (ARM64)
    *   **OCPUs:** 4
    *   **RAM:** 24 GB (This is plenty; Standard Intel/AMD free tier with 1GB RAM will **NOT** work).
*   **OS:** Ubuntu 22.04 (ARM64 version) or Oracle Linux.

### Local Tools
*   Terminal / SSH Client

## 2. Server Setup

SSH into your new server:
```bash
ssh ubuntu@your-server-ip
```

### Install Docker & Git
```bash
# Update and install basics
sudo apt-get update && sudo apt-get install -y git curl

# Install Docker (Official convenience script)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (avoids sudo usage)
sudo usermod -aG docker $USER
newgrp docker
```

## 3. Clone & Configure

1.  **Clone your repository:**
    ```bash
    git clone https://github.com/yourusername/your-repo.git app
    cd app/deployment
    ```

2.  **Configure Environment:**
    ```bash
    cp .env.example .env
    nano .env
    ```

3.  **Generate Keys (CRITICAL):**
    You need to generate specific keys for Supabase to work.
    
    *   **JWT_SECRET:** Run `openssl rand -hex 32` and paste it into `.env`.
    *   **ANON_KEY & SERVICE_ROLE_KEY:** Go to [Supabase JWT Helper](https://jwt.io/).
        *   Select Algorithm: `HS256`.
        *   **Payload for ANON_KEY:**
            ```json
            {
              "role": "anon",
              "iss": "supabase",
              "iat": 1700000000,
              "exp": 4850000000
            }
            ```
        *   **Payload for SERVICE_ROLE_KEY:**
            ```json
            {
              "role": "service_role",
              "iss": "supabase",
              "iat": 1700000000,
              "exp": 4850000000
            }
            ```
        *   **Verify Signature:** Paste your `JWT_SECRET` (from step 3a) into the secret field.
        *   Copy the resulting Tokens on the left into your `.env` file for `ANON_KEY` and `SERVICE_ROLE_KEY`.

4.  **Set Database Password:**
    Change `POSTGRES_PASSWORD` to something secure.

## 4. Deploy

Run the stack:
```bash
docker compose up -d
```

Check logs:
```bash
docker compose logs -f backend
```

## 5. Accessing Services

*   **Backend API:** `http://your-server-ip:8000`
*   **Supabase Studio (Dashboard):** `http://your-server-ip:3000`
    *   *Note: Open ports 8000 and 3000 in your Oracle Cloud Security List (Ingress Rules).*

## 6. Database Migrations

Since this is a fresh database, it will be empty. You need to run your migrations.

**Option A: Manual SQL Execution (Easiest)**
1.  Open Supabase Studio (`http://your-server-ip:3000`).
2.  Go to the **SQL Editor**.
3.  Copy/Paste the content of your `backend/migrations/*.sql` files and run them.

**Option B: Python Script**
If your backend has a migration script, you can run it inside the container:
```bash
docker compose exec backend python scripts/run_migrations.py
```
