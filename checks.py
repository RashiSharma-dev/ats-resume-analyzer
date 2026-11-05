import re
import pdfplumber
from docx import Document

# ---------- File inspection ----------

def inspect_file(file):
    """Look at the raw file: page count, tables, images."""
    info = {"type": "", "pages": None, "tables": 0, "images": 0}
    file.seek(0)
    name = file.name.lower()
    if name.endswith(".pdf"):
        info["type"] = "pdf"
        with pdfplumber.open(file) as pdf:
            info["pages"] = len(pdf.pages)
            info["images"] = sum(len(p.images) for p in pdf.pages)
    elif name.endswith(".docx"):
        info["type"] = "docx"
        doc = Document(file)
        info["tables"] = len(doc.tables)
        info["images"] = len(doc.inline_shapes)
    file.seek(0)
    return info


# ---------- Formatting / ATS readability ----------

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{8,}\d")
ICON_RE = re.compile(r"[\u2600-\u27BF\U0001F300-\U0001FAFF]")
INLINE_RE = re.compile(r"\s+[•●▪◦]\s+")


def _has_phone(text):
    for m in PHONE_RE.findall(text):
        if 10 <= len(re.sub(r"\D", "", m)) <= 13:
            return True
    return False


def _column_lines(text):
    """Count lines that look like two columns read side by side."""
    count = 0
    for line in text.splitlines():
        parts = INLINE_RE.split(line.strip())
        if len(parts) == 2 and all(len(p.split()) >= 3 for p in parts):
            count += 1
    return count


def formatting_checks(parsed, info):
    text = parsed["text"]
    low = text.lower()
    words = parsed["word_count"]
    pages = info["pages"]
    missing = parsed["missing"]
    checks = []

    def add(passed, weight, ok_msg, fix_msg):
        checks.append({"passed": passed, "weight": weight,
                       "message": ok_msg if passed else fix_msg})

    add(words >= 150, 15,
        "Text can be read by software.",
        "Very little text was found. The resume may be an image or scan; export it as a text-based PDF or DOCX.")
    add(bool(EMAIL_RE.search(text)), 10,
        "Email address found.",
        "No email address found. Add one at the top.")
    add(_has_phone(text), 10,
        "Phone number found.",
        "No phone number found. Add one in the header.")
    add("linkedin" in low or "github" in low, 5,
        "LinkedIn or GitHub profile mentioned.",
        "No LinkedIn or GitHub mention. Add at least one profile link.")
    add(not missing, 15,
        "Standard section headings detected.",
        "Missing or unrecognised headings: " + ", ".join(s.title() for s in missing)
        + ". Use standard names like Skills, Education, Projects.")

    length_ok = 200 <= words <= 900 and (pages is None or pages <= 2)
    if words < 200:
        length_msg = f"Resume is short ({words} words). Add detail to projects and experience."
    elif words > 900:
        length_msg = f"Resume is long ({words} words). Trim to 1-2 pages."
    else:
        length_msg = f"Resume is {pages} pages. Keep it to 2 pages or fewer."
    add(length_ok, 10, "Resume length is appropriate.", length_msg)

    add(info["tables"] == 0, 10,
        "No tables detected.",
        f"{info['tables']} table(s) found. Some ATS read tables in the wrong order; use plain text with headings.")
    add(info["images"] == 0, 5,
        "No images or graphics detected.",
        "Images/graphics found (photo, logo or skill bars). ATS cannot read them; remove them.")
    icons = len(ICON_RE.findall(text.replace("➢", "").replace("➤", "")))
    add(icons < 3, 10,
        "No decorative icons or symbols.",
        "Decorative icons/symbols found. They can turn into garbage text in an ATS; use plain text.")
    add(_column_lines(text) < 2, 10,
        "Single-column text flow.",
        "Parts of your resume look like two columns read side by side (for example certifications "
        "next to achievements). Some ATS mix up the text this way; a single-column layout is safest.")

    score = sum(c["weight"] for c in checks if c["passed"])
    return {"score": score, "checks": checks}


# ---------- Impact of bullet points (fresher-friendly) ----------

BULLET_RE = re.compile(r"^\s*[•▪●◦·\-\*–—➢➤■□\uf0b7\uf0a7\uf076]+\s*")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
SKIP_STARTS = {"tech", "tools", "stack", "link", "github", "demo", "live",
               "other", "technologies"}

WEAK_STARTS = {"responsible", "worked", "helped", "assisted", "involved",
               "tasked", "participated", "duties"}
WEAK_RE = re.compile(
    r"\b(responsible for|worked on|worked with|helped|assisted|involved in|"
    r"duties included|tasked with|participated in|various|etc|familiar with)\b")
PRONOUN_RE = re.compile(r"\b(i|my|me)\b")

ACTION_VERBS = {
    "built", "developed", "designed", "created", "implemented", "engineered",
    "led", "managed", "launched", "deployed", "automated", "optimized",
    "optimised", "improved", "reduced", "increased", "achieved", "analyzed",
    "analysed", "trained", "tested", "integrated", "migrated", "architected",
    "established", "streamlined", "delivered", "collaborated", "coordinated",
    "researched", "evaluated", "constructed", "programmed", "configured",
    "maintained", "organized", "organised", "presented", "mentored", "won",
    "ran", "wrote", "drove", "boosted", "cut", "saved", "scaled", "fine-tuned",
    "finetuned", "debugged", "refactored", "documented", "visualized",
    "spearheaded", "initiated", "resolved", "generated", "secured", "published",
}


def _is_strong_start(word):
    w = re.sub(r"[^a-z\-]", "", word.lower())
    return w not in WEAK_STARTS and (w in ACTION_VERBS or (w.endswith("ed") and len(w) > 4))


def split_bullets(section_text):
    bullets = []
    for raw in section_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        has_marker = bool(BULLET_RE.match(line))
        clean = BULLET_RE.sub("", line).strip()
        # a line holding several bullets (or two columns) is split into separate items
        pieces = [p.strip() for p in INLINE_RE.split(clean) if p.strip()]
        for i, piece in enumerate(pieces):
            if i == 0 and not has_marker and bullets and piece[0].islower():
                bullets[-1] += " " + piece  # wrapped line of the previous bullet
            else:
                bullets.append(piece)
    return bullets


def _is_candidate(b):
    """Only real achievement bullets are judged, not titles, tech lists or certificates."""
    words = b.split()
    if len(words) < 6 or "|" in b or b.endswith(":"):
        return False
    first = words[0].lower().strip(":")
    if first in SKIP_STARTS:
        return False
    strong = _is_strong_start(words[0])
    if "(" in b and b.count(",") >= 2 and not strong:
        return False  # project title with a tech stack in brackets
    if re.search(r"\s[–—-]\s", b) and not strong:
        return False  # "Course – Issuer" style certificate lines
    return True


def _has_metric(b):
    return bool(re.search(r"\d", YEAR_RE.sub("", b)))


def impact_analysis(parsed):
    sections = parsed["sections"]
    raw = []
    for name in ("experience", "projects"):
        raw += split_bullets(sections.get(name, ""))
    bullets = [b for b in raw if _is_candidate(b)]
    n = len(bullets)
    if n == 0:
        return {"bullets_checked": 0, "score": 0, "verb_pct": 0,
                "metric_pct": 0, "weak_bullets": []}

    verb_count = metric_count = weak_count = 0
    flagged = []
    for b in bullets:
        must, optional = [], []
        if _is_strong_start(b.split()[0]):
            verb_count += 1
        else:
            must.append("start with a strong action verb (Built, Developed, Reduced...)")
        if _has_metric(b):
            metric_count += 1
        else:
            optional.append("(optional) add a number or result if you have one, "
                            "e.g. users, accuracy, time saved")
        m = WEAK_RE.search(b.lower())
        if m:
            weak_count += 1
            must.append(f'replace the weak phrase "{m.group(0)}"')
        if PRONOUN_RE.search(b.lower()):
            must.append("remove I/my/me")
        if len(b.split()) > 30:
            must.append("shorten it (over 30 words)")
        if must or optional:
            flagged.append({"text": b, "issues": must + optional, "must": len(must)})

    flagged.sort(key=lambda w: (-w["must"], -len(w["issues"])))
    verb_pct = 100 * verb_count / n
    metric_pct = 100 * metric_count / n
    metric_component = min(metric_pct / 30, 1) * 100   # 30% quantified = full marks
    weak_component = 100 * (1 - weak_count / n)
    score = 0.5 * verb_pct + 0.3 * metric_component + 0.2 * weak_component

    return {
        "bullets_checked": n,
        "score": round(score, 1),
        "verb_pct": round(verb_pct),
        "metric_pct": round(metric_pct),
        "weak_bullets": [{"text": w["text"], "issues": w["issues"]} for w in flagged[:6]],
    }
