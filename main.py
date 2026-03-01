from fastapi import FastAPI
from pydantic import BaseModel
from database import get_conn

app = FastAPI()


# health check
@app.get("/")
def root():
    return {"status": "ok"}


# model request
class ChatRequest(BaseModel):
    message: str


# endpoint chat
@app.post("/chat")
def chat(req: ChatRequest):

    user_message = req.message

    conn = get_conn()
    cursor = conn.cursor()

    # buat tabel jika belum ada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            message TEXT
        )
    """)

    # simpan pesan user
    cursor.execute(
        "INSERT INTO chat_history (role, message) VALUES (?, ?)",
        ("user", user_message)
    )

    # response sementara
    ai_reply = f"echo: {user_message}"

    # simpan response AI
    cursor.execute(
        "INSERT INTO chat_history (role, message) VALUES (?, ?)",
        ("assistant", ai_reply)
    )

    conn.commit()
    conn.close()

    return {"reply": ai_reply}


# endpoint lihat history (opsional tapi penting untuk debug)
@app.get("/history")
def history():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, role, message
        FROM chat_history
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": r[0], "role": r[1], "message": r[2]}
        for r in rows
    ]
