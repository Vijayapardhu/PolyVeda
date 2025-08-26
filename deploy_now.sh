#!/bin/bash

# Quick deployment script for PolyVeda
echo "🚀 PolyVeda Quick Deployment"
echo "============================"

# Check current status
echo "📋 Current Status:"
echo "   Latest commit: $(git log --oneline -1)"
echo "   Branch: $(git branch --show-current)"
echo "   Remote: $(git remote get-url origin)"

# Force push to ensure latest changes are deployed
echo ""
echo "🔄 Pushing latest changes..."
git push origin cursor/develop-polyveda-academic-hub-project-dfed --force

echo ""
echo "✅ Changes pushed successfully!"
echo ""
echo "🎯 Next Steps:"
echo "1. Go to Render Dashboard: https://dashboard.render.com"
echo "2. Click on your polyveda-web-7ovk service"
echo "3. Click 'Manual Deploy' → 'Deploy latest commit'"
echo "4. Or wait for auto-deploy (if enabled)"
echo ""
echo "🔍 Monitor deployment:"
echo "   - Watch build logs in Render Dashboard"
echo "   - Look for: 'Successfully installed Django...'"
echo "   - Look for: 'Static files collected'"
echo "   - Look for: 'Migrations applied'"
echo ""
echo "🌐 Test your app:"
echo "   - Main: https://polyveda-web-7ovk.onrender.com"
echo "   - Health: https://polyveda-web-7ovk.onrender.com/health/"
echo "   - Admin: https://polyveda-web-7ovk.onrender.com/admin/"
echo ""
echo "🔑 Default login:"
echo "   - Email: admin@polyveda.com"
echo "   - Password: admin123456"
echo ""
echo "🚀 Happy deploying!"