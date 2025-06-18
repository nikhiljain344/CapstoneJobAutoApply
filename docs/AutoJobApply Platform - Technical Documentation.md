# AutoJobApply Platform - Technical Documentation

## Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  Flask Backend  │    │   PostgreSQL    │
│   (Port 5173)   │◄──►│   (Port 5002)   │◄──►│    Database     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Celery Workers │◄──►│  Redis Queue    │
                       │  (Automation)   │    │   (Port 6379)   │
                       └─────────────────┘    └─────────────────┘
```

### Technology Stack

#### Backend
- **Framework**: Flask 3.0+ with Blueprint architecture
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with Flask-JWT-Extended
- **Queue System**: Celery with Redis broker
- **Web Automation**: Selenium + Puppeteer (pyppeteer)
- **NLP Processing**: spaCy with en_core_web_sm model
- **File Processing**: PyPDF2, python-docx for resume parsing

#### Frontend
- **Framework**: React 18+ with Vite
- **Styling**: Tailwind CSS with responsive design
- **State Management**: React Context API
- **HTTP Client**: Fetch API with JWT authentication
- **UI Components**: Custom components with Tailwind

#### Infrastructure
- **Message Queue**: Redis for Celery task management
- **File Storage**: Local filesystem (AWS S3 ready)
- **Process Management**: Background workers for automation
- **CORS**: Enabled for cross-origin requests

## Database Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    zip_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE
);
```

#### User Profiles Table
```sql
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    resume_filename VARCHAR(255),
    resume_text TEXT,
    total_experience FLOAT DEFAULT 0.0,
    experience_level VARCHAR(20),
    skills TEXT, -- JSON array
    summary TEXT,
    salary_preferences JSON,
    location_preferences JSON,
    company_preferences JSON,
    job_type_preferences JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Job Applications Table
```sql
CREATE TABLE job_applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    job_id VARCHAR(255),
    job_url TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    application_method VARCHAR(50),
    notes TEXT
);
```

#### Application Queue Table
```sql
CREATE TABLE application_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    job_id VARCHAR(255),
    job_url TEXT NOT NULL,
    priority INTEGER DEFAULT 3,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

## API Endpoints

### Authentication Endpoints
```
POST /api/auth/register          # User registration
POST /api/auth/login             # User login
POST /api/auth/logout            # User logout
GET  /api/auth/me                # Get current user info
```

### Profile Management
```
GET    /api/profile              # Get user profile
PUT    /api/profile              # Update user profile
GET    /api/profile/education    # Get education records
POST   /api/profile/education    # Add education record
GET    /api/profile/experience   # Get work experience
POST   /api/profile/experience   # Add work experience
```

### Resume Processing
```
POST /api/resume/upload          # Upload and process resume
POST /api/resume/analyze         # Analyze resume text
GET  /api/resume/skills/suggestions # Get skill suggestions
```

### Job Matching
```
POST /api/matching/find-matches  # Find job matches
POST /api/matching/explain-match # Explain specific match
GET  /api/matching/preferences   # Get matching preferences
POST /api/matching/update-preferences # Update preferences
```

### Queue Management
```
POST   /api/queue/add-to-queue   # Add job to application queue
GET    /api/queue/queue-status   # Get queue status
DELETE /api/queue/remove-from-queue/{id} # Remove from queue
POST   /api/queue/bulk-apply     # Bulk add jobs to queue
GET    /api/queue/task-status/{task_id} # Get task status
GET    /api/queue/application-stats # Get application statistics
```

### Analytics
```
GET /api/analytics/dashboard-stats    # Dashboard overview
GET /api/analytics/application-trends # Application trends
GET /api/analytics/success-metrics    # Success metrics
GET /api/analytics/performance-insights # AI insights
GET /api/analytics/export-data        # Export user data
```

## Core Services

### Resume Processor (`resume_processor.py`)

#### Key Features
- **Multi-format Support**: PDF and DOCX file parsing
- **Text Extraction**: Clean text extraction with formatting preservation
- **Skills Identification**: NLP-based skill extraction using spaCy
- **Experience Calculation**: Smart experience level determination
- **Profile Auto-population**: Automatic user profile updates

#### Usage Example
```python
from src.services.resume_processor import ResumeProcessor

processor = ResumeProcessor()
result = processor.process_resume_file('/path/to/resume.pdf')

# Result contains:
# - extracted_text
# - identified_skills
# - experience_years
# - experience_level
# - profile_updates
```

### Job Matching Engine (`job_matching.py`)

#### Matching Algorithm
1. **Skills Matching**: Jaccard similarity with skill synonyms
2. **Experience Matching**: Level and years compatibility scoring
3. **Location Matching**: Geospatial distance calculations
4. **Salary Matching**: Range overlap and preference scoring
5. **Company Matching**: Preference-based filtering

#### Scoring System
- **Skills Score**: 0-100 based on skill overlap and relevance
- **Experience Score**: 0-100 based on level and years match
- **Location Score**: 0-100 based on distance and remote preferences
- **Salary Score**: 0-100 based on range compatibility
- **Overall Score**: Weighted average of all factors

#### Usage Example
```python
from src.services.job_matching import JobMatchingEngine

engine = JobMatchingEngine()
matches = engine.find_best_matches(user_profile, job_list, limit=10)

# Returns sorted list of jobs with match scores and explanations
```

### Automation System (`automation_tasks.py`)

#### Bot Capabilities
- **Multi-platform Support**: Indeed, company websites, generic forms
- **Anti-detection**: User agent rotation, timing randomization
- **Form Intelligence**: Auto-detection of form fields and types
- **Screening Questions**: Automated answering of common questions
- **Error Recovery**: Retry logic and failure handling

#### Supported Platforms
1. **Indeed**: Native Indeed application forms
2. **External Sites**: Company career pages
3. **Generic Forms**: Any standard job application form

#### Usage Example
```python
from src.services.automation_tasks import apply_to_job

# Celery task - runs asynchronously
task = apply_to_job.delay(user_id, job_id, job_url)

# Monitor task progress
result = task.get()  # Blocks until completion
```

## Frontend Architecture

### Component Structure
```
src/
├── components/
│   └── Navbar.jsx           # Navigation component
├── contexts/
│   └── AuthContext.jsx      # Authentication state management
├── pages/
│   ├── LandingPage.jsx      # Marketing landing page
│   ├── LoginPage.jsx        # User login
│   ├── RegisterPage.jsx     # User registration
│   ├── Dashboard.jsx        # Main dashboard with analytics
│   ├── ProfilePage.jsx      # User profile management
│   ├── JobsPage.jsx         # Job search and matching
│   └── ApplicationsPage.jsx # Application tracking
└── App.jsx                  # Main app component with routing
```

### State Management
- **AuthContext**: Global authentication state
- **Local State**: Component-specific state with useState
- **API Integration**: Fetch-based HTTP client with JWT tokens

### Responsive Design
- **Mobile-first**: Tailwind CSS responsive utilities
- **Breakpoints**: sm, md, lg, xl for different screen sizes
- **Touch-friendly**: Large buttons and touch targets

## Deployment Guide

### Local Development Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export DATABASE_URL=postgresql://user:pass@localhost/autojobapply
export JWT_SECRET_KEY=your-secret-key
export REDIS_URL=redis://localhost:6379/0

# Run the application
python src/main.py
```

#### Frontend Setup
```bash
cd frontend
npm install  # or pnpm install
npm run dev  # Starts development server on port 5173
```

#### Redis Setup
```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis
redis-server

# Start Celery worker (in separate terminal)
cd backend
source venv/bin/activate
celery -A src.services.celery_config.celery_app worker --loglevel=info
```

### Production Deployment

#### Environment Variables
```bash
# Backend (.env)
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@prod-db:5432/autojobapply
JWT_SECRET_KEY=secure-random-key
REDIS_URL=redis://redis-server:6379/0
SECRET_KEY=flask-secret-key

# External Services
SENDGRID_API_KEY=your-sendgrid-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=your-s3-bucket
```

#### Docker Configuration
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5002
CMD ["python", "src/main.py"]

# Frontend Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

#### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5002:5002"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/autojobapply
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=autojobapply
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery:
    build: ./backend
    command: celery -A src.services.celery_config.celery_app worker --loglevel=info
    depends_on:
      - redis
      - db

volumes:
  postgres_data:
```

## Security Considerations

### Authentication Security
- **JWT Tokens**: Secure token-based authentication
- **Password Hashing**: bcrypt with salt rounds
- **Token Expiration**: Configurable token lifetime
- **CORS Configuration**: Restricted origins in production

### Data Protection
- **Input Validation**: Server-side validation for all inputs
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Protection**: Input sanitization and output encoding
- **File Upload Security**: File type validation and size limits

### Automation Security
- **Anti-detection**: Sophisticated bot detection avoidance
- **Rate Limiting**: Controlled application frequency
- **User Agent Rotation**: Dynamic user agent strings
- **Proxy Support**: Ready for proxy integration

## Performance Optimization

### Database Optimization
- **Indexing**: Proper indexes on frequently queried columns
- **Connection Pooling**: SQLAlchemy connection pool
- **Query Optimization**: Efficient queries with joins and filters

### Caching Strategy
- **Redis Caching**: Cache frequently accessed data
- **Application Cache**: In-memory caching for static data
- **CDN Ready**: Static asset optimization

### Scalability Features
- **Horizontal Scaling**: Stateless application design
- **Load Balancing**: Ready for multiple instances
- **Queue System**: Distributed task processing
- **Microservices Ready**: Modular architecture for service separation

## Monitoring and Logging

### Application Monitoring
- **Health Checks**: Built-in health check endpoints
- **Error Tracking**: Comprehensive error logging
- **Performance Metrics**: Response time and throughput tracking

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

## Testing Strategy

### Backend Testing
```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# API tests
python -m pytest tests/api/
```

### Frontend Testing
```bash
# Component tests
npm run test

# E2E tests
npm run test:e2e
```

## Troubleshooting

### Common Issues

#### Backend Won't Start
1. Check Python version (3.11+)
2. Verify all dependencies installed
3. Check database connection
4. Verify environment variables

#### Celery Tasks Not Processing
1. Check Redis connection
2. Verify Celery worker is running
3. Check task queue status
4. Review worker logs

#### Frontend Build Errors
1. Check Node.js version (18+)
2. Clear node_modules and reinstall
3. Check for TypeScript errors
4. Verify API endpoints

### Performance Issues

#### Slow Database Queries
1. Add database indexes
2. Optimize query patterns
3. Use connection pooling
4. Consider read replicas

#### High Memory Usage
1. Optimize Celery worker count
2. Implement result cleanup
3. Use pagination for large datasets
4. Monitor memory leaks

## Future Enhancements

### Planned Features
1. **Real-time Notifications**: WebSocket integration
2. **Advanced Analytics**: Machine learning insights
3. **Mobile App**: React Native application
4. **API Rate Limiting**: Advanced rate limiting
5. **Multi-tenant Support**: Enterprise features

### Integration Roadmap
1. **Job Board APIs**: Indeed, LinkedIn, Monster
2. **Email Services**: SendGrid, AWS SES
3. **File Storage**: AWS S3, Google Cloud Storage
4. **Payment Processing**: Stripe integration
5. **Monitoring**: DataDog, New Relic integration

This technical documentation provides comprehensive guidance for developers to understand, maintain, and extend the AutoJobApply platform.

