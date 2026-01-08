"""
Time utilities for contextual greetings based on Colombia timezone.

This module provides functions to determine time-appropriate greetings
and farewells based on the current time in America/Bogota (UTC-5).

Time ranges:
- Morning (mañana): 6:00am - 11:59am → "Buenos días"
- Afternoon (tarde): 12:00pm - 6:59pm → "Buenas tardes"
- Evening (noche): 7:00pm - 5:59am → "Buenas noches"
"""

from datetime import datetime, timezone, timedelta
from typing import Literal

try:
    from zoneinfo import ZoneInfo
    ZONEINFO_AVAILABLE = True
except ImportError:
    ZONEINFO_AVAILABLE = False

BOGOTA_TZ = "America/Bogota"
TimeOfDay = Literal["mañana", "tarde", "noche"]


def get_bogota_time() -> datetime:
    """
    Get current datetime in America/Bogota timezone (UTC-5).

    Returns:
        datetime: Current time in Bogota timezone with timezone info attached

    Example:
        >>> from datetime import datetime
        >>> result = get_bogota_time()
        >>> result.hour  # Will be in Bogota time (UTC-5)
        8

    Note:
        Uses ZoneInfo if available (Python 3.9+), otherwise falls back
        to a fixed UTC-5 offset. Colombia does not observe DST, so the
        offset is always UTC-5.
    """
    if ZONEINFO_AVAILABLE:
        try:
            return datetime.now(ZoneInfo(BOGOTA_TZ))
        except Exception:
            # Fallback if ZoneInfo fails for any reason
            pass

    # Fallback: use fixed UTC-5 offset (Colombia has no DST)
    bogota_offset = timezone(timedelta(hours=-5))
    return datetime.now(bogota_offset)


def get_time_of_day_period() -> TimeOfDay:
    """
    Determine time period based on current Bogota time.

    Time ranges (as confirmed by user requirements):
    - Morning (mañana): 6:00am - 11:59am
    - Afternoon (tarde): 12:00pm - 6:59pm
    - Evening (noche): 7:00pm - 5:59am

    Returns:
        str: 'mañana', 'tarde', or 'noche'

    Example:
        >>> # At 8:00am Bogota time
        >>> get_time_of_day_period()
        'mañana'

        >>> # At 2:00pm Bogota time
        >>> get_time_of_day_period()
        'tarde'

        >>> # At 9:00pm Bogota time
        >>> get_time_of_day_period()
        'noche'
    """
    now = get_bogota_time()
    hour = now.hour

    if 6 <= hour < 12:
        return "mañana"
    elif 12 <= hour < 19:
        return "tarde"
    else:  # 19-23 and 0-5
        return "noche"


def get_greeting() -> str:
    """
    Get time-appropriate greeting based on current Bogota time.

    Returns:
        str: 'Buenos días', 'Buenas tardes', or 'Buenas noches'

    Example:
        >>> # At 8:00am Bogota time
        >>> get_greeting()
        'Buenos días'

        >>> # At 2:00pm Bogota time
        >>> get_greeting()
        'Buenas tardes'

        >>> # At 9:00pm Bogota time
        >>> get_greeting()
        'Buenas noches'
    """
    period = get_time_of_day_period()
    greetings = {
        "mañana": "Buenos días",
        "tarde": "Buenas tardes",
        "noche": "Buenas noches"
    }
    return greetings[period]


def get_farewell() -> str:
    """
    Get time-appropriate farewell based on current Bogota time.

    Returns:
        str: Farewell message appropriate for time of day

    Example:
        >>> # At 8:00am Bogota time
        >>> get_farewell()
        'Que tenga un excelente día'

        >>> # At 2:00pm Bogota time
        >>> get_farewell()
        'Que tenga una excelente tarde'

        >>> # At 9:00pm Bogota time
        >>> get_farewell()
        'Que tenga una excelente noche'
    """
    period = get_time_of_day_period()
    farewells = {
        "mañana": "Que tenga un excelente día",
        "tarde": "Que tenga una excelente tarde",
        "noche": "Que tenga una excelente noche"
    }
    return farewells[period]
