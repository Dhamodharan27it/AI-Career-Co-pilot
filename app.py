import os
import requests
import pdfplumber
from flask import Flask, redirect, session, jsonify, render_template, request
from werkzeug.utils import secure_filename
from openai import OpenAI
from authlib.integrations.flask_client import OAuth
from authlib.integrations.base_client.errors import OAuthError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_hackathon_key")

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"]   = bool(os.getenv("RENDER"))
app.config["SESSION_COOKIE_HTTPONLY"] = True

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ── NVIDIA NIM client
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN")  # ✅ FIXED: load GitHub token

client = OpenAI(
    api_key=NVIDIA_API_KEY,
    base_url="https://integrate.api.nvidia.com/v1"
)

# ── Auth0
oauth = OAuth(app)
oauth.register(
    name="auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration',
    client_kwargs={"scope": "openid profile email"}
)

# ── Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    callback_url = os.getenv("AUTH0_CALLBACK_URL")
    return oauth.auth0.authorize_redirect(redirect_uri=callback_url)

@app.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        return redirect("/")
    try:
        token = oauth.auth0.authorize_access_token()
        user  = oauth.auth0.get(
            f'https://{os.getenv("AUTH0_DOMAIN")}/userinfo'
        ).json()
        session["user"] = user
        return redirect("/dashboard")
    except OAuthError as e:
        print(f"[CALLBACK] OAuthError: {e}")
        return redirect("/")
    except Exception as e:
        print(f"[CALLBACK] Exception: {e}")
        return redirect("/")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", user=session["user"])

@app.route("/logout")
def logout():
    session.clear()
    domain    = os.getenv("AUTH0_DOMAIN")
    client_id = os.getenv("AUTH0_CLIENT_ID")
    return_to = os.getenv("AUTH0_LOGOUT_URL", "https://dauthverse-ai.onrender.com")
    return redirect(f"https://{domain}/v2/logout?client_id={client_id}&returnTo={return_to}")

@app.route("/api/data")
def api_data():
    return jsonify({"name": "DHAMODHARAN A", "project": "AI Career Copilot"})

# ── AI helper
def get_ai_reply(user_message, resume_skills, github_skills):
    """Call NVIDIA NIM and return a plain string reply."""

    # Quick greeting shortcut (no API call needed)
    if user_message.strip().lower() in ["hi", "hello", "hey", "hii", "hlo", "greetings"]:
        return (
            "Hey Buddy! 👋 Welcome to your AI Career Mentor!\n\n"
            "I can help you with:\n"
            "• Career guidance & path suggestions\n"
            "• Skill improvement tips\n"
            "• Resume advice\n"
            "• Project ideas\n\n"
            "Try asking:\n"
            "- What skills should I learn for AI?\n"
            "- How can I improve my resume?\n"
            "- Am I job ready?"
        )

    # Verify API key is present before attempting call
    if not NVIDIA_API_KEY:
        return (
            "⚠️ NVIDIA_API_KEY is not set on the server.\n\n"
            "Please add it in your Render dashboard under Environment Variables and redeploy."
        )

    prompt = f"""You are an expert AI Career Mentor helping a student grow their tech career.

Student's Resume Skills: {resume_skills if resume_skills else 'Not uploaded yet'}
Student's GitHub Skills: {github_skills if github_skills else 'Not connected yet'}

Student's Question: {user_message}

Instructions:
- Answer in simple English, be concise and actionable.
- Use emojis to keep it friendly.
- Give specific advice based on the skills listed above.
- Keep the tone encouraging.
- End with 1-2 clear next steps the student can take right now.
"""

    response = client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=512
    )
    return response.choices[0].message.content


# ── /ai-chat endpoint
@app.route("/ai-chat", methods=["POST"])
def ai_chat_route():
    try:
        data         = request.get_json(force=True)
        user_message = (data.get("message") or "").strip()

        if not user_message:
            return jsonify({"reply": "Please type a question first! 😊"})

        resume_skills = session.get("resume_skills", [])
        github_skills = session.get("github_skills", [])

        reply = get_ai_reply(user_message, resume_skills, github_skills)
        return jsonify({"reply": reply})

    except Exception as e:
        print(f"[AI CHAT ERROR] {type(e).__name__}: {e}")
        # Return a real error message so the frontend shows it — not the placeholder
        return jsonify({
            "reply": f"⚠️ AI error: {str(e)}\n\nCheck that NVIDIA_API_KEY is set correctly on Render."
        }), 500


# ── Resume upload
@app.route("/upload", methods=["POST"])
def upload_resume():
    try:
        file     = request.files["resume"]
        filename = secure_filename(file.filename)
        path     = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted

        text_lower = text.lower()
        keywords   = [
            "python", "java", "machine learning", "deep learning",
            "html", "css", "javascript", "typescript",
            "sql", "react", "flask", "django", "fastapi",
            "docker", "kubernetes", "aws", "git", "linux",
            "tensorflow", "pytorch", "pandas", "numpy"
        ]
        resume_skills = [s.capitalize() for s in keywords if s in text_lower]
        session["resume_skills"] = resume_skills
        return jsonify({"message": "Resume uploaded successfully", "skills": resume_skills})

    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")
        return jsonify({"message": "Upload failed", "error": str(e)}), 500


# ── GitHub analysis
@app.route("/github-analysis", methods=["POST"])
def github_analysis():
    try:
        username = request.json.get("username", "").strip()
        if not username:
            return jsonify({"error": "Username is required"}), 400

        response = requests.get(
            f"https://api.github.com/users/{username}/repos",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"Bearer {GITHUB_TOKEN}"  # ✅ FIXED: token added
            },
            timeout=10
        )
        if response.status_code != 200:
            return jsonify({"error": "GitHub user not found or API error"}), 404

        repos      = response.json()
        repo_count = len(repos)
        languages  = {}
        project_list = []

        for repo in repos:
            project_list.append({"name": repo.get("name"), "language": repo.get("language")})
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

        top_language  = max(languages, key=languages.get) if languages else "None"
        github_skills = list(languages.keys())
        session["github_skills"] = github_skills

        resume_skills   = session.get("resume_skills", [])
        combined_skills = list(set(github_skills + resume_skills))

        score = min(100, repo_count * 10 + len(resume_skills) * 5)
        level = "Strong Profile" if score > 70 else "Growing Profile" if score > 40 else "Beginner profile"

        suggestions = []
        if repo_count < 5:
            suggestions.append("Build more GitHub projects to show range")
        if len(resume_skills) < 3:
            suggestions.append("Add more skills to your resume")
        if "Python" not in combined_skills:
            suggestions.append("Learn Python — essential for AI/ML roles")
        if "JavaScript" not in combined_skills:
            suggestions.append("Add JavaScript for frontend & full-stack roles")

        career = "General Developer"
        if "Java"       in combined_skills: career = "Backend Developer"
        if "Python"     in combined_skills: career = "AI/ML Engineer"
        if "JavaScript" in combined_skills: career = "Full Stack Developer"

        return jsonify({
            "github_user":     username,
            "repo_count":      repo_count,
            "languages":       languages,
            "top_language":    top_language,
            "resume_skills":   resume_skills,
            "combined_skills": combined_skills,
            "score":           score,
            "profile_level":   level,
            "projects":        project_list,
            "suggestions":     suggestions,
            "career":          career
        })

    except Exception as e:
        print(f"[GITHUB ERROR] {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)