from datetime import datetime, timezone
import dateutil.parser

def get_utc_now_iso() -> str:
    """Returns current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()

def format_date_str(date_input: str) -> str:
    """Parses various date string formats into standard YYYY-MM-DD format."""
    if not date_input:
        return get_utc_now_iso()[:10]
    try:
        parsed = dateutil.parser.parse(date_input)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return str(date_input)[:10]
