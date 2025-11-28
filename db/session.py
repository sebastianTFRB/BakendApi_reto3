# db/session.py

def get_db():
    raise RuntimeError(
        "SQLAlchemy DB session is disabled. Use Supabase client instead."
    )
