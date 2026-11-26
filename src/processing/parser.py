"""
Configuration and Profile Parser
"""

import yaml
import os
from typing import Dict, Any

def load_profile(profile_path: str = None) -> Dict[str, Any]:
    if profile_path is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        profile_path = os.path.join(project_root, 'config', 'profile.yaml')
    
    with open(profile_path, 'r', encoding='utf-8') as f:
        profile = yaml.safe_load(f)
    
    return profile.get('candidate', {})

def load_search_queries(queries_path: str = None) -> Dict[str, Any]:
    if queries_path is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        queries_path = os.path.join(project_root, 'config', 'search_queries.yaml')
    
    with open(queries_path, 'r', encoding='utf-8') as f:
        queries = yaml.safe_load(f)
    
    return queries