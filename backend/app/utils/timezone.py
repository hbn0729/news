from datetime import datetime, timezone, date, time, timedelta
from zoneinfo import ZoneInfo

# Source timezone mapping
SOURCE_TIMEZONES: dict[str, ZoneInfo] = {
    "sina": ZoneInfo("Asia/Shanghai"),
    "eastmoney": ZoneInfo("Asia/Shanghai"),
    "xueqiu": ZoneInfo("Asia/Shanghai"),
    "cls": ZoneInfo("Asia/Shanghai"),
    "itjuzi": ZoneInfo("Asia/Shanghai"),
    "36kr": ZoneInfo("Asia/Shanghai"),
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


def local_day_bounds_utc(
    day: date, tz_name: str = "Asia/Shanghai"
) -> tuple[datetime, datetime]:
    tz = ZoneInfo(tz_name)
    start_local = datetime.combine(day, time.min).replace(tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def retention_cutoff_utc(
    retention_days: int,
    tz_name: str = "Asia/Shanghai",
    now_utc: datetime | None = None,
) -> datetime:
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    tz = ZoneInfo(tz_name)
    today_local = now_utc.astimezone(tz).date()
    cutoff_day_local = today_local - timedelta(days=retention_days)
    cutoff_local = datetime.combine(cutoff_day_local, time.min).replace(tzinfo=tz)
    return cutoff_local.astimezone(timezone.utc)
