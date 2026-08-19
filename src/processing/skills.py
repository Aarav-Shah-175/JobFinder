import re
from typing import List, Dict, Set, Any
from src.utils.text import normalize_string

SKILL_SYNONYMS = {
    "c++": ["cpp", "c/c++", "c plus plus"],
    "java": ["java 8", "java 11", "java 17", "java 21", "core java"],
    "python": ["python3", "py"],
    "javascript": ["js", "ecmascript"],
    "postgresql": ["postgres", "postgresql db", "psql"],
    "sqlite": ["sqlite3"],
    "aws": ["amazon web services", "aws cloud"],
    "webauthn": ["passkeys", "fido2", "fido"],
    "openmpi": ["mpi", "parallel computing", "open mpi"],
    "scapy": ["packet inspection", "network security", "intrusion detection", "iptables"],
    "mediapipe": ["facenet", "mtcnn", "facemesh", "face recognition"],
    "opencv": ["computer vision", "image processing"],
    "react": ["reactjs", "react.js"],
    "redux": ["redux toolkit", "rtk"],
    "django": ["django framework", "django rest framework", "drf"],
    "rest apis": ["rest api", "restful apis", "restful web services"],
    "jwt": ["json web token", "jwt authentication"],
    "bcrypt": ["password hashing", "hashing"],
    "firebase": ["firebase auth", "firebase database"],
    "supabase": ["supabase db"],
    "dsa": ["data structures", "algorithms", "data structures & algorithms", "problem solving"],
    "system design": ["distributed systems", "microservices", "scalable systems"]
}

DOMAIN_KEYWORDS = {
    "backend": ["backend", "rest api", "django", "postgresql", "firebase", "jwt", "sql", "microservices", "node", "express", "fastapi", "spring boot"],
    "systems": ["c++", "openmpi", "systems engineering", "operating systems", "parallel computing", "hpc", "high performance", "hashing", "xxhash", "file systems", "distributed systems", "ipc", "low level"],
    "security": ["cybersecurity", "webauthn", "passkeys", "scapy", "iptables", "network security", "intrusion detection", "anti-spoofing", "replay attack", "hmac", "authentication", "biometrics", "penetration", "application security", "appsec"],
    "ai_cv": ["computer vision", "opencv", "mediapipe", "facenet", "mtcnn", "image recognition", "perceptual hashing", "cosine similarity", "ai", "machine learning", "deep learning", "neural networks", "pytorch", "tensorflow"],
    "frontend": ["react", "redux", "html", "css", "javascript", "typescript", "ui", "ux", "frontend", "web development"]
}

PROJECT_SIGNALS = {
    "secure_attendance": [
        "webauthn", "passkeys", "biometrics", "anti-spoofing", "facenet", "mediapipe", "mtcnn", "hmac", "subnet validation", "replay attack", "liveness"
    ],
    "duplicate_finder": [
        "c++", "openmpi", "xxhash", "perceptual hashing", "distributed processing", "ipc", "sqlite caching", "parallel computing", "hpc", "high performance computing"
    ],
    "nidps": [
        "scapy", "iptables", "ddos detection", "port scan", "packet processing", "packet inspection", "intrusion detection", "intrusion prevention", "automated blocking"
    ]
}

def extract_skills(text: str) -> List[str]:
    """Extracts candidate tech skills and canonical names from job description."""
    norm_text = normalize_string(text)
    detected_skills = set()

    for canonical, synonyms in SKILL_SYNONYMS.items():
        # Check canonical
        pattern = r'\b' + re.escape(canonical) + r'\b'
        if re.search(pattern, norm_text):
            detected_skills.add(canonical.title() if len(canonical) > 3 else canonical.upper())
            continue
        # Check synonyms
        for syn in synonyms:
            syn_pattern = r'\b' + re.escape(syn) + r'\b'
            if re.search(syn_pattern, norm_text):
                detected_skills.add(canonical.title() if len(canonical) > 3 else canonical.upper())
                break

    return sorted(list(detected_skills))

def extract_domains(text: str) -> List[str]:
    """Identifies primary domain categories mentioned in text."""
    norm_text = normalize_string(text)
    matched_domains = []

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', norm_text))
        if score >= 1:
            matched_domains.append(domain)

    return matched_domains

def match_project_signals(text: str) -> Dict[str, float]:
    """Scores alignment with Aarav's 3 major projects."""
    norm_text = normalize_string(text)
    project_scores = {}

    for proj_key, signals in PROJECT_SIGNALS.items():
        matches = sum(1 for sig in signals if re.search(r'\b' + re.escape(sig) + r'\b', norm_text))
        # Normalized score between 0.0 and 1.0
        score = min(1.0, matches / 2.0)
        project_scores[proj_key] = score

    return project_scores
