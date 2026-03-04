#!/bin/bash
# VPS Deployment Script for Mermaid Diagram Fixes
# Run this from your local machine to deploy all changes to VPS

set -e

echo "=============================================="
echo "   MERMAID DIAGRAM FIXES - VPS DEPLOYMENT"
echo "=============================================="
echo ""

# Configuration
VPS_USER="ubuntu"
VPS_HOST="15.237.208.231"
VPS_PATH="/var/www/benchside-backend/backend"
SSH_KEY="~/.ssh/lightsail_key"

echo "Step 1: Deploying files to VPS..."
echo ""

# Deploy Python files
rsync -avz -e "ssh -i $SSH_KEY" \
  backend/app/services/mermaid_validator.py \
  $VPS_USER@$VPS_HOST:$VPS_PATH/app/services/

rsync -avz -e "ssh -i $SSH_KEY" \
  backend/tests/test_mermaid_validator.py \
  $VPS_USER@$VPS_HOST:$VPS_PATH/tests/

rsync -avz -e "ssh -i $SSH_KEY" \
  backend/app/services/ai.py \
  $VPS_USER@$VPS_HOST:$VPS_PATH/app/services/

# Deploy frontend file
rsync -avz -e "ssh -i $SSH_KEY" \
  frontend/src/components/chat/MermaidRenderer.tsx \
  $VPS_USER@$VPS_HOST:$VPS_PATH/../frontend/src/components/chat/

echo "✅ Files deployed successfully"
echo ""

echo "Step 2: Running tests on VPS..."
echo ""

# Run tests on VPS
ssh -i $SSH_KEY $VPS_USER@$VPS_HOST << 'EOF'
cd /var/www/benchside-backend/backend
source .venv/bin/activate

echo "Running Mermaid validator tests..."
pytest tests/test_mermaid_validator.py -v --tb=short

TEST_EXIT=$?
if [ $TEST_EXIT -eq 0 ]; then
    echo ""
    echo "✅ All tests passed"
else
    echo ""
    echo "❌ Tests failed with exit code $TEST_EXIT"
    exit 1
fi
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "=============================================="
    echo "   DEPLOYMENT FAILED - TESTS DID NOT PASS"
    echo "=============================================="
    exit 1
fi

echo ""
echo "Step 3: Restarting PM2 service..."
echo ""

ssh -i $SSH_KEY $VPS_USER@$VPS_HOST << 'EOF'
cd /var/www/benchside-backend/backend
pm2 restart benchside-api
sleep 3
pm2 status benchside-api
EOF

echo ""
echo "Step 4: Verifying service health..."
echo ""

ssh -i $SSH_KEY $VPS_USER@$VPS_HOST << 'EOF'
echo "Checking PM2 logs for errors..."
pm2 logs benchside-api --lines 20 --nostream | grep -i "error\|exception" || echo "No errors found in recent logs"

echo ""
echo "Checking service status..."
pm2 status benchside-api | grep -q "online"
if [ $? -eq 0 ]; then
    echo "✅ PM2 service is online and healthy"
else
    echo "❌ PM2 service is NOT online"
    exit 1
fi
EOF

echo ""
echo "=============================================="
echo "   DEPLOYMENT COMPLETE ✅"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Test deep research with a query that generates Mermaid diagrams"
echo "2. Verify diagrams render without errors"
echo "3. Check VPS logs for any Mermaid-related warnings"
echo ""
echo "Example test query:"
echo '  "Create a flowchart showing the mechanism of artemisinin in cancer treatment"'
echo ""
