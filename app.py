import streamlit as st
import ui
from resume_parser import safe_parse
from keywords import extract_other_keywords
from scorer import analyze
from checks import inspect_file, formatting_checks
from final_score import overall_score
from fixer import (collect_bullets, check_bullet, impact_from_list,
                   apply_edits, get_help, apply_verb)

st.set_page_config(page_title="ATS Analyzer", page_icon="🎯", layout="wide")
ui.inject_css()
ui.hero()
st.page_link("pages/1_Resume_Builder.py", label="No strong resume yet? Build one here", icon="📝")

col1, col2 = st.columns(2, gap="large")
with col1:
    with st.container(key="card_upload"):
        ui.card_title("📄", "Upload Resume", "PDF or DOCX")
        resume = st.file_uploader("Resume file", type=["pdf", "docx"],
                                  label_visibility="collapsed")
with col2:
    with st.container(key="card_jd"):
        ui.card_title("📋", "Paste Job Description",
                      "Copy from LinkedIn, Naukri, company careers pages")
        jd = st.text_area("Job description", height=170, label_visibility="collapsed",
                          placeholder="Paste the full job description here...")
        if jd.strip():
            st.caption(f"{len(jd.split())} words")


def compute(A, texts):
    working = apply_edits(A["parsed"], A["bullets"], texts)
    res = analyze(working, A["jd"])
    imp = impact_from_list(texts)
    resume_lower = working["text"].lower()
    other_missing = [k["keyword"] for k in A["other_kw"]
                     if k["keyword"] not in resume_lower]
    final = overall_score(res, working, A["fmt"], imp, other_missing)
    return res, imp, other_missing, final


def use_verb(i):
    st.session_state[f"bullet_{i}"] = apply_verb(
        st.session_state[f"bullet_{i}"], st.session_state[f"verb_{i}"])


def reset_edits():
    for i, b in enumerate(st.session_state["analysis"]["bullets"]):
        st.session_state[f"bullet_{i}"] = b["text"]


st.write("")
run = st.button("Check Resume-to-Job Description Matching Score", type="primary",
                use_container_width=True)

# ---------- Run the analysis ----------
if run:
    if not (resume and len(jd.split()) >= 30):
        st.warning("Upload a resume and paste the full job description (at least 30 words).")
    else:
        with st.spinner("Analyzing your resume..."):
            parsed = safe_parse(resume)
            if not parsed["text"].strip():
                st.session_state.pop("analysis", None)
                st.error("No text could be read. The resume may be a scanned image, "
                         "which ATS systems cannot read either.")
            else:
                info = inspect_file(resume)
                A = {
                    "parsed": parsed,
                    "jd": jd,
                    "fmt": formatting_checks(parsed, info),
                    "bullets": collect_bullets(parsed),
                    "other_kw": extract_other_keywords(jd),
                }
                for k in [k for k in st.session_state
                          if k.startswith(("bullet_", "verb_"))]:
                    del st.session_state[k]
                for i, b in enumerate(A["bullets"]):
                    st.session_state[f"bullet_{i}"] = b["text"]
                checks0 = [check_bullet(b["text"]) for b in A["bullets"]]
                A["todo"] = sorted(
                    (i for i, c in enumerate(checks0) if c["must"] or c["optional"]),
                    key=lambda i: -len(checks0[i]["must"]))
                _, _, _, final0 = compute(A, [b["text"] for b in A["bullets"]])
                A["start_total"] = final0["total"]
                st.session_state["analysis"] = A

# ---------- Show results ----------
A = st.session_state.get("analysis")
if A:
    texts = [st.session_state.get(f"bullet_{i}", b["text"])
             for i, b in enumerate(A["bullets"])]
    res, imp, other_missing, final = compute(A, texts)
    parsed, fmt = A["parsed"], A["fmt"]
    delta = round(final["total"] - A["start_total"], 1)

    st.write("")
    left, right = st.columns([1, 1.5], gap="large")
    with left:
        ui.gauge(final["total"], final["label"], delta)
    with right:
        st.subheader("Fix this first")
        ui.fix_cards(final["fixes"])

    with st.expander("How the score is calculated"):
        ui.breakdown_bars(final["breakdown"])

    tab_fix, tab1, tab2, tab3 = st.tabs(
        ["Fix my bullets", "Job match", "Resume health", "Sections"])

    # ----- Bullet Fixer -----
    with tab_fix:
        st.write("Edit your bullet points below. The score updates as you edit. "
                 "Press Ctrl+Enter or tap outside the box to apply a change.")
        st.info("Only write what is true. Add numbers only if you have the real figures.")
        if not A["bullets"]:
            st.info("No bullet points were found under Experience or Projects. "
                    "Add bullets that describe what you did and the result.")
        else:
            todo = A["todo"]
            st.caption(f"{len(A['bullets']) - len(todo)} bullet(s) already look good.")
            for i in todo:
                c = check_bullet(texts[i])
                help_ = get_help(A["bullets"][i]["text"])
                with st.container(key=f"card_fix_{i}"):
                    st.text_area(f"Bullet {i + 1}", key=f"bullet_{i}", height=100)
                    if not c["must"] and not c["optional"]:
                        st.success("Looks good")
                    for msg in c["must"]:
                        st.markdown(f"❌ {msg}")
                    for msg in c["optional"]:
                        st.markdown(f"💡 {msg}")
                    if not c["strong"]:
                        v1, v2 = st.columns([3, 1])
                        v1.selectbox("Pick a starting verb", help_["verbs"],
                                     key=f"verb_{i}")
                        v2.button("Apply verb", key=f"apply_{i}",
                                  on_click=use_verb, args=(i,))
                    if not c["metric"]:
                        with st.expander("Need a number? Answer these questions"):
                            for q in help_["questions"]:
                                st.markdown(f"- {q}")
                    with st.expander("Fill-in template"):
                        st.code(help_["template"], language="text")

            st.button("Reset all edits", on_click=reset_edits)
            st.subheader("Your improved bullets")
            st.caption("Copy these into your resume using the copy icon in the box.")
            st.code("\n".join("• " + t.strip() for t in texts if t.strip()),
                    language="text")

    # ----- Job match -----
    with tab1:
        m1, m2 = st.columns(2)
        m1.metric("Keyword match", f"{res['keyword_score']}%")
        m2.metric("Text similarity", f"{res['similarity']}%")
        if res["total_jd_skills"] == 0:
            st.info("No known technical skills were found in this job description.")
        else:
            st.subheader(f"Missing skills ({len(res['missing'])})")
            if res["missing"]:
                st.caption("Red: required and repeated. Amber: required. Grey: preferred.")
                ui.skill_chips(res["missing"], "missing")
            else:
                st.success("Your resume covers every skill in this job description.")
            st.subheader(f"Matched skills ({len(res['matched'])})")
            if res["matched"]:
                ui.skill_chips(res["matched"], "matched")
        if res["soft_missing"]:
            st.write("**Soft skills to show evidence of**")
            ui.tags([pretty for pretty in (ui.pretty(r["skill"]) for r in res["soft_missing"])])
        if other_missing:
            st.write("**Other job description keywords not in your resume**")
            ui.tags(other_missing)

    # ----- Resume health -----
    with tab2:
        h1, h2 = st.columns(2)
        h1.metric("Formatting score", f"{fmt['score']}%")
        h2.metric("Impact score",
                  f"{imp['score']}%" if imp["bullets_checked"] else "N/A")
        st.subheader("Formatting and ATS readability")
        for c in fmt["checks"]:
            st.markdown(("✅ " if c["passed"] else "❌ ") + c["message"])
        st.subheader("Impact of your bullet points")
        if imp["bullets_checked"] == 0:
            st.info("No bullet points were found under Experience or Projects, "
                    "so impact could not be checked.")
        else:
            i1, i2 = st.columns(2)
            i1.metric("Start with an action verb", f"{imp['verb_pct']}%")
            i2.metric("Contain numbers", f"{imp['metric_pct']}%")
            st.caption(f"{imp['bullets_checked']} bullet points checked.")
            if imp["weak_bullets"]:
                st.write("**Bullets still to improve (weakest first):**")
                for w in imp["weak_bullets"]:
                    st.markdown(f"> {w['text']}")
                    st.caption("Fix: " + "; ".join(w["issues"]))
            else:
                st.success("Your bullet points look strong.")

    # ----- Sections -----
    with tab3:
        if parsed["missing"]:
            st.warning("Missing resume sections: " +
                       ", ".join(s.title() for s in parsed["missing"]))
        for name, content in parsed["sections"].items():
            with st.expander(name.title()):
                st.text(content)
