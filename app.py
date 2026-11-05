import streamlit as st
from resume_parser import parse_resume

st.set_page_config(page_title="ATS Analyzer", layout="wide")
st.title("Run your resume through the shortlisting simulator")

col1, col2 = st.columns(2)
with col1:
    resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])
with col2:
    jd = st.text_area("Paste Job Description", height=250)

if st.button("Check Resume-to-Job Description Matching Score"):
    if resume and jd:
        result = parse_resume(resume)
        if not result["text"].strip():
            st.error("No text could be read. The resume may be a scanned image, "
                     "which ATS systems cannot read either.")
        else:
            st.success(f"Read {result['word_count']} words from your resume.")
            st.subheader("Sections detected")
            for name, content in result["sections"].items():
                with st.expander(name.title()):
                    st.text(content)
            if result["missing"]:
                st.warning("Missing sections: " +
                           ", ".join(s.title() for s in result["missing"]))
    else:
        st.warning("Upload a resume and paste a job description.")