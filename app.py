import streamlit as st

st.set_page_config(page_title="ATS Analyzer", layout="wide")
st.title("Run your resume through the shortlisting simulator")

col1, col2 = st.columns(2)
with col1:
    resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])
with col2:
    jd = st.text_area("Paste Job Description", height=250)

if st.button("Check Resume-to-Job Description Matching Score"):
    if resume and jd:
        st.success("Received. Scoring comes later.")
    else:
        st.warning("Upload a resume and paste a job description.")
