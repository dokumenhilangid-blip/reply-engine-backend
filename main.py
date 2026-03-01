from fastapi import FastAPI
from pydantic import BaseModel
from database import get_conn
import os
import requests

app = FastAPI()


class ChatRequest(BaseModel):
    message: str

def call_groq(user_message: str):

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        return f"GROQ ERROR: {response.text}"

    result = response.json()

    return result["choices"][0]["message"]["content"]


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):

    user_message = req.message

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            message TEXT
        )
    """)

    cursor.execute(
        "INSERT INTO chat_history (role, message) VALUES (?, ?)",
        ("user", user_message)
    )

    conn.commit()

    # call Groq AI
    ai_reply = call_groq(user_message)

    cursor.execute(
        "INSERT INTO chat_history (role, message) VALUES (?, ?)",
        ("assistant", ai_reply)
    )

    conn.commit()
    conn.close()

    return {
        "reply": ai_reply
    }


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
    ]
