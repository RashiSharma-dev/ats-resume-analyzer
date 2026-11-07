import html
import streamlit as st

SPECIAL = {
    "node.js": "Node.js", "scikit-learn": "scikit-learn", "power bi": "Power BI",
    "tensorflow": "TensorFlow", "pytorch": "PyTorch", "opencv": "OpenCV",
    "mysql": "MySQL", "postgresql": "PostgreSQL", "mongodb": "MongoDB",
    "javascript": "JavaScript", "typescript": "TypeScript", "fastapi": "FastAPI",
    "langchain": "LangChain", "langgraph": "LangGraph", "hugging face": "Hugging Face",
    "aws": "AWS", "gcp": "GCP", "sql": "SQL", "nlp": "NLP", "llm": "LLM",
    "html": "HTML", "css": "CSS", "etl": "ETL", "oop": "OOP", "rag": "RAG",
    "mlops": "MLOps", "ci/cd": "CI/CD", "a/b testing": "A/B Testing",
    "rest api": "REST API", "agentic ai": "Agentic AI", "generative ai": "Generative AI",
    "r programming": "R", "c++": "C++", "c#": "C#", "github": "GitHub",
}


def pretty(skill):
    s = skill.lower()
    return SPECIAL.get(s, s.title())


def score_color(s):
    if s >= 70:
        return "#16a34a"
    if s >= 45:
        return "#f59e0b"
    return "#ef4444"


CSS = """
.stApp{background:radial-gradient(1200px 520px at 50% -10%,#e9ecff 0%,#f6f7ff 45%,#ffffff 100%);}
.block-container{max-width:1100px;padding-top:2.2rem;padding-bottom:4rem;}
footer{visibility:hidden;}

div.hero{text-align:center;margin:0 auto 1.4rem;max-width:820px;}
div.hero .pill{display:inline-block;font-size:.72rem;font-weight:700;letter-spacing:.12em;color:#4338ca;background:#eef0ff;border:1px solid #d9ddff;padding:.28rem .85rem;border-radius:999px;}
div.hero h1{font-size:2.6rem !important;line-height:1.15 !important;font-weight:800 !important;margin:.9rem 0 .6rem !important;padding:0 !important;color:#14172f;letter-spacing:-.02em;}
div.hero .grad{background:linear-gradient(90deg,#4f46e5,#38bdf8);-webkit-background-clip:text;background-clip:text;color:transparent;}
div.hero p{color:#5b6082;font-size:1.02rem;margin:0;}

[class*="st-key-card"]{background:#ffffff;border:1px solid #e6e9f7;border-radius:18px;padding:1.1rem 1.2rem;box-shadow:0 8px 28px rgba(79,70,229,.07);}
.ctitle{display:flex;align-items:center;gap:.7rem;margin-bottom:.6rem;}
.cicon{width:38px;height:38px;border-radius:12px;background:#eef0ff;display:flex;align-items:center;justify-content:center;font-size:1.1rem;}
.ct{font-weight:700;color:#14172f;line-height:1.2;}
.cs{font-size:.78rem;color:#7a7f9e;}

[data-testid="stFileUploaderDropzone"]{background:#f3faf5;border:1.5px dashed #86c9a0;border-radius:14px;}
textarea{border-radius:12px !important;}

button[kind="primary"],button[data-testid="stBaseButton-primary"]{background:linear-gradient(90deg,#3730a3,#4f8ef7 55%,#38bdf8);border:0;border-radius:999px;padding:.85rem 1.4rem;font-weight:700;color:#ffffff;box-shadow:0 10px 26px rgba(79,70,229,.30);transition:transform .15s ease,box-shadow .15s ease;}
button[kind="primary"]:hover,button[data-testid="stBaseButton-primary"]:hover{transform:translateY(-1px);box-shadow:0 14px 30px rgba(79,70,229,.36);color:#ffffff;}
.stButton>button{border-radius:12px;}

.scorecard{text-align:center;padding:1.4rem 1rem;background:#ffffff;border:1px solid #e6e9f7;border-radius:20px;box-shadow:0 8px 28px rgba(79,70,229,.07);}
.gauge{width:176px;height:176px;border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center;background:conic-gradient(var(--c) calc(var(--p) * 1%),#e8ebf7 0);}
.gauge-in{width:136px;height:136px;border-radius:50%;background:#ffffff;display:flex;flex-direction:column;align-items:center;justify-content:center;}
.gnum{font-size:2.7rem;font-weight:800;line-height:1;color:#14172f;}
.gsub{font-size:.75rem;color:#7a7f9e;margin-top:.25rem;}
.glabel{font-weight:700;margin-top:.9rem;color:#14172f;}
.gdelta{font-size:.82rem;font-weight:600;margin-top:.3rem;}
.gdelta.up{color:#16a34a;}
.gdelta.down{color:#dc2626;}
.gnote{font-size:.72rem;color:#8a8fab;margin-top:.7rem;}

.fixcard{display:flex;gap:.9rem;align-items:flex-start;background:#ffffff;border:1px solid #e6e9f7;border-radius:16px;padding:.85rem 1rem;margin-bottom:.6rem;}
.fixnum{flex:0 0 auto;width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#4f46e5,#38bdf8);color:#ffffff;font-weight:700;display:flex;align-items:center;justify-content:center;font-size:.9rem;}
.fixtitle{font-weight:700;color:#14172f;display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;}
.gain{font-size:.72rem;font-weight:700;color:#15803d;background:#e7f7ec;border-radius:999px;padding:.12rem .55rem;}
.fixdetail{color:#4a4f70;font-size:.9rem;margin-top:.25rem;}

.brow{margin-bottom:.8rem;}
.btop{display:flex;justify-content:space-between;gap:.6rem;font-size:.86rem;color:#2b2f55;margin-bottom:.25rem;flex-wrap:wrap;}
.btrack{height:9px;background:#e8ebf7;border-radius:999px;overflow:hidden;}
.bfill{height:100%;border-radius:999px;}

.chips{display:flex;flex-wrap:wrap;gap:.45rem;margin:.3rem 0 1rem;}
.chip{display:inline-flex;align-items:center;gap:.4rem;padding:.3rem .75rem;border-radius:999px;font-size:.84rem;font-weight:600;border:1px solid transparent;}
.chip small{font-size:.66rem;font-weight:700;opacity:.75;text-transform:uppercase;letter-spacing:.04em;}
.c-high{background:#fdecec;color:#b42318;border-color:#f8cfcf;}
.c-med{background:#fff4e0;color:#b45309;border-color:#fbe0b0;}
.c-low{background:#eef0f6;color:#555b7a;border-color:#dde0ec;}
.c-ok{background:#e7f7ec;color:#15803d;border-color:#c5ebd0;}
.c-tag{background:#eef0ff;color:#4338ca;border-color:#d9ddff;}

[data-testid="stMetric"]{background:#ffffff;border:1px solid #e6e9f7;border-radius:14px;padding:.7rem 1rem;}
button[data-baseweb="tab"]{font-weight:600;}
div[data-baseweb="base-input"]{background:transparent !important;}
div[data-baseweb="input"],div[data-baseweb="textarea"],div[data-baseweb="select"]>div{background:#ffffff !important;border:1.5px solid #c9d0e8 !important;border-radius:12px !important;box-shadow:0 1px 2px rgba(20,23,47,.05);}
div[data-baseweb="input"]:focus-within,div[data-baseweb="textarea"]:focus-within,div[data-baseweb="select"]>div:focus-within{border-color:#4f46e5 !important;box-shadow:0 0 0 3px rgba(79,70,229,.15) !important;}
div[data-baseweb="input"] input,div[data-baseweb="textarea"] textarea{background:transparent !important;}

@media (max-width: 640px){
  .block-container{padding:1rem .85rem 3rem;}
  div.hero h1{font-size:1.75rem !important;}
  div.hero p{font-size:.92rem;}
  [class*="st-key-card"]{padding:.9rem .9rem;}
  .gauge{width:148px;height:148px;}
  .gauge-in{width:112px;height:112px;}
  .gnum{font-size:2.2rem;}
  .fixcard{padding:.75rem .8rem;}
}
"""


def inject_css():
    st.markdown("<style>" + CSS + "</style>", unsafe_allow_html=True)


def hero():
    st.markdown(
        '<div class="hero"><span class="pill">ATS ANALYZER</span>'
        '<h1>Run your resume through the <span class="grad">shortlisting simulator</span></h1>'
        '<p>Upload your resume, paste the job description, get an instant match score, '
        'then fix the weak points right here.</p></div>',
        unsafe_allow_html=True)


def card_title(icon, title, sub=""):
    st.markdown(
        f'<div class="ctitle"><span class="cicon">{icon}</span><div>'
        f'<div class="ct">{html.escape(title)}</div>'
        f'<div class="cs">{html.escape(sub)}</div></div></div>',
        unsafe_allow_html=True)


def gauge(score, label, delta=0):
    c = score_color(score)
    d = ""
    if delta:
        cls = "up" if delta > 0 else "down"
        d = f'<div class="gdelta {cls}">{delta:+.1f} since you started editing</div>'
    st.markdown(
        f'<div class="scorecard"><div class="gauge" style="--p:{score};--c:{c}">'
        f'<div class="gauge-in"><span class="gnum">{score:.0f}</span>'
        f'<span class="gsub">out of 100</span></div></div>'
        f'<div class="glabel">{html.escape(label)}</div>{d}'
        f'<div class="gnote">Estimate only. Real ATS software does not publish its scoring.</div>'
        f'</div>',
        unsafe_allow_html=True)


def fix_cards(fixes):
    if not fixes:
        st.success("Nothing major to fix. Your resume matches this job well.")
        return
    parts = []
    for i, f in enumerate(fixes, 1):
        parts.append(
            f'<div class="fixcard"><div class="fixnum">{i}</div><div class="fixbody">'
            f'<div class="fixtitle">{html.escape(f["title"])}'
            f'<span class="gain">+{f["gain"]} pts</span></div>'
            f'<div class="fixdetail">{html.escape(f["detail"])}</div></div></div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


def breakdown_bars(rows):
    parts = []
    for r in rows:
        s = int(r["Score"].split("/")[0])
        parts.append(
            f'<div class="brow"><div class="btop"><span>{html.escape(r["Component"])}</span>'
            f'<span>{s}/100 &middot; weight {html.escape(r["Weight"])}</span></div>'
            f'<div class="btrack"><div class="bfill" '
            f'style="width:{s}%;background:{score_color(s)}"></div></div></div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


def skill_chips(rows, mode):
    if not rows:
        return
    out = []
    for r in rows:
        name = html.escape(pretty(r["skill"]))
        if mode == "missing":
            cls = {"High": "c-high", "Medium": "c-med", "Low": "c-low"}[r["priority"]]
            out.append(f'<span class="chip {cls}">{name}<small>{r["priority"]}</small></span>')
        else:
            out.append(f'<span class="chip c-ok">{name}</span>')
    st.markdown('<div class="chips">' + "".join(out) + "</div>", unsafe_allow_html=True)


def tags(items):
    if not items:
        return
    out = [f'<span class="chip c-tag">{html.escape(str(t))}</span>' for t in items]
    st.markdown('<div class="chips">' + "".join(out) + "</div>", unsafe_allow_html=True)
