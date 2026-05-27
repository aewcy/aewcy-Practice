from datetime import datetime, timedelta


def utc_time() -> datetime:
    return datetime.utcnow()


def add_days(dt: datetime, days: int) -> datetime:
    return dt + timedelta(days=days)
