import pandas as pd
import streamlit as st
from resume_parser import parse_resume
from keywords import extract_other_keywords
from scorer import analyze
from checks import inspect_file, formatting_checks, impact_analysis
from final_score import overall_score

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


if st.button("Check Resume-to-Job Description Matching Score", use_container_width=True):
    if not (resume and jd):
        st.warning("Upload a resume and paste a job description.")
    else:
        parsed = parse_resume(resume)
        if not parsed["text"].strip():
            st.error("No text could be read. The resume may be a scanned image, "
                     "which ATS systems cannot read either.")
        else:
            res = analyze(parsed, jd)
            info = inspect_file(resume)
            fmt = formatting_checks(parsed, info)
            imp = impact_analysis(parsed)

            resume_lower = parsed["text"].lower()
            other_missing = [k["keyword"] for k in extract_other_keywords(jd)
                             if k["keyword"] not in resume_lower]
            final = overall_score(res, parsed, fmt, imp, other_missing)

            # ----- Headline score -----
            st.divider()
            st.header(f"ATS match estimate: {final['total']} / 100")
            st.subheader(final["label"])
            st.progress(min(int(final["total"]), 100))
            st.caption("This is an estimate. Real ATS software does not publish its scoring.")

            # ----- Fix this first -----
            st.subheader("Fix this first")
            if final["fixes"]:
                for i, f in enumerate(final["fixes"], 1):
                    st.markdown(f"**{i}. {f['title']}** (about +{f['gain']} points)")
                    st.write(f["detail"])
            else:
                st.success("Nothing major to fix. Your resume matches this job well.")

            # ----- Breakdown -----
            st.subheader("How the score is calculated")
            st.dataframe(pd.DataFrame(final["breakdown"]), hide_index=True)

            # ----- Details -----
            tab1, tab2, tab3 = st.tabs(["Job match", "Resume health", "Sections"])

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
                        st.write("**Bullets to improve (weakest first):**")
                        for w in imp["weak_bullets"]:
                            st.markdown(f"> {w['text']}")
                            st.caption("Fix: " + "; ".join(w["issues"]))
                        st.info("Formula for a strong bullet: Action verb + what you built "
                                "+ tools used + measurable result.")
                    else:
                        st.success("Your bullet points look strong.")

            with tab3:
                if parsed["missing"]:
                    st.warning("Missing resume sections: " +
                               ", ".join(s.title() for s in parsed["missing"]))
                for name, content in parsed["sections"].items():
                    with st.expander(name.title()):
                        st.text(content)
