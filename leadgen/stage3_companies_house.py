"""Stage 3 - resolve Companies House numbers.

The search endpoint is a fuzzy free-text index, so a name hit on its own is not
evidence: 'MCR Gas' returns plausible-looking companies all over the country.
Every match must therefore clear an address gate against the Location column
before the number is written, per the user's instruction.

Matching policy in force: registered-office town matches Location, OR the
registered postcode area maps to the same city (config.POSTCODE_AREA_TO_CITY).
The basis of each accepted match is recorded in 'Companies House Match Basis'
so postcode-only matches stay auditable.
"""
from __future__ import annotations

import logging
from urllib.parse import quote_plus

from . import config
from .fetcher import Fetcher
from .store import FailureLog, set_if_blank
from .textutil import name_similarity, name_tokens, town_matches

log = logging.getLogger("leadgen")

API_ROOT = "https://api.company-information.service.gov.uk"

# Statuses that still identify the right legal entity. Dissolved companies are
# recorded but flagged, since a dissolved match usually means the trading entity
# is a different one.
LIVE_STATUSES = {"active", "open"}


def address_blob(item: dict) -> str:
    """Everything address-shaped in a search hit, as one searchable string."""
    parts: list[str] = []
    snippet = item.get("address_snippet")
    if snippet:
        parts.append(str(snippet))
    address = item.get("address") or item.get("registered_office_address") or {}
    if isinstance(address, dict):
        for key in ("address_line_1", "address_line_2", "locality", "region",
                    "postal_code", "country", "premises"):
            value = address.get(key)
            if value:
                parts.append(str(value))
    return ", ".join(parts)


def search_companies(name: str, fetcher: Fetcher, api_key: str,
                     items_per_page: int = 20) -> tuple[list[dict], str | None]:
    url = (f"{API_ROOT}/search/companies?q={quote_plus(name)}"
           f"&items_per_page={items_per_page}")
    payload, err = fetcher.get_json(
        url,
        auth=(api_key, ""),          # CH uses HTTP Basic: key as username
        headers={"Accept": "application/json"},
        cache_namespace="ch:search",
        cache_key=f"{name}|{items_per_page}",
    )
    if err:
        return [], err
    items = (payload or {}).get("items") or []
    return items, None


def pick_match(company: str, location: str, items: list[dict]
               ) -> tuple[dict | None, str, str]:
    """Choose the best address-verified match.

    Returns (item, basis, reject_reason). ``item`` is None when nothing clears
    both gates, and reject_reason explains what was closest.
    """
    scored: list[tuple[float, str, dict]] = []
    best_name_only = 0.0
    town_fail_count = 0

    for item in items:
        title = item.get("title") or item.get("company_name") or ""
        sim = name_similarity(company, title)
        best_name_only = max(best_name_only, sim)
        if sim < config.CH_NAME_SIMILARITY_THRESHOLD:
            continue

        matched, basis = town_matches(location, address_blob(item))
        if not matched:
            town_fail_count += 1
            continue

        status = (item.get("company_status") or "").lower()
        # Rank: name similarity first, then prefer active, then prefer a direct
        # town hit over a postcode-area inference.
        rank = sim + (0.06 if status in LIVE_STATUSES else 0.0) \
            + (0.03 if basis == "town" else 0.0)
        scored.append((rank, basis, item))

    if not scored:
        if town_fail_count:
            reason = (f"name matched {town_fail_count} compan"
                      f"{'y' if town_fail_count == 1 else 'ies'} but none "
                      f"registered in '{location}'")
        elif items:
            reason = f"no name match above {config.CH_NAME_SIMILARITY_THRESHOLD} " \
                     f"(best {best_name_only:.2f})"
        else:
            reason = "no search results"
        return None, "", reason

    scored.sort(key=lambda t: -t[0])
    _, basis, item = scored[0]
    return item, basis, ""


def normalise_number(number: str) -> str:
    """CH numbers are 8 chars: all-digit ones are zero-padded, Scottish/NI
    prefixed ones (SC, NI, OC, SO) are left as-is."""
    value = (number or "").strip().upper()
    if value.isdigit():
        return value.zfill(8)
    return value


def resolve(row: dict[str, str], fetcher: Fetcher, api_key: str,
            failures: FailureLog, row_num: int) -> bool:
    company = row.get("Company Name", "")
    location = row.get("Location", "")

    # Try the full name, then a trade-word-stripped variant, since many firms
    # register under a shorter name than they trade as.
    queries = [company]
    distinctive = name_tokens(company, drop_trade_words=True)
    if distinctive and " ".join(distinctive) != " ".join(name_tokens(company)):
        queries.append(" ".join(distinctive))

    last_reason = "no search results"
    for query in queries:
        items, err = search_companies(query, fetcher, api_key)
        if err:
            failures.record("stage3", row_num, company, "ch_api_error",
                            f"q='{query}' {err}")
            if "401" in err:
                raise PermissionError(err)
            continue

        item, basis, reason = pick_match(company, location, items)
        if item is None:
            last_reason = reason
            continue

        number = normalise_number(item.get("company_number", ""))
        if not number:
            last_reason = "match had no company_number"
            continue

        status = (item.get("company_status") or "").lower()
        set_if_blank(row, "Companies House Number", number)
        row["Companies House Name Matched"] = item.get("title", "")
        row["Companies House Status"] = status
        row["Companies House Match Basis"] = basis
        row["Companies House Address"] = address_blob(item)

        if status not in LIVE_STATUSES:
            failures.record("stage3", row_num, company, "ch_match_not_active",
                            f"{number} {item.get('title','')} status={status}")
        return True

    failures.record("stage3", row_num, company, "ch_no_verified_match",
                    f"location='{location}' {last_reason}")
    row["Companies House Match Basis"] = ""
    return False


def run(rows: list[dict[str, str]], fetcher: Fetcher, failures: FailureLog,
        checkpoint, limit: int | None = None) -> dict[str, int]:
    api_key = config.companies_house_key()
    stats = {"matched": 0, "unmatched": 0, "already_had": 0, "skipped_no_key": 0}

    if not api_key:
        log.error(
            "Companies House API key not found. Set COMPANIES_HOUSE_API_KEY in "
            "the environment or in .env, then re-run stage 3."
        )
        stats["skipped_no_key"] = len(rows)
        failures.record("stage3", 0, "-", "ch_no_api_key",
                        "COMPANIES_HOUSE_API_KEY unset; stage 3 skipped entirely")
        return stats

    todo = [(i, r) for i, r in enumerate(rows, start=2)
            if not str(r.get("Companies House Number", "") or "").strip()]
    stats["already_had"] = len(rows) - len(todo)
    if limit:
        todo = todo[:limit]

    for n, (row_num, row) in enumerate(todo, start=1):
        company = row.get("Company Name", "")
        log.info("[stage3 %d/%d] %s", n, len(todo), company)
        try:
            if resolve(row, fetcher, api_key, failures, row_num):
                stats["matched"] += 1
            else:
                stats["unmatched"] += 1
        except PermissionError:
            log.error("Companies House rejected the API key - aborting stage 3.")
            failures.record("stage3", row_num, company, "ch_auth_failed",
                            "aborted remaining rows")
            break
        except Exception as exc:  # noqa: BLE001
            failures.record("stage3", row_num, company, "unhandled_exception",
                            f"{type(exc).__name__}: {exc}")

        if n % 10 == 0:
            checkpoint()

    checkpoint()
    return stats
