# GitHub Setup Instructions

The PharmGPT Next.js project is ready to be pushed to GitHub. Follow these steps:

## Prerequisites
- GitHub account (create at https://github.com if needed)
- Git installed on your machine
- SSH key or personal access token configured

## Step 1: Create a New Repository on GitHub

1. Go to https://github.com/new
2. Enter repository name: `pharmgpt-nextjs`
3. Add description: "PharmGPT - AI-Powered Pharmaceutical Intelligence (Next.js)"
4. Choose visibility: Public or Private
5. Do NOT initialize with README (we already have one)
6. Click "Create repository"

## Step 2: Add Remote and Push

Copy the repository URL from GitHub (either HTTPS or SSH), then run:

### Using HTTPS (easier for first-time setup):
```bash
cd nextjs-pharmgpt
git remote add origin https://github.com/YOUR_USERNAME/pharmgpt-nextjs.git
git branch -M main
git push -u origin main
```

### Using SSH (if you have SSH keys configured):
```bash
cd nextjs-pharmgpt
git remote add origin git@github.com:YOUR_USERNAME/pharmgpt-nextjs.git
git branch -M main
git push -u origin main
```

## Step 3: Verify

Visit `https://github.com/YOUR_USERNAME/pharmgpt-nextjs` to confirm the push was successful.

## Step 4: Add Collaborators (Optional)

1. Go to repository Settings
2. Click "Collaborators" (left sidebar)
3. Click "Add people"
4. Enter GitHub usernames to invite

## Useful Git Commands

### Check remote configuration
```bash
git remote -v
```

### View commit history
```bash
git log --oneline
```

### Create a new branch for features
```bash
git checkout -b feature/your-feature-name
git push -u origin feature/your-feature-name
```

### Pull latest changes
```bash
git pull origin main
```

## GitHub Actions (Optional)

Create `.github/workflows/deploy.yml` for automatic deployment:

```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: vercel/action@master
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

## Troubleshooting

### "fatal: remote origin already exists"
```bash
git remote remove origin
# Then add the correct remote
```

### "Permission denied (publickey)"
- Check SSH key is added to GitHub: https://github.com/settings/keys
- Or use HTTPS instead of SSH

### "fatal: 'origin' does not appear to be a 'git' repository"
```bash
git remote add origin <your-repo-url>
```

## Next Steps

1. ✅ Repository created and pushed
2. ⏳ Add GitHub Actions for CI/CD
3. ⏳ Set up branch protection rules
4. ⏳ Add issue templates
5. ⏳ Create pull request template

## Resources

- [GitHub Docs](https://docs.github.com)
- [Git Basics](https://git-scm.com/book/en/v2)
- [GitHub CLI](https://cli.github.com)
