from datetime import date, datetime, timedelta

from app.core.constants import DAYS_DATE_FILTER_RANGE


def default_from_date() -> date:
    return datetime.now().date() - timedelta(days=DAYS_DATE_FILTER_RANGE)


def default_to_date() -> date:
    return datetime.now().date()
