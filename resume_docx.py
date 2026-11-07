import io
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt

FONT = "Calibri"
RIGHT_EDGE = Inches(6.85)


def bullet_lines(text):
    """Split a text box into clean lines, removing bullet symbols the user typed."""
    out = []
    for line in (text or "").splitlines():
        clean = re.sub(r"^[\s•▪●◦·\-\*–—➢➤]+", "", line).strip()
        if clean:
            out.append(clean)
    return out


def _run(p, text, size=10.5, bold=False, italic=False):
    r = p.add_run(text)
    r.font.name = FONT
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    return r


def _spacing(p, before=0, after=0):
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)


def _heading(doc, title):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for key, value in (("w:val", "single"), ("w:sz", "6"),
                       ("w:space", "1"), ("w:color", "808080")):
        bottom.set(qn(key), value)
    borders.append(bottom)
    pPr.append(borders)
    _spacing(p, before=8, after=3)
    _run(p, title.upper(), size=11, bold=True)


def _bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    _spacing(p, 0, 1)
    _run(p, text)


def _title_row(doc, left, right=""):
    p = doc.add_paragraph()
    _spacing(p, 3, 0)
    p.paragraph_format.tab_stops.add_tab_stop(RIGHT_EDGE, WD_TAB_ALIGNMENT.RIGHT)
    _run(p, left, bold=True)
    if right:
        _run(p, "\t" + right)


def _detail(doc, text):
    p = doc.add_paragraph()
    _spacing(p, 0, 1)
    _run(p, text, italic=True)


def build_docx(d):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)  # A4
    sec.left_margin = sec.right_margin = Inches(0.7)
    sec.top_margin = sec.bottom_margin = Inches(0.6)
    doc.styles["Normal"].font.name = FONT
    doc.styles["Normal"].font.size = Pt(10.5)

    # Header: name and one contact line
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _spacing(p, 0, 2)
    _run(p, d["name"].strip() or "Your Name", size=18, bold=True)
    contact = [d[k].strip() for k in ("city", "email", "phone", "linkedin", "github")
               if d[k].strip()]
    if contact:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _spacing(p, 0, 0)
        _run(p, " | ".join(contact), size=10)

    # Summary
    if d["summary"].strip():
        _heading(doc, "Summary")
        p = doc.add_paragraph()
        _spacing(p, 0, 0)
        _run(p, " ".join(d["summary"].split()))

    # Education
    edu = [e for e in d["education"] if e["institute"].strip() or e["degree"].strip()]
    if edu:
        _heading(doc, "Education")
        for e in edu:
            _title_row(doc, e["institute"].strip() or e["degree"].strip(), e["years"].strip())
            line = ", ".join(x for x in (e["degree"].strip() if e["institute"].strip() else "",
                                         e["score"].strip()) if x)
            if line:
                _detail(doc, line)

    # Skills
    skills = [(label, v.strip()) for label, v in d["skills"] if v.strip()]
    if skills:
        _heading(doc, "Skills")
        for label, v in skills:
            p = doc.add_paragraph()
            _spacing(p, 0, 1)
            _run(p, f"{label}: ", bold=True)
            _run(p, v)

    # Projects
    projects = [pr for pr in d["projects"] if pr["title"].strip()]
    if projects:
        _heading(doc, "Projects")
        for pr in projects:
            head = " | ".join(x for x in (pr["title"].strip(), pr["tech"].strip(),
                                          pr["link"].strip()) if x)
            p = doc.add_paragraph()
            _spacing(p, 3, 0)
            _run(p, head, bold=True)
            for b in bullet_lines(pr["bullets"]):
                _bullet(doc, b)

    # Experience / internships
    jobs = [e for e in d["experience"] if e["role"].strip() or e["org"].strip()]
    if jobs:
        _heading(doc, "Experience")
        for e in jobs:
            title = " - ".join(x for x in (e["role"].strip(), e["org"].strip()) if x)
            _title_row(doc, title, e["dates"].strip())
            for b in bullet_lines(e["bullets"]):
                _bullet(doc, b)

    # Certifications and achievements
    for title, key in (("Certifications", "certifications"), ("Achievements", "achievements")):
        items = bullet_lines(d[key])
        if items:
            _heading(doc, title)
            for item in items:
                _bullet(doc, item)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
