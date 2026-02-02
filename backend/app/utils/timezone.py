from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Source timezone mapping
SOURCE_TIMEZONES: dict[str, ZoneInfo] = {
    "sina": ZoneInfo("Asia/Shanghai"),
    "eastmoney": ZoneInfo("Asia/Shanghai"),
    "xueqiu": ZoneInfo("Asia/Shanghai"),
    "cls": ZoneInfo("Asia/Shanghai"),
    "yahoo": ZoneInfo("America/New_York"),
}


def normalize_to_utc(dt: datetime, source: str) -> datetime:
    """Convert source timezone time to UTC."""
    if dt.tzinfo is None:
        # No timezone info, use source default timezone
        source_tz = SOURCE_TIMEZONES.get(source, ZoneInfo("UTC"))
        dt = dt.replace(tzinfo=source_tz)

    return dt.astimezone(timezone.utc)


def format_for_display(dt: datetime, user_tz: str = "Asia/Shanghai") -> str:
    """Convert to user timezone for display."""
    local_dt = dt.astimezone(ZoneInfo(user_tz))
    return local_dt.strftime("%Y-%m-%d %H:%M")


def parse_datetime(date_str: str, source: str) -> datetime:
    """Parse datetime string from various sources."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return normalize_to_utc(dt, source)
        except ValueError:
            continue

    # Fallback: return current time
    return datetime.now(timezone.utc)
