"""Stage 4 - rescore Lead Score /100 from the verified signals.

The scoring philosophy is the user's: the score measures unmet need, not
company quality. A firm with live chat, online booking, a modern responsive
site and a CRM has already solved the problem being sold, so it scores near
zero. A firm with a dead domain and a phone number scores near the top.

Weights (total 100):
    28  site presence and health   - no site / broken / expired TLS / http-only
    18  no live chat
    18  outdated technology score  - scaled from the 1-10 stage 2 score
    14  no online booking
    12  contact friction           - form-only and no-route score highest
    10  no CRM

The original heuristic score is preserved in 'Lead Score (Original)' before the
rescored value overwrites 'Lead Score /100' (the one overwrite the user
authorised).
"""
from __future__ import annotations

import logging

from .store import FailureLog

log = logging.getLogger("leadgen")

W_PRESENCE = 28
W_CHAT = 18
W_OUTDATED = 18
W_BOOKING = 14
W_CONTACT = 12
W_CRM = 10

# Health label -> points out of W_PRESENCE.
PRESENCE_POINTS = {
    "none": 28,          # no website discovered at all
    "unreachable": 28,   # DNS failure, connection refused, timeout
    "broken": 26,        # 404 / 410 / 5xx on the homepage
    "placeholder": 22,   # resolves, but parked or "coming soon"
    "insecure": 24,      # expired/invalid certificate, or http-only
    "unknown": 20,       # robots-blocked or not yet checked
    "ok": 0,
}

# Primary contact method -> points out of W_CONTACT.
CONTACT_POINTS = {
    "none": 12,      # no contact route at all
    "form": 12,      # form-only: enquiries queue in an inbox, nobody answers live
    "mailto": 9,
    "phone": 7,
    "": 7,           # unknown; a phone number exists in the CSV either way
}

# When there is no site, stage 2 signals cannot be measured. Absence of a web
# presence is itself the strongest form of "outdated", so it is scored near the
# top of the band rather than as a zero, and confidence is downgraded.
NO_SITE_OUTDATED_PROXY = 14


def _yes(value: str) -> bool:
    return str(value or "").strip().lower() in {"yes", "y", "true", "1"}


def _has(row: dict[str, str], vendor_col: str, fallback_col: str) -> bool:
    if str(row.get(vendor_col, "") or "").strip():
        return True
    return _yes(row.get(fallback_col, ""))


def score_row(row: dict[str, str]) -> tuple[int, str, str]:
    """Return (score, breakdown, confidence)."""
    has_site = bool(str(row.get("Website", "") or "").strip())
    health = (row.get("Site Health") or "").strip().lower()
    checked = bool(str(row.get("HTTP Status", "") or "").strip())

    if not has_site:
        health = "none"
    elif not health:
        health = "unknown"

    parts: list[str] = []
    total = 0

    presence = PRESENCE_POINTS.get(health, PRESENCE_POINTS["unknown"])
    total += presence
    parts.append(f"site[{health}]={presence}/{W_PRESENCE}")

    if has_site and checked:
        chat = 0 if _has(row, "Live Chat Vendor", "Live Chat (unverified)") else W_CHAT
        booking = 0 if _has(row, "Online Booking Vendor", "Online Booking (unverified)") else W_BOOKING
        crm = 0 if _has(row, "CRM Vendor", "Uses CRM (unverified)") else W_CRM

        raw = str(row.get("Website Outdated Score (unverified)", "") or "").strip()
        try:
            outdated_raw = max(1, min(10, int(float(raw))))
            outdated = round(W_OUTDATED * (outdated_raw - 1) / 9)
            outdated_label = f"outdated[{outdated_raw}/10]"
        except (TypeError, ValueError):
            outdated = round(W_OUTDATED * 0.5)
            outdated_label = "outdated[unmeasured]"

        contact_key = (row.get("Contact Method") or "").strip().lower()
        contact = CONTACT_POINTS.get(contact_key, CONTACT_POINTS[""])
        contact_label = f"contact[{contact_key or 'unknown'}]"

        confidence = "high" if health in ("ok", "insecure", "broken", "placeholder") else "medium"
    else:
        # No site (or never audited): infer from the absence of any web presence.
        chat, booking, crm = W_CHAT, W_BOOKING, W_CRM
        outdated = NO_SITE_OUTDATED_PROXY
        outdated_label = "outdated[no-site-proxy]"
        contact = CONTACT_POINTS["phone"]
        contact_label = "contact[phone-only:no-site]"
        confidence = "low"

    total += chat + booking + outdated + contact + crm
    parts.append(f"chat={chat}/{W_CHAT}")
    parts.append(f"booking={booking}/{W_BOOKING}")
    parts.append(f"{outdated_label}={outdated}/{W_OUTDATED}")
    parts.append(f"{contact_label}={contact}/{W_CONTACT}")
    parts.append(f"crm={crm}/{W_CRM}")

    score = max(0, min(100, total))
    return score, " ".join(parts), confidence


def run(rows: list[dict[str, str]], failures: FailureLog, checkpoint,
        limit: int | None = None) -> dict[str, int]:
    stats = {"rescored": 0, "high_confidence": 0, "medium_confidence": 0,
             "low_confidence": 0, "moved_up": 0, "moved_down": 0, "unchanged": 0}

    target = rows[:limit] if limit else rows
    for row_num, row in enumerate(target, start=2):
        company = row.get("Company Name", "")
        try:
            score, breakdown, confidence = score_row(row)
        except Exception as exc:  # noqa: BLE001
            failures.record("stage4", row_num, company, "scoring_failed",
                            f"{type(exc).__name__}: {exc}")
            continue

        original = str(row.get("Lead Score /100", "") or "").strip()
        # Preserve the original once, and never let a re-run clobber the backup
        # with an already-rescored value.
        if original and not str(row.get("Lead Score (Original)", "") or "").strip():
            row["Lead Score (Original)"] = original

        row["Lead Score /100"] = str(score)   # authorised overwrite
        row["Lead Score Breakdown"] = breakdown
        row["Lead Score Confidence"] = confidence

        stats["rescored"] += 1
        stats[f"{confidence}_confidence"] += 1
        baseline = str(row.get("Lead Score (Original)", "") or original or "").strip()
        if baseline.isdigit():
            delta = score - int(baseline)
            if delta > 0:
                stats["moved_up"] += 1
            elif delta < 0:
                stats["moved_down"] += 1
            else:
                stats["unchanged"] += 1

    checkpoint()
    return stats
