"""
KnowShift Backend — Supabase Client
Initialises a single Supabase client using credentials from app.config.
Import the `supabase` object anywhere you need to interact with the database.
"""

import logging
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)

# Single shared client — attempt connection; log and continue on failure so
# the app can still start and the /health endpoint reports the error.
try:
    supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
    logger.info("Supabase client created for %s", settings.supabase_url)
except Exception as _exc:
    logger.warning("Supabase client creation failed (%s) — running in degraded mode", _exc)
    supabase = None  # type: ignore[assignment]

__all__ = ["supabase"]
