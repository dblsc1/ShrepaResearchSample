"""Seat names and license ids: a license is <prefix>-<n>, the prefix is the seat name without non-letters, upper-cased
(the same rule as ppo's make_prefix)."""
import re


def prefix(seat: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", seat.upper())


def listed(params, kind: str, seat: str) -> list:
    """The seats params lists under <kind>.<seat>, e.g. after.bear_researcher=bull_researcher."""
    return [s for s in (params.get(f"{kind}.{seat}") or "").split(",") if s]


def seat_of(license_id) -> str:
    return (license_id or "").split("-", 1)[0]
