import sys
import os
import argparse
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.db import DatabaseManager

# Fix stdout encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

VALID_STATUSES = ["NEW", "SAVED", "APPLIED", "OA", "INTERVIEW", "REJECTED", "OFFER", "IGNORED"]

def list_jobs(db: DatabaseManager, status_filter: str = None, min_score: float = 65.0):
    jobs = db.get_all_jobs()
    if status_filter:
        jobs = [j for j in jobs if j.get("status") == status_filter.upper()]

    jobs = [j for j in jobs if j.get("match_score", 0) >= min_score]

    print(f"\n===============================================================================")
    print(f"               AARAV'S JOB APPLICATIONS TRACKER ({len(jobs)} jobs)")
    print(f"===============================================================================\n")

    for j in jobs[:20]:
        print(f"[{j.get('id')}] {j.get('company')} — {j.get('title')}")
        print(f"  Score: {j.get('match_score')}/100 | Status: [{j.get('status')}] | Loc: {j.get('normalized_location')}")
        print(f"  URL: {j.get('url')}")
        if j.get("match_reasons", {}).get("why"):
            print(f"  Highlights: {j['match_reasons']['why'][0]}")
        print("-" * 75)

def update_status(db: DatabaseManager, job_id: str, status: str, notes: str = ""):
    status_upper = status.upper()
    if status_upper not in VALID_STATUSES:
        print(f"Error: Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}")
        return

    db.update_job_status(job_id, status_upper, notes)
    print(f"✓ Job [{job_id}] updated to status: {status_upper}")

def show_analytics(db: DatabaseManager):
    jobs = db.get_all_jobs()
    counts = {st: 0 for st in VALID_STATUSES}
    for j in jobs:
        st = j.get("status", "NEW")
        counts[st] = counts.get(st, 0) + 1

    total = len(jobs)
    applied_count = counts["APPLIED"] + counts["OA"] + counts["INTERVIEW"] + counts["OFFER"] + counts["REJECTED"]

    print("\n===============================================================================")
    print("                     APPLICATION FUNNEL ANALYTICS")
    print("===============================================================================\n")
    print(f"Total Discovered Jobs : {total}")
    print(f"Newly Shortlisted     : {counts['NEW']}")
    print(f"Saved Jobs            : {counts['SAVED']}")
    print(f"Applications Sent     : {counts['APPLIED']}")
    print(f"Online Assessments    : {counts['OA']}")
    print(f"Interviews            : {counts['INTERVIEW']}")
    print(f"Offers                : {counts['OFFER']}")
    print(f"Rejections            : {counts['REJECTED']}")
    print(f"Ignored               : {counts['IGNORED']}")
    print("-" * 75)
    if total > 0:
        print(f"Application Rate       : {(applied_count/total)*100:.1f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aarav's Job Application Tracker")
    parser.add_argument("--list", action="store_true", help="List tracked jobs")
    parser.add_argument("--status", help="Filter by status (NEW, SAVED, APPLIED, OA, INTERVIEW, etc.)")
    parser.add_argument("--min-score", type=float, default=60.0, help="Minimum score filter")
    parser.add_argument("--update", help="Job ID to update status")
    parser.add_argument("--set-status", help="New status for specified job ID")
    parser.add_argument("--notes", default="", help="Optional notes for status update")
    parser.add_argument("--stats", action="store_true", help="Show application funnel analytics")

    args = parser.parse_args()
    db = DatabaseManager()

    if args.update and args.set_status:
        update_status(db, args.update, args.set_status, args.notes)
    elif args.stats:
        show_analytics(db)
    else:
        list_jobs(db, status_filter=args.status, min_score=args.min_score)
