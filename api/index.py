from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import os
import json
from urllib import request, error

# Load .env locally if available; Vercel uses project env vars
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <h2>🔥 Hot Mess Coach</h2>
    <form action="/chat" method="post">
        <p>Your message:</p>
        <textarea name="user_message" rows="4" cols="50">I feel like a hot mess today...</textarea><br><br>
        <button type="submit">Coach me</button>
    </form>
    """


def get_coach_reply(user_message: str) -> str:
    if not OPENAI_API_KEY:
        return "Missing OPENAI_API_KEY. Set it in your environment."

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a supportive mental coach who helps overwhelmed people feel calmer."},
            {"role": "user", "content": user_message},
        ],
    }

    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = str(e)
        return f"OpenAI API error: {e.code} {e.reason}\n{body}"
    except Exception as e:
        return f"Request failed: {e}"


@app.post("/chat", response_class=HTMLResponse)
def chat(user_message: str = Form(...)):
    coach_reply = get_coach_reply(user_message)
    return f"""
    <h2>🔥 Hot Mess Coach Says</h2>
    <div style="white-space: pre-wrap; border: 1px solid #ccc; padding: 12px; border-radius: 8px;">
        {coach_reply}
    </div>
    <br><a href="/">⬅ Back</a>
    """


