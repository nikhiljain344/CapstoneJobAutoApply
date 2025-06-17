from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from src.models.user import db

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100), unique=True, nullable=False, index=True)  # Job board's ID
    source = db.Column(db.String(50), nullable=False)  # indeed, monster, etc.
    
    # Job details
    title = db.Column(db.String(200), nullable=False, index=True)
    company = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    
    # Location
    location = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(10))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Job details
    job_type = db.Column(db.String(50))  # full-time, part-time, contract, etc.
    experience_level = db.Column(db.String(20))  # entry, mid, senior
    remote_type = db.Column(db.String(20))  # remote, hybrid, onsite
    
    # Salary information
    min_salary = db.Column(db.Integer)
    max_salary = db.Column(db.Integer)
    salary_type = db.Column(db.String(20))  # annual, hourly
    
    # Application details
    application_url = db.Column(db.String(500))
    application_method = db.Column(db.String(50))  # api, upload, email
    company_website = db.Column(db.String(200))
    
    # Skills and keywords
    required_skills = db.Column(db.Text)  # JSON array
    preferred_skills = db.Column(db.Text)  # JSON array
    keywords = db.Column(db.Text)  # For search indexing
    
    # Metadata
    posted_date = db.Column(db.DateTime)
    expires_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    applications = db.relationship('JobApplication', backref='job', lazy=True)
    
    def calculate_match_score(self, user):
        """Calculate job match score for a user"""
        # This is a simplified version - in production, use more sophisticated matching
        score = 0.0
        
        # Experience level match (30%)
        if self.experience_level == user.get_experience_level():
            score += 0.3
        
        # Location match (20%) - simplified for now
        if self.remote_type == 'remote':
            score += 0.2
        
        # Skills match (50%) - simplified for now
        # In production, implement proper skill matching algorithm
        score += 0.5  # Placeholder
        
        return min(score, 1.0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'external_id': self.external_id,
            'source': self.source,
            'title': self.title,
            'company': self.company,
            'description': self.description,
            'location': self.location,
            'city': self.city,
            'state': self.state,
            'job_type': self.job_type,
            'experience_level': self.experience_level,
            'remote_type': self.remote_type,
            'min_salary': self.min_salary,
            'max_salary': self.max_salary,
            'salary_type': self.salary_type,
            'application_url': self.application_url,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'expires_date': self.expires_date.isoformat() if self.expires_date else None,
            'is_active': self.is_active
        }

class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    
    # Application details
    application_method = db.Column(db.String(50), nullable=False)  # api, upload, text
    status = db.Column(db.String(50), default='pending')  # pending, submitted, failed, rejected, interview, hired
    
    # Application data
    resume_used = db.Column(db.String(500))  # S3 key or text content
    cover_letter = db.Column(db.Text)
    application_data = db.Column(db.Text)  # JSON of form data submitted
    
    # Tracking
    applied_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    response_received_at = db.Column(db.DateTime)
    last_status_update = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Automation details
    automation_log = db.Column(db.Text)  # JSON log of automation steps
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    # Matching score
    match_score = db.Column(db.Float)  # Score when job was matched
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'job': self.job.to_dict() if self.job else None,
            'application_method': self.application_method,
            'status': self.status,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'response_received_at': self.response_received_at.isoformat() if self.response_received_at else None,
            'match_score': self.match_score,
            'retry_count': self.retry_count,
            'error_message': self.error_message
        }

class ApplicationQueue(db.Model):
    __tablename__ = 'application_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    
    # Queue management
    priority = db.Column(db.Integer, default=0)  # Higher number = higher priority
    status = db.Column(db.String(50), default='queued')  # queued, processing, completed, failed
    scheduled_for = db.Column(db.DateTime)  # When to process this application
    
    # Processing details
    worker_id = db.Column(db.String(100))  # ID of worker processing this
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Retry logic
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    next_retry_at = db.Column(db.DateTime)
    
    # Results
    result_data = db.Column(db.Text)  # JSON result from processing
    error_message = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', backref='queued_applications')
    job = db.relationship('Job', backref='queued_applications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_id': self.job_id,
            'priority': self.priority,
            'status': self.status,
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class JobSearchHistory(db.Model):
    __tablename__ = 'job_search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Search parameters
    search_query = db.Column(db.String(500))
    location = db.Column(db.String(200))
    radius_miles = db.Column(db.Integer)
    experience_level = db.Column(db.String(20))
    job_type = db.Column(db.String(50))
    remote_type = db.Column(db.String(20))
    
    # Results
    total_jobs_found = db.Column(db.Integer)
    jobs_matched = db.Column(db.Integer)
    jobs_applied = db.Column(db.Integer)
    
    # Metadata
    search_source = db.Column(db.String(50))  # indeed, monster, etc.
    search_duration_ms = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'search_query': self.search_query,
            'location': self.location,
            'total_jobs_found': self.total_jobs_found,
            'jobs_matched': self.jobs_matched,
            'jobs_applied': self.jobs_applied,
            'search_source': self.search_source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

