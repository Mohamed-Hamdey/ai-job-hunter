"""
CV Matching Engine
"""

import re
from typing import Dict, Any, List

class CVMatcher:
    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        self.skills = self._extract_all_skills(profile)
        self.target_titles = [
            'ai engineer', 'machine learning engineer', 'ml engineer',
            'deep learning engineer', 'computer vision engineer',
            'nlp engineer', 'applied ai engineer', 'ai developer',
            'llm engineer', 'generative ai engineer', 'rag developer'
        ]
        self.adjacent_titles = ['python developer', 'software engineer', 'data scientist']
    
    def _extract_all_skills(self, profile: Dict[str, Any]) -> set:
        skills = set()
        tech_skills = profile.get('technical_skills', {})
        for category, skill_list in tech_skills.items():
            if isinstance(skill_list, list):
                for skill in skill_list:
                    skills.add(skill.lower())
        return skills
    
    def score_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        title_score = self._score_title_relevance(job)
        skills_score = self._score_skills_match(job)
        experience_score = self._score_experience_compatibility(job)
        location_score = self._score_location_eligibility(job)
        freshness_score = self._score_freshness(job)
        project_score = self._score_project_relevance(job)
        
        total_score = min(title_score + skills_score + experience_score + 
                         location_score + freshness_score + project_score, 100)
        
        explanation = self._generate_explanation(job, title_score, skills_score, 
                                                experience_score, location_score, 
                                                freshness_score, project_score)
        
        return {
            'score': total_score,
            'explanation': explanation,
            'matched_skills': self._get_matched_skills(job),
            'missing_skills': self._get_missing_skills(job),
            'breakdown': {
                'title': title_score, 'skills': skills_score,
                'experience': experience_score, 'location': location_score,
                'freshness': freshness_score, 'project': project_score
            }
        }
    
    def _score_title_relevance(self, job: Dict[str, Any]) -> int:
        title = job.get('title', '').lower()
        for target in self.target_titles:
            if target in title:
                return 25
        for adjacent in self.adjacent_titles:
            if adjacent in title:
                desc = job.get('description', '').lower()
                if any(kw in desc for kw in ['machine learning', 'ai', 'deep learning']):
                    return 15
                else:
                    return 5
        return 0
    
    def _score_skills_match(self, job: Dict[str, Any]) -> int:
        description = job.get('description', '').lower()
        required_skills = self._extract_required_skills(description)
        if not required_skills:
            return 15
        
        matched = sum(1 for skill in required_skills if skill in self.skills)
        total = len(required_skills)
        return int((matched / total) * 30) if total > 0 else 15
    
    def _extract_required_skills(self, description: str) -> set:
        tech_keywords = [
            'python', 'java', 'c++', 'sql', 'tensorflow', 'keras',
            'pytorch', 'scikit-learn', 'opencv', 'numpy', 'pandas',
            'machine learning', 'deep learning', 'nlp', 'computer vision',
            'aws', 'docker', 'kubernetes', 'git', 'flask', 'django'
        ]
        return {kw for kw in tech_keywords if kw in description}
    
    def _score_experience_compatibility(self, job: Dict[str, Any]) -> int:
        seniority = job.get('seniority', 'unknown').lower()
        if seniority in ['intern', 'junior']:
            return 15
        elif seniority == 'mid':
            return 10
        elif seniority in ['senior', 'manager']:
            return 0
        else:
            description = job.get('description', '').lower()
            if any(kw in description for kw in ['junior', 'entry level', 'graduate']):
                return 12
            elif any(kw in description for kw in ['senior', 'lead', 'principal']):
                return 2
            else:
                return 8
    
    def _score_location_eligibility(self, job: Dict[str, Any]) -> int:
        from src.processing.location_filter import LocationFilter
        filter_obj = LocationFilter()
        eligibility = filter_obj.check_eligibility(job)
        
        if eligibility == 'eligible':
            return 15
        elif eligibility == 'needs_verification':
            return 8
        else:
            return 0
    
    def _score_freshness(self, job: Dict[str, Any]) -> int:
        published_at = job.get('published_at')
        if not published_at:
            return 5
        
        try:
            from datetime import datetime
            pub_date = datetime.fromisoformat(published_at)
            days_old = (datetime.utcnow() - pub_date).days
            
            if days_old <= 3: return 10
            elif days_old <= 7: return 7
            elif days_old <= 14: return 5
            elif days_old <= 30: return 3
            else: return 1
        except:
            return 5
    
    def _score_project_relevance(self, job: Dict[str, Any]) -> int:
        description = job.get('description', '').lower()
        project_keywords = {
            'yolo': ['yolo', 'object detection', 'vehicle detection'],
            'ocr': ['ocr', 'optical character recognition', 'text extraction'],
            'computer_vision': ['computer vision', 'image processing', 'opencv'],
            'rag': ['rag', 'retrieval augmented', 'retrieval-augmented'],
            'nlp': ['nlp', 'natural language', 'text processing'],
            'anomaly_detection': ['anomaly detection', 'network traffic']
        }
        
        matched_projects = sum(1 for project, keywords in project_keywords.items() 
                              if any(kw in description for kw in keywords))
        
        if matched_projects >= 3: return 5
        elif matched_projects >= 2: return 4
        elif matched_projects >= 1: return 3
        else: return 1
    
    def _get_matched_skills(self, job: Dict[str, Any]) -> List[str]:
        description = job.get('description', '').lower()
        required_skills = self._extract_required_skills(description)
        return [skill.title() for skill in required_skills if skill in self.skills]
    
    def _get_missing_skills(self, job: Dict[str, Any]) -> List[str]:
        description = job.get('description', '').lower()
        required_skills = self._extract_required_skills(description)
        return [skill.title() for skill in required_skills if skill not in self.skills]
    
    def _generate_explanation(self, job, title_score, skills_score, experience_score, 
                             location_score, freshness_score, project_score) -> str:
        parts = []
        if title_score >= 20:
            parts.append(f"Excellent title match for '{job.get('title', '')}'")
        elif title_score >= 10:
            parts.append(f"Good title relevance for '{job.get('title', '')}'")
        
        if skills_score >= 20:
            parts.append("Strong technical skills overlap")
        elif skills_score >= 10:
            parts.append("Moderate skills match")
        
        if experience_score >= 12:
            parts.append("Well-suited for your experience level")
        
        if location_score == 15:
            parts.append("Location is eligible")
        elif location_score == 8:
            parts.append("Location eligibility needs verification")
        
        if project_score >= 3:
            parts.append("Relevant to your project experience")
        
        return ". ".join(parts) if parts else "Standard match"