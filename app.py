import pandas as pd
import streamlit as st
from resume_parser import parse_resume
from keywords import extract_other_keywords
from scorer import analyze

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

            m1, m2 = st.columns(2)
            m1.metric("Keyword match", f"{res['keyword_score']}%")
            m2.metric("Text similarity", f"{res['similarity']}%")
            st.progress(min(int(res["keyword_score"]), 100))

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

            if res["not_in_skills_section"]:
                st.warning(
                    "These skills appear in your resume but not in your Skills section. "
                    "Add them there so ATS filters catch them: "
                    + ", ".join(s.title() for s in res["not_in_skills_section"])
                )

            if res["soft_missing"]:
                st.write("**Soft skills to show evidence of:** " +
                         ", ".join(r["skill"].title() for r in res["soft_missing"]))

            resume_lower = parsed["text"].lower()
            other_missing = [k["keyword"] for k in extract_other_keywords(jd)
                             if k["keyword"] not in resume_lower]
            if other_missing:
                st.write("**Other JD keywords not in your resume:** " + ", ".join(other_missing))

            if parsed["missing"]:
                st.warning("Missing resume sections: " +
                           ", ".join(s.title() for s in parsed["missing"]))

            with st.expander("Resume sections detected"):
                for name, content in parsed["sections"].items():
                    st.markdown(f"**{name.title()}**")
                    st.text(content)
