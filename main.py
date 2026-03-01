from fastapi import FastAPI
from database import init_db, get_conn

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"status": "backend alive"}

@app.get("/test-db")
def test_db():
    return {"status": "database ready"}


@app.get("/test-write")
def test_write():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT
        )
    """)

    cursor.execute(
        "INSERT INTO test_table (message) VALUES (?)",
        ("hello persistent storage",)
    )

    conn.commit()
    conn.close()

    return {"status": "write success"}


@app.get("/test-read")
def test_read():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, message FROM test_table ORDER BY id DESC LIMIT 1"
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return {"id": row[0], "message": row[1]}
    else:
        return {"status": "no data"}
