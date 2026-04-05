import spacy
import re
from collections import Counter

nlp = spacy.load("en_core_web_sm")

GENERIC_STOPWORDS = [
    "experience", "knowledge", "understanding", "ability", "skills",
    "working", "using", "good", "strong", "excellent", "team",
    "communication", "problem", "solving", "years", "work", "etc",
    "will", "must", "should", "able", "also", "well", "can", "the",
    "and", "for", "with", "you", "our", "are", "this", "that", "have"
]

TECH_PATTERN = re.compile(
    r'\b(python|java|sql|aws|docker|kubernetes|terraform|flask|django|'
    r'react|node|git|linux|bash|ci/cd|jenkins|ansible|nginx|mysql|'
    r'postgresql|mongodb|redis|kafka|spark|hadoop|tensorflow|pytorch|'
    r'scikit|pandas|numpy|nlp|spacy|nltk|rest|api|microservices|'
    r'spring|hibernate|ec2|s3|lambda|iam|vpc|azure|gcp|devops|'
    r'machine learning|deep learning|data science|cloud|html|css|'
    r'javascript|typescript|kotlin|swift|rust|golang|c\+\+|r\b)\b',
    re.IGNORECASE
)

def extract_jd_keywords(job_description):
    """Extract meaningful keywords from job description using NLP + regex"""
    if not job_description or len(job_description.strip()) < 10:
        return []

    # Extract tech keywords using pattern matching
    tech_keywords = [k.lower() for k in TECH_PATTERN.findall(job_description)]

    # Extract noun phrases using spaCy
    doc = nlp(job_description.lower())
    noun_phrases = []
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip()
        words = phrase.split()
        # Keep 1-3 word phrases, filter stopwords
        if 1 <= len(words) <= 3:
            if not any(sw in words for sw in GENERIC_STOPWORDS):
                if len(phrase) > 2:
                    noun_phrases.append(phrase)

    # Combine and deduplicate
    all_keywords = list(set(tech_keywords + noun_phrases))
    return all_keywords


def match_keywords(resume_text, jd_keywords):
    """Match JD keywords against resume text"""
    resume_lower = resume_text.lower()
    matched = []
    missing = []

    for kw in jd_keywords:
        if kw.lower() in resume_lower:
            matched.append(kw)
        else:
            missing.append(kw)

    return matched, missing


def calculate_ats_score(sections, job_description=""):
    score = 0
    breakdown = {}
    all_text = " ".join(sections.values())

    # Contact (10 pts)
    contact = sections.get("contact", "")
    contact_score = 0
    if "@" in contact: contact_score += 4
    if any(c.isdigit() for c in contact): contact_score += 3
    if "linkedin" in contact.lower(): contact_score += 3
    breakdown["contact"] = min(contact_score, 10)
    score += breakdown["contact"]

    # Education (15 pts)
    edu = sections.get("education", "")
    edu_score = 0
    if any(w in edu.lower() for w in ["b.tech", "bachelor", "master", "degree"]): edu_score += 8
    if any(w in edu.lower() for w in ["cgpa", "gpa", "percentage"]): edu_score += 4
    if re.search(r"\d{4}", edu): edu_score += 3
    breakdown["education"] = min(edu_score, 15)
    score += breakdown["education"]

    # Experience (20 pts)
    exp = sections.get("experience", "")
    exp_score = 0
    if len(exp.strip()) > 50: exp_score += 8
    if any(w in exp.lower() for w in ["improved","built","developed","automated","reduced","designed","deployed"]): exp_score += 7
    if re.search(r"\d+%|\d+ (users|records|services|systems)", exp): exp_score += 5
    breakdown["experience"] = min(exp_score, 20)
    score += breakdown["experience"]

    # Skills (20 pts)
    skills = sections.get("skills", "")
    tech_in_skills = TECH_PATTERN.findall(skills)
    skill_score = min(len(set(tech_in_skills)) * 3, 20)
    breakdown["skills"] = skill_score
    score += skill_score

    # Projects (20 pts)
    projects = sections.get("projects", "")
    proj_score = 0
    if len(projects.strip()) > 100: proj_score += 10
    tech_in_projects = TECH_PATTERN.findall(projects)
    if len(set(tech_in_projects)) >= 2: proj_score += 10
    breakdown["projects"] = min(proj_score, 20)
    score += breakdown["projects"]

    # Certifications (15 pts)
    certs = sections.get("certifications", "")
    cert_score = 0
    if len(certs.strip()) > 20: cert_score += 10
    if re.search(r"\d{4}", certs): cert_score += 5
    breakdown["certifications"] = min(cert_score, 15)
    score += breakdown["certifications"]

    # JD keyword matching
    jd_keywords = extract_jd_keywords(job_description) if job_description else []
    if jd_keywords:
        matched, missing = match_keywords(all_text, jd_keywords)
        # Boost score based on keyword match %
        if len(jd_keywords) > 0:
            match_pct = len(matched) / len(jd_keywords)
            score = int(score * (0.7 + 0.3 * match_pct))
    else:
        matched = list(set(TECH_PATTERN.findall(all_text)))
        missing = []

    return {
        "total_score": min(score, 100),
        "breakdown": breakdown,
        "matched_keywords": [m.lower() for m in matched],
        "missing_keywords": [m.lower() for m in missing[:10]],
        "total_keywords_found": len(matched),
        "total_keywords_possible": len(jd_keywords) if jd_keywords else len(matched),
        "jd_mode": bool(job_description)
    }