import streamlit as st
from fixer import check_bullet
from resume_docx import build_docx, bullet_lines

st.set_page_config(page_title="Resume Builder", layout="wide")
st.title("Resume Builder for freshers")
st.write("Fill in your real details. The app builds a clean, single-column, "
         "ATS-friendly resume and flags weak bullet points while you type.")
st.info("Only write what is true. Add numbers only if you have the real figures.")
st.page_link("app.py", label="Back to the ATS analyzer", icon="🏠")


def feedback(text):
    """Show must-fix and optional notes for each bullet line in a text box."""
    for line in bullet_lines(text):
        c = check_bullet(line)
        short = line if len(line) <= 55 else line[:55] + "..."
        if c["must"]:
            st.markdown(f"❌ **{short}** {'; '.join(c['must'])}")
        elif c["optional"]:
            st.caption(f"💡 {short} Add a number or result if you have one.")


# ---------- 1. Contact ----------
st.header("1. Contact")
c1, c2 = st.columns(2)
name = c1.text_input("Full name")
city = c2.text_input("City, State")
email = c1.text_input("Email")
phone = c2.text_input("Phone (with country code)", placeholder="+91 98765 43210")
linkedin = c1.text_input("LinkedIn URL")
github = c2.text_input("GitHub URL")

# ---------- 2. Summary ----------
st.header("2. Summary (optional)")
summary = st.text_area("Summary", height=100, label_visibility="collapsed")
st.caption("2-3 lines. Template: Final-year [degree] student with hands-on projects in "
           "[area]. Skilled in [3 skills]. Looking for [role] opportunities.")

# ---------- 3. Education ----------
st.header("3. Education")
n_edu = st.number_input("Number of education entries", 1, 3, 1)
education = []
for i in range(int(n_edu)):
    st.markdown(f"**Entry {i + 1}**")
    a, b = st.columns(2)
    education.append({
        "institute": a.text_input("College / school", key=f"edu_inst_{i}"),
        "degree": b.text_input("Degree and branch", key=f"edu_deg_{i}",
                               placeholder="B.Tech, Computer Science (AI/ML)"),
        "years": a.text_input("Years", key=f"edu_years_{i}", placeholder="2022 - 2026"),
        "score": b.text_input("CGPA / percentage", key=f"edu_score_{i}",
                              placeholder="CGPA: 8.5"),
    })

# ---------- 4. Skills ----------
st.header("4. Skills")
st.caption("Separate skills with commas. List only what you can discuss in an interview.")
skills = [
    ("Languages", st.text_input("Languages", placeholder="Python, Java, SQL")),
    ("Frameworks & Libraries", st.text_input("Frameworks & Libraries",
                                             placeholder="Streamlit, scikit-learn, React")),
    ("Tools & Databases", st.text_input("Tools & Databases",
                                        placeholder="Git, Docker, MySQL")),
    ("Concepts", st.text_input("Concepts",
                               placeholder="Machine Learning, NLP, Data Structures")),
]

# ---------- 5. Projects ----------
st.header("5. Projects")
n_proj = st.number_input("Number of projects", 0, 6, 2)
projects = []
for i in range(int(n_proj)):
    with st.container(border=True):
        st.markdown(f"**Project {i + 1}**")
        a, b = st.columns(2)
        title = a.text_input("Project name", key=f"proj_title_{i}")
        tech = b.text_input("Tools used", key=f"proj_tech_{i}",
                            placeholder="Python, Streamlit, scikit-learn")
        link = a.text_input("Link (optional)", key=f"proj_link_{i}",
                            placeholder="github.com/yourname/project")
        bullets = st.text_area("What you did (one bullet per line)", key=f"proj_b_{i}",
                               height=120,
                               placeholder="Built a ... using ... that ...")
        feedback(bullets)
        projects.append({"title": title, "tech": tech, "link": link, "bullets": bullets})
st.caption("Bullet formula: Action verb + what you built + tools + result. "
           "Example: Built a resume parser in Python that reads PDF and DOCX files.")

# ---------- 6. Experience ----------
st.header("6. Internships / experience (optional)")
n_exp = st.number_input("Number of entries", 0, 3, 0)
experience = []
for i in range(int(n_exp)):
    with st.container(border=True):
        st.markdown(f"**Entry {i + 1}**")
        a, b = st.columns(2)
        role = a.text_input("Role", key=f"exp_role_{i}")
        org = b.text_input("Organization", key=f"exp_org_{i}")
        dates = a.text_input("Dates", key=f"exp_dates_{i}", placeholder="Jun 2025 - Aug 2025")
        bullets = st.text_area("What you did (one bullet per line)", key=f"exp_b_{i}",
                               height=120)
        feedback(bullets)
        experience.append({"role": role, "org": org, "dates": dates, "bullets": bullets})

# ---------- 7. Certifications and achievements ----------
st.header("7. Certifications and achievements (optional)")
certifications = st.text_area("Certifications (one per line)", height=100,
                              placeholder="Cloud Computing - NPTEL (2025)")
achievements = st.text_area("Achievements, hackathons, positions (one per line)", height=100,
                            placeholder="Top 10 in College Coding Contest (2025)")

# ---------- 8. Download ----------
st.header("8. Download")
data = {
    "name": name, "city": city, "email": email, "phone": phone,
    "linkedin": linkedin, "github": github, "summary": summary,
    "education": education, "skills": skills, "projects": projects,
    "experience": experience, "certifications": certifications,
    "achievements": achievements,
}

missing = []
if not name.strip():
    missing.append("your name")
if not email.strip():
    missing.append("your email")
if not phone.strip():
    missing.append("your phone number")
if not (linkedin.strip() or github.strip()):
    missing.append("a LinkedIn or GitHub link")
if not any(v.strip() for _, v in skills):
    missing.append("your skills")
if sum(1 for p in projects if p["title"].strip()) < 2:
    missing.append("at least 2 projects")
if missing:
    st.warning("Recommended before downloading: add " + ", ".join(missing) + ".")

if name.strip():
    st.download_button(
        "Download resume (DOCX)",
        data=build_docx(data),
        file_name=name.strip().replace(" ", "_") + "_Resume.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )
else:
    st.button("Download resume (DOCX)", disabled=True, use_container_width=True)
    st.caption("Enter your name to enable the download.")

st.caption("For a PDF: open the downloaded file in Word and choose File, Save As, PDF.")
st.page_link("app.py", label="Check this resume against a job description", icon="🎯")
