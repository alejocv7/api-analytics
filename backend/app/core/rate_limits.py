"""
Centralized rate limit configuration.

Limits use slowapi's string format: "<count>/<period>"
Periods: second, minute, hour, day
"""

# Global safety net (applied via SlowAPIMiddleware to all routes, by IP)
GLOBAL = "120/minute"

# Auth endpoints (by IP — no user identity yet)
AUTH_REGISTER = "5/minute"
AUTH_LOGIN = "10/minute"

# Tracking endpoint (by API key project)
TRACK = "100/minute"

# Dashboard / data read endpoints (by authenticated user)
DATA_READ = "60/minute"

# Write/mutate endpoints (by authenticated user)
DATA_WRITE = "20/minute"

# Destructive endpoints (by authenticated user)
DATA_DELETE = "10/minute"

# Key rotation (by authenticated user)
KEY_ROTATE = "5/minute"
