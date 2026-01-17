from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3, uuid, qrcode, os

app = FastAPI()

DB = "tickets.db"
os.makedirs("qrcodes", exist_ok=True)

def get_db():
    return sqlite3.connect(DB)

class TicketCreate(BaseModel):
    full_name: str
    phone: str
    email: str
    event_date: str

@app.post("/create-ticket")
def create_ticket(data: TicketCreate):
    code = str(uuid.uuid4())

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            phone TEXT,
            email TEXT,
            event_date TEXT,
            ticket_code TEXT UNIQUE,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        INSERT INTO tickets (full_name, phone, email, event_date, ticket_code, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data.full_name, data.phone, data.email, data.event_date, code, "valid"))
    conn.commit()
    conn.close()

    qr = qrcode.make(code)
    qr_path = f"qrcodes/{code}.png"
    qr.save(qr_path)

    return {
        "ticket_code": code,
        "qr_code_url": qr_path
    }

@app.get("/verify/{ticket_code}")
def verify_ticket(ticket_code: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT status FROM tickets WHERE ticket_code = ?", (ticket_code,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Bilet tapılmadı")

    if row[0] == "used":
        return {"status": "used", "message": "Bu bilet artıq istifadə olunub."}

    cur.execute("UPDATE tickets SET status = 'used' WHERE ticket_code = ?", (ticket_code,))
    conn.commit()
    conn.close()

    return {"status": "valid", "message": "Giriş icazəlidir."}
