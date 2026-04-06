import os
from flask import Flask, redirect, session, jsonify, render_template, request
from werkzeug.utils import secure_filename
from openai import OpenAI
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import pdfplumber
import requests
from flask import request, jsonify

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_hackathon_key"

# Upload folder
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create folder if not exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# OAuth setup
oauth = OAuth(app)

oauth.register(
    name="auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration',
    client_kwargs={"scope": "openid profile email"}
    
)

# Home
@app.route("/")
def home():
    return render_template("index.html")

# Login
@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=os.getenv("AUTH0_CALLBACK_URL")
    )

# Callback
@app.route("/callback")
def callback():
    error = request.args.get("error")

    if error:
        return redirect("/")
    token = oauth.auth0.authorize_access_token()

    user = oauth.auth0.get(
        f"https://{os.getenv('AUTH0_DOMAIN')}/userinfo"
    ).json()

    session["user"] = user
    return redirect("/dashboard")

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", user=session["user"])

# AI Career Copilot

@app.route("/ai-chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message")

        resume_skills = session.get("resume_skills", [])
        github_skills = session.get("github_skills", [])

        # CALL FUNCTION CORRECTLY
        reply = ai_chat(user_message, resume_skills, github_skills)

        return jsonify({"reply": reply})

    except Exception as e:
        print("Error in AI Chat:", e)
        return jsonify({
            "reply": f"""
        Ai career mentor
        
        Based on your current skills:
         Improve your GitHub projects (add real-world features)
         Learn trending skills like AI, Web Development, or Cloud
         Build at least 2–3 strong portfolio projects

         Next Step:
        Start one mini project today and upload it to GitHub!
        """
    })

    


# AI FUNCTION 
from openai import OpenAI
client = OpenAI(api_key=os.getenv("NVIDIA_API_KEY"))

def ai_chat(user_message, resume_skills, github_skills):

    # GREETING FIRST (FAST RESPONSE)
    if user_message.lower() in ["hi", "hello", "hey", "hii", "hlo", "greetings"]:
        return f"""
Hey Buddy! 👋
Welcome to your AI Career Mentor!

I'm your AI Career Copilot 

I can help you with:
• Career guidance
• Skill improvement
• Resume tips
• Project ideas

Try asking:
- What skills should I learn for AI?
- How can I improve my resume?
- Am I job ready?
"""

    # AI RESPONSE
    prompt = f"""
You are an AI Career Mentor.

Student Resume Skills:
{resume_skills}

Student GitHub Skills:
{github_skills}

User Question:
{user_message}

instruction:
-Answer in simple english, be concise and actionable.
-Use emojis to make it friendly.
-Provide specific advice based on the skills listed.
-If the user asks about career paths, suggest roles based on their skills.
-If the user asks about improving their resume, give 3 specific tips.
-suggest waht to improve based on the skills and github repos
-keep the tone friendly and encouraging.
-keep it short and to the point, no long explanations.
-at the end, always give 1-2 specific next steps the user can take to improve their career prospects. 
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return jsonify({
        "reply": f"""
🚀 AI Career Tip:

Based on your profile, here’s what you can do:

👉 Improve your projects (add real-world use cases)
👉 Learn in-demand skills like AI, Web Dev, or Cloud
👉 Build at least 2–3 strong portfolio projects

💡 Next Step:
Start one mini project today and push it to GitHub!
"""

    })

# Resume Upload

@app.route("/upload", methods=["POST"])
def upload_resume():
    file = request.files["resume"]

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(path)

    text = ""

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted

    text_lower = text.lower()

    keywords = [
        "python", "java", "machine learning",
        "html", "css", "javascript",
        "sql", "react", "flask"
    ]

    resume_skills = []

    #  FIXED LOOP (was outside before)
    for skill in keywords:
        if skill in text_lower:
            resume_skills.append(skill.capitalize())

    #  REMOVE DUPLICATE LOGIC (you had this twice)

    #  SAVE IN SESSION
    session["resume_skills"] = resume_skills

    return jsonify({
        "message": "Resume uploaded successfully",
        "skills": resume_skills
    })

#  GitHub Analysis API WITH AI LOGIC

@app.route("/github-analysis", methods=["POST"])
def github_analysis():
    username = request.json.get("username")

    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({
            "error": "GitHub user not found or API error"
        }), 404
    repos = response.json()

    project_list = []
    for repo in repos:
        project_list.append({
            "name": repo.get("name"),
            "language": repo.get("language")
        })
    repo_count = len(repos)

    languages = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
    top_language = max(languages, key=languages.get) if languages else "None"
    
    # DEFINE FIRST
    github_skills = list(languages.keys())
    session["github_skills"] = github_skills

    # resume..
    resume_skills = session.get("resume_skills", [])
    combined_skills = list(set(github_skills + resume_skills))

    score = min(100, repo_count * 10 + len(resume_skills) * 5)
    if score > 70:
        level = "Strong Profile"
    elif score > 40:
        level = "Growing Profile"
    else:
        level = "Beginner profile"
      

    suggestions = []

    if repo_count < 5:
        suggestions.append("Build more GitHub projects")

    if len(resume_skills) < 3:
        suggestions.append("Add more skills to your resume")

    if "Python" not in combined_skills:
        suggestions.append("Learn Python for AI roles")

    if "JavaScript" not in combined_skills:
        suggestions.append("Add frontend skills")

    career = "General Developer"

    if "Java" in combined_skills:
        career = "Backend Developer"
    if "Python" in combined_skills:
        career = "AI/ML Engineer"
    if "JavaScript" in combined_skills:
        career = "Full Stack Developer"

    return jsonify({
        "github_user": username,
        "repo_count": repo_count,
        "languages": languages,
        "top_language": top_language,
        "resume_skills": resume_skills,
        "combined_skills": combined_skills,
        "score": score,
        "profile_level": level,
        "projects": project_list,
        "suggestions": suggestions,
        "career": career


    })

# Test API
@app.route("/api/data")
def api_data():
    return jsonify({
        "name": "DHAMODHARAN A",
        "project": "AI Career Copilot",
        "goal": "Win Auth0 Hackathon"
    })

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)