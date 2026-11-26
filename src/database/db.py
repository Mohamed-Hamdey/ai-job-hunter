"""
SQLite Database Manager
"""

import sqlite3
import os
from typing import List, Dict, Any
from datetime import datetime

class JobDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, 'data', 'jobs.db')
        self.db_path = db_path
        self.conn = None
    
    def initialize(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_job_id TEXT,
                job_key TEXT UNIQUE NOT NULL,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT,
                work_mode TEXT,
                description TEXT,
                job_url TEXT,
                application_url TEXT,
                published_at TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                seniority TEXT,
                experience_required TEXT,
                matched_skills TEXT,
                missing_skills TEXT,
                match_score REAL,
                match_explanation TEXT,
                eligibility_status TEXT DEFAULT 'needs_verification',
                status TEXT DEFAULT 'new',
                notified_at TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_key ON jobs(job_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notified ON jobs(notified_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_score ON jobs(match_score)")
        self.conn.commit()
    
    def upsert_job(self, job: Dict[str, Any]) -> bool:
        cursor = self.conn.cursor()
        now = datetime.utcnow().isoformat()
        
        cursor.execute("SELECT id FROM jobs WHERE job_key = ?", (job['job_key'],))
        existing = cursor.fetchone()
        is_new = existing is None
        
        if is_new:
            cursor.execute("""
                INSERT INTO jobs (
                    source, source_job_id, job_key, company, title,
                    location, work_mode, description, job_url, application_url,
                    published_at, first_seen_at, last_seen_at, seniority,
                    experience_required, matched_skills, missing_skills,
                    match_score, match_explanation, eligibility_status,
                    status, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.get('source', ''), job.get('source_job_id'), job['job_key'],
                job.get('company', ''), job.get('title', ''), job.get('location', ''),
                job.get('work_mode', ''), job.get('description', ''), job.get('job_url', ''),
                job.get('application_url', ''), job.get('published_at'),
                job.get('first_seen_at', now), job.get('last_seen_at', now),
                job.get('seniority', ''), job.get('experience_required'),
                ','.join(job.get('matched_skills', [])),
                ','.join(job.get('missing_skills', [])),
                job.get('match_score', 0), job.get('match_explanation', ''),
                job.get('eligibility_status', 'needs_verification'), 'new', 1, now, now
            ))
        else:
            job_id = existing['id']
            cursor.execute("""
                UPDATE jobs SET
                    last_seen_at = ?, description = ?, match_score = ?,
                    match_explanation = ?, matched_skills = ?, missing_skills = ?,
                    eligibility_status = ?, is_active = 1, updated_at = ?
                WHERE id = ?
            """, (
                now, job.get('description', ''), job.get('match_score', 0),
                job.get('match_explanation', ''),
                ','.join(job.get('matched_skills', [])),
                ','.join(job.get('missing_skills', [])),
                job.get('eligibility_status', 'needs_verification'), now, job_id
            ))
        
        self.conn.commit()
        return is_new
    
    def get_qualifying_jobs(self, min_score: float = 70.0) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM jobs
            WHERE notified_at IS NULL AND match_score >= ? AND is_active = 1
            ORDER BY match_score DESC, first_seen_at ASC
        """, (min_score,))
        
        rows = cursor.fetchall()
        jobs = [dict(row) for row in rows]
        
        for job in jobs:
            job['matched_skills'] = job['matched_skills'].split(',') if job.get('matched_skills') else []
            job['missing_skills'] = job['missing_skills'].split(',') if job.get('missing_skills') else []
        
        return jobs
    
    def mark_as_notified(self, job_id: int):
        cursor = self.conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute("UPDATE jobs SET notified_at = ?, updated_at = ? WHERE id = ?", (now, now, job_id))
        self.conn.commit()
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()