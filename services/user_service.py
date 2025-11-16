from db import get_db

def get_users():
    conn = get_db()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": r["id"], "name": r["name"], "email": r["email"], "age": r["age"]} for r in rows]