import enum


class ProjectRole(enum.StrEnum):
    owner = "owner"
    member = "member"
    viewer = "viewer"


class TimeGranularity(enum.StrEnum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
