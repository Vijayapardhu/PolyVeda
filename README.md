# PolyVeda - Unified Academic Hub

A comprehensive academic management system for polytechnic institutions, providing centralized access to courses, attendance, assessments, resources, and administrative workflows.

## 🎯 Vision

PolyVeda solves scattered information, manual workflows, and poor visibility into academic progress by centralizing authentication, courses, attendance, assessments, resources, notices, forms, and analytics in one responsive web application.

## 🚀 Features

### Core Modules
- **Authentication & Onboarding** - Secure login with role-based access control
- **Profile & KYC** - Student and faculty profile management
- **Academics** - Courses, timetables, attendance tracking, assessments
- **Learning Resources** - Notes, PPTs, lab manuals with versioning
- **Announcements & Events** - Department notices with push notifications
- **Assignments & Submissions** - File uploads with plagiarism detection
- **Requests & Forms** - Bonafide certificates, leave requests, grievances
- **Hall Ticket & Results** - PDF generation with QR codes
- **Support & Helpdesk** - Ticketing system with SLA tracking
- **Analytics & Dashboards** - Role-based insights and reports

## 🛠 Tech Stack

- **Frontend**: HTML + Tailwind CSS + Vanilla JS/Alpine.js
- **Backend**: Django + Django REST Framework
- **Database**: PostgreSQL
- **Cache**: Redis
- **Storage**: Object storage (S3-compatible)
- **Email**: SendGrid/Gmail SMTP
- **Deployment**: Docker + Render/Fly.io

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (for frontend assets)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd polyveda
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your database and email settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### 3. Frontend Setup

```bash
# Install Tailwind CSS
npm install

# Build CSS
npm run build:css

# Watch for changes (development)
npm run watch:css
```

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb polyveda_dev

# Run migrations
python manage.py migrate

# Load initial data (optional)
python manage.py loaddata initial_data
```

## 📁 Project Structure

```
polyveda/
├── backend/                 # Django application
│   ├── polyveda/           # Main project settings
│   ├── accounts/           # Authentication & user management
│   ├── academics/          # Courses, attendance, assessments
│   ├── resources/          # Learning materials
│   ├── announcements/      # Notices and events
│   ├── forms/             # Requests and certificates
│   ├── support/           # Helpdesk and tickets
│   └── analytics/         # Dashboards and reports
├── frontend/              # Static files and templates
│   ├── static/           # CSS, JS, images
│   ├── templates/        # HTML templates
│   └── components/       # Reusable UI components
├── docs/                 # Documentation
├── tests/               # Test suites
└── deployment/          # Docker and deployment configs
```

## 🔐 Environment Variables

Create a `.env` file with the following variables:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/polyveda_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Storage
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=your-region
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test academics

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚀 Deployment

### Development
```bash
python manage.py runserver
```

### Production
```bash
# Build Docker image
docker build -t polyveda .

# Run with Docker Compose
docker-compose up -d
```

## 📊 Success Metrics

- Reduce manual work by ≥60%
- Increase student engagement (DAU/MAU ≥ 35%)
- Page load speed < 2s on 4G
- API response time p95 < 400ms
- 99.5% monthly uptime
- Zero broken data flows in nightly checks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Email: support@polyveda.edu
- Documentation: [docs.polyveda.edu](https://docs.polyveda.edu)