import re


def safe_url(value):
    """Return the URL only if it is http(s); otherwise "". Stops `javascript:`
    and similar schemes from ever being stored or rendered as a link."""
    v = (value or "").strip()
    return v if re.match(r"^https?://", v, re.I) else ""
