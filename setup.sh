#!/bin/bash

# PolyVeda Setup Script
# This script sets up the PolyVeda project for development

set -e

echo "🚀 Setting up PolyVeda - Unified Academic Hub"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_warning "This script is optimized for Linux. Some features may not work on other operating systems."
fi

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    print_success "Python $python_version is compatible"
else
    print_error "Python 3.11 or higher is required. Current version: $python_version"
    exit 1
fi

# Check Node.js version
print_status "Checking Node.js version..."
if command -v node &> /dev/null; then
    node_version=$(node --version | cut -d'v' -f2)
    required_node_version="18.0.0"
    
    if [ "$(printf '%s\n' "$required_node_version" "$node_version" | sort -V | head -n1)" = "$required_node_version" ]; then
        print_success "Node.js $node_version is compatible"
    else
        print_warning "Node.js 18.0.0 or higher is recommended. Current version: $node_version"
    fi
else
    print_warning "Node.js not found. Installing Node.js 18.x..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Create virtual environment
print_status "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt
print_success "Python dependencies installed"

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install
print_success "Node.js dependencies installed"

# Build frontend assets
print_status "Building frontend assets..."
npm run build:css
print_success "Frontend assets built"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p media staticfiles logs
print_success "Directories created"

# Copy environment file
if [ ! -f ".env" ]; then
    print_status "Creating environment file..."
    cp .env.example .env
    print_warning "Please edit .env file with your configuration"
else
    print_warning "Environment file already exists"
fi

# Check if PostgreSQL is installed
print_status "Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    print_success "PostgreSQL is installed"
else
    print_warning "PostgreSQL not found. Please install PostgreSQL 14+"
    print_status "You can install it with: sudo apt-get install postgresql postgresql-contrib"
fi

# Check if Redis is installed
print_status "Checking Redis..."
if command -v redis-server &> /dev/null; then
    print_success "Redis is installed"
else
    print_warning "Redis not found. Please install Redis 6+"
    print_status "You can install it with: sudo apt-get install redis-server"
fi

# Create database (if PostgreSQL is available)
if command -v psql &> /dev/null; then
    print_status "Setting up database..."
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw polyveda_dev; then
        print_warning "Database 'polyveda_dev' already exists"
    else
        sudo -u postgres createdb polyveda_dev
        print_success "Database 'polyveda_dev' created"
    fi
fi

# Run Django migrations
print_status "Running Django migrations..."
cd backend
python manage.py makemigrations
python manage.py migrate
cd ..
print_success "Database migrations completed"

# Create superuser
print_status "Creating superuser..."
echo "Please create a superuser account:"
cd backend
python manage.py createsuperuser
cd ..
print_success "Superuser created"

# Set up development data (optional)
read -p "Do you want to load sample data for development? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Loading sample data..."
    cd backend
    python manage.py loaddata sample_data
    cd ..
    print_success "Sample data loaded"
fi

# Set up Git hooks (optional)
read -p "Do you want to set up Git hooks for code quality? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Setting up Git hooks..."
    mkdir -p .git/hooks
    
    # Pre-commit hook
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for code quality

echo "Running pre-commit checks..."

# Check Python code style
cd backend
python -m flake8 . --max-line-length=88 --exclude=__pycache__,migrations
if [ $? -ne 0 ]; then
    echo "Python code style check failed"
    exit 1
fi

# Run tests
python manage.py test --keepdb
if [ $? -ne 0 ]; then
    echo "Tests failed"
    exit 1
fi

echo "Pre-commit checks passed"
EOF
    
    chmod +x .git/hooks/pre-commit
    print_success "Git hooks configured"
fi

# Final setup instructions
echo
echo "🎉 PolyVeda setup completed successfully!"
echo "=========================================="
echo
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start the development server:"
echo "   cd backend && python manage.py runserver"
echo "3. Open http://localhost:8000 in your browser"
echo
echo "For production deployment:"
echo "1. Use Docker Compose: docker-compose up -d"
echo "2. Or follow the deployment guide in docs/DEPLOYMENT.md"
echo
echo "Useful commands:"
echo "- Start development: cd backend && python manage.py runserver"
echo "- Run tests: cd backend && python manage.py test"
echo "- Build CSS: npm run build:css"
echo "- Watch CSS: npm run watch:css"
echo "- Docker development: docker-compose --profile development up"
echo "- Docker production: docker-compose --profile production up"
echo
echo "Documentation:"
echo "- Project structure: docs/PROJECT_STRUCTURE.md"
echo "- API documentation: docs/API_DOCUMENTATION.md"
echo "- Deployment guide: docs/DEPLOYMENT.md"
echo
print_success "Setup completed! Happy coding! 🚀"