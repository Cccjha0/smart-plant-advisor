import mimetypes
from typing import Optional

from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY

_supabase_client: Optional[Client] = None


def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase credentials are not set (SUPABASE_URL/SUPABASE_KEY)")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


def upload_bytes(bucket: str, path: str, data: bytes, content_type: Optional[str] = None) -> str:
    client = get_supabase()
    if not content_type:
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    client.storage.from_(bucket).upload(path, data, {"content-type": content_type, "upsert": True})
    public_url = client.storage.from_(bucket).get_public_url(path)
    return public_url
