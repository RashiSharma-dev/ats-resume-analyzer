import pandas as pd
import streamlit as st
from resume_parser import parse_resume
from keywords import extract_other_keywords
from scorer import analyze
from checks import inspect_file, formatting_checks
from final_score import overall_score
from fixer import (collect_bullets, check_bullet, impact_from_list,
                   apply_edits, get_help, apply_verb)

st.set_page_config(page_title="ATS Analyzer", layout="wide")
st.title("Run your resume through the shortlisting simulator")

col1, col2 = st.columns(2)
with col1:
    resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])
with col2:
    jd = st.text_area("Paste Job Description", height=250)


def to_table(rows):
    return pd.DataFrame([
        {
            "Skill": r["skill"].title(),
            "Priority": r["priority"],
            "Found in": ", ".join(s.title() for s in r["found_in"]) or "-",
        }
        for r in rows
    ])


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


# ---------- Run the analysis ----------
if st.button("Check Resume-to-Job Description Matching Score", use_container_width=True):
    if not (resume and jd):
        st.warning("Upload a resume and paste a job description.")
    else:
        parsed = parse_resume(resume)
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
            for k in [k for k in st.session_state if k.startswith(("bullet_", "verb_"))]:
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

    st.divider()
    delta = round(final["total"] - A["start_total"], 1)
    st.metric("ATS match estimate", f"{final['total']} / 100",
              delta=f"{delta:+.1f}" if delta else None)
    st.subheader(final["label"])
    st.progress(min(int(final["total"]), 100))
    st.caption("This is an estimate. Real ATS software does not publish its scoring.")

    st.subheader("Fix this first")
    if final["fixes"]:
        for i, f in enumerate(final["fixes"], 1):
            st.markdown(f"**{i}. {f['title']}** (about +{f['gain']} points)")
            st.write(f["detail"])
    else:
        st.success("Nothing major to fix. Your resume matches this job well.")

    st.subheader("How the score is calculated")
    st.dataframe(pd.DataFrame(final["breakdown"]), hide_index=True)

    tab_fix, tab1, tab2, tab3 = st.tabs(
        ["Fix my bullets", "Job match", "Resume health", "Sections"])

    # ----- Bullet Fixer -----
    with tab_fix:
        st.write("Edit your bullet points below. The score above updates as you edit. "
                 "Press Ctrl+Enter or tap outside the box to apply a change.")
        st.info("Only write what is true. Add numbers only if you have the real figures.")
        if not A["bullets"]:
            st.info("No bullet points were found under Experience or Projects. "
                    "Add bullets that describe what you did and the result.")
        else:
            todo = A["todo"]
            ok_now = sum(1 for i in todo if not check_bullet(texts[i])["must"])
            st.caption(f"{len(A['bullets']) - len(todo)} bullet(s) already look good. "
                       f"Bullets below without must-fix issues: {ok_now} of {len(todo)}.")
            for i in todo:
                c = check_bullet(texts[i])
                help_ = get_help(A["bullets"][i]["text"])
                with st.container(border=True):
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
                st.dataframe(to_table(res["missing"]), hide_index=True)
            else:
                st.success("Your resume covers every skill in this job description.")
            st.subheader(f"Matched skills ({len(res['matched'])})")
            if res["matched"]:
                st.dataframe(to_table(res["matched"]), hide_index=True)
        if res["soft_missing"]:
            st.write("**Soft skills to show evidence of:** " +
                     ", ".join(r["skill"].title() for r in res["soft_missing"]))
        if other_missing:
            st.write("**Other JD keywords not in your resume:** " +
                     ", ".join(other_missing))

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
