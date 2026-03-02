from fastapi import FastAPI
from pydantic import BaseModel
from database import get_conn
import os
import requests
from datetime import datetime

app = FastAPI()


# =========================
# Request Model
# =========================

class ChatRequest(BaseModel):
    message: str


# =========================
# Groq AI Call
# =========================

def call_groq(messages):

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 512
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        return f"GROQ ERROR: {response.text}"

    result = response.json()

    return result["choices"][0]["message"]["content"]


# =========================
# Telegram Send
# =========================

def send_telegram(message: str):

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    requests.post(url, json=payload)


# =========================
# Root
# =========================

@app.get("/")
def root():
    return {"status": "ok"}


# =========================
# Chat Endpoint
# =========================

@app.post("/chat")
def chat(req: ChatRequest):

    conn = get_conn()
    cursor = conn.cursor()

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
        ("user", req.message)
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
    rows.reverse()

    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

    for row in rows:
        messages.append({
            "role": row[0],
            "content": row[1]
        })

    messages.append({
        "role": "user",
        "content": req.message
    })

    ai_reply = call_groq(messages)

    cursor.execute(
        "INSERT INTO chat_history (role, message) VALUES (?, ?)",
        ("assistant", ai_reply)
    )

    conn.commit()
    conn.close()

    return {"reply": ai_reply}


# =========================
# History Endpoint
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
    ]


# =========================
# Scrape Endpoint
# =========================

@app.get("/scrape")
def scrape():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            content TEXT,
            created_at TEXT
        )
    """)

    sample_data = [
        ("reddit", "Python job demand increasing"),
        ("reddit", "AI engineer salaries rising"),
        ("jobs", "Remote backend roles growing")
    ]

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    for source, content in sample_data:
        cursor.execute(
            "INSERT INTO raw_data (source, content, created_at) VALUES (?, ?, ?)",
            (source, content, now)
        )

    conn.commit()
    conn.close()

    return {
        "status": "scrape complete",
        "records_added": len(sample_data)
    }


# =========================
# Analyze Endpoint
# =========================

@app.get("/analyze")
def analyze():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal TEXT,
            confidence REAL,
            created_at TEXT
        )
    """)

    cursor.execute("""
        SELECT content
        FROM raw_data
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = cursor.fetchall()

    text_data = "\n".join([row[0] for row in rows])

    messages = [
        {
            "role": "system",
            "content": "Analyze job market trends and produce intelligence insights."
        },
        {
            "role": "user",
            "content": text_data
        }
    ]

    signal = call_groq(messages)

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO signals (signal, confidence, created_at) VALUES (?, ?, ?)",
        (signal, 0.9, now)
    )

    conn.commit()
    conn.close()

    return {
        "status": "analysis complete",
        "signal": signal
    }


# =========================
# Get Signals
# =========================

@app.get("/signals")
def get_signals():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, signal, confidence, created_at
        FROM signals
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "signal": row[1],
            "confidence": row[2],
            "created_at": row[3]
        }
        for row in rows
    ]


# =========================
# Cron Automation
# =========================

@app.get("/cron/run")
def run_cron():

    scrape()

    result = analyze()

    signal = result["signal"]

    send_telegram(signal)

    return {
        "status": "automation complete",
        "signal": signal
    }
