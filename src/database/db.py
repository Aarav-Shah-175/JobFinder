import os
import sqlite3
import json
import hashlib
from typing import List, Dict, Any, Optional
from src.utils.dates import get_utc_now_iso

class DatabaseManager:
    def __init__(self, db_path: str = "data/jobs.db", json_path: str = "data/jobs.json"):
        self.db_path = db_path
        self.json_path = json_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
        self._sync_from_json()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
        with self._get_connection() as conn:
            conn.executescript(sql_script)

    def _sync_from_json(self):
        """Loads persistent JSON data into SQLite if DB is empty or missing records."""
        if not os.path.exists(self.json_path):
            return
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                jobs = json.load(f)
            if not isinstance(jobs, list):
                return
            with self._get_connection() as conn:
                for job in jobs:
                    conn.execute("""
                        INSERT OR IGNORE INTO jobs (
                            id, source, source_job_id, company, title, normalized_title,
                            location, normalized_location, remote, employment_type,
                            description, skills, url, company_url, posted_at,
                            discovered_at, last_seen_at, first_seen_at, match_score,
                            match_reasons, status, raw_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        job.get("id"),
                        job.get("source"),
                        job.get("source_job_id"),
                        job.get("company"),
                        job.get("title"),
                        job.get("normalized_title"),
                        job.get("location"),
                        job.get("normalized_location"),
                        1 if job.get("remote") else 0,
                        job.get("employment_type"),
                        job.get("description"),
                        json.dumps(job.get("skills", [])),
                        job.get("url"),
                        job.get("company_url"),
                        job.get("posted_at"),
                        job.get("discovered_at"),
                        job.get("last_seen_at"),
                        job.get("first_seen_at"),
                        job.get("match_score", 0.0),
                        json.dumps(job.get("match_reasons", {})),
                        job.get("status", "NEW"),
                        json.dumps(job.get("raw_data", {}))
                    ))
                conn.commit()
        except Exception as e:
            print(f"Error syncing from JSON: {e}")

    def export_to_json(self):
        """Exports all jobs from SQLite into canonical jobs.json for GitHub Actions persistence."""
        jobs = self.get_all_jobs()
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2)

    def generate_job_id(self, company: str, title: str, url: str) -> str:
        raw_key = f"{company.strip().lower()}:{title.strip().lower()}:{url.strip().lower()}"
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()[:16]

    def get_job_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE url = ?", (url,)).fetchone()
            if row:
                d = dict(row)
                d["skills"] = json.loads(d["skills"]) if d.get("skills") else []
                d["match_reasons"] = json.loads(d["match_reasons"]) if d.get("match_reasons") else {}
                d["raw_data"] = json.loads(d["raw_data"]) if d.get("raw_data") else {}
                return d
        return None

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY match_score DESC").fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["skills"] = json.loads(d["skills"]) if d.get("skills") else []
                d["match_reasons"] = json.loads(d["match_reasons"]) if d.get("match_reasons") else {}
                d["raw_data"] = json.loads(d["raw_data"]) if d.get("raw_data") else {}
                result.append(d)
            return result

    def upsert_job(self, job: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """
        Upserts job record into DB.
        Returns tuple: (is_new: bool, final_job_dict: Dict)
        """
        now = get_utc_now_iso()
        existing = self.get_job_by_url(job["url"])

        job_id = job.get("id") or self.generate_job_id(job["company"], job["title"], job["url"])
        job["id"] = job_id

        if existing:
            # Job was previously seen! Update last_seen_at and score/status if applicable
            is_new = False
            # Preserve existing user status (e.g., APPLIED, OA, REJECTED)
            preserved_status = existing.get("status", "NEW")
            # If status was OLD or NEW, keep track
            first_seen = existing.get("first_seen_at", now)

            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE jobs SET
                        last_seen_at = ?,
                        match_score = ?,
                        match_reasons = ?,
                        description = ?,
                        skills = ?
                    WHERE id = ?
                """, (
                    now,
                    job.get("match_score", existing.get("match_score", 0.0)),
                    json.dumps(job.get("match_reasons", existing.get("match_reasons", {}))),
                    job.get("description", existing.get("description", "")),
                    json.dumps(job.get("skills", existing.get("skills", []))),
                    job_id
                ))
                conn.commit()

            updated_job = self.get_job_by_url(job["url"])
            return False, updated_job
        else:
            # Entirely NEW job
            is_new = True
            first_seen = now
            job["discovered_at"] = job.get("discovered_at") or now
            job["first_seen_at"] = first_seen
            job["last_seen_at"] = now
            job["status"] = job.get("status") or "NEW"

            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO jobs (
                        id, source, source_job_id, company, title, normalized_title,
                        location, normalized_location, remote, employment_type,
                        description, skills, url, company_url, posted_at,
                        discovered_at, last_seen_at, first_seen_at, match_score,
                        match_reasons, status, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job["id"],
                    job.get("source", "unknown"),
                    job.get("source_job_id", ""),
                    job.get("company", ""),
                    job.get("title", ""),
                    job.get("normalized_title", ""),
                    job.get("location", ""),
                    job.get("normalized_location", ""),
                    1 if job.get("remote") else 0,
                    job.get("employment_type", "Full-time"),
                    job.get("description", ""),
                    json.dumps(job.get("skills", [])),
                    job["url"],
                    job.get("company_url", ""),
                    job.get("posted_at", now[:10]),
                    job["discovered_at"],
                    job["last_seen_at"],
                    job["first_seen_at"],
                    job.get("match_score", 0.0),
                    json.dumps(job.get("match_reasons", {})),
                    job["status"],
                    json.dumps(job.get("raw_data", {}))
                ))
                conn.commit()

            new_job = self.get_job_by_url(job["url"])
            return True, new_job

    def update_job_status(self, job_id: str, status: str, notes: str = ""):
        now = get_utc_now_iso()
        with self._get_connection() as conn:
            conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
            conn.execute("""
                INSERT INTO applications (job_id, status, status_changed_at, applied_at, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, status, now, now if status == 'APPLIED' else None, notes))
            conn.commit()
        self.export_to_json()
