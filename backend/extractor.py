import pdfplumber
import re

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def extract_sections(text):
    sections = {
        "contact": "",
        "education": "",
        "experience": "",
        "skills": "",
        "projects": "",
        "certifications": ""
    }

    lines = text.split("\n")
    current_section = "contact"

    section_keywords = {
        "education": ["education", "qualification"],
        "experience": ["experience", "internship", "work history"],
        "skills": ["skills", "technical skills"],
        "projects": ["projects", "project"],
        "certifications": ["certifications", "certificates"]
    }

    for line in lines:
        line_lower = line.lower().strip()
        matched = False
        for section, keywords in section_keywords.items():
            if any(kw in line_lower for kw in keywords):
                current_section = section
                matched = True
                break
        if not matched:
            sections[current_section] += line + "\n"

    return sections