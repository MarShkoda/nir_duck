from datetime import datetime

import pytz

__all__ = ["now_utc"]


def now_utc():
    return datetime.now(tz=pytz.utc)
