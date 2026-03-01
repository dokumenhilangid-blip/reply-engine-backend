from database import get_conn

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
