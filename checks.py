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


def _has_phone(text):
    for m in PHONE_RE.findall(text):
        if 10 <= len(re.sub(r"\D", "", m)) <= 13:
            return True
    return False


def formatting_checks(parsed, info):
    text = parsed["text"]
    low = text.lower()
    words = parsed["word_count"]
    pages = info["pages"]
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
    add(_has_phone(text[:600]), 10,
        "Phone number found.",
        "No phone number found near the top. Add one in the header.")
    add("linkedin" in low or "github" in low, 5,
        "LinkedIn or GitHub profile mentioned.",
        "No LinkedIn or GitHub mention. Add at least one profile link.")

    found, missing = parsed["found"], parsed["missing"]
    add(len(found) >= 4, 20,
        "Standard section headings detected.",
        "Missing or unrecognised headings: " + ", ".join(s.title() for s in missing)
        + ". Use standard names like Skills, Education, Projects.")

    length_ok = 250 <= words <= 900 and (pages is None or pages <= 2)
    if words < 250:
        length_msg = f"Resume is short ({words} words). Add detail to projects and experience."
    elif words > 900:
        length_msg = f"Resume is long ({words} words). Trim to 1-2 pages."
    else:
        length_msg = f"Resume is {pages} pages. Keep it to 2 pages or fewer."
    add(length_ok, 15, "Resume length is appropriate.", length_msg)

    add(info["tables"] == 0, 10,
        "No tables detected.",
        f"{info['tables']} table(s) found. Some ATS read tables in the wrong order; use plain text with headings.")
    add(info["images"] == 0, 5,
        "No images or graphics detected.",
        "Images/graphics found (photo, logo or skill bars). ATS cannot read them; remove them.")
    add(len(ICON_RE.findall(text)) < 3, 10,
        "No decorative icons or symbols.",
        "Decorative icons/symbols found. They can turn into garbage text in an ATS; use plain text.")

    score = sum(c["weight"] for c in checks if c["passed"])
    return {"score": score, "checks": checks}


# ---------- Impact of bullet points ----------

BULLET_RE = re.compile(r"^\s*[•▪●◦·\-\*–—➢➤■□\uf0b7\uf0a7\uf076]+\s*")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
SKIP_STARTS = {"tech", "tools", "stack", "link", "github", "demo", "live"}

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


def split_bullets(section_text):
    bullets = []
    for raw in section_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        has_marker = bool(BULLET_RE.match(line))
        clean = BULLET_RE.sub("", line).strip()
        if not clean:
            continue
        if not has_marker and bullets and clean[0].islower():
            bullets[-1] += " " + clean  # wrapped line of the previous bullet
        else:
            bullets.append(clean)
    return bullets


def _is_candidate(b):
    words = b.split()
    if len(words) < 6 or "|" in b or b.endswith(":"):
        return False
    return words[0].lower().strip(":") not in SKIP_STARTS


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
    weak_bullets = []
    for b in bullets:
        issues = []
        first = re.sub(r"[^a-z\-]", "", b.split()[0].lower())
        strong = (first in ACTION_VERBS or (first.endswith("ed") and len(first) > 4)) \
                 and first not in WEAK_STARTS
        if strong:
            verb_count += 1
        else:
            issues.append("start with a strong action verb (Built, Developed, Reduced...)")
        if _has_metric(b):
            metric_count += 1
        else:
            issues.append("add a number or measurable result")
        m = WEAK_RE.search(b.lower())
        if m:
            weak_count += 1
            issues.append(f'replace the weak phrase "{m.group(0)}"')
        if PRONOUN_RE.search(b.lower()):
            issues.append("remove I/my/me")
        if len(b.split()) > 30:
            issues.append("shorten it (over 30 words)")
        if issues:
            weak_bullets.append({"text": b, "issues": issues})

    weak_bullets.sort(key=lambda w: -len(w["issues"]))
    verb_pct = 100 * verb_count / n
    metric_pct = 100 * metric_count / n
    metric_component = min(metric_pct / 50, 1) * 100   # 50% quantified = full marks
    weak_component = 100 * (1 - weak_count / n)
    score = 0.4 * verb_pct + 0.4 * metric_component + 0.2 * weak_component

    return {
        "bullets_checked": n,
        "score": round(score, 1),
        "verb_pct": round(verb_pct),
        "metric_pct": round(metric_pct),
        "weak_bullets": weak_bullets[:8],
    }
