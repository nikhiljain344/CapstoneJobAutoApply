import re
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

class JobMatchingEngine:
    """
    Advanced job matching engine that uses multiple algorithms to match users with jobs:
    1. Skills-based matching using TF-IDF and cosine similarity
    2. Experience level matching
    3. Location-based filtering (geospatial)
    4. Salary range matching
    5. Company preferences
    6. Job type preferences (remote, hybrid, on-site)
    """
    
    def __init__(self):
        self.skill_weights = {
            'exact_match': 1.0,
            'partial_match': 0.7,
            'related_match': 0.5
        }
        
        self.experience_weights = {
            'exact_match': 1.0,
            'one_level_diff': 0.8,
            'two_level_diff': 0.5
        }
        
        # Common skill synonyms and related skills
        self.skill_synonyms = {
            'javascript': ['js', 'node.js', 'nodejs', 'react', 'angular', 'vue'],
            'python': ['django', 'flask', 'fastapi', 'pandas', 'numpy'],
            'java': ['spring', 'hibernate', 'maven', 'gradle'],
            'sql': ['mysql', 'postgresql', 'sqlite', 'oracle', 'mongodb'],
            'aws': ['amazon web services', 'ec2', 's3', 'lambda', 'cloudformation'],
            'docker': ['containerization', 'kubernetes', 'k8s'],
            'machine learning': ['ml', 'ai', 'artificial intelligence', 'deep learning', 'tensorflow', 'pytorch'],
            'frontend': ['front-end', 'ui', 'ux', 'css', 'html', 'sass', 'less'],
            'backend': ['back-end', 'server-side', 'api', 'microservices'],
            'devops': ['ci/cd', 'jenkins', 'gitlab', 'github actions', 'terraform']
        }
        
        # Job title hierarchies for experience matching
        self.job_hierarchies = {
            'software engineer': ['junior software engineer', 'software engineer', 'senior software engineer', 'lead software engineer', 'principal engineer'],
            'data scientist': ['junior data scientist', 'data scientist', 'senior data scientist', 'lead data scientist', 'principal data scientist'],
            'product manager': ['associate product manager', 'product manager', 'senior product manager', 'director of product', 'vp of product'],
            'designer': ['junior designer', 'designer', 'senior designer', 'lead designer', 'design director']
        }

    def normalize_skills(self, skills: List[str]) -> List[str]:
        """Normalize and expand skills using synonyms"""
        normalized_skills = set()
        
        for skill in skills:
            skill_lower = skill.lower().strip()
            normalized_skills.add(skill_lower)
            
            # Add synonyms
            for main_skill, synonyms in self.skill_synonyms.items():
                if skill_lower == main_skill or skill_lower in synonyms:
                    normalized_skills.add(main_skill)
                    normalized_skills.update(synonyms)
        
        return list(normalized_skills)

    def calculate_skills_match(self, user_skills: List[str], job_requirements: List[str]) -> float:
        """
        Calculate skills match score using TF-IDF and cosine similarity
        
        Returns:
            Float between 0 and 1 representing match quality
        """
        if not user_skills or not job_requirements:
            return 0.0
        
        # Normalize skills
        user_skills_norm = self.normalize_skills(user_skills)
        job_requirements_norm = self.normalize_skills(job_requirements)
        
        # Create skill documents
        user_doc = ' '.join(user_skills_norm)
        job_doc = ' '.join(job_requirements_norm)
        
        # Calculate TF-IDF similarity
        try:
            vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform([user_doc, job_doc])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except ValueError:
            # Fallback to simple overlap calculation
            user_set = set(user_skills_norm)
            job_set = set(job_requirements_norm)
            
            if not job_set:
                return 0.0
            
            overlap = len(user_set.intersection(job_set))
            similarity = overlap / len(job_set)
        
        # Boost score for exact matches
        exact_matches = 0
        for job_skill in job_requirements_norm:
            if job_skill in user_skills_norm:
                exact_matches += 1
        
        exact_match_bonus = (exact_matches / len(job_requirements_norm)) * 0.2
        
        return min(1.0, similarity + exact_match_bonus)

    def calculate_experience_match(self, user_experience: Dict, job_requirements: Dict) -> float:
        """
        Calculate experience match score
        
        Args:
            user_experience: {'years': int, 'level': str, 'titles': List[str]}
            job_requirements: {'min_years': int, 'max_years': int, 'level': str, 'title': str}
        
        Returns:
            Float between 0 and 1 representing match quality
        """
        score = 0.0
        
        # Years of experience matching
        user_years = user_experience.get('years', 0)
        min_years = job_requirements.get('min_years', 0)
        max_years = job_requirements.get('max_years', 100)
        
        if min_years <= user_years <= max_years:
            score += 0.4  # Perfect years match
        elif user_years >= min_years:
            # Overqualified but still good
            excess_years = user_years - max_years
            penalty = min(0.2, excess_years * 0.05)  # Small penalty for being overqualified
            score += max(0.2, 0.4 - penalty)
        else:
            # Underqualified
            years_short = min_years - user_years
            penalty = min(0.4, years_short * 0.1)
            score += max(0.0, 0.4 - penalty)
        
        # Experience level matching
        user_level = user_experience.get('level', '').lower()
        job_level = job_requirements.get('level', '').lower()
        
        level_mapping = {'entry': 1, 'junior': 1, 'mid': 2, 'senior': 3, 'lead': 4, 'principal': 5}
        
        user_level_num = level_mapping.get(user_level, 2)
        job_level_num = level_mapping.get(job_level, 2)
        
        level_diff = abs(user_level_num - job_level_num)
        
        if level_diff == 0:
            score += 0.3  # Perfect level match
        elif level_diff == 1:
            score += 0.2  # One level difference
        elif level_diff == 2:
            score += 0.1  # Two levels difference
        # No points for 3+ level difference
        
        # Job title relevance
        user_titles = [title.lower() for title in user_experience.get('titles', [])]
        job_title = job_requirements.get('title', '').lower()
        
        title_score = 0.0
        for user_title in user_titles:
            if job_title in user_title or user_title in job_title:
                title_score = 0.3
                break
            
            # Check for related titles in hierarchies
            for hierarchy in self.job_hierarchies.values():
                if any(title in user_title for title in hierarchy) and any(title in job_title for title in hierarchy):
                    title_score = 0.2
                    break
        
        score += title_score
        
        return min(1.0, score)

    def calculate_location_match(self, user_location: Dict, job_location: Dict, max_distance_miles: float = 30) -> float:
        """
        Calculate location match score using geospatial distance
        
        Args:
            user_location: {'lat': float, 'lng': float, 'zip_code': str, 'remote_ok': bool}
            job_location: {'lat': float, 'lng': float, 'zip_code': str, 'remote': bool, 'hybrid': bool}
            max_distance_miles: Maximum acceptable distance in miles
        
        Returns:
            Float between 0 and 1 representing match quality
        """
        # Remote work preferences
        if job_location.get('remote', False) and user_location.get('remote_ok', True):
            return 1.0
        
        if job_location.get('hybrid', False) and user_location.get('hybrid_ok', True):
            return 0.9
        
        # Calculate geographic distance
        user_lat = user_location.get('lat')
        user_lng = user_location.get('lng')
        job_lat = job_location.get('lat')
        job_lng = job_location.get('lng')
        
        if not all([user_lat, user_lng, job_lat, job_lng]):
            # Fallback to ZIP code comparison if coordinates not available
            user_zip = user_location.get('zip_code', '')
            job_zip = job_location.get('zip_code', '')
            
            if user_zip and job_zip:
                # Simple ZIP code proximity (first 3 digits)
                if user_zip[:3] == job_zip[:3]:
                    return 0.8
                elif user_zip[:2] == job_zip[:2]:
                    return 0.6
                else:
                    return 0.3
            
            return 0.5  # Unknown location, neutral score
        
        # Haversine formula for distance calculation
        distance_miles = self.calculate_distance(user_lat, user_lng, job_lat, job_lng)
        
        if distance_miles <= 5:
            return 1.0
        elif distance_miles <= 15:
            return 0.9
        elif distance_miles <= max_distance_miles:
            return 0.7
        elif distance_miles <= max_distance_miles * 1.5:
            return 0.4
        else:
            return 0.1

    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c

    def calculate_salary_match(self, user_preferences: Dict, job_salary: Dict) -> float:
        """
        Calculate salary match score
        
        Args:
            user_preferences: {'min_salary': int, 'max_salary': int}
            job_salary: {'min': int, 'max': int, 'currency': str}
        
        Returns:
            Float between 0 and 1 representing match quality
        """
        user_min = user_preferences.get('min_salary', 0)
        user_max = user_preferences.get('max_salary', 1000000)
        
        job_min = job_salary.get('min', 0)
        job_max = job_salary.get('max', 0)
        
        if job_min == 0 and job_max == 0:
            return 0.5  # No salary info, neutral score
        
        # Calculate overlap between ranges
        overlap_start = max(user_min, job_min)
        overlap_end = min(user_max, job_max)
        
        if overlap_start <= overlap_end:
            # There's an overlap
            overlap_size = overlap_end - overlap_start
            user_range_size = user_max - user_min
            job_range_size = job_max - job_min
            
            if user_range_size == 0:
                return 1.0 if job_min >= user_min else 0.0
            
            overlap_ratio = overlap_size / user_range_size
            return min(1.0, overlap_ratio)
        else:
            # No overlap
            if job_max < user_min:
                # Job pays too little
                gap = user_min - job_max
                penalty = min(0.5, gap / user_min)
                return max(0.0, 0.5 - penalty)
            else:
                # Job pays more than expected (good!)
                return 0.8

    def calculate_company_match(self, user_preferences: Dict, job_company: Dict) -> float:
        """
        Calculate company match score based on user preferences
        
        Args:
            user_preferences: {'preferred_companies': List[str], 'company_size': str, 'industry': str}
            job_company: {'name': str, 'size': str, 'industry': str, 'rating': float}
        
        Returns:
            Float between 0 and 1 representing match quality
        """
        score = 0.5  # Base score
        
        # Preferred companies
        preferred_companies = [c.lower() for c in user_preferences.get('preferred_companies', [])]
        company_name = job_company.get('name', '').lower()
        
        if preferred_companies and any(pref in company_name for pref in preferred_companies):
            score += 0.3
        
        # Company size preference
        user_size_pref = user_preferences.get('company_size', '').lower()
        job_company_size = job_company.get('size', '').lower()
        
        if user_size_pref and user_size_pref == job_company_size:
            score += 0.1
        
        # Industry preference
        user_industry = user_preferences.get('industry', '').lower()
        job_industry = job_company.get('industry', '').lower()
        
        if user_industry and user_industry in job_industry:
            score += 0.1
        
        # Company rating bonus
        company_rating = job_company.get('rating', 3.0)
        if company_rating >= 4.5:
            score += 0.1
        elif company_rating >= 4.0:
            score += 0.05
        
        return min(1.0, score)

    def calculate_overall_match_score(self, user_profile: Dict, job: Dict, weights: Optional[Dict] = None) -> Dict:
        """
        Calculate overall match score combining all factors
        
        Args:
            user_profile: Complete user profile with skills, experience, location, preferences
            job: Job posting with requirements, location, salary, company info
            weights: Custom weights for different factors
        
        Returns:
            Dict with overall score and breakdown of individual scores
        """
        if weights is None:
            weights = {
                'skills': 0.35,
                'experience': 0.25,
                'location': 0.20,
                'salary': 0.10,
                'company': 0.10
            }
        
        # Calculate individual scores
        skills_score = self.calculate_skills_match(
            user_profile.get('skills', []),
            job.get('required_skills', [])
        )
        
        experience_score = self.calculate_experience_match(
            user_profile.get('experience', {}),
            job.get('experience_requirements', {})
        )
        
        location_score = self.calculate_location_match(
            user_profile.get('location', {}),
            job.get('location', {})
        )
        
        salary_score = self.calculate_salary_match(
            user_profile.get('salary_preferences', {}),
            job.get('salary', {})
        )
        
        company_score = self.calculate_company_match(
            user_profile.get('company_preferences', {}),
            job.get('company', {})
        )
        
        # Calculate weighted overall score
        overall_score = (
            skills_score * weights['skills'] +
            experience_score * weights['experience'] +
            location_score * weights['location'] +
            salary_score * weights['salary'] +
            company_score * weights['company']
        )
        
        return {
            'overall_score': round(overall_score, 3),
            'breakdown': {
                'skills': round(skills_score, 3),
                'experience': round(experience_score, 3),
                'location': round(location_score, 3),
                'salary': round(salary_score, 3),
                'company': round(company_score, 3)
            },
            'weights_used': weights,
            'match_quality': self.get_match_quality_label(overall_score)
        }

    def get_match_quality_label(self, score: float) -> str:
        """Convert numeric score to quality label"""
        if score >= 0.9:
            return 'Excellent'
        elif score >= 0.8:
            return 'Very Good'
        elif score >= 0.7:
            return 'Good'
        elif score >= 0.6:
            return 'Fair'
        elif score >= 0.5:
            return 'Poor'
        else:
            return 'Very Poor'

    def find_best_matches(self, user_profile: Dict, jobs: List[Dict], limit: int = 20) -> List[Dict]:
        """
        Find best job matches for a user
        
        Args:
            user_profile: Complete user profile
            jobs: List of job postings
            limit: Maximum number of matches to return
        
        Returns:
            List of jobs with match scores, sorted by score descending
        """
        matches = []
        
        for job in jobs:
            try:
                match_result = self.calculate_overall_match_score(user_profile, job)
                
                job_with_score = job.copy()
                job_with_score['match_score'] = match_result['overall_score']
                job_with_score['match_breakdown'] = match_result['breakdown']
                job_with_score['match_quality'] = match_result['match_quality']
                
                matches.append(job_with_score)
                
            except Exception as e:
                logging.error(f"Error calculating match for job {job.get('id', 'unknown')}: {e}")
                continue
        
        # Sort by match score descending
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches[:limit]

    def explain_match(self, user_profile: Dict, job: Dict) -> Dict:
        """
        Provide detailed explanation of why a job matches or doesn't match
        
        Returns:
            Dict with detailed explanations for each factor
        """
        match_result = self.calculate_overall_match_score(user_profile, job)
        
        explanations = {
            'overall_assessment': f"This job is a {match_result['match_quality'].lower()} match with a score of {match_result['overall_score']:.1%}",
            'factors': {}
        }
        
        # Skills explanation
        skills_score = match_result['breakdown']['skills']
        if skills_score >= 0.8:
            explanations['factors']['skills'] = "Your skills are an excellent match for this role's requirements."
        elif skills_score >= 0.6:
            explanations['factors']['skills'] = "Your skills align well with most of the job requirements."
        elif skills_score >= 0.4:
            explanations['factors']['skills'] = "You have some relevant skills, but may need to develop additional ones."
        else:
            explanations['factors']['skills'] = "This role requires skills that don't closely match your current skillset."
        
        # Experience explanation
        exp_score = match_result['breakdown']['experience']
        if exp_score >= 0.8:
            explanations['factors']['experience'] = "Your experience level is perfectly suited for this position."
        elif exp_score >= 0.6:
            explanations['factors']['experience'] = "Your experience is a good fit for this role."
        elif exp_score >= 0.4:
            explanations['factors']['experience'] = "You may be slightly under or over-qualified for this position."
        else:
            explanations['factors']['experience'] = "There's a significant mismatch between your experience and the role requirements."
        
        # Location explanation
        loc_score = match_result['breakdown']['location']
        if loc_score >= 0.9:
            explanations['factors']['location'] = "The job location is ideal for your preferences."
        elif loc_score >= 0.7:
            explanations['factors']['location'] = "The location works well with your preferences."
        elif loc_score >= 0.5:
            explanations['factors']['location'] = "The location is acceptable but may require some commuting."
        else:
            explanations['factors']['location'] = "The location may not be convenient for your situation."
        
        return explanations

