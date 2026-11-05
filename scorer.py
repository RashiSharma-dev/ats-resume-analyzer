from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from keywords import HARD_PATTERNS, SOFT_PATTERNS, extract_skills, extract_soft_skills

PRIORITY_WEIGHT = {"High": 3, "Medium": 2, "Low": 1}


def _found(patterns, text):
    text = text.lower()
    return any(p.search(text) for p in patterns)


def match_skills(resume, jd_items, pattern_map):
    """Split JD skills into matched and missing, noting where each was found."""
    matched, missing = [], []
    for item in jd_items:
        patterns = pattern_map[item["skill"]]
        found_in = [
            name for name, content in resume["sections"].items()
            if content and _found(patterns, content)
        ]
        row = {**item, "found_in": found_in}
        (matched if found_in else missing).append(row)
    return matched, missing


def keyword_score(matched, missing):
    """Percentage of JD skills found, weighted by priority (High=3, Medium=2, Low=1)."""
    everything = matched + missing
    total = sum(PRIORITY_WEIGHT[r["priority"]] for r in everything)
    if total == 0:
        return 0.0
    got = sum(PRIORITY_WEIGHT[r["priority"]] for r in matched)
    return round(100 * got / total, 1)


def text_similarity(resume_text, jd_text):
    """TF-IDF cosine similarity between the two texts, as a percentage."""
    try:
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        m = vec.fit_transform([resume_text, jd_text])
        return round(float(cosine_similarity(m[0], m[1])[0][0]) * 100, 1)
    except ValueError:
        return 0.0


def analyze(resume, jd_text):
    jd_skills = extract_skills(jd_text)
    jd_soft = extract_soft_skills(jd_text)

    matched, missing = match_skills(resume, jd_skills, HARD_PATTERNS)
    soft_matched, soft_missing = match_skills(resume, jd_soft, SOFT_PATTERNS)

    # Skills present in the resume but NOT listed in its Skills section
    not_in_skills_section = [r["skill"] for r in matched if "skills" not in r["found_in"]]

    return {
        "keyword_score": keyword_score(matched, missing),
        "similarity": text_similarity(resume["text"], jd_text),
        "matched": matched,
        "missing": missing,
        "soft_matched": soft_matched,
        "soft_missing": soft_missing,
        "not_in_skills_section": not_in_skills_section,
        "total_jd_skills": len(jd_skills),
    }
