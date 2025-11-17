from db import get_db
from psycopg2.extras import RealDictCursor

def get_users():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM tbl_m_users;")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return [
        {
            "userId": r["userId"],
            "name": r["firstName"],
            "email": r["userName"]
        }
        for r in rows
    ]