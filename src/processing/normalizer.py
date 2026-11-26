"""
Job Normalizer
"""

import re
import hashlib
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from datetime import datetime

class JobNormalizer:
    def normalize(self, raw_job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not raw_job:
            return None
        
        try:
            description_html = raw_job.get('description_html', '')
            description_text = self._clean_html(description_html)
            job_key = self._generate_job_key(raw_job)
            location = raw_job.get('location', 'Unknown')
            work_mode = self._extract_work_mode(location, description_text)
            seniority = self._extract_seniority(raw_job.get('title', ''), description_text)
            experience_required = self._extract_experience(description_text)
            
            published_at = raw_job.get('posted_at')
            if published_at:
                published_at = self._parse_date(published_at)
            
            normalized = {
                'source': raw_job.get('source', 'unknown'),
                'source_job_id': raw_job.get('source_job_id'),
                'job_key': job_key,
                'company': raw_job.get('company', 'Unknown'),
                'title': raw_job.get('title', 'Unknown'),
                'location': location,
                'work_mode': work_mode,
                'description': description_text,
                'job_url': raw_job.get('url', ''),
                'application_url': raw_job.get('application_url', raw_job.get('url', '')),
                'published_at': published_at,
                'seniority': seniority,
                'experience_required': experience_required,
                'first_seen_at': datetime.utcnow().isoformat(),
                'last_seen_at': datetime.utcnow().isoformat(),
                'is_active': True
            }
            
            return normalized
            
        except Exception as e:
            print(f"Error normalizing job: {e}")
            return None
    
    def _clean_html(self, html: str) -> str:
        if not html:
            return ''
        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _generate_job_key(self, job: Dict[str, Any]) -> str:
        source = job.get('source', 'unknown')
        if job.get('source_job_id'):
            return f"{source}:{job['source_job_id']}"
        
        company = job.get('company', '').lower().strip()
        title = job.get('title', '').lower().strip()
        url = job.get('url', '')
        key_string = f"{source}:{company}:{title}:{url}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _extract_work_mode(self, location: str, description: str) -> str:
        location_lower = location.lower()
        desc_lower = description.lower()
        
        if 'remote' in location_lower or 'remote' in desc_lower[:500]:
            return 'remote'
        elif 'hybrid' in location_lower or 'hybrid' in desc_lower[:500]:
            return 'hybrid'
        else:
            return 'on-site'
    
    def _extract_seniority(self, title: str, description: str) -> str:
        title_lower = title.lower()
        desc_lower = description.lower()
        
        seniority_keywords = {
            'intern': ['intern', 'internship'],
            'junior': ['junior', 'jr', 'entry level', 'graduate', 'new grad'],
            'mid': ['mid-level', 'mid level'],
            'senior': ['senior', 'sr', 'staff', 'principal', 'lead'],
            'manager': ['manager', 'director']
        }
        
        for level, keywords in seniority_keywords.items():
            for keyword in keywords:
                if keyword in title_lower or keyword in desc_lower[:300]:
                    return level
        
        return 'unknown'
    
    def _extract_experience(self, description: str) -> Optional[str]:
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\s*-\s*(\d+)\s*years?',
            r'experience[:\s]+(\d+)\+?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.isoformat()
        except:
            pass
        try:
            from dateutil import parser as date_parser
            dt = date_parser.parse(date_str)
            return dt.isoformat()
        except:
            pass
        return date_str