# AI-Career-Co-pilot
Your intelligent career mentor powered by AI

📌 Overview

AI Career Copilot is a smart web application that helps students understand their career readiness.

It analyzes:

📄 Resume (PDF)
🐙 GitHub Profile

And provides:

✅ Skill extraction
📊 Career readiness score
🎯 Career path suggestions
🤖 AI-based mentoring
🎯 Problem

Students often don’t know:

What skills they have
What skills they are missing
Which career path suits them
💡 Solution

AI Career Copilot solves this by:

Extracting skills from resumes
Analyzing GitHub projects
Combining both data sources
Giving personalized career guidance
✨ Features
📄 Resume Skill Extraction (PDF upload)
🐙 GitHub Profile Analysis
📊 Career Readiness Score
🧠 AI Career Mentor Chat
🎯 Career Path Recommendation
📌 Personalized Suggestions
🎨 Modern Interactive Dashboard UI
🧠 How It Works
User logs in (Auth0 authentication)
Uploads resume (PDF)
Enters GitHub username
System:
Extracts skills from resume
Fetches GitHub repositories
Analyzes languages & projects
AI generates:
Career score
Suggestions
Career path
User can chat with AI mentor
🛠 Tech Stack

Frontend:

HTML
CSS
JavaScript

Backend:

Flask (Python)

Authentication:

Auth0

AI Integration:

OpenAI / NVIDIA API

Other Tools:

PDFPlumber (resume parsing)
GitHub API (repo analysis)
📊 Project Architecture
User → Frontend (Dashboard)
     → Flask Backend
         → Resume Parser
         → GitHub API
         → AI Model
     → Response → UI Dashboard
🎥 Demo Video

👉 

📂 Installation
git clone https://github.com/your-username/ai-career-copilot.git
cd ai-career-copilot

Create virtual environment
python -m venv .venv

Activate environment
.venv\Scripts\activate

Install dependencies
pip install -r requirements.txt

Run the app
python app.py

🔑 Environment Variables

Create a .env file:

AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_secret
AUTH0_DOMAIN=your_domain
AUTH0_CALLBACK_URL=http://localhost:5000/callback
OPENAI_API_KEY=your_api_key

📈 Future Improvements
📊 More advanced AI analysis
🧠 Resume improvement suggestions
🌐 Job recommendations
📱 Mobile-friendly version
🔗 LinkedIn integration
👨‍💻 Author

Dhamodharan A
B.Tech IT Student
Hackathon Builder 🚀

🏆 Goal

Build something that helps students grow their careers using AI

⭐ Support

If you like this project:

⭐ Star the repo
🍴 Fork it
💬 Share feedback

