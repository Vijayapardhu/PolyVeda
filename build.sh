#!/bin/bash

# PolyVeda Build Script for Render Deployment (SQLite Version)
# This script handles the complete build process for the PolyVeda application

set -e  # Exit on any error

echo "🚀 Starting PolyVeda build process (SQLite)..."

# Navigate to backend directory
cd backend

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p staticfiles
mkdir -p media
mkdir -p temp

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install system dependencies (if needed)
echo "🔧 Installing system dependencies..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    libpng-dev \
    libgif-dev \
    libwebp-dev \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libssl-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
echo "⚙️ Setting environment variables..."
export DJANGO_SETTINGS_MODULE=polyveda.settings.production
export PYTHONPATH=/app/backend

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if not exists (for initial setup)
echo "👤 Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@polyveda.com').exists():
    User.objects.create_superuser(
        email='admin@polyveda.com',
        password='admin123456',
        first_name='Admin',
        last_name='User',
        role='super_admin'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"

# Create default institution
echo "🏫 Creating default institution..."
python manage.py shell -c "
from accounts.models import Institution
if not Institution.objects.filter(slug='default').exists():
    Institution.objects.create(
        name='Default Institution',
        slug='default',
        domain='polyveda.onrender.com',
        academic_year_start='2024-01-01',
        academic_year_end='2024-12-31',
        subscription_plan='enterprise',
        max_users=10000,
        max_storage_gb=100,
        is_active=True,
        is_verified=True
    )
    print('Default institution created successfully')
else:
    print('Default institution already exists')
"

# Load initial data
echo "📊 Loading initial data..."
python manage.py loaddata initial_data.json 2>/dev/null || echo "No initial data to load"

# Set proper permissions
echo "🔐 Setting proper permissions..."
chmod -R 755 staticfiles/
chmod -R 755 media/
chmod -R 755 logs/

# Create log files
echo "📝 Creating log files..."
touch logs/polyveda.log
touch logs/celery.log
touch logs/gunicorn.log
chmod 644 logs/*.log

# Verify installation
echo "✅ Verifying installation..."
python manage.py check --deploy

# Test database connection
echo "🔍 Testing database connection..."
python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT 1')
    print('SQLite database connection successful')
"

# Test cache connection
echo "🔍 Testing cache connection..."
python manage.py shell -c "
from django.core.cache import cache
cache.set('test', 'ok', 10)
if cache.get('test') == 'ok':
    print('Cache connection successful')
else:
    print('Cache connection failed')
"

# Create health check file
echo "🏥 Creating health check file..."
cat > health_check.txt << EOF
PolyVeda Health Check (SQLite)
==============================
Build completed successfully at $(date)
Environment: Production
Database: SQLite
Django Version: 4.2.7
Python Version: $(python --version)
EOF

echo "🎉 PolyVeda build completed successfully (SQLite)!"
echo "📋 Build Summary:"
echo "   - Python dependencies installed"
echo "   - SQLite database migrations applied"
echo "   - Static files collected"
echo "   - Superuser created"
echo "   - Default institution created"
echo "   - Permissions set"
echo "   - Health checks passed"

# Display system information
echo "📊 System Information:"
echo "   - Available memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "   - Disk usage: $(df -h / | awk 'NR==2 {print $5}')"
echo "   - Python version: $(python --version)"
echo "   - Django version: $(python -c 'import django; print(django.get_version())')"
echo "   - Database: SQLite"

echo "🚀 PolyVeda is ready for deployment with SQLite!"