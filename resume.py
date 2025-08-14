import streamlit as st
import fitz
import spacy
import plotly.graph_objects as go
import google.generativeai as genai
from fuzzywuzzy import process
genai.configure(api_key="AIzaSyAyzfIQWu77PzQI3ynqg2Wu3rAz_FU3dsE")
nlp = spacy.load("en_core_web_sm")
career_paths = {
    "Full Stack Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js", "Python", "Django", "SQL", "TypeScript"],
    "Machine Learning Engineer": ["Python", "TensorFlow", "PyTorch", "Scikit-Learn", "Pandas"],
    "Cybersecurity Specialist": ["Network Security", "Cryptography", "Ethical Hacking", "Firewalls", "SIEM"],
    "Data Scientist": ["Python", "R", "SQL", "Pandas", "Machine Learning"],
    "Cloud Engineer": ["AWS", "Azure", "Google Cloud", "Docker", "Kubernetes"],
    "DevOps Engineer": ["CI/CD", "Jenkins", "Docker", "Kubernetes", "AWS"],
    "Software Engineer": ["Java", "Python", "C++", "OOP", "Data Structures"]
}
def extract_text(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    return text.strip()
def extract_skills(text):
    doc = nlp(text)
    tokens = [token.text for token in doc if token.is_alpha]

    all_skills = {skill.lower(): skill for skills in career_paths.values() for skill in skills}

    detected_skills = set()
    for token in tokens:
        match, score = process.extractOne(token.lower(), all_skills.keys())
        if score > 85: 
            detected_skills.add(all_skills[match]) 

    return list(detected_skills)
def analyze_skill_gap(current_skills, target_role):
    required_skills = set(career_paths[target_role])
    matched_skills = {skill for skill in required_skills if skill.lower() in (s.lower() for s in current_skills)}
    missing_skills = required_skills - matched_skills
    return matched_skills, missing_skills

def analyze_resume_with_gemini(pdf_text, target_role):
    prompt = f"""
    You are a chatbot helping students by guiding them with the correct study methodology.
    From this résumé, give me a good study plan and the topics that I am missing to become a {target_role}.
    Be brief and only give concise information in the form of bullet points. Also give me 3 links to coursera or udemy to the topics that I have to learn. It should be in the form
    1. Topic 1 - [Coursera](link) | [Udemy](link)... and the link should be in the form:
    https://www.udemy.com/courses/search/?src=ukw&q=<missing skills>
    https://www.coursera.org/search?query=<missing skills>

    Résumé Content:
    {pdf_text}
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error generating study plan: {e}"


def plot_radar_chart(current_skills, target_role):
    required_skills = career_paths[target_role][:5] 
    skill_levels = [1 if skill in current_skills else 0 for skill in required_skills]

    fig = go.Figure()


    fig.add_trace(go.Scatterpolar(
        r=skill_levels + [skill_levels[0]],
        theta=required_skills + [required_skills[0]],
        fill='toself',
        name='Your Skills',
        line=dict(color='blue', width=2),
        fillcolor='rgba(0, 0, 255, 0.3)'
    ))

    fig.add_trace(go.Scatterpolar(
        r=[1] * (len(required_skills) + 1),
        theta=required_skills + [required_skills[0]],
        fill='toself',
        name='Required Skills',
        line=dict(color='red', width=2, dash='dash'),
        fillcolor='rgba(255, 0, 0, 0.2)'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title="Top 5 Skills Radar Chart"
    )

    return fig

st.markdown("<h1 style='color: red;'> Skill Builder & AI Study Guide</h1>", unsafe_allow_html=True)
st.write("Upload your résumé and select your desired career path to analyze skill gaps and get a personalized study plan!")
uploaded_pdf = st.file_uploader("Upload Your Résumé (PDF)", type=["pdf"])
target_role = st.selectbox("Select Your Target Career Path", list(career_paths.keys()))
if uploaded_pdf:
    with st.spinner("Analyzing résumé..."):
        resume_text = extract_text(uploaded_pdf)
        current_skills = extract_skills(resume_text)
        matched_skills, missing_skills = analyze_skill_gap(current_skills, target_role)

    st.subheader("✅ Skills Found in Your Résumé")
    st.write(", ".join(matched_skills) if matched_skills else "No relevant skills found.")

    st.subheader("❌ Missing Skills")
    st.write(", ".join(missing_skills) if missing_skills else "You have all required skills!")

    st.plotly_chart(plot_radar_chart(matched_skills, target_role))

    if st.button("Generate Study Plan"):
        with st.spinner("Generating AI Study Plan..."):
            study_plan = analyze_resume_with_gemini(resume_text, target_role)
        st.subheader("📖 AI-Powered Study Plan")
        st.markdown(study_plan)

    
