# AutoJobApply Platform

A comprehensive auto-apply job application platform that automatically applies to 10+ relevant jobs per user per day with intelligent experience classification and resume automation.

## Project Structure

```
autojobapply-platform/
├── frontend/          # React.js frontend application
├── backend/           # Flask backend API
├── docs/             # Documentation
├── docker/           # Docker configurations
└── README.md         # This file
```

## Core Features

### 🎯 Automated Job Applications
- Automatically applies to 10+ relevant jobs per user per day (Monday-Friday)
- Intelligent job matching within 30-mile radius
- Multi-method application: API → File Upload → Text Fallback

### 🧠 Experience Classification
- Smart calculation: Work Experience + Education Credits
- Level classification: Entry (<3 years), Mid (3-8 years), Senior (>8 years)
- Direct vs indirect work experience weighting

### 📄 Resume Management
- Multiple upload formats (PDF/DOCX)
- Automatic parsing and text extraction
- Secure AWS S3 storage with encryption

### 🔍 Job Matching Algorithm
- Skills match (50%) + Experience alignment (30%) + Education (20%)
- Location-based filtering with PostGIS
- Real-time job board integration (Indeed, Monster)

## Technology Stack

### Frontend
- **React.js** with TypeScript
- **Tailwind CSS** for styling
- **shadcn/ui** components
- **React Router** for navigation
- **Framer Motion** for animations

### Backend
- **Flask** with Python
- **PostgreSQL** with PostGIS for geospatial queries
- **Redis** with Bull.js for job queues
- **AWS S3** for file storage
- **Puppeteer** for web automation

### Infrastructure
- **Docker** for containerization
- **AWS** for cloud services
- **Kubernetes** for orchestration (production)
- **Grafana** for monitoring

## Security Features

- AES-256 encryption for PII and resumes
- JWT authentication with secure token handling
- GDPR compliance with 1-click data export/deletion
- Rate limiting and DDoS protection
- Proxy rotation and CAPTCHA solving for anti-blocking

## Scalability Design

- Microservices architecture
- Horizontal scaling with Kubernetes
- Database read replicas
- Redis clustering for queue management
- Auto-scaling worker pools

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 14+
- Redis 6+

### Development Setup

1. **Frontend Setup**
   ```bash
   cd frontend
   pnpm install
   pnpm run dev
   ```

2. **Backend Setup**
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt
   python src/main.py
   ```

## API Documentation

The API follows RESTful conventions with the following main endpoints:

- `/api/auth/*` - Authentication and user management
- `/api/profile/*` - User profile and resume management
- `/api/jobs/*` - Job search and application tracking
- `/api/applications/*` - Application history and status

## Contributing

This codebase is designed for scalability, security, and maintainability:

1. **Modular Architecture**: Clear separation of concerns
2. **Type Safety**: TypeScript frontend, type hints in Python
3. **Testing**: Comprehensive test coverage
4. **Documentation**: Inline comments and API docs
5. **Security**: Built-in security best practices

## License

Proprietary - All rights reserved

