from .connection import Connection

db: Connection = None
def get_db() -> Connection:
    global db
    if db is None:
        db = Connection()
    return db