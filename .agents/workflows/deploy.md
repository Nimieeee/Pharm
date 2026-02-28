---
description: Deploy the backend to the Lightsail VPS
---

To deploy the backend changes to the VPS, follow these steps:

1. **Sync files using rsync**
// turbo
```bash
rsync -avz -e "ssh -i ~/.ssh/lightsail_key" --exclude 'venv' --exclude '.venv' --exclude '__pycache__' --exclude '.git' --exclude 'node_modules' --exclude '.next' --exclude '.env' backend/ ubuntu@15.237.208.231:/var/www/pharmgpt-backend/backend/
```

2. **Restart the backend service via PM2**
*Note: We use `pharmgpt-api` bound to port 7860 to match the Nginx configuration block.*
// turbo
```bash
ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 restart pharmgpt-api"
```

3. **Verify the service is online**
```bash
ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 logs pharmgpt-api --lines 20 --nostream"
```

4. **Deploy the frontend changes to GitHub (triggers Vercel)**
*Note: Always verify the frontend build locally before pushing to prevent Vercel TypeErrors.*
// turbo
```bash
cd frontend && npm run build && cd .. && git add . && git commit -m "chore(deploy): trigger Vercel deployment" && git push origin master
```
