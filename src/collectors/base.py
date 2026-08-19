import time
import requests
from typing import List, Dict, Any, Optional
from src.utils.logging import setup_logger

class BaseCollector:
    def __init__(self, name: str, rate_limit_delay: float = 1.0):
        self.name = name
        self.rate_limit_delay = rate_limit_delay
        self.logger = setup_logger(f"collector.{name}")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 JobFinder/1.0"
        }

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        """Abstract method to fetch job listings from source."""
        raise NotImplementedError("Subclasses must implement fetch_jobs()")

    def safe_get(self, url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Optional[requests.Response]:
        """Performs a polite HTTP GET request with retries and delay."""
        time.sleep(self.rate_limit_delay)
        for attempt in range(2):
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=timeout)
                if resp.status_code == 200:
                    return resp
                self.logger.warning(f"HTTP {resp.status_code} for URL: {url}")
            except Exception as e:
                self.logger.warning(f"Request attempt {attempt+1} failed for {url}: {e}")
                time.sleep(1.0)
        return None
