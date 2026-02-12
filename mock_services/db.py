import aiosqlite

DB_PATH = "mock.db"

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    try:
        yield db
    finally:
        await db.close()
