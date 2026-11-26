"""
Location and Eligibility Filter
"""

import re
from typing import Dict, Any

class LocationFilter:
    ELIGIBLE_LOCATIONS = [
        'egypt', 'cairo', 'giza', 'alexandria', 'new cairo', 
        'maadi', 'smart village', '6th of october'
    ]
    
    def check_eligibility(self, job: Dict[str, Any]) -> str:
        location = job.get('location', '').lower()
        work_mode = job.get('work_mode', '').lower()
        description = job.get('description', '').lower()
        
        if self._is_egypt_location(location):
            return 'eligible'
        
        if work_mode == 'remote':
            return self._check_remote_eligibility(description)
        
        if self._mentions_relocation(description):
            return 'needs_verification'
        
        if not location or location == 'unknown':
            return 'needs_verification'
        
        return 'ineligible'
    
    def _is_egypt_location(self, location: str) -> bool:
        for eligible in self.ELIGIBLE_LOCATIONS:
            if eligible in location:
                return True
        return False
    
    def _check_remote_eligibility(self, description: str) -> str:
        restriction_patterns = [
            r'must be located in\s+([^(Egypt)]+)',
            r'restricted to\s+([^(Egypt)]+)',
            r'only open to\s+([^(Egypt)]+)',
            r'(US|USA|United States|UK|Europe|EU)\s+(residents|citizens|based)'
        ]
        
        for pattern in restriction_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return 'ineligible'
        
        if re.search(r'(EST|PST|CST|MST|GMT[-+]\d)', description, re.IGNORECASE):
            return 'needs_verification'
        
        return 'needs_verification'
    
    def _mentions_relocation(self, description: str) -> bool:
        relocation_keywords = ['relocation', 'visa sponsorship', 'work permit', 'relocate']
        for keyword in relocation_keywords:
            if keyword in description.lower():
                return True
        return False