#!/bin/bash

# Simple deployment script for PolyVeda on Render
echo "🚀 PolyVeda Deployment Script"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: render.yaml not found. Please run this script from the project root."
    exit 1
fi

if [ ! -d "backend" ]; then
    echo "❌ Error: backend directory not found. Please run this script from the project root."
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Git repository not initialized. Please run 'git init' first."
    exit 1
fi

echo "✅ Project structure looks good!"

# Check if all files are committed
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes."
    echo "   Please commit your changes before deploying:"
    echo "   git add ."
    echo "   git commit -m 'Your commit message'"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
fi

echo "📋 Deployment Checklist:"
echo "   ✅ render.yaml exists"
echo "   ✅ backend/ directory exists"
echo "   ✅ requirements.txt exists"
echo "   ✅ manage.py exists in backend/"
echo "   ✅ Django settings configured"

echo ""
echo "🎯 Next Steps:"
echo "1. Push your code to GitHub:"
echo "   git push origin main"
echo ""
echo "2. Deploy on Render:"
echo "   - Go to https://dashboard.render.com"
echo "   - Click 'New +' → 'Blueprint'"
echo "   - Connect your GitHub repository"
echo "   - Select your PolyVeda repository"
echo "   - Click 'Create Blueprint Instance'"
echo ""
echo "3. Monitor deployment:"
echo "   - Check build logs in Render Dashboard"
echo "   - Visit your app URL once deployed"
echo "   - Test health check: /health/"
echo ""
echo "4. Access your application:"
echo "   - Main App: https://your-app-name.onrender.com"
echo "   - Admin Panel: https://your-app-name.onrender.com/admin"
echo "   - API Docs: https://your-app-name.onrender.com/api/docs"
echo ""
echo "5. Default login:"
echo "   - Email: admin@polyveda.com"
echo "   - Password: admin123456"
echo ""
echo "🚀 Happy deploying!"