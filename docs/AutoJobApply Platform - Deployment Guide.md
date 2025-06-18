# AutoJobApply Platform - Deployment Guide

## 🚀 Quick Start (Development)

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 14+ (optional for development, uses SQLite by default)

### 1. Backend Setup
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the backend
python src/main.py
# Backend will run on http://localhost:5001
```

### 2. Frontend Setup
```bash
cd frontend
pnpm install
pnpm run dev --host
# Frontend will run on http://localhost:5173
```

### 3. Test the Application
- Visit http://localhost:5173
- Register a new account or use demo credentials:
  - Email: test@example.com
  - Password: TestPassword123

## 🏭 Production Deployment

### Backend Deployment (AWS/Heroku/DigitalOcean)

#### Option 1: AWS ECS with Docker
```dockerfile
# Dockerfile for backend
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
EXPOSE 5001

CMD ["python", "src/main.py"]
```

#### Option 2: Heroku
```bash
# Install Heroku CLI and login
heroku create autojobapply-api
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set JWT_SECRET_KEY=your-jwt-secret
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main
```

#### Option 3: DigitalOcean App Platform
```yaml
# .do/app.yaml
name: autojobapply-backend
services:
- name: api
  source_dir: /backend
  github:
    repo: your-username/autojobapply-platform
    branch: main
  run_command: python src/main.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: FLASK_ENV
    value: production
  - key: SECRET_KEY
    value: your-secret-key
    type: SECRET
databases:
- name: autojobapply-db
  engine: PG
  version: "14"
```

### Frontend Deployment

#### Option 1: Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Set environment variables in Vercel dashboard
VITE_API_URL=https://your-backend-url.com/api
```

#### Option 2: Netlify
```bash
# Build the project
cd frontend
pnpm run build

# Deploy to Netlify
# Upload the dist/ folder to Netlify
# Set environment variables in Netlify dashboard
```

#### Option 3: AWS CloudFront + S3
```bash
# Build the project
cd frontend
pnpm run build

# Upload to S3
aws s3 sync dist/ s3://your-bucket-name --delete

# Configure CloudFront distribution
# Set up custom domain and SSL certificate
```

## 🗄️ Database Setup

### PostgreSQL with PostGIS (Production)
```sql
-- Create database
CREATE DATABASE autojobapply;

-- Enable PostGIS extension for geospatial queries
\c autojobapply;
CREATE EXTENSION postgis;

-- Create user
CREATE USER autojobapply_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE autojobapply TO autojobapply_user;
```

### Database Migration
```bash
# Initialize migrations (first time only)
cd backend
source venv/bin/activate
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

## 🔧 Environment Configuration

### Backend Environment Variables (.env)
```bash
# Application
FLASK_ENV=production
SECRET_KEY=your-super-secret-production-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-production-key-min-32-chars

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# AWS S3 (for resume storage)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=autojobapply-resumes
AWS_S3_REGION=us-east-1

# Redis (for job queue)
REDIS_URL=redis://your-redis-host:6379/0

# Email Service
SENDGRID_API_KEY=your_sendgrid_api_key
MAIL_FROM_EMAIL=noreply@autojobapply.com

# Job Board APIs
INDEED_API_KEY=your_indeed_api_key
MONSTER_API_KEY=your_monster_api_key
GOOGLE_GEOCODING_API_KEY=your_google_api_key
```

### Frontend Environment Variables
```bash
# .env.production
VITE_API_URL=https://your-backend-domain.com/api
VITE_APP_NAME=AutoJobApply
VITE_ENVIRONMENT=production
```

## 🔒 Security Configuration

### SSL/TLS Setup
```nginx
# Nginx configuration
server {
    listen 443 ssl http2;
    server_name api.autojobapply.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Security Headers
```python
# Add to Flask app
from flask_talisman import Talisman

Talisman(app, force_https=True)
```

### Rate Limiting
```python
# Add to Flask app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

## 📊 Monitoring Setup

### Application Monitoring (Sentry)
```python
# Backend monitoring
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

```javascript
// Frontend monitoring
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "your-sentry-dsn",
  environment: "production"
});
```

### Health Check Endpoints
```python
# Already implemented in the backend
GET /api/health
# Returns: {"status": "healthy", "version": "1.0.0"}
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{secrets.HEROKU_API_KEY}}
        heroku_app_name: "autojobapply-api"
        heroku_email: "your-email@example.com"
        appdir: "backend"

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.ORG_ID}}
        vercel-project-id: ${{ secrets.PROJECT_ID}}
        working-directory: ./frontend
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pip install pytest pytest-flask
pytest tests/
```

### Frontend Tests
```bash
cd frontend
pnpm test
```

## 📈 Scaling Considerations

### Database Scaling
- **Read Replicas**: For read-heavy workloads
- **Connection Pooling**: Use PgBouncer or similar
- **Indexing**: Add indexes for frequently queried fields

### Application Scaling
- **Horizontal Scaling**: Multiple backend instances behind load balancer
- **Caching**: Redis for session storage and API caching
- **CDN**: CloudFront for static assets

### Queue Processing
```python
# Separate worker processes for job applications
# Use Celery with Redis broker
from celery import Celery

celery = Celery('autojobapply')
celery.config_from_object('celeryconfig')

@celery.task
def process_job_application(user_id, job_id):
    # Application processing logic
    pass
```

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure CORS is configured in Flask app
   - Check frontend API URL configuration

2. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check firewall rules for database access

3. **JWT Token Issues**
   - Ensure JWT_SECRET_KEY is set
   - Check token expiration settings

4. **File Upload Issues**
   - Verify AWS S3 credentials
   - Check bucket permissions

### Logs and Debugging
```bash
# Backend logs
heroku logs --tail --app autojobapply-api

# Frontend logs (Vercel)
vercel logs autojobapply-frontend

# Database logs
heroku pg:logs --app autojobapply-api
```

## 📞 Support

For deployment issues or questions:
1. Check the logs first
2. Verify environment variables
3. Test API endpoints individually
4. Check database connectivity

The application is designed to be deployment-friendly with clear error messages and comprehensive logging.

