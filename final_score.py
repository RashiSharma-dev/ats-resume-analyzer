from resume_parser import EXPECTED_SECTIONS
from scorer import PRIORITY_WEIGHT

BASE_WEIGHTS = {
    "Keyword match": 40,
    "Content similarity": 20,
    "Section completeness": 15,
    "Formatting": 15,
    "Impact of bullets": 10,
}
OPTIONAL_SECTIONS = ["summary", "experience", "certifications", "achievements"]
SIMILARITY_FULL_MARKS = 30  # a TF-IDF similarity of 30% counts as a full match


def section_score(parsed):
    base = 80 * len(parsed["found"]) / len(EXPECTED_SECTIONS)
    extras = 5 * sum(1 for s in OPTIONAL_SECTIONS
                     if parsed["sections"].get(s, "").strip())
    return min(base + extras, 100)


def label_for(total):
    if total >= 80:
        return "Strong match: ready to apply"
    if total >= 65:
        return "Good match: a few fixes will make it strong"
    if total >= 45:
        return "Needs work: follow the fixes below"
    return "Weak match for this job: major gaps"


def build_fixes(res, parsed, fmt, imp, other_missing, weights, sim_scaled):
    fixes = []

    def add(title, detail, gain):
        fixes.append({"title": title, "detail": detail, "gain": max(1, round(gain))})

    # 1. Missing skills
    everything = res["matched"] + res["missing"]
    total_w = sum(PRIORITY_WEIGHT[r["priority"]] for r in everything) or 1
    w_kw = weights.get("Keyword match", 0)
    core = [r for r in res["missing"] if r["priority"] in ("High", "Medium")]
    nice = [r for r in res["missing"] if r["priority"] == "Low"]
    if core:
        gain = w_kw * sum(PRIORITY_WEIGHT[r["priority"]] for r in core) / total_w
        names = ", ".join(r["skill"].title() for r in core)
        add("Cover the skills this job requires",
            f"Missing: {names}. Add each one only if you have really used it "
            "(in a project, course or internship). If you haven't, learn the basics "
            "and build a small project with it.", gain)
    if nice:
        gain = w_kw * sum(PRIORITY_WEIGHT[r["priority"]] for r in nice) / total_w
        names = ", ".join(r["skill"].title() for r in nice)
        add("Nice-to-have skills",
            f"The job lists these as preferred: {names}. Add them if you know them.", gain)

    # 2. Skills in the resume but outside the Skills section
    if res["not_in_skills_section"]:
        add("Move skills into your Skills section",
            "These appear elsewhere in your resume but not under Skills: "
            + ", ".join(s.title() for s in res["not_in_skills_section"]) + ".", 2)

    # 3. Missing sections
    w_sec = weights.get("Section completeness", 0)
    for s in parsed["missing"]:
        add(f"Add a {s.title()} section",
            "Recruiters and ATS expect this section.",
            (80 / len(EXPECTED_SECTIONS)) * w_sec / 100)

    # 4. Formatting problems
    w_fmt = weights.get("Formatting", 0)
    for c in fmt["checks"]:
        if not c["passed"]:
            add("Fix a formatting issue", c["message"], c["weight"] * w_fmt / 100)

    # 5. Weak bullets
    w_imp = weights.get("Impact of bullets", 0)
    must_fix = [w for w in imp["weak_bullets"]
                if any(not i.startswith("(optional)") for i in w["issues"])]
    if must_fix:
        add("Rewrite your weakest bullet points",
            f"{len(must_fix)} bullet(s) need a stronger start or clearer wording. "
            "See the Resume health tab for each one.",
            (100 - imp["score"]) * w_imp / 100)

    # 6. Wording similar to the job description
    if sim_scaled < 60 and other_missing:
        add("Use the job description's wording",
            "Where it is true for you, use phrases from the job description, such as: "
            + ", ".join(other_missing[:5]) + ".",
            (100 - sim_scaled) * weights.get("Content similarity", 0) / 100 * 0.5)

    # 7. Soft skills
    if res["soft_missing"]:
        add("Show evidence of soft skills",
            "Add a bullet that shows: "
            + ", ".join(r["skill"].title() for r in res["soft_missing"])
            + ". Example: your role in a team project or hackathon.", 1)

    fixes.sort(key=lambda f: -f["gain"])
    return fixes[:5]


def overall_score(res, parsed, fmt, imp, other_missing=None):
    other_missing = other_missing or []
    sim_scaled = min(res["similarity"] / SIMILARITY_FULL_MARKS, 1) * 100
    keyword = res["keyword_score"] if res["total_jd_skills"] else sim_scaled

    scores = {
        "Keyword match": keyword,
        "Content similarity": sim_scaled,
        "Section completeness": section_score(parsed),
        "Formatting": fmt["score"],
        "Impact of bullets": imp["score"] if imp["bullets_checked"] else None,
    }
    active = {k: v for k, v in scores.items() if v is not None}
    weight_sum = sum(BASE_WEIGHTS[k] for k in active)
    weights = {k: 100 * BASE_WEIGHTS[k] / weight_sum for k in active}
    total = sum(active[k] * weights[k] / 100 for k in active)

    breakdown = [
        {"Component": k, "Score": f"{round(v)}/100", "Weight": f"{round(weights[k])}%"}
        for k, v in active.items()
    ]
    return {
        "total": round(total, 1),
        "label": label_for(total),
        "breakdown": breakdown,
        "fixes": build_fixes(res, parsed, fmt, imp, other_missing, weights, sim_scaled),
    }
