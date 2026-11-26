#!/usr/bin/env python3
"""
AI Job Hunter - Main Entry Point
"""

import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('ai_job_hunter')


def main():
    """Main execution flow for AI Job Hunter."""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("AI Job Hunter - Starting daily job search")
    logger.info("=" * 60)
    
    try:
        # Step 1: Initialize database
        logger.info("Step 1: Initializing database...")
        from src.database.db import JobDatabase
        db = JobDatabase()
        db.initialize()
        
        # Step 2: Load candidate profile
        logger.info("Step 2: Loading candidate profile...")
        from src.processing.parser import load_profile
        profile = load_profile()
        
        # Step 3: Discover jobs from sources
        logger.info("Step 3: Discovering jobs from sources...")
        all_jobs = []
        
        # Greenhouse source
        try:
            from src.sources.greenhouse import GreenhouseSource
            greenhouse = GreenhouseSource()
            greenhouse_jobs = greenhouse.fetch_jobs()
            all_jobs.extend(greenhouse_jobs)
            logger.info(f"Found {len(greenhouse_jobs)} jobs from Greenhouse")
        except Exception as e:
            logger.error(f"Error fetching from Greenhouse: {e}")
        
        # Lever source
        try:
            from src.sources.lever import LeverSource
            lever = LeverSource()
            lever_jobs = lever.fetch_jobs()
            all_jobs.extend(lever_jobs)
            logger.info(f"Found {len(lever_jobs)} jobs from Lever")
        except Exception as e:
            logger.error(f"Error fetching from Lever: {e}")
        
        logger.info(f"Total jobs discovered: {len(all_jobs)}")
        
        # Step 4: Normalize and process jobs
        logger.info("Step 4: Normalizing job records...")
        from src.processing.normalizer import JobNormalizer
        normalizer = JobNormalizer()
        normalized_jobs = []
        
        for job in all_jobs:
            try:
                normalized = normalizer.normalize(job)
                if normalized:
                    normalized_jobs.append(normalized)
            except Exception as e:
                logger.warning(f"Failed to normalize job: {e}")
        
        logger.info(f"Successfully normalized {len(normalized_jobs)} jobs")
        
        # Step 5: Score and match jobs against CV
        logger.info("Step 5: Scoring jobs against candidate profile...")
        from src.scoring.matcher import CVMatcher
        matcher = CVMatcher(profile)
        scored_jobs = []
        
        for job in normalized_jobs:
            try:
                score_result = matcher.score_job(job)
                job['match_score'] = score_result['score']
                job['match_explanation'] = score_result['explanation']
                job['matched_skills'] = score_result['matched_skills']
                job['missing_skills'] = score_result['missing_skills']
                scored_jobs.append(job)
            except Exception as e:
                logger.warning(f"Failed to score job: {e}")
        
        logger.info(f"Scored {len(scored_jobs)} jobs")
        
        # Step 6: Store in database with deduplication
        logger.info("Step 6: Storing jobs in database...")
        new_jobs_count = 0
        for job in scored_jobs:
            try:
                is_new = db.upsert_job(job)
                if is_new:
                    new_jobs_count += 1
            except Exception as e:
                logger.error(f"Failed to store job: {e}")
        
        logger.info(f"Stored {new_jobs_count} new jobs")
        
        # Step 7: Select jobs for email notification
        logger.info("Step 7: Selecting jobs for notification...")
        min_score = 70  # Minimum score threshold
        qualifying_jobs = db.get_qualifying_jobs(min_score=min_score)
        
        logger.info(f"Found {len(qualifying_jobs)} qualifying jobs for notification")
        
        # Step 8: Send email report if there are qualifying jobs
        if qualifying_jobs:
            logger.info("Step 8: Sending email report...")
            from src.notifications.email_report import EmailReporter
            reporter = EmailReporter()
            success = reporter.send_report(qualifying_jobs)
            
            if success:
                for job in qualifying_jobs:
                    db.mark_as_notified(job['id'])
                logger.info("Email sent successfully and jobs marked as notified")
            else:
                logger.warning("Email delivery failed - jobs will be retried next run")
        else:
            logger.info("No qualifying jobs to report")
        
        # Step 9: Generate run summary
        logger.info("=" * 60)
        logger.info("Run Summary:")
        logger.info(f"  Total jobs discovered: {len(all_jobs)}")
        logger.info(f"  Successfully normalized: {len(normalized_jobs)}")
        logger.info(f"  Successfully scored: {len(scored_jobs)}")
        logger.info(f"  New jobs stored: {new_jobs_count}")
        logger.info(f"  Qualifying for notification: {len(qualifying_jobs)}")
        logger.info("=" * 60)
        logger.info("AI Job Hunter - Completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()