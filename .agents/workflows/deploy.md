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
// turbo
```bash
ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 restart pharmgpt-backend"
```

3. **Verify the service is online**
```bash
ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 status"
```
