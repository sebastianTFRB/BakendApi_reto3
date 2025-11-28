from supabase import Client


class BaseRepository:
    def __init__(self, supabase: Client):
        self.supabase = supabase
