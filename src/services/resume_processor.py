import os
import re
import spacy
import PyPDF2
from docx import Document
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy loading of NLTK data
def load_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)

# Lazy loading of spaCy model
_nlp = None
def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            # Load the small model with reduced components
            _nlp = spacy.load('en_core_web_sm', disable=['ner', 'parser', 'textcat'])
            # Reduce max length to save memory
            _nlp.max_length = 1000000  # 1M chars instead of default 2M
        except OSError:
            logger.error("spaCy model not found. Installing...")
            os.system('python -m spacy download en_core_web_sm')
            _nlp = spacy.load('en_core_web_sm', disable=['ner', 'parser', 'textcat'])
    return _nlp

class ResumeProcessor:
    """
    Comprehensive resume processing service that can:
    1. Extract text from PDF and DOCX files
    2. Parse and extract structured information
    3. Identify skills, experience, education
    4. Auto-populate user profiles
    """
    
    def __init__(self):
        # Lazy load NLTK data
        load_nltk_data()
        self.stop_words = None  # Lazy load stop words
        
        # Common skills database (expandable)
        self.technical_skills = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
                'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html', 'css', 'sass', 'less'
            ],
            'frameworks': [
                'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring', 'laravel',
                'rails', 'asp.net', 'bootstrap', 'tailwind', 'jquery', 'next.js', 'nuxt.js'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle', 'sqlite',
                'cassandra', 'dynamodb', 'firebase', 'supabase'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean', 'vercel', 'netlify'
            ],
            'tools': [
                'git', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github', 'jira', 'confluence',
                'slack', 'figma', 'sketch', 'photoshop', 'illustrator'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving', 'analytical thinking',
                'project management', 'time management', 'adaptability', 'creativity', 'collaboration'
            ]
        }
        
        # Education patterns
        self.education_patterns = {
            'degrees': [
                r'bachelor(?:\'s)?(?:\s+of)?(?:\s+science)?(?:\s+in)?',
                r'master(?:\'s)?(?:\s+of)?(?:\s+science)?(?:\s+in)?',
                r'phd|ph\.d|doctorate',
                r'associate(?:\'s)?(?:\s+of)?(?:\s+science)?(?:\s+in)?',
                r'high\s+school|diploma',
                r'b\.s\.|b\.a\.|m\.s\.|m\.a\.|m\.b\.a\.|b\.sc\.|m\.sc\.'
            ],
            'institutions': [
                r'university', r'college', r'institute', r'school', r'academy'
            ]
        }
        
        # Experience patterns
        self.experience_patterns = [
            r'(\d{1,2})\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d{1,2})\+?\s*yrs?\s*(?:of\s*)?experience',
            r'experience.*?(\d{1,2})\+?\s*years?',
            r'(\d{4})\s*[-–]\s*(\d{4}|\w+)',  # Date ranges
            r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4}|present|current)'
        ]

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logging.error(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logging.error(f"Error extracting text from DOCX: {e}")
            return ""

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from file based on extension"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from resume text"""
        contact_info = {}
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Phone extraction
        phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                contact_info['phone'] = phones[0]
                break
        
        # Address extraction (basic)
        address_pattern = r'\d+\s+[A-Za-z\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Place|Pl)'
        addresses = re.findall(address_pattern, text, re.IGNORECASE)
        if addresses:
            contact_info['address'] = addresses[0]
        
        # ZIP code extraction
        zip_pattern = r'\b\d{5}(?:-\d{4})?\b'
        zips = re.findall(zip_pattern, text)
        if zips:
            contact_info['zip_code'] = zips[0]
        
        return contact_info

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract technical and soft skills from resume text"""
        text_lower = text.lower()
        found_skills = {}
        
        for category, skills_list in self.technical_skills.items():
            found_skills[category] = []
            for skill in skills_list:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills[category].append(skill)
        
        # Remove empty categories
        found_skills = {k: v for k, v in found_skills.items() if v}
        
        return found_skills

    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information from resume text"""
        education_list = []
        
        # Split text into sentences for better parsing
        sentences = sent_tokenize(text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check for degree patterns
            for degree_pattern in self.education_patterns['degrees']:
                degree_match = re.search(degree_pattern, sentence_lower)
                if degree_match:
                    education_entry = {
                        'degree': sentence.strip(),
                        'institution': '',
                        'year': '',
                        'field_of_study': ''
                    }
                    
                    # Look for institution
                    for inst_pattern in self.education_patterns['institutions']:
                        if re.search(inst_pattern, sentence_lower):
                            education_entry['institution'] = sentence.strip()
                            break
                    
                    # Look for year
                    year_pattern = r'\b(19|20)\d{2}\b'
                    year_match = re.search(year_pattern, sentence)
                    if year_match:
                        education_entry['year'] = year_match.group()
                    
                    # Extract field of study (basic)
                    field_patterns = [
                        r'in\s+([A-Za-z\s]+)',
                        r'of\s+([A-Za-z\s]+)',
                        r'major\s+([A-Za-z\s]+)'
                    ]
                    for pattern in field_patterns:
                        field_match = re.search(pattern, sentence, re.IGNORECASE)
                        if field_match:
                            education_entry['field_of_study'] = field_match.group(1).strip()
                            break
                    
                    education_list.append(education_entry)
                    break
        
        return education_list

    def extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience from resume text"""
        experience_list = []
        
        # Split text into sections (basic approach)
        lines = text.split('\n')
        current_job = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for job titles (lines with common job keywords)
            job_keywords = [
                'engineer', 'developer', 'manager', 'analyst', 'specialist', 'coordinator',
                'director', 'lead', 'senior', 'junior', 'intern', 'consultant', 'architect'
            ]
            
            if any(keyword in line.lower() for keyword in job_keywords):
                if current_job:
                    experience_list.append(current_job)
                
                current_job = {
                    'title': line,
                    'company': '',
                    'start_date': '',
                    'end_date': '',
                    'description': ''
                }
            
            # Look for company names (lines after job titles)
            elif current_job and not current_job.get('company'):
                # Simple heuristic: if line doesn't contain dates, it might be company
                if not re.search(r'\d{4}', line):
                    current_job['company'] = line
            
            # Look for date ranges
            elif current_job:
                date_match = re.search(r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4}|present|current)', line, re.IGNORECASE)
                if date_match:
                    current_job['start_date'] = date_match.group(1)
                    current_job['end_date'] = date_match.group(2)
                else:
                    # Add to description
                    if current_job.get('description'):
                        current_job['description'] += ' ' + line
                    else:
                        current_job['description'] = line
        
        # Add the last job if exists
        if current_job:
            experience_list.append(current_job)
        
        return experience_list

    def calculate_total_experience(self, work_experience: List[Dict[str, str]]) -> float:
        """Calculate total years of experience"""
        total_years = 0.0
        
        for job in work_experience:
            start_date = job.get('start_date', '')
            end_date = job.get('end_date', '')
            
            if start_date and end_date:
                try:
                    # Parse start year
                    start_year_match = re.search(r'\d{4}', start_date)
                    if start_year_match:
                        start_year = int(start_year_match.group())
                    else:
                        continue
                    
                    # Parse end year
                    if 'present' in end_date.lower() or 'current' in end_date.lower():
                        end_year = datetime.now().year
                    else:
                        end_year_match = re.search(r'\d{4}', end_date)
                        if end_year_match:
                            end_year = int(end_year_match.group())
                        else:
                            continue
                    
                    # Calculate years for this job
                    job_years = max(0, end_year - start_year)
                    total_years += job_years
                    
                except (ValueError, AttributeError):
                    continue
        
        # Also look for explicit experience mentions
        text_experience = self.extract_years_from_text(' '.join([job.get('description', '') for job in work_experience]))
        if text_experience > total_years:
            total_years = text_experience
        
        return total_years

    def extract_years_from_text(self, text: str) -> float:
        """Extract years of experience mentioned in text"""
        max_years = 0.0
        
        for pattern in self.experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        # Handle date ranges
                        if len(match) == 2 and match[0].isdigit() and match[1].isdigit():
                            years = int(match[1]) - int(match[0])
                            max_years = max(max_years, years)
                        elif len(match) == 1:
                            years = float(match[0])
                            max_years = max(max_years, years)
                    else:
                        years = float(match)
                        max_years = max(max_years, years)
                except (ValueError, TypeError):
                    continue
        
        return max_years

    def classify_experience_level(self, total_years: float) -> str:
        """Classify experience level based on total years"""
        if total_years < 3:
            return 'entry'
        elif total_years <= 8:
            return 'mid'
        else:
            return 'senior'

    def process_resume(self, file_path: str) -> Dict:
        """
        Main method to process a resume file and extract all information
        
        Returns:
            Dict containing all extracted information
        """
        try:
            # Extract text from file
            text = self.extract_text_from_file(file_path)
            
            if not text:
                raise ValueError("Could not extract text from file")
            
            # Extract all information
            contact_info = self.extract_contact_info(text)
            skills = self.extract_skills(text)
            education = self.extract_education(text)
            work_experience = self.extract_work_experience(text)
            total_experience_years = self.calculate_total_experience(work_experience)
            experience_level = self.classify_experience_level(total_experience_years)
            
            # Extract name (first line heuristic)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            name = lines[0] if lines else ""
            
            return {
                'success': True,
                'extracted_data': {
                    'name': name,
                    'contact_info': contact_info,
                    'skills': skills,
                    'education': education,
                    'work_experience': work_experience,
                    'total_experience_years': total_experience_years,
                    'experience_level': experience_level,
                    'raw_text': text
                }
            }
            
        except Exception as e:
            logging.error(f"Error processing resume: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def auto_populate_profile(self, extracted_data: Dict, user_id: int) -> Dict:
        """
        Auto-populate user profile based on extracted resume data
        
        This method would integrate with the database models to update user profile
        """
        try:
            from src.models.user import User, Education, WorkExperience, UserProfile
            from src.main import db
            
            # Get user
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            data = extracted_data
            
            # Update basic user info if not already set
            if not user.name and data.get('name'):
                user.name = data['name']
            
            contact_info = data.get('contact_info', {})
            if not user.phone and contact_info.get('phone'):
                user.phone = contact_info['phone']
            if not user.address and contact_info.get('address'):
                user.address = contact_info['address']
            if not user.zip_code and contact_info.get('zip_code'):
                user.zip_code = contact_info['zip_code']
            
            # Create or update user profile
            profile = UserProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                profile = UserProfile(user_id=user_id)
                db.session.add(profile)
            
            # Update profile with extracted data
            profile.resume_text = data.get('raw_text', '')
            profile.total_experience_years = data.get('total_experience_years', 0)
            profile.experience_level = data.get('experience_level', 'entry')
            
            # Store skills as JSON
            skills = data.get('skills', {})
            all_skills = []
            for category, skill_list in skills.items():
                all_skills.extend(skill_list)
            profile.skills = all_skills
            
            # Add education entries
            for edu_data in data.get('education', []):
                existing_edu = Education.query.filter_by(
                    user_id=user_id,
                    degree=edu_data.get('degree', '')
                ).first()
                
                if not existing_edu:
                    education = Education(
                        user_id=user_id,
                        degree=edu_data.get('degree', ''),
                        institution=edu_data.get('institution', ''),
                        field_of_study=edu_data.get('field_of_study', ''),
                        graduation_year=int(edu_data.get('year', 0)) if edu_data.get('year', '').isdigit() else None
                    )
                    db.session.add(education)
            
            # Add work experience entries
            for work_data in data.get('work_experience', []):
                existing_work = WorkExperience.query.filter_by(
                    user_id=user_id,
                    job_title=work_data.get('title', ''),
                    company=work_data.get('company', '')
                ).first()
                
                if not existing_work:
                    work_experience = WorkExperience(
                        user_id=user_id,
                        job_title=work_data.get('title', ''),
                        company=work_data.get('company', ''),
                        start_date=work_data.get('start_date', ''),
                        end_date=work_data.get('end_date', ''),
                        description=work_data.get('description', ''),
                        is_direct_experience=True  # Assume direct experience from resume
                    )
                    db.session.add(work_experience)
            
            # Recalculate experience
            profile.calculate_total_experience()
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Profile updated successfully',
                'updated_fields': {
                    'name': user.name,
                    'phone': user.phone,
                    'address': user.address,
                    'zip_code': user.zip_code,
                    'total_experience_years': profile.total_experience_years,
                    'experience_level': profile.experience_level,
                    'skills_count': len(profile.skills or []),
                    'education_count': len(data.get('education', [])),
                    'work_experience_count': len(data.get('work_experience', []))
                }
            }
            
        except Exception as e:
            logging.error(f"Error auto-populating profile: {e}")
            return {'success': False, 'error': str(e)}

