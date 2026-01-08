"""
Unit tests for time utilities module.

Tests time-based greeting and farewell logic with comprehensive coverage
of all time ranges, boundaries, and edge cases.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

try:
    from zoneinfo import ZoneInfo
    ZONEINFO_AVAILABLE = True
except ImportError:
    ZONEINFO_AVAILABLE = False

from src.shared.utils.time_utils import (
    get_bogota_time,
    get_time_of_day_period,
    get_greeting,
    get_farewell,
    BOGOTA_TZ
)


@pytest.mark.unit
class TestTimeUtils:
    """Test suite for time utility functions"""

    def test_get_bogota_time_returns_datetime(self):
        """Test that get_bogota_time returns a datetime object"""
        result = get_bogota_time()
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    @pytest.mark.skipif(not ZONEINFO_AVAILABLE, reason="ZoneInfo not available")
    def test_get_bogota_time_returns_correct_timezone(self):
        """Test that get_bogota_time returns Bogota timezone when ZoneInfo available"""
        result = get_bogota_time()
        # Check that timezone info is present and represents UTC-5
        # Colombia is always UTC-5 (no DST)
        utc_offset = result.utcoffset()
        assert utc_offset == timedelta(hours=-5)

    @pytest.mark.parametrize("hour,expected_period", [
        # Morning range (6am - 11:59am)
        (6, "mañana"),   # Morning start
        (8, "mañana"),   # Mid-morning
        (10, "mañana"),  # Late morning
        (11, "mañana"),  # Morning end (11:59am)

        # Afternoon range (12pm - 6:59pm)
        (12, "tarde"),   # Afternoon start
        (14, "tarde"),   # Mid-afternoon
        (16, "tarde"),   # Late afternoon
        (18, "tarde"),   # Afternoon end (6:59pm)

        # Evening range (7pm - 5:59am)
        (19, "noche"),   # Evening start
        (20, "noche"),   # Evening
        (22, "noche"),   # Late evening
        (23, "noche"),   # Late night
        (0, "noche"),    # Midnight
        (2, "noche"),    # Early morning hours
        (4, "noche"),    # Before dawn
        (5, "noche"),    # Early morning (5:59am)
    ])
    def test_get_time_of_day_period_all_ranges(self, hour, expected_period):
        """Test time period detection for all hour ranges"""
        # Create mock time with fixed timezone
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, hour, 30, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, hour, 30, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            result = get_time_of_day_period()
            assert result == expected_period, f"Hour {hour} should be '{expected_period}', got '{result}'"

    def test_boundary_11_59am_is_morning(self):
        """Test boundary: 11:59am should be morning (mañana)"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 11, 59, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 11, 59, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_time_of_day_period() == "mañana"
            assert get_greeting() == "Buenos días"

    def test_boundary_12_00pm_is_afternoon(self):
        """Test boundary: 12:00pm should be afternoon (tarde)"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 12, 0, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 12, 0, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_time_of_day_period() == "tarde"
            assert get_greeting() == "Buenas tardes"

    def test_boundary_6_59pm_is_afternoon(self):
        """Test boundary: 6:59pm should be afternoon (tarde)"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 18, 59, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 18, 59, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_time_of_day_period() == "tarde"
            assert get_greeting() == "Buenas tardes"

    def test_boundary_7_00pm_is_evening(self):
        """Test boundary: 7:00pm should be evening (noche)"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 19, 0, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 19, 0, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_time_of_day_period() == "noche"
            assert get_greeting() == "Buenas noches"

    def test_boundary_5_59am_is_evening(self):
        """Test boundary: 5:59am should be evening (noche)"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 5, 59, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 5, 59, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_time_of_day_period() == "noche"
            assert get_greeting() == "Buenas noches"

    def test_boundary_6_00am_is_morning(self):
        """Test boundary: 6:00am should be morning (mañana)"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 6, 0, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 6, 0, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_time_of_day_period() == "mañana"
            assert get_greeting() == "Buenos días"

    def test_get_greeting_morning(self):
        """Test morning greeting (6am-11:59am) returns 'Buenos días'"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 8, 30, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 8, 30, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_greeting() == "Buenos días"

    def test_get_greeting_afternoon(self):
        """Test afternoon greeting (12pm-6:59pm) returns 'Buenas tardes'"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 14, 30, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 14, 30, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_greeting() == "Buenas tardes"

    def test_get_greeting_evening(self):
        """Test evening greeting (7pm-5:59am) returns 'Buenas noches'"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 20, 30, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 20, 30, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_greeting() == "Buenas noches"

    def test_get_farewell_morning(self):
        """Test morning farewell returns 'Que tenga un excelente día'"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 8, 0, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 8, 0, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_farewell() == "Que tenga un excelente día"

    def test_get_farewell_afternoon(self):
        """Test afternoon farewell returns 'Que tenga una excelente tarde'"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 14, 0, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 14, 0, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_farewell() == "Que tenga una excelente tarde"

    def test_get_farewell_evening(self):
        """Test evening farewell returns 'Que tenga una excelente noche'"""
        if ZONEINFO_AVAILABLE:
            mock_time = datetime(2025, 1, 7, 20, 0, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            mock_time = datetime(2025, 1, 7, 20, 0, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=mock_time):
            assert get_farewell() == "Que tenga una excelente noche"

    def test_get_greeting_returns_string(self):
        """Test that get_greeting always returns a string"""
        result = get_greeting()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_farewell_returns_string(self):
        """Test that get_farewell always returns a string"""
        result = get_farewell()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_time_of_day_period_returns_valid_value(self):
        """Test that get_time_of_day_period returns valid period"""
        result = get_time_of_day_period()
        assert result in ["mañana", "tarde", "noche"]

    def test_greeting_consistency_with_period(self):
        """Test that greeting is consistent with time period"""
        if ZONEINFO_AVAILABLE:
            morning_time = datetime(2025, 1, 7, 9, 0, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            morning_time = datetime(2025, 1, 7, 9, 0, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=morning_time):
            period = get_time_of_day_period()
            greeting = get_greeting()

            if period == "mañana":
                assert greeting == "Buenos días"
            elif period == "tarde":
                assert greeting == "Buenas tardes"
            else:  # noche
                assert greeting == "Buenas noches"

    def test_farewell_consistency_with_period(self):
        """Test that farewell is consistent with time period"""
        if ZONEINFO_AVAILABLE:
            afternoon_time = datetime(2025, 1, 7, 15, 0, tzinfo=ZoneInfo(BOGOTA_TZ))
        else:
            afternoon_time = datetime(2025, 1, 7, 15, 0, tzinfo=timezone(timedelta(hours=-5)))

        with patch('src.shared.utils.time_utils.get_bogota_time', return_value=afternoon_time):
            period = get_time_of_day_period()
            farewell = get_farewell()

            if period == "mañana":
                assert farewell == "Que tenga un excelente día"
            elif period == "tarde":
                assert farewell == "Que tenga una excelente tarde"
            else:  # noche
                assert farewell == "Que tenga una excelente noche"
