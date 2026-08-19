import feedparser
from typing import List, Dict, Any
from src.collectors.base import BaseCollector
from src.config import get_config
from src.utils.text import clean_text, normalize_url
from src.utils.dates import format_date_str

class RSSCollector(BaseCollector):
    def __init__(self, rate_limit_delay: float = 0.5):
        super().__init__("RSS", rate_limit_delay)

    def fetch_jobs_from_feed(self, feed_name: str, feed_url: str) -> List[Dict[str, Any]]:
        self.logger.info(f"Parsing RSS Feed: {feed_name} ({feed_url})...")
        try:
            feed = feedparser.parse(feed_url)
            results = []
            for entry in feed.entries:
                title = entry.get("title", "")
                link = entry.get("link", "")
                published = entry.get("published", entry.get("updated", ""))
                summary = clean_text(entry.get("summary", entry.get("description", "")))
                author = entry.get("author", entry.get("company", "Tech Company"))

                if not title or not link:
                    continue

                results.append({
                    "source": f"RSS ({feed_name})",
                    "source_job_id": entry.get("id", link),
                    "company": author,
                    "title": title,
                    "location": "Remote",
                    "remote": True,
                    "employment_type": "Full-time",
                    "description": summary,
                    "url": normalize_url(link),
                    "company_url": feed_url,
                    "posted_at": format_date_str(published),
                    "raw_data": {"title": title, "link": link, "summary": summary[:200]}
                })
            return results
        except Exception as e:
            self.logger.warning(f"Error parsing RSS feed {feed_name}: {e}")
            return []

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        config = get_config()
        rss_cfg = config.sources.get("sources", {}).get("rss", {})
        feeds = rss_cfg.get("feeds", [])
        all_jobs = []

        for f in feeds:
            f_name = f.get("name", "RSS")
            f_url = f.get("url")
            if f_url:
                jobs = self.fetch_jobs_from_feed(f_name, f_url)
                all_jobs.extend(jobs)

        return all_jobs
