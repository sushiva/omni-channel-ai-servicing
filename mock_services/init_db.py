import aiosqlite
import asyncio
from mock_services.db import DB_PATH

async def init_db():
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT,
        intent TEXT,
        details TEXT,
        status TEXT
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS case_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER,
        note TEXT
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id TEXT PRIMARY KEY,
        address TEXT
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS workflows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        payload TEXT,
        status TEXT
    )
    """)
    await db.execute("""
        INSERT OR IGNORE INTO customers (id, address)
        VALUES ('cust123', '{"street": "1 Main St", "city": "Charlotte"}')
    """)

    await db.commit()
    await db.close()


asyncio.run(init_db())

