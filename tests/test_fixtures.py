import unittest
import os
import shutil
import tempfile
from src.processing.normalize import normalize_job_dict
from src.processing.deduplicate import deduplicate_jobs
from src.processing.eligibility import evaluate_eligibility
from src.processing.scoring import score_job
from src.database.db import DatabaseManager

class TestJobFinderPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_jobs.db")
        self.json_path = os.path.join(self.temp_dir, "test_jobs.json")
        self.db = DatabaseManager(db_path=self.db_path, json_path=self.json_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_case_1_standard_sde_entry(self):
        """Test 1: Standard Entry-level SDE, 0-2 yrs, Java/C++, Bangalore, 2027 batch -> High score."""
        raw_job = {
            "source": "TestBoard",
            "company": "Amazon",
            "title": "Software Development Engineer I",
            "location": "Bangalore, India",
            "description": "We are looking for entry level Software Development Engineers and Interns. Required: Java, C++, DSA, PostgreSQL. 0 years experience / Freshers. Open for 2027 batch graduates.",
            "url": "https://example.com/jobs/sde-1-amazon"
        }
        norm_job = normalize_job_dict(raw_job)
        score_res = score_job(norm_job)

        self.assertTrue(score_res["is_eligible"])
        self.assertGreaterEqual(score_res["match_score"], 80.0)

    def test_case_2_senior_sde_rejection(self):
        """Test 2: Senior Software Engineer 5+ years -> Expect Reject."""
        raw_job = {
            "source": "TestBoard",
            "company": "TechCorp",
            "title": "Senior Software Engineer",
            "location": "Bangalore",
            "description": "Requires 5+ years of experience in Java, Spring Boot, Microservices.",
            "url": "https://example.com/jobs/sr-sde-techcorp"
        }
        norm_job = normalize_job_dict(raw_job)
        score_res = score_job(norm_job)

        self.assertFalse(score_res["is_eligible"])
        self.assertEqual(score_res["match_score"], 0.0)
        self.assertEqual(score_res["category"], "❌ NOT ELIGIBLE")

    def test_case_3_security_intern_specialized_match(self):
        """Test 3: Security Engineer Intern, Python, Networking -> Expect High Specialized Match."""
        raw_job = {
            "source": "TestBoard",
            "company": "Cloudflare",
            "title": "Security Engineer Intern",
            "location": "Bangalore",
            "description": "Internship for cybersecurity enthusiasts. Topics: Python, Scapy, Network security, Intrusion detection, WebAuthn, Passkeys, DDoS mitigation.",
            "url": "https://example.com/jobs/sec-intern-cloudflare"
        }
        norm_job = normalize_job_dict(raw_job)
        score_res = score_job(norm_job)

        self.assertTrue(score_res["is_eligible"])
        self.assertGreaterEqual(score_res["match_score"], 85.0)

    def test_case_4_cpp_systems_specialized_match(self):
        """Test 4: C++ Systems Engineer, OpenMPI, Distributed systems -> Expect High Specialized Match."""
        raw_job = {
            "source": "TestBoard",
            "company": "Nvidia",
            "title": "Systems Software Engineer Intern",
            "location": "Pune",
            "description": "Focus on C++, OpenMPI, parallel computing, high performance computing, xxHash, distributed file processing, IPC.",
            "url": "https://example.com/jobs/systems-intern-nvidia"
        }
        norm_job = normalize_job_dict(raw_job)
        score_res = score_job(norm_job)

        self.assertTrue(score_res["is_eligible"])
        self.assertGreaterEqual(score_res["match_score"], 85.0)

    def test_case_5_ml_research_scientist_rejection(self):
        """Test 5: Machine Learning Research Scientist, PhD required -> Expect Reject / Low."""
        raw_job = {
            "source": "TestBoard",
            "company": "DeepMind",
            "title": "Senior Research Scientist - AI",
            "location": "Bangalore",
            "description": "Must have PhD in Machine Learning and 5+ years research publication track record.",
            "url": "https://example.com/jobs/ml-scientist-deepmind"
        }
        norm_job = normalize_job_dict(raw_job)
        score_res = score_job(norm_job)

        self.assertFalse(score_res["is_eligible"])
        self.assertEqual(score_res["match_score"], 0.0)

    def test_case_6_duplicate_sources_merging(self):
        """Test 6: Same job from two different sources -> Expect 1 job with 2 sources."""
        job_source_1 = {
            "source": "Greenhouse",
            "company": "Razorpay",
            "title": "Software Engineer I",
            "location": "Bangalore",
            "url": "https://boards.greenhouse.io/razorpay/jobs/12345"
        }
        job_source_2 = {
            "source": "Lever",
            "company": "Razorpay",
            "title": "Software Engineer I",
            "location": "Bangalore",
            "url": "https://jobs.lever.co/razorpay/12345"
        }
        deduped = deduplicate_jobs([job_source_1, job_source_2])

        self.assertEqual(len(deduped), 1)
        self.assertIn("Greenhouse", deduped[0]["sources"])
        self.assertIn("Lever", deduped[0]["sources"])

    def test_case_7_daily_new_job_logic(self):
        """Test 7: Same job discovered yesterday and today -> Expect Not NEW on 2nd run."""
        job = {
            "source": "Greenhouse",
            "company": "Atlassian",
            "title": "SDE Intern",
            "location": "Bangalore",
            "url": "https://example.com/jobs/atlassian-sde-intern",
            "description": "Java, C++, React 2027 batch",
            "match_score": 90.0
        }

        # Run 1: First time seen
        is_new_1, saved_1 = self.db.upsert_job(job)
        self.assertTrue(is_new_1)
        self.assertEqual(saved_1["status"], "NEW")

        # Run 2: Discovered again today
        is_new_2, saved_2 = self.db.upsert_job(job)
        self.assertFalse(is_new_2)

if __name__ == "__main__":
    unittest.main()
