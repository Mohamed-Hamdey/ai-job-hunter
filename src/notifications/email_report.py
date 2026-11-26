"""
Email Report Generator
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime

class EmailReporter:
    def __init__(self):
        self.smtp_host = 'smtp.gmail.com'
        self.smtp_port = 587
        self.sender_email = os.getenv('GMAIL_ADDRESS')
        self.app_password = os.getenv('GMAIL_APP_PASSWORD')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')
    
    def send_report(self, jobs: List[Dict[str, Any]]) -> bool:
        if not jobs:
            return True
        
        try:
            subject = self._generate_subject(jobs)
            html_body = self._generate_html_body(jobs)
            text_body = self._generate_text_body(jobs)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.ehlo()
            server.starttls()
            server.login(self.sender_email, self.app_password)
            server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
            server.quit()
            
            print(f"Email sent successfully to {self.recipient_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def _generate_subject(self, jobs: List[Dict[str, Any]]) -> str:
        date_str = datetime.now().strftime('%d %B %Y')
        return f"AI Job Hunter | {len(jobs)} New Matches | {date_str}"
    
    def _generate_html_body(self, jobs: List[Dict[str, Any]]) -> str:
        date_str = datetime.now().strftime('%d %B %Y')
        excellent = sum(1 for j in jobs if j.get('match_score', 0) >= 85)
        strong = sum(1 for j in jobs if 70 <= j.get('match_score', 0) < 85)
        needs_verification = sum(1 for j in jobs if j.get('eligibility_status') == 'needs_verification')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .job-card {{ border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; }}
        .score-excellent {{ color: #27ae60; font-weight: bold; }}
        .score-strong {{ color: #2980b9; font-weight: bold; }}
        .meta {{ color: #7f8c8d; font-size: 0.9em; }}
        .skills {{ background-color: #e8f6f3; padding: 5px 10px; border-radius: 3px; display: inline-block; margin: 2px; }}
        .missing {{ background-color: #fadbd8; padding: 5px 10px; border-radius: 3px; display: inline-block; margin: 2px; }}
        .button {{ display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 3px; margin: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AI JOB HUNTER</h1>
        <p>Daily Opportunities — {date_str}</p>
    </div>
    
    <div class="summary">
        <strong>New jobs:</strong> {len(jobs)}<br>
        <strong>Excellent matches (85-100):</strong> {excellent}<br>
        <strong>Strong matches (70-84):</strong> {strong}<br>
        <strong>Needs eligibility verification:</strong> {needs_verification}
    </div>
"""
        
        for i, job in enumerate(jobs, 1):
            score = job.get('match_score', 0)
            score_class = 'score-excellent' if score >= 85 else 'score-strong'
            matched_skills = ''.join([f'<span class="skills">{s}</span>' for s in job.get('matched_skills', [])])
            missing_skills = ''.join([f'<span class="missing">{s}</span>' for s in job.get('missing_skills', [])])
            
            html += f"""
    <div class="job-card">
        <h2>{i}. {job.get('title', 'Unknown')}</h2>
        <p><strong>Company:</strong> {job.get('company', 'Unknown')}</p>
        <p class="{score_class}">Match: {score:.0f}/100</p>
        <p class="meta">
            <strong>Location:</strong> {job.get('location', 'Unknown')} | 
            <strong>Work Mode:</strong> {job.get('work_mode', 'Unknown')} | 
            <strong>Seniority:</strong> {job.get('seniority', 'Unknown')}
        </p>
        <p class="meta"><strong>Eligibility:</strong> {job.get('eligibility_status', 'Unknown')}</p>
        
        <p><strong>Matched Skills:</strong><br>{matched_skills or 'None identified'}</p>
        <p><strong>Missing Skills:</strong><br>{missing_skills or 'None identified'}</p>
        
        <p><strong>Why it matches:</strong><br>{job.get('match_explanation', 'No explanation available')}</p>
        
        <a href="{job.get('job_url', '#')}" class="button">View Original Job</a>
        <a href="{job.get('application_url', '#')}" class="button">Apply</a>
    </div>
"""
        
        html += """
    <div style="margin-top: 30px; padding: 15px; background-color: #fef9e7; border-radius: 5px;">
        <p><em>This report contains newly discovered opportunities. Please verify the original vacancy before applying.</em></p>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_text_body(self, jobs: List[Dict[str, Any]]) -> str:
        date_str = datetime.now().strftime('%d %B %Y')
        text = f"AI JOB HUNTER\nDaily Opportunities — {date_str}\n"
        text += "=" * 60 + "\n\n"
        text += f"New jobs: {len(jobs)}\n"
        
        for i, job in enumerate(jobs, 1):
            text += f"{i}. {job.get('title', 'Unknown')}\n"
            text += f"   Company: {job.get('company', 'Unknown')}\n"
            text += f"   Match: {job.get('match_score', 0):.0f}/100\n"
            text += f"   Location: {job.get('location', 'Unknown')}\n"
            text += f"   Work Mode: {job.get('work_mode', 'Unknown')}\n"
            text += f"   Seniority: {job.get('seniority', 'Unknown')}\n"
            text += f"   Eligibility: {job.get('eligibility_status', 'Unknown')}\n"
            text += f"   Matched Skills: {', '.join(job.get('matched_skills', []))}\n"
            text += f"   Missing Skills: {', '.join(job.get('missing_skills', []))}\n"
            text += f"   Why it matches: {job.get('match_explanation', 'N/A')}\n"
            text += f"   View: {job.get('job_url', 'N/A')}\n"
            text += f"   Apply: {job.get('application_url', 'N/A')}\n\n"
            text += "-" * 60 + "\n\n"
        
        text += "This report contains newly discovered opportunities.\n"
        text += "Please verify the original vacancy before applying.\n"
        return text