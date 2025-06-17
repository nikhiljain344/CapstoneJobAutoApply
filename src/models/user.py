from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    zip_code = db.Column(db.String(10), nullable=False, index=True)
    
    # Geospatial data for location-based matching
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Relationships
    education = db.relationship('Education', backref='user', lazy=True, cascade='all, delete-orphan')
    work_experience = db.relationship('WorkExperience', backref='user', lazy=True, cascade='all, delete-orphan')
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    applications = db.relationship('JobApplication', backref='user', lazy=True, cascade='all, delete-orphan')
    preferences = db.relationship('UserPreferences', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def calculate_total_experience(self):
        """Calculate total experience based on work history and education"""
        work_years = 0
        for work in self.work_experience:
            if work.end_date and work.start_date:
                years = (work.end_date - work.start_date).days / 365.25
                # Direct experience counts 100%, indirect counts 50%
                multiplier = 1.0 if work.is_direct else 0.5
                work_years += years * multiplier
        
        # Education credits
        education_credits = {
            'high_school': 0,
            'associate': 1,
            'bachelor': 2,
            'master': 3,
            'phd': 4
        }
        
        education_years = 0
        for edu in self.education:
            education_years += education_credits.get(edu.degree_type, 0)
        
        return work_years + education_years
    
    def get_experience_level(self):
        """Get experience level classification"""
        total_years = self.calculate_total_experience()
        if total_years < 3:
            return 'entry'
        elif total_years <= 8:
            return 'mid'
        else:
            return 'senior'
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'zip_code': self.zip_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'total_experience': self.calculate_total_experience(),
            'experience_level': self.get_experience_level()
        }

class Education(db.Model):
    __tablename__ = 'education'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    institution = db.Column(db.String(200), nullable=False)
    degree_type = db.Column(db.String(50), nullable=False)  # high_school, associate, bachelor, master, phd
    field_of_study = db.Column(db.String(200))
    graduation_year = db.Column(db.Integer)
    gpa = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'institution': self.institution,
            'degree_type': self.degree_type,
            'field_of_study': self.field_of_study,
            'graduation_year': self.graduation_year,
            'gpa': self.gpa
        }

class WorkExperience(db.Model):
    __tablename__ = 'work_experience'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # NULL if current job
    is_current = db.Column(db.Boolean, default=False)
    is_direct = db.Column(db.Boolean, default=True)  # Direct vs indirect experience
    description = db.Column(db.Text)
    skills = db.Column(db.Text)  # JSON string of skills
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def calculate_years(self):
        """Calculate years of experience for this job"""
        end = self.end_date or datetime.now().date()
        return (end - self.start_date).days / 365.25
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_title': self.job_title,
            'company': self.company,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_current': self.is_current,
            'is_direct': self.is_direct,
            'description': self.description,
            'skills': self.skills,
            'years': self.calculate_years()
        }

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Resume information
    resume_s3_key = db.Column(db.String(500))  # S3 object key
    resume_filename = db.Column(db.String(255))
    resume_text = db.Column(db.Text)  # Parsed resume text
    resume_uploaded_at = db.Column(db.DateTime)
    
    # Calculated experience
    total_experience = db.Column(db.Float, default=0.0)
    experience_level = db.Column(db.String(20))  # entry, mid, senior
    
    @property
    def total_experience_years(self):
        """Alias for total_experience for compatibility"""
        return self.total_experience
    
    # Skills and preferences
    skills = db.Column(db.Text)  # JSON string of skills
    summary = db.Column(db.Text)
    
    # Job matching preferences (JSON fields)
    salary_preferences = db.Column(db.JSON)
    location_preferences = db.Column(db.JSON)
    company_preferences = db.Column(db.JSON)
    job_type_preferences = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'resume_filename': self.resume_filename,
            'resume_uploaded_at': self.resume_uploaded_at.isoformat() if self.resume_uploaded_at else None,
            'total_experience': self.total_experience,
            'experience_level': self.experience_level,
            'skills': self.skills,
            'summary': self.summary
        }

class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Salary preferences
    min_salary = db.Column(db.Integer)
    max_salary = db.Column(db.Integer)
    salary_type = db.Column(db.String(20), default='annual')  # annual, hourly
    
    # Location preferences
    max_commute_miles = db.Column(db.Integer, default=30)
    remote_ok = db.Column(db.Boolean, default=True)
    hybrid_ok = db.Column(db.Boolean, default=True)
    onsite_ok = db.Column(db.Boolean, default=True)
    
    # Job preferences
    job_types = db.Column(db.Text)  # JSON array of preferred job types
    industries = db.Column(db.Text)  # JSON array of preferred industries
    company_sizes = db.Column(db.Text)  # JSON array of preferred company sizes
    
    # Application preferences
    auto_respond_yes = db.Column(db.Boolean, default=True)  # Auto-respond "Yes" to screening questions
    daily_application_limit = db.Column(db.Integer, default=10)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'min_salary': self.min_salary,
            'max_salary': self.max_salary,
            'salary_type': self.salary_type,
            'max_commute_miles': self.max_commute_miles,
            'remote_ok': self.remote_ok,
            'hybrid_ok': self.hybrid_ok,
            'onsite_ok': self.onsite_ok,
            'job_types': self.job_types,
            'industries': self.industries,
            'company_sizes': self.company_sizes,
            'auto_respond_yes': self.auto_respond_yes,
            'daily_application_limit': self.daily_application_limit
        }

