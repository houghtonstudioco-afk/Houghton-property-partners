"""Response cache, failure log and CSV checkpointing.

Three separate concerns, but they share one job: make a run resumable and make
a failed run inspectable.
"""
from __future__ import annotations

import csv
import json
import logging
import os
import sqlite3
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from . import config
from .schema import OUTPUT_COLUMNS

log = logging.getLogger("leadgen")


# ------------------------------------------------------------------ cache ----

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS http_cache (
    url         TEXT PRIMARY KEY,
    status      INTEGER,
    final_url   TEXT,
    headers     TEXT,
    body        TEXT,
    error       TEXT,
    ssl_status  TEXT,
    fetched_at  REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS kv_cache (
    namespace   TEXT NOT NULL,
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,
    fetched_at  REAL NOT NULL,
    PRIMARY KEY (namespace, key)
);
CREATE TABLE IF NOT EXISTS robots_cache (
    host        TEXT PRIMARY KEY,
    body        TEXT,
    fetched_at  REAL NOT NULL
);
"""


@dataclass
class CachedResponse:
    """A fetch outcome, whether it succeeded or not.

    Failures are cached too — re-running should not re-attempt 176 dead
    domains from scratch.
    """
    url: str
    status: int | None = None
    final_url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""
    error: str | None = None
    ssl_status: str | None = None
    from_cache: bool = False

    @property
    def ok(self) -> bool:
        return self.error is None and self.status is not None and 200 <= self.status < 300


class Cache:
    def __init__(self, path: Path | None = None, ttl_days: int | None = None):
        self.path = Path(path or config.CACHE_DB)
        self.ttl_seconds = (ttl_days if ttl_days is not None else config.CACHE_TTL_DAYS) * 86400
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def _fresh(self, fetched_at: float) -> bool:
        return (time.time() - fetched_at) < self.ttl_seconds

    # -- HTTP responses --

    def get_response(self, url: str) -> CachedResponse | None:
        row = self.conn.execute(
            "SELECT * FROM http_cache WHERE url = ?", (url,)
        ).fetchone()
        if row is None or not self._fresh(row["fetched_at"]):
            return None
        return CachedResponse(
            url=row["url"],
            status=row["status"],
            final_url=row["final_url"],
            headers=json.loads(row["headers"] or "{}"),
            body=row["body"] or "",
            error=row["error"],
            ssl_status=row["ssl_status"],
            from_cache=True,
        )

    def put_response(self, resp: CachedResponse) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO http_cache "
            "(url, status, final_url, headers, body, error, ssl_status, fetched_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                resp.url, resp.status, resp.final_url,
                json.dumps(resp.headers), resp.body, resp.error,
                resp.ssl_status, time.time(),
            ),
        )
        self.conn.commit()

    # -- arbitrary JSON payloads (search results, Companies House hits) --

    def get_json(self, namespace: str, key: str) -> Any | None:
        row = self.conn.execute(
            "SELECT value, fetched_at FROM kv_cache WHERE namespace=? AND key=?",
            (namespace, key),
        ).fetchone()
        if row is None or not self._fresh(row["fetched_at"]):
            return None
        return json.loads(row["value"])

    def put_json(self, namespace: str, key: str, value: Any) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO kv_cache (namespace, key, value, fetched_at) "
            "VALUES (?,?,?,?)",
            (namespace, key, json.dumps(value), time.time()),
        )
        self.conn.commit()

    # -- robots.txt (own table: longer-lived, tiny) --

    def get_robots(self, host: str) -> str | None:
        row = self.conn.execute(
            "SELECT body, fetched_at FROM robots_cache WHERE host=?", (host,)
        ).fetchone()
        if row is None or (time.time() - row["fetched_at"]) > 7 * 86400:
            return None
        return row["body"] or ""

    def put_robots(self, host: str, body: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO robots_cache (host, body, fetched_at) VALUES (?,?,?)",
            (host, body, time.time()),
        )
        self.conn.commit()

    def stats(self) -> dict[str, int]:
        q = lambda sql: self.conn.execute(sql).fetchone()[0]  # noqa: E731
        return {
            "http_responses": q("SELECT COUNT(*) FROM http_cache"),
            "http_errors": q("SELECT COUNT(*) FROM http_cache WHERE error IS NOT NULL"),
            "kv_entries": q("SELECT COUNT(*) FROM kv_cache"),
            "robots": q("SELECT COUNT(*) FROM robots_cache"),
        }

    def close(self) -> None:
        self.conn.close()


# ------------------------------------------------------------ failure log ----

class FailureLog:
    """Append-only, one line per failure, greppable.

    Format: ISO8601 | stage | row | company | code | detail
    """

    def __init__(self, path: Path | None = None):
        self.path = Path(path or config.FAILURE_LOG)
        self.counts: dict[str, int] = {}
        self._handle = None

    def _open(self):
        if self._handle is None:
            new = not self.path.exists()
            self._handle = self.path.open("a", encoding="utf-8")
            if new:
                self._handle.write(
                    "# timestamp | stage | row | company | code | detail\n"
                )
        return self._handle

    def record(self, stage: str, row_num: int, company: str, code: str, detail: str = "") -> None:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        clean = lambda s: str(s).replace("|", "/").replace("\n", " ").strip()  # noqa: E731
        line = f"{ts} | {stage} | {row_num} | {clean(company)} | {code} | {clean(detail)}\n"
        self._open().write(line)
        self._handle.flush()
        self.counts[code] = self.counts.get(code, 0) + 1
        log.debug("failure recorded: %s %s %s", stage, company, code)

    def summary(self) -> str:
        if not self.counts:
            return "no failures recorded"
        return ", ".join(f"{k}={v}" for k, v in sorted(self.counts.items(), key=lambda kv: -kv[1]))

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


# ------------------------------------------------------------------- CSV -----

def read_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = [{k: (v if v is not None else "") for k, v in r.items()} for r in reader]
    return rows


def write_rows_atomic(path: Path, rows: Iterable[dict[str, str]],
                      columns: list[str] | None = None) -> None:
    """Write the CSV via a temp file + rename.

    A checkpoint that dies mid-write must not leave a truncated output file
    behind, since the whole point of checkpointing is that the partial results
    survive.
    """
    path = Path(path)
    columns = columns or OUTPUT_COLUMNS
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({c: row.get(c, "") for c in columns})
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def set_if_blank(row: dict[str, str], column: str, value: Any) -> bool:
    """Fill a column only when it is currently blank.

    Returns True if the value was written. This is the single choke point for
    the "never overwrite an existing non-blank value" rule — stage code must
    not assign to row[...] for original columns directly.
    """
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    if str(row.get(column, "") or "").strip():
        return False
    row[column] = text
    return True
