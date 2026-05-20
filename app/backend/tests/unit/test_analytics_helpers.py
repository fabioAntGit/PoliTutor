from datetime import date, timedelta

import pytest

from app.backend.services.analytics import _fill_activity_dates


def _day(offset: int) -> str:
    return (date.today() + timedelta(days=offset)).strftime("%Y-%m-%d")


def test_empty_raw_produces_all_zeros():
    result = _fill_activity_dates([], 7)
    assert len(result.data) == 7
    assert all(point.questions == 0 for point in result.data)


def test_range_start_and_end_dates():
    result = _fill_activity_dates([], 7)
    assert result.data[0].date == _day(-6)
    assert result.data[-1].date == _day(0)


@pytest.mark.parametrize("days", [7, 30, 90])
def test_output_length_matches_days(days):
    result = _fill_activity_dates([], days)
    assert len(result.data) == days


def test_known_dates_keep_counts_and_gaps_filled():
    raw = [
        {"date": _day(-6), "questions": 3},
        {"date": _day(0), "questions": 5},
    ]
    result = _fill_activity_dates(raw, 7)
    assert result.data[0].questions == 3
    assert result.data[-1].questions == 5
    assert result.data[3].questions == 0


def test_dates_are_chronologically_ordered():
    result = _fill_activity_dates([], 30)
    dates = [point.date for point in result.data]
    assert dates == sorted(dates)
