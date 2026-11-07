import csv
import glob
import os

from resume_parser import parse_resume
from keywords import extract_other_keywords
from scorer import analyze
from checks import inspect_file, formatting_checks, impact_analysis
from final_score import overall_score

RESUME_DIR = os.path.join("tests", "resumes")
JD_DIR = os.path.join("tests", "jds")
OUT_CSV = os.path.join("tests", "results.csv")
COLS = ["resume", "jd", "total", "keyword", "similarity", "formatting",
        "impact", "missing_skills", "label", "error"]


def analyze_pair(resume_path, jd_text):
    with open(resume_path, "rb") as f:
        parsed = parse_resume(f)
    if not parsed["text"].strip():
        return {"error": "no readable text"}
    with open(resume_path, "rb") as f:
        info = inspect_file(f)
    res = analyze(parsed, jd_text)
    fmt = formatting_checks(parsed, info)
    imp = impact_analysis(parsed)
    low = parsed["text"].lower()
    other = [k["keyword"] for k in extract_other_keywords(jd_text)
             if k["keyword"] not in low]
    final = overall_score(res, parsed, fmt, imp, other)
    return {
        "total": final["total"],
        "keyword": res["keyword_score"],
        "similarity": res["similarity"],
        "formatting": fmt["score"],
        "impact": imp["score"] if imp["bullets_checked"] else "n/a",
        "missing_skills": len(res["missing"]),
        "label": final["label"],
    }


def main():
    resumes = sorted(glob.glob(os.path.join(RESUME_DIR, "*.pdf"))
                     + glob.glob(os.path.join(RESUME_DIR, "*.docx")))
    jds = sorted(glob.glob(os.path.join(JD_DIR, "*.txt")))
    if not resumes or not jds:
        print("Put resumes in tests/resumes and job descriptions (.txt) in tests/jds.")
        return

    rows = []
    for r in resumes:
        for j in jds:
            with open(j, encoding="utf-8", errors="ignore") as f:
                jd_text = f.read()
            row = {"resume": os.path.basename(r), "jd": os.path.basename(j)}
            try:
                row.update(analyze_pair(r, jd_text))
            except Exception as e:
                row["error"] = f"{type(e).__name__}: {e}"
            rows.append(row)

    print(" | ".join(c[:12].ljust(12) for c in COLS))
    print("-" * 140)
    for row in rows:
        print(" | ".join(str(row.get(c, ""))[:12].ljust(12) for c in COLS))

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {len(rows)} results to {OUT_CSV}")


if __name__ == "__main__":
    main()
