from fastapi import FastAPI
from pydantic import BaseModel
from database import get_conn
import os
import requests

app = FastAPI()


# =========================
# REQUEST MODEL
# =========================
class ChatRequest(BaseModel):
    message: str


# =========================
# GROQ CALL FUNCTION
# =========================
def call_groq(messages):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "ERROR: GROQ_API_KEY not set"

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 512
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code != 200:
            return f"GROQ ERROR: {response.text}"

        result = response.json()

        return result["choices"][0]["message"]["content"]

    except Exception as e:

        return f"SYSTEM ERROR: {str(e)}"


# =========================
# ROOT ENDPOINT
# =========================
@app.get("/")
def root():
    return {"status": "ok"}


# =========================
# CHAT ENDPOINT (WITH MEMORY)
# =========================
@app.post("/chat")
def chat(req: ChatRequest):

    user_message = req.message

    conn = get_conn()
    cursor = conn.cursor()

    # ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            message TEXT
        )
    """)

    # save user message
    cursor.execute(
        "INSERT INTO chat_history (role, message) VALUES (?, ?)",
        ("user", user_message)
    )

    conn.commit()

    # get last 10 messages
    cursor.execute("""
        SELECT role, message
        FROM chat_history
        ORDER BY id DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()

    # reverse to chronological order
    rows.reverse()

    # build messages context
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        }
    ]

    for row in rows:

        messages.append({
            "role": row[0],
            "content": row[1]
        })

    # call groq with context
    ai_reply = call_groq(messages)

    # save assistant reply
    cursor.execute(
        "INSERT INTO chat_history (role, message) VALUES (?, ?)",
        ("assistant", ai_reply)
    )

    conn.commit()
    conn.close()

    return {
        "reply": ai_reply
    }


# =========================
# HISTORY ENDPOINT
# =========================
@app.get("/history")
def history():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, role, message
        FROM chat_history
        ORDER BY id DESC
        LIMIT 50
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "role": row[1],
            "message": row[2]
        }
        for row in rows
    ]        ORDER BY id DESC
        LIMIT 50
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "role": row[1],
            "message": row[2]
        }
        for row in rows
    ]
