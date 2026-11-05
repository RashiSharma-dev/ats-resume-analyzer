import re
import pdfplumber
from docx import Document

# Section name -> headings people commonly use for it
SECTION_ALIASES = {
    "summary": ["summary", "professional summary", "profile", "objective",
                "career objective", "about me"],
    "skills": ["skills", "technical skills", "key skills", "core competencies",
               "skills & tools", "technologies"],
    "education": ["education", "academic background", "academics",
                  "educational qualifications", "qualifications"],
    "experience": ["experience", "work experience", "professional experience",
                   "internship", "internships", "employment history"],
    "projects": ["projects", "academic projects", "personal projects",
                 "key projects"],
    "certifications": ["certifications", "certificates", "courses"],
    "achievements": ["achievements", "awards", "honors", "honours",
                     "extracurricular activities"],
}

# Sections an ATS (and recruiter) expects to see
EXPECTED_SECTIONS = ["summary", "skills", "education", "experience", "projects"]

# Reverse lookup: "technical skills" -> "skills"
HEADING_LOOKUP = {
    alias: section
    for section, aliases in SECTION_ALIASES.items()
    for alias in aliases
}


def extract_text_from_pdf(file):
    pages = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages)


def extract_text_from_docx(file):
    doc = Document(file)
    lines = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                lines.append(cell.text)
    return "\n".join(lines)


def extract_text(file):
    name = file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file)
    if name.endswith(".docx"):
        return extract_text_from_docx(file)
    raise ValueError("Only PDF and DOCX files are supported.")


def detect_sections(text):
    sections = {"header": []}  # name, email, phone usually sit above the first heading
    current = "header"
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        cleaned = re.sub(r"[^a-z& ]", "", line.lower()).strip()
        if len(line) <= 40 and cleaned in HEADING_LOOKUP:
            current = HEADING_LOOKUP[cleaned]
            sections.setdefault(current, [])
        else:
            sections[current].append(line)
    return {name: "\n".join(lines) for name, lines in sections.items()}


def parse_resume(file):
    text = extract_text(file)
    sections = detect_sections(text)
    found = [s for s in EXPECTED_SECTIONS if sections.get(s, "").strip()]
    missing = [s for s in EXPECTED_SECTIONS if s not in found]
    return {
        "text": text,
        "sections": sections,
        "found": found,
        "missing": missing,
        "word_count": len(text.split()),
    }
