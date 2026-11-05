import re
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
from skills_db import SKILLS, SOFT_SKILLS

PREFERRED_MARKERS = ("preferred", "nice to have", "good to have", "bonus", "desirable", "a plus")
REQUIRED_HEADINGS = ("requirement", "qualification", "responsibilit", "must have",
                     "required", "what you", "skills")
BULLETS = ("-", "•", "*", "–")

EXTRA_STOP = {
    "experience", "work", "working", "team", "teams", "ability", "strong", "years",
    "year", "knowledge", "skills", "skill", "role", "job", "candidate", "company",
    "business", "including", "related", "using", "etc", "good", "new", "help",
    "support", "key", "based", "understanding", "environment", "responsible",
}


def _compile(term):
    # match whole terms only, so "java" does not match inside "javascript"
    return re.compile(r"(?<![a-z0-9+#])" + re.escape(term) + r"(?![a-z0-9+#])")


def _build(skill_map):
    return {skill: [_compile(a) for a in aliases] for skill, aliases in skill_map.items()}


HARD_PATTERNS = _build(SKILLS)
SOFT_PATTERNS = _build(SOFT_SKILLS)


def _count(patterns, text):
    return sum(len(p.findall(text)) for p in patterns)


def _classify(patterns_map, jd_text):
    """Return {skill: {"count": n, "preferred_only": bool}}."""
    found = {}
    mode = "required"
    for raw in jd_text.lower().splitlines():
        line = raw.strip()
        if not line:
            continue
        is_bullet = line.startswith(BULLETS)
        is_heading = len(line) < 60 and not is_bullet
        has_pref = any(m in line for m in PREFERRED_MARKERS)
        if is_heading and has_pref:
            mode = "preferred"
            continue
        if is_heading and any(h in line for h in REQUIRED_HEADINGS):
            mode = "required"
            continue
        line_mode = "preferred" if has_pref else mode
        for skill, patterns in patterns_map.items():
            n = _count(patterns, line)
            if n:
                entry = found.setdefault(skill, {"count": 0, "preferred_only": True})
                entry["count"] += n
                if line_mode == "required":
                    entry["preferred_only"] = False
    return found


def _rank(found):
    rows = []
    for skill, info in found.items():
        if info["preferred_only"]:
            priority = "Low"
        elif info["count"] >= 2:
            priority = "High"
        else:
            priority = "Medium"
        rows.append({"skill": skill, "mentions": info["count"], "priority": priority})
    order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(rows, key=lambda r: (order[r["priority"]], -r["mentions"], r["skill"]))


def extract_skills(jd_text):
    return _rank(_classify(HARD_PATTERNS, jd_text))


def extract_soft_skills(jd_text):
    return _rank(_classify(SOFT_PATTERNS, jd_text))


def extract_other_keywords(jd_text, top_n=12):
    """Frequent phrases from the JD that are NOT in the skills dictionary."""
    known = {a for aliases in SKILLS.values() for a in aliases}
    known |= {a for aliases in SOFT_SKILLS.values() for a in aliases}
    stops = list(ENGLISH_STOP_WORDS | EXTRA_STOP)
    try:
        vec = CountVectorizer(ngram_range=(1, 2), stop_words=stops,
                              token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]+\b")
        counts = vec.fit_transform([jd_text.lower()]).toarray()[0]
    except ValueError:
        return []
    ranked = sorted(zip(vec.get_feature_names_out(), counts), key=lambda x: -x[1])
    out = []
    for term, c in ranked:
        if c >= 2 and term not in known:
            out.append({"keyword": term, "mentions": int(c)})
        if len(out) == top_n:
            break
    return out


if __name__ == "__main__":
    sample = """
    Requirements:
    - 3+ years of Python and SQL experience
    - Experience with machine learning, TensorFlow and AWS
    - Strong communication skills
    Preferred qualifications:
    - Knowledge of Docker and Kubernetes
    - Experience with A/B testing
    """
    print(extract_skills(sample))
    print(extract_soft_skills(sample))
