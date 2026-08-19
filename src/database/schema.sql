CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_job_id TEXT,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    normalized_title TEXT,
    location TEXT,
    normalized_location TEXT,
    remote INTEGER DEFAULT 0,
    employment_type TEXT,
    description TEXT,
    skills TEXT,
    url TEXT UNIQUE NOT NULL,
    company_url TEXT,
    posted_at TEXT,
    discovered_at TEXT,
    last_seen_at TEXT,
    first_seen_at TEXT,
    match_score REAL DEFAULT 0.0,
    match_reasons TEXT,
    status TEXT DEFAULT 'NEW',
    raw_data TEXT
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL,
    status_changed_at TEXT,
    applied_at TEXT,
    notes TEXT,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs(match_score);
