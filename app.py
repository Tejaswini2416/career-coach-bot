import gradio as gr
import pdfplumber
import docx
import json
import pandas as pd
from groq import Groq

# 🔐 Paste your NEW Groq API key here
client = Groq(api_key="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")

# ----------------------------
# Resume text extraction
# ----------------------------
def extract_text(file):
    text = ""
    if file:
        if file.name.endswith(".pdf"):
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
        elif file.name.endswith(".docx"):
            doc = docx.Document(file)
            for p in doc.paragraphs:
                text += p.text + "\n"
    return text

# ----------------------------
# Save student data
# ----------------------------
def save_student(name, skills, question, feedback):
    try:
        with open("students.json", "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append({
        "name": name,
        "skills": skills,
        "question": question,
        "ai_feedback": feedback
    })

    with open("students.json", "w") as f:
        json.dump(data, f, indent=4)

# ----------------------------
# AI Career Advisor
# ----------------------------
def career_advisor(name, skills, user_input, resume):
    try:
        resume_text = extract_text(resume)

        prompt = f"""
You are a senior career counselor and hiring manager.

Student profile:
Name: {name}
Current skills: {skills}

Resume content:
{resume_text}

Student question:
{user_input}

Your task:
1. Recommend the TOP 3 career roles that best match this student.
2. For each role, explain WHY it fits their background.
3. Identify missing or weak skills for these roles.
4. Give a Resume Score from 1 to 10 with justification.
5. Give 5 clear, practical improvement steps (courses, skills, projects).

Output format:

CAREER RECOMMENDATIONS:
- Role 1:
- Role 2:
- Role 3:

SKILL GAPS:
- ...

RESUME SCORE:
x / 10 – explanation

IMPROVEMENT PLAN:
1.
2.
3.
4.
5.
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        reply = response.choices[0].message.content

        save_student(name, skills, user_input, reply)

        return reply

    except Exception as e:
        return f"Groq Error: {str(e)}"

# ----------------------------
# Load Dashboard
# ----------------------------
def load_dashboard():
    try:
        with open("students.json") as f:
            data = json.load(f)
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["name", "skills", "question", "ai_feedback"])

# ----------------------------
# Gradio UI
# ----------------------------
with gr.Blocks() as iface:
    gr.Markdown("## 🎓 AI Career Advisor & Student Dashboard")

    with gr.Tab("Career Advisor"):
        name = gr.Textbox(label="Your Name")
        skills = gr.Textbox(label="Your Skills")
        question = gr.Textbox(label="Ask Career Question")
        resume = gr.File(label="Upload Resume (PDF/DOCX)")
        output = gr.Textbox(label="AI Advice", lines=12)
        btn = gr.Button("Get Career Advice")

        btn.click(career_advisor, [name, skills, question, resume], output)

    with gr.Tab("Student Dashboard"):
        table = gr.Dataframe()
        refresh = gr.Button("Load Student Records")
        refresh.click(load_dashboard, None, table)

iface.launch()
