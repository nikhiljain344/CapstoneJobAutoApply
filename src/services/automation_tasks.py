import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from celery import current_task
from pyppeteer import launch
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.services.celery_config import celery_app
from src.models.user import User, UserProfile
from src.models.job import Job, JobApplication, ApplicationQueue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobApplicationBot:
    """
    Automated job application bot using Selenium and Puppeteer
    """
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
    def setup_driver(self):
        """Setup Selenium WebDriver with anti-detection measures"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Anti-detection measures
        chrome_options.add_argument(f"--user-agent={self.user_agent}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")  # Can be enabled for specific sites
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Close WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def apply_to_indeed_job(self, job_url: str, user_profile: Dict) -> Dict:
        """Apply to a job on Indeed"""
        try:
            if not self.setup_driver():
                return {'success': False, 'error': 'Failed to setup browser'}
            
            self.driver.get(job_url)
            time.sleep(2)
            
            # Look for "Apply Now" button
            apply_buttons = [
                "//button[contains(text(), 'Apply now')]",
                "//a[contains(text(), 'Apply now')]",
                "//button[contains(@class, 'apply')]",
                "//a[contains(@class, 'apply')]"
            ]
            
            apply_button = None
            for xpath in apply_buttons:
                try:
                    apply_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not apply_button:
                return {'success': False, 'error': 'Apply button not found'}
            
            apply_button.click()
            time.sleep(2)
            
            # Check if redirected to external site
            current_url = self.driver.current_url
            if 'indeed.com' not in current_url:
                return self.apply_to_external_site(current_url, user_profile)
            
            # Fill Indeed application form
            return self.fill_indeed_application_form(user_profile)
            
        except Exception as e:
            logger.error(f"Error applying to Indeed job: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            self.close_driver()
    
    def fill_indeed_application_form(self, user_profile: Dict) -> Dict:
        """Fill Indeed's application form"""
        try:
            # Fill basic information
            form_fields = {
                'name': user_profile.get('name', ''),
                'email': user_profile.get('email', ''),
                'phone': user_profile.get('phone', ''),
                'location': user_profile.get('address', '')
            }
            
            for field_name, value in form_fields.items():
                if not value:
                    continue
                    
                field_selectors = [
                    f"input[name*='{field_name}']",
                    f"input[id*='{field_name}']",
                    f"input[placeholder*='{field_name}']"
                ]
                
                for selector in field_selectors:
                    try:
                        field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        field.clear()
                        field.send_keys(value)
                        break
                    except NoSuchElementException:
                        continue
            
            # Handle screening questions
            self.answer_screening_questions()
            
            # Upload resume if required
            resume_upload = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            if resume_upload and user_profile.get('resume_path'):
                resume_upload[0].send_keys(user_profile['resume_path'])
                time.sleep(2)
            
            # Submit application
            submit_buttons = [
                "button[type='submit']",
                "input[type='submit']",
                "button[contains(text(), 'Submit')]",
                "button[contains(text(), 'Apply')]"
            ]
            
            for selector in submit_buttons:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    submit_button.click()
                    time.sleep(3)
                    break
                except NoSuchElementException:
                    continue
            
            # Check for success confirmation
            success_indicators = [
                "Application submitted",
                "Thank you for applying",
                "Your application has been sent",
                "Application complete"
            ]
            
            page_text = self.driver.page_source.lower()
            for indicator in success_indicators:
                if indicator.lower() in page_text:
                    return {'success': True, 'message': 'Application submitted successfully'}
            
            return {'success': False, 'error': 'Could not confirm application submission'}
            
        except Exception as e:
            logger.error(f"Error filling Indeed form: {e}")
            return {'success': False, 'error': str(e)}
    
    def answer_screening_questions(self):
        """Answer common screening questions automatically"""
        try:
            # Common screening questions and answers
            screening_answers = {
                'authorized to work': 'yes',
                'require sponsorship': 'no',
                'willing to relocate': 'yes',
                'available to start': 'immediately',
                'years of experience': '5',
                'salary expectation': '80000',
                'notice period': '2 weeks'
            }
            
            # Find all form elements that might be screening questions
            questions = self.driver.find_elements(By.CSS_SELECTOR, "label, .question, .form-group")
            
            for question in questions:
                question_text = question.text.lower()
                
                for keyword, answer in screening_answers.items():
                    if keyword in question_text:
                        # Find associated input field
                        input_field = None
                        
                        # Try different methods to find the input
                        try:
                            input_field = question.find_element(By.CSS_SELECTOR, "input, select, textarea")
                        except NoSuchElementException:
                            try:
                                input_field = question.find_element(By.XPATH, ".//following-sibling::*//input | .//following-sibling::*//select")
                            except NoSuchElementException:
                                continue
                        
                        if input_field:
                            input_type = input_field.get_attribute('type')
                            
                            if input_type == 'radio':
                                # For radio buttons, find the "yes" option
                                radio_options = self.driver.find_elements(By.CSS_SELECTOR, f"input[name='{input_field.get_attribute('name')}']")
                                for radio in radio_options:
                                    if answer.lower() in radio.get_attribute('value').lower():
                                        radio.click()
                                        break
                            elif input_type == 'checkbox':
                                if answer.lower() == 'yes':
                                    input_field.click()
                            elif input_field.tag_name == 'select':
                                from selenium.webdriver.support.ui import Select
                                select = Select(input_field)
                                try:
                                    select.select_by_visible_text(answer)
                                except:
                                    try:
                                        select.select_by_value(answer)
                                    except:
                                        pass
                            else:
                                input_field.clear()
                                input_field.send_keys(answer)
                        
                        break
                        
        except Exception as e:
            logger.error(f"Error answering screening questions: {e}")
    
    def apply_to_external_site(self, job_url: str, user_profile: Dict) -> Dict:
        """Apply to job on external company website"""
        try:
            self.driver.get(job_url)
            time.sleep(3)
            
            # Look for application form or apply button
            apply_selectors = [
                "button[contains(text(), 'Apply')]",
                "a[contains(text(), 'Apply')]",
                "input[value*='Apply']",
                ".apply-button",
                "#apply-button"
            ]
            
            for selector in apply_selectors:
                try:
                    apply_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    apply_element.click()
                    time.sleep(2)
                    break
                except NoSuchElementException:
                    continue
            
            # Fill generic application form
            return self.fill_generic_application_form(user_profile)
            
        except Exception as e:
            logger.error(f"Error applying to external site: {e}")
            return {'success': False, 'error': str(e)}
    
    def fill_generic_application_form(self, user_profile: Dict) -> Dict:
        """Fill a generic application form"""
        try:
            # Map of common field names to user profile data
            field_mapping = {
                'first_name': user_profile.get('name', '').split()[0] if user_profile.get('name') else '',
                'last_name': ' '.join(user_profile.get('name', '').split()[1:]) if user_profile.get('name') else '',
                'email': user_profile.get('email', ''),
                'phone': user_profile.get('phone', ''),
                'address': user_profile.get('address', ''),
                'city': user_profile.get('city', ''),
                'state': user_profile.get('state', ''),
                'zip': user_profile.get('zip_code', ''),
                'linkedin': user_profile.get('linkedin_url', ''),
                'portfolio': user_profile.get('portfolio_url', ''),
                'website': user_profile.get('website_url', '')
            }
            
            # Find and fill form fields
            for field_name, value in field_mapping.items():
                if not value:
                    continue
                
                field_selectors = [
                    f"input[name*='{field_name}']",
                    f"input[id*='{field_name}']",
                    f"input[placeholder*='{field_name}']",
                    f"input[class*='{field_name}']"
                ]
                
                for selector in field_selectors:
                    try:
                        field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        field.clear()
                        field.send_keys(value)
                        break
                    except NoSuchElementException:
                        continue
            
            # Handle file uploads
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            for file_input in file_inputs:
                if user_profile.get('resume_path'):
                    file_input.send_keys(user_profile['resume_path'])
                    time.sleep(1)
            
            # Answer screening questions
            self.answer_screening_questions()
            
            # Submit form
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[contains(text(), 'Submit')]",
                "button[contains(text(), 'Send')]",
                "button[contains(text(), 'Apply')]"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    submit_button.click()
                    time.sleep(3)
                    break
                except NoSuchElementException:
                    continue
            
            return {'success': True, 'message': 'Application submitted to external site'}
            
        except Exception as e:
            logger.error(f"Error filling generic form: {e}")
            return {'success': False, 'error': str(e)}

# Celery Tasks
@celery_app.task(bind=True, max_retries=3)
def apply_to_job(self, user_id: int, job_id: str, job_url: str):
    """
    Apply to a job automatically
    
    Args:
        user_id: ID of the user applying
        job_id: ID of the job
        job_url: URL of the job posting
    """
    try:
        # Update task status
        current_task.update_state(state='PROGRESS', meta={'status': 'Starting application process'})
        
        # Get user profile
        from src.main import db
        user = User.query.get(user_id)
        if not user:
            raise Exception(f"User {user_id} not found")
        
        user_profile_obj = UserProfile.query.filter_by(user_id=user_id).first()
        if not user_profile_obj:
            raise Exception(f"User profile for {user_id} not found")
        
        # Build user profile for application
        user_profile = {
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'address': user.address,
            'zip_code': user.zip_code,
            'resume_path': None  # Would be set if resume file exists
        }
        
        current_task.update_state(state='PROGRESS', meta={'status': 'Initializing browser'})
        
        # Initialize application bot
        bot = JobApplicationBot(headless=True)
        
        # Determine job board and apply accordingly
        if 'indeed.com' in job_url:
            result = bot.apply_to_indeed_job(job_url, user_profile)
        else:
            result = bot.apply_to_external_site(job_url, user_profile)
        
        # Record application in database
        application = JobApplication(
            user_id=user_id,
            job_id=job_id,
            job_url=job_url,
            status='submitted' if result['success'] else 'failed',
            applied_at=datetime.utcnow(),
            application_method='automated',
            notes=result.get('message', result.get('error', ''))
        )
        
        db.session.add(application)
        db.session.commit()
        
        if result['success']:
            current_task.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Application submitted successfully',
                    'application_id': application.id,
                    'message': result['message']
                }
            )
        else:
            current_task.update_state(
                state='FAILURE',
                meta={
                    'status': 'Application failed',
                    'error': result['error']
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in apply_to_job task: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'status': 'Task failed', 'error': str(e)}
        )
        raise self.retry(countdown=60, exc=e)

@celery_app.task(bind=True)
def scrape_job_details(self, job_url: str):
    """
    Scrape additional job details from job posting
    
    Args:
        job_url: URL of the job posting
    """
    try:
        current_task.update_state(state='PROGRESS', meta={'status': 'Scraping job details'})
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(job_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract job details (this would be customized for each job board)
        job_details = {
            'title': '',
            'company': '',
            'location': '',
            'description': '',
            'requirements': [],
            'salary': '',
            'job_type': '',
            'posted_date': ''
        }
        
        # Indeed-specific scraping
        if 'indeed.com' in job_url:
            job_details = scrape_indeed_job(soup)
        # Add other job boards as needed
        
        current_task.update_state(
            state='SUCCESS',
            meta={'status': 'Job details scraped successfully', 'job_details': job_details}
        )
        
        return job_details
        
    except Exception as e:
        logger.error(f"Error scraping job details: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'status': 'Scraping failed', 'error': str(e)}
        )
        return {'error': str(e)}

def scrape_indeed_job(soup):
    """Scrape job details from Indeed"""
    job_details = {}
    
    try:
        # Job title
        title_elem = soup.find('h1', class_='jobsearch-JobInfoHeader-title')
        job_details['title'] = title_elem.get_text(strip=True) if title_elem else ''
        
        # Company name
        company_elem = soup.find('span', class_='jobsearch-InlineCompanyRating-companyName')
        job_details['company'] = company_elem.get_text(strip=True) if company_elem else ''
        
        # Location
        location_elem = soup.find('div', {'data-testid': 'job-location'})
        job_details['location'] = location_elem.get_text(strip=True) if location_elem else ''
        
        # Job description
        desc_elem = soup.find('div', {'id': 'jobDescriptionText'})
        job_details['description'] = desc_elem.get_text(strip=True) if desc_elem else ''
        
        # Salary
        salary_elem = soup.find('span', class_='jobsearch-JobMetadataHeader-item')
        job_details['salary'] = salary_elem.get_text(strip=True) if salary_elem else ''
        
    except Exception as e:
        logger.error(f"Error parsing Indeed job: {e}")
    
    return job_details

@celery_app.task
def send_notification(user_id: int, message: str, notification_type: str = 'info'):
    """
    Send notification to user (email, SMS, etc.)
    
    Args:
        user_id: ID of the user
        message: Notification message
        notification_type: Type of notification (info, success, error)
    """
    try:
        # In production, this would send actual notifications
        # For now, just log the notification
        logger.info(f"Notification for user {user_id}: {message} (type: {notification_type})")
        
        # Here you would integrate with email service, SMS service, etc.
        # Example: send_email(user.email, subject, message)
        
        return {'success': True, 'message': 'Notification sent'}
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return {'success': False, 'error': str(e)}

@celery_app.task
def process_application_queue():
    """
    Process pending applications in the queue
    """
    try:
        from src.main import db
        
        # Get pending applications
        pending_applications = ApplicationQueue.query.filter_by(
            status='pending'
        ).order_by(ApplicationQueue.created_at).limit(10).all()
        
        for queue_item in pending_applications:
            # Mark as processing
            queue_item.status = 'processing'
            queue_item.started_at = datetime.utcnow()
            db.session.commit()
            
            # Start application task
            apply_to_job.delay(
                queue_item.user_id,
                queue_item.job_id,
                queue_item.job_url
            )
            
            # Mark as queued for processing
            queue_item.status = 'queued'
            db.session.commit()
        
        return {'processed': len(pending_applications)}
        
    except Exception as e:
        logger.error(f"Error processing application queue: {e}")
        return {'error': str(e)}

@celery_app.task
def cleanup_old_tasks():
    """
    Clean up old completed tasks and logs
    """
    try:
        # Clean up old application records (older than 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        from src.main import db
        old_applications = JobApplication.query.filter(
            JobApplication.applied_at < cutoff_date,
            JobApplication.status.in_(['failed', 'rejected'])
        ).all()
        
        for app in old_applications:
            db.session.delete(app)
        
        db.session.commit()
        
        return {'cleaned_up': len(old_applications)}
        
    except Exception as e:
        logger.error(f"Error cleaning up old tasks: {e}")
        return {'error': str(e)}

