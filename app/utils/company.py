from app.core.constants import (
    COMPANIES_MEMBERS_PAGE_LIMIT,
    COMPANIES_PAGE_LIMIT,
    COMPANIES_USERS_REQUEST_PAGE_LIMIT,
)


def get_companies_page_limit() -> int:
    return COMPANIES_PAGE_LIMIT


def get_companies_members_page_limit() -> int:
    return COMPANIES_MEMBERS_PAGE_LIMIT


def get_companies_users_request_page_limit() -> int:
    return COMPANIES_USERS_REQUEST_PAGE_LIMIT
