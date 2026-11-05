import pandas as pd
import streamlit as st
from resume_parser import parse_resume
from keywords import extract_skills, extract_soft_skills, extract_other_keywords

st.set_page_config(page_title="ATS Analyzer", layout="wide")
st.title("Run your resume through the shortlisting simulator")

col1, col2 = st.columns(2)
with col1:
    resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])
with col2:
    jd = st.text_area("Paste Job Description", height=250)

if st.button("Check Resume-to-Job Description Matching Score"):
    if not (resume and jd):
        st.warning("Upload a resume and paste a job description.")
    else:
        result = parse_resume(resume)
        if not result["text"].strip():
            st.error("No text could be read. The resume may be a scanned image, "
                     "which ATS systems cannot read either.")
        else:
            st.success(f"Read {result['word_count']} words from your resume.")

            st.subheader("Skills the job description asks for")
            skills = extract_skills(jd)
            if skills:
                st.dataframe(pd.DataFrame(skills), use_container_width=True, hide_index=True)
            else:
                st.info("No known technical skills found in this job description.")

            soft = extract_soft_skills(jd)
            if soft:
                st.write("**Soft skills:** " + ", ".join(s["skill"] for s in soft))

            other = extract_other_keywords(jd)
            if other:
                st.write("**Other frequent keywords:** " +
                         ", ".join(k["keyword"] for k in other))

            with st.expander("Resume sections detected (Day 1)"):
                for name, content in result["sections"].items():
                    st.markdown(f"**{name.title()}**")
                    st.text(content)
                if result["missing"]:
                    st.warning("Missing sections: " +
                               ", ".join(s.title() for s in result["missing"]))