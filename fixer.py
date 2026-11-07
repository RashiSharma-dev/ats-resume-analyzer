import re
from checks import (split_bullets, _is_candidate, _is_strong_start, _has_metric,
                    WEAK_RE, PRONOUN_RE)

WEAK_PHRASES = [
    "participated in", "responsible for", "worked on", "worked with",
    "helped with", "helped to", "helped", "assisted in", "assisted with",
    "assisted", "involved in", "tasked with", "duties included",
]
WEAK_START_RE = re.compile(r"^(?:" + "|".join(WEAK_PHRASES) + r")\s+", re.I)

# (keywords, starting verbs, fill-in template, questions that help find a real number)
GROUPS = [
    (("model", "ml", "ai", "machine", "predict", "classif", "neural", "nlp", "llm",
      "chatbot", "detect", "recommend"),
     ["Trained", "Developed", "Fine-tuned", "Evaluated", "Implemented"],
     "Trained [model] on [dataset] using [tools], achieving [accuracy or result].",
     ["What accuracy, F1 score or error rate did you reach?",
      "How many records or images were in the dataset?",
      "How many classes, features or models did you compare?"]),
    (("data", "analysis", "analytics", "dashboard", "visual", "report", "sql", "insight"),
     ["Analyzed", "Visualized", "Cleaned", "Built", "Presented"],
     "Analyzed [dataset] using [tools] to find [insight], which [helped whom do what].",
     ["How many rows or records did you analyze?",
      "What insight or decision did it support?",
      "How much time did it save?"]),
    (("hackathon", "contest", "competition", "coding", "event", "club", "team"),
     ["Competed in", "Led", "Collaborated on", "Organized", "Won"],
     "Led a team of [number] to build [what] using [tools] at [event], placing [rank or result].",
     ["Which hackathons or contests, and what did you build?",
      "How many teams or participants took part?",
      "What rank or prize did you get, and how many members were on your team?"]),
    (("web", "app", "apps", "website", "portal", "system", "api", "stack", "frontend",
      "backend", "platform"),
     ["Built", "Developed", "Designed", "Deployed", "Implemented"],
     "Built [what] using [tools] that lets [users] do [what], with [number] features/modules.",
     ["How many features, pages or modules does it have (login, dashboard...)?",
      "How many users or test records did you use?",
      "Is it deployed? How fast or how much time does it save?"]),
    (("intern", "course", "training", "certif", "learn", "nptel", "virtual"),
     ["Completed", "Learned", "Applied", "Built", "Studied"],
     "Completed [course or internship] and applied [skill] to build [what].",
     ["How many weeks or modules did it cover?",
      "What did you build or apply from it?",
      "Did you get a score, grade or certificate?"]),
]
DEFAULT = {
    "verbs": ["Built", "Developed", "Designed", "Implemented", "Created", "Led"],
    "template": "Built [what] using [tools] that [does what], resulting in [number or result].",
    "questions": ["How many users, records or features were involved?",
                  "How much time or effort did it save?",
                  "What improved, and by how much?"],
}


def _hit(words, key):
    if len(key) <= 3:
        return key in words
    return any(w.startswith(key) for w in words)


def get_help(text):
    words = set(re.findall(r"[a-z]+", text.lower()))
    for keys, verbs, template, questions in GROUPS:
        if any(_hit(words, k) for k in keys):
            return {"verbs": verbs, "template": template, "questions": questions}
    return DEFAULT


def apply_verb(text, verb):
    t = WEAK_START_RE.sub("", text.strip()).strip(" -•")
    if not t:
        return verb
    if t.split()[0].lower() == verb.lower():
        return t[0].upper() + t[1:]
    return f"{verb} {t}"


def collect_bullets(parsed):
    """Every real bullet from Experience and Projects (same filter as the Day 4 checks)."""
    out = []
    for section in ("experience", "projects"):
        for b in split_bullets(parsed["sections"].get(section, "")):
            if _is_candidate(b):
                out.append({"section": section, "text": b})
    return out


def check_bullet(text):
    t = text.strip()
    words = t.split()
    if not words:
        return {"strong": False, "metric": False, "weak": False,
                "must": ["write something here"], "optional": []}
    must, optional = [], []
    strong = _is_strong_start(words[0])
    if not strong:
        must.append("start with a strong action verb (Built, Developed, Reduced...)")
    metric = _has_metric(t)
    if not metric:
        optional.append("(optional) add a number or result if you have one, "
                        "e.g. users, accuracy, time saved")
    m = WEAK_RE.search(t.lower())
    if m:
        must.append(f'replace the weak phrase "{m.group(0)}"')
    if PRONOUN_RE.search(t.lower()):
        must.append("remove I/my/me")
    if len(words) > 30:
        must.append("shorten it (over 30 words)")
    if len(words) < 6:
        must.append("add more detail (a bullet should be a full sentence)")
    return {"strong": strong, "metric": metric, "weak": bool(m),
            "must": must, "optional": optional}


def impact_from_list(texts):
    """Same formula as the Day 4 impact score, but for the current (edited) bullets."""
    texts = [t.strip() for t in texts if t.strip()]
    n = len(texts)
    if n == 0:
        return {"bullets_checked": 0, "score": 0, "verb_pct": 0,
                "metric_pct": 0, "weak_bullets": []}
    verb = metric = weak = 0
    flagged = []
    for t in texts:
        c = check_bullet(t)
        verb += c["strong"]
        metric += c["metric"]
        weak += c["weak"]
        if c["must"] or c["optional"]:
            flagged.append({"text": t, "issues": c["must"] + c["optional"],
                            "must": len(c["must"])})
    flagged.sort(key=lambda w: (-w["must"], -len(w["issues"])))
    verb_pct = 100 * verb / n
    metric_pct = 100 * metric / n
    metric_component = min(metric_pct / 30, 1) * 100
    weak_component = 100 * (1 - weak / n)
    score = 0.5 * verb_pct + 0.3 * metric_component + 0.2 * weak_component
    return {
        "bullets_checked": n,
        "score": round(score, 1),
        "verb_pct": round(verb_pct),
        "metric_pct": round(metric_pct),
        "weak_bullets": [{"text": w["text"], "issues": w["issues"]} for w in flagged[:6]],
    }


def apply_edits(parsed, bullets, texts):
    """Return a copy of the resume that includes the student's edited bullets."""
    extra = {}
    for b, new in zip(bullets, texts):
        if new.strip() and new.strip() != b["text"]:
            extra.setdefault(b["section"], []).append(new.strip())
    if not extra:
        return parsed
    sections = dict(parsed["sections"])
    text = parsed["text"]
    for sec, items in extra.items():
        block = "\n".join(items)
        sections[sec] = (sections.get(sec, "") + "\n" + block).strip()
        text += "\n" + block
    return {**parsed, "sections": sections, "text": text,
            "word_count": len(text.split())}
