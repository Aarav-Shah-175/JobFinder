import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
from typing import List, Dict, Any

from src.config import get_config
from src.database.db import DatabaseManager
from src.processing.normalize import normalize_job_dict
from src.processing.deduplicate import deduplicate_jobs
from src.processing.scoring import score_job
from src.collectors.greenhouse import GreenhouseCollector
from src.collectors.lever import LeverCollector
from src.collectors.ashby import AshbyCollector
from src.collectors.workable import WorkableCollector
from src.collectors.hackernews import HackerNewsCollector
from src.collectors.rss import RSSCollector
from src.reporting.markdown import generate_markdown_report
from src.reporting.csv import export_applications_csv
from src.reporting.github_summary import write_github_step_summary
from src.notifications.telegram import send_telegram_notification
from src.notifications.email_notifier import send_email_notification
from src.utils.logging import setup_logger

def run_pipeline(config_dir: str = "config") -> Dict[str, Any]:
    logger = setup_logger("job_finder_main")
    logger.info("Initializing Aarav's Personal Job Intelligence System...")

    config = get_config(config_dir)
    db = DatabaseManager()

    # 1. Initialize Collectors based on sources.yaml
    sources_cfg = config.sources.get("sources", {})
    collectors = []

    if sources_cfg.get("greenhouse", {}).get("enabled", True):
        collectors.append(GreenhouseCollector(sources_cfg.get("greenhouse", {}).get("rate_limit_delay_seconds", 1.0)))

    if sources_cfg.get("lever", {}).get("enabled", True):
        collectors.append(LeverCollector(sources_cfg.get("lever", {}).get("rate_limit_delay_seconds", 1.0)))

    if sources_cfg.get("ashby", {}).get("enabled", True):
        collectors.append(AshbyCollector(sources_cfg.get("ashby", {}).get("rate_limit_delay_seconds", 1.0)))

    if sources_cfg.get("workable", {}).get("enabled", True):
        collectors.append(WorkableCollector(sources_cfg.get("workable", {}).get("rate_limit_delay_seconds", 1.0)))

    if sources_cfg.get("hackernews", {}).get("enabled", True):
        collectors.append(HackerNewsCollector(sources_cfg.get("hackernews", {}).get("rate_limit_delay_seconds", 0.5)))

    if sources_cfg.get("rss", {}).get("enabled", True):
        collectors.append(RSSCollector(sources_cfg.get("rss", {}).get("rate_limit_delay_seconds", 0.5)))

    raw_jobs: List[Dict[str, Any]] = []
    source_statuses: Dict[str, str] = {}

    # 2. Run Job Discovery across Collectors safely
    for collector in collectors:
        try:
            logger.info(f"Running collector: {collector.name}...")
            jobs = collector.fetch_jobs()
            raw_jobs.extend(jobs)
            source_statuses[collector.name] = f"✓ {len(jobs)} jobs discovered"
            logger.info(f"Collector {collector.name} completed successfully with {len(jobs)} jobs.")
        except Exception as e:
            logger.error(f"Collector {collector.name} encountered error: {e}")
            source_statuses[collector.name] = f"✗ Failed ({e})"

    logger.info(f"Total raw jobs collected: {len(raw_jobs)}")

    # 3. Normalization
    normalized_jobs = [normalize_job_dict(j) for j in raw_jobs]

    # 4. Deduplication
    unique_jobs = deduplicate_jobs(normalized_jobs)
    logger.info(f"Unique jobs after deduplication: {len(unique_jobs)}")

    # 5. Scoring & Eligibility Filtering
    scored_jobs = []
    new_jobs_today = []

    for job in unique_jobs:
        scoring_res = score_job(job, db=db)
        job.update(scoring_res)

        is_new, updated_job = db.upsert_job(job)

        if updated_job:
            scored_jobs.append(updated_job)
            if is_new:
                new_jobs_today.append(updated_job)

    db.export_to_json()

    scored_jobs.sort(key=lambda x: x.get("match_score", 0.0), reverse=True)
    new_jobs_today.sort(key=lambda x: x.get("match_score", 0.0), reverse=True)

    top_matches = [j for j in new_jobs_today if j.get("match_score", 0.0) >= 80.0]

    stats = {
        "raw_count": len(raw_jobs),
        "unique_count": len(unique_jobs),
        "new_count": len(new_jobs_today),
        "top_matches_count": len(top_matches)
    }

    # 6. Generate Reports & Notifications
    md_file = generate_markdown_report(new_jobs_today if new_jobs_today else scored_jobs, stats, source_statuses)
    csv_file = export_applications_csv(scored_jobs)
    write_github_step_summary(stats, top_matches)

    # Optional Free Notifications
    send_telegram_notification(top_matches)
    send_email_notification(top_matches, md_file)

    logger.info("Pipeline execution finished successfully.")
    logger.info(f"Markdown Report: {md_file}")
    logger.info(f"CSV Export: {csv_file}")

    return {
        "stats": stats,
        "scored_jobs": scored_jobs,
        "new_jobs": new_jobs_today,
        "top_matches": top_matches,
        "markdown_report": md_file,
        "csv_export": csv_file
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aarav's Personal Job Intelligence System CLI")
    parser.add_argument("--config", default="config", help="Path to config directory")
    args = parser.parse_args()

    run_pipeline(args.config)
