import enum


class ProjectRole(enum.StrEnum):
    owner = "owner"
    member = "member"
    viewer = "viewer"


class TimeGranularity(enum.StrEnum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


class StatsFields(enum.StrEnum):
    request_count = "request_count"
    avg_response_time_ms = "avg_response_time_ms"
    slowest_request_ms = "slowest_request_ms"
    fastest_request_ms = "fastest_request_ms"
    error_count = "error_count"
    error_rate = "error_rate"


class TokenTransport(enum.StrEnum):
    COOKIE = "cookie"
    BEARER = "bearer"
