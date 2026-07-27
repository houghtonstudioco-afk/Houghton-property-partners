#!/usr/bin/env python3
"""Enrich the UK gas/oil/industrial engineering lead list.

Four stages, each independently runnable and each checkpointing to the output
CSV so a crashed or rate-limited run never loses completed work:

    1  discover official websites          (search API or DDG + domain guessing)
    2  audit each site                     (health, chat, booking, CRM, age)
    3  resolve Companies House numbers     (address-verified matches only)
    4  rescore Lead Score /100             (from stage 2/3 signals)

The input file is opened read-only and never modified.

Usage
-----
    python enrich_leads.py --stages all
    python enrich_leads.py --stages 1,2 --limit 10
    python enrich_leads.py --stages 4              # cheap, no network
    python enrich_leads.py --stages 2 --offline    # replay from cache only
    python enrich_leads.py --report

Credentials are read from the environment or a local .env (never committed):
    COMPANIES_HOUSE_API_KEY=...
    BRAVE_SEARCH_API_KEY=...      # or SERPER_API_KEY, or GOOGLE_CSE_KEY+CX
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from leadgen import config
from leadgen.fetcher import Fetcher
from leadgen.schema import (
    APPENDED_COLUMNS,
    ORIGINAL_COLUMNS,
    OUTPUT_COLUMNS,
)
from leadgen.store import Cache, FailureLog, read_rows, write_rows_atomic

log = logging.getLogger("leadgen")


def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.RUN_LOG, encoding="utf-8"),
        ],
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def load_working_rows(input_csv: Path, output_csv: Path) -> list[dict[str, str]]:
    """Load the output CSV if a previous run produced one, else the input.

    Resuming from the output is what makes the pipeline restartable. The
    original file is only ever read.
    """
    source = output_csv if output_csv.exists() else input_csv
    rows = read_rows(source)
    if not rows:
        raise SystemExit(f"No data rows found in {source}")

    if source == input_csv:
        missing = [c for c in ORIGINAL_COLUMNS if c not in rows[0]]
        unexpected = [c for c in rows[0] if c not in ORIGINAL_COLUMNS]
        if missing or unexpected:
            raise SystemExit(
                "Input CSV schema does not match the expected 24 columns.\n"
                f"  missing:    {missing}\n  unexpected: {unexpected}\n"
                "Update leadgen/schema.py if the source file has legitimately "
                "changed - refusing to guess which column is which."
            )
        log.info("loaded %d rows from %s (fresh start)", len(rows), source.name)
    else:
        log.info("resuming from %s (%d rows)", source.name, len(rows))

    for row in rows:
        for column in APPENDED_COLUMNS:
            row.setdefault(column, "")
    return rows


def print_report(rows: list[dict[str, str]]) -> None:
    total = len(rows)

    def count(predicate) -> int:
        return sum(1 for r in rows if predicate(r))

    def filled(col: str) -> int:
        return count(lambda r: str(r.get(col, "") or "").strip())

    print(f"\n{'=' * 66}\n ENRICHMENT REPORT - {total} rows\n{'=' * 66}")

    print("\nStage 1  websites")
    print(f"  found                 {filled('Website'):>4}")
    for level in ("high", "medium", "none"):
        n = count(lambda r, lv=level: (r.get("Website Confidence") or "") == lv)
        print(f"    confidence {level:<8}{n:>4}")

    print("\nStage 2  site audit")
    print(f"  checked               {filled('HTTP Status'):>4}")
    health: dict[str, int] = {}
    for r in rows:
        key = (r.get("Site Health") or "not checked").strip() or "not checked"
        health[key] = health.get(key, 0) + 1
    for key, n in sorted(health.items(), key=lambda kv: -kv[1]):
        print(f"    {key:<18}{n:>4}")
    print(f"  has live chat         {count(lambda r: bool((r.get('Live Chat Vendor') or '').strip())):>4}")
    print(f"  has online booking    {count(lambda r: bool((r.get('Online Booking Vendor') or '').strip())):>4}")
    print(f"  has CRM               {count(lambda r: bool((r.get('CRM Vendor') or '').strip())):>4}")
    contact: dict[str, int] = {}
    for r in rows:
        key = (r.get("Contact Method") or "not checked").strip() or "not checked"
        contact[key] = contact.get(key, 0) + 1
    print("  contact method")
    for key, n in sorted(contact.items(), key=lambda kv: -kv[1]):
        print(f"    {key:<18}{n:>4}")

    print("\nStage 3  Companies House")
    print(f"  numbers resolved      {filled('Companies House Number'):>4}")
    basis: dict[str, int] = {}
    for r in rows:
        key = (r.get("Companies House Match Basis") or "").strip()
        if key:
            basis[key] = basis.get(key, 0) + 1
    for key, n in sorted(basis.items(), key=lambda kv: -kv[1]):
        print(f"    via {key:<14}{n:>4}")

    print("\nStage 4  lead score")
    scores = [int(r["Lead Score /100"]) for r in rows
              if str(r.get("Lead Score /100", "")).strip().isdigit()]
    if scores:
        buckets = [(90, 101), (80, 90), (70, 80), (60, 70), (40, 60), (0, 40)]
        for lo, hi in buckets:
            n = sum(1 for s in scores if lo <= s < hi)
            bar = "#" * min(n, 50)
            print(f"    {lo:>3}-{hi - 1:<3} {n:>4}  {bar}")
        print(f"  mean {sum(scores) / len(scores):.1f}   "
              f"min {min(scores)}   max {max(scores)}")
    conf: dict[str, int] = {}
    for r in rows:
        key = (r.get("Lead Score Confidence") or "not scored").strip() or "not scored"
        conf[key] = conf.get(key, 0) + 1
    for key, n in sorted(conf.items(), key=lambda kv: -kv[1]):
        print(f"    confidence {key:<8}{n:>4}")

    print(f"\n  Top 10 prospects")
    ranked = sorted(
        (r for r in rows if str(r.get("Lead Score /100", "")).strip().isdigit()),
        key=lambda r: -int(r["Lead Score /100"]),
    )[:10]
    for r in ranked:
        print(f"    {r['Lead Score /100']:>3}  {r['Company Name'][:38]:<38} "
              f"{(r.get('Site Health') or 'no site')[:12]:<12} "
              f"{r.get('Location', '')[:22]}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enrich the gas/oil/industrial engineering lead CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--stages", default="all",
                        help="comma list of 1,2,3,4 or 'all' (default: all)")
    parser.add_argument("--input", type=Path, default=config.INPUT_CSV)
    parser.add_argument("--output", type=Path, default=config.OUTPUT_CSV)
    parser.add_argument("--limit", type=int, default=None,
                        help="process at most N rows per stage (for a test run)")
    parser.add_argument("--offline", action="store_true",
                        help="never touch the network; serve from cache only")
    parser.add_argument("--ignore-robots", action="store_true",
                        help="skip robots.txt checks (off by default)")
    parser.add_argument("--cache", type=Path, default=config.CACHE_DB)
    parser.add_argument("--fresh", action="store_true",
                        help="start from the input CSV, ignoring existing output")
    parser.add_argument("--report", action="store_true",
                        help="print a summary of the current output CSV and exit")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    config.load_dotenv()
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    setup_logging(args.verbose)

    if args.report:
        if not args.output.exists():
            raise SystemExit(f"{args.output} does not exist yet - run a stage first.")
        print_report(read_rows(args.output))
        return 0

    if args.input.resolve() == args.output.resolve():
        raise SystemExit("Refusing to write output over the input file.")

    stages = ([1, 2, 3, 4] if args.stages.strip().lower() == "all"
              else [int(s) for s in args.stages.split(",") if s.strip()])
    for stage in stages:
        if stage not in (1, 2, 3, 4):
            raise SystemExit(f"Unknown stage: {stage}")

    if args.fresh and args.output.exists():
        backup = args.output.with_suffix(".csv.bak")
        args.output.replace(backup)
        log.info("--fresh: moved previous output to %s", backup.name)

    rows = load_working_rows(args.input, args.output)

    cache = Cache(args.cache)
    failures = FailureLog()
    fetcher = Fetcher(
        cache,
        offline=args.offline,
        respect_robots=not args.ignore_robots,
    )

    def checkpoint() -> None:
        write_rows_atomic(args.output, rows, OUTPUT_COLUMNS)

    checkpoint()   # write the full-width file immediately
    log.info("output: %s (%d columns)", args.output, len(OUTPUT_COLUMNS))
    if args.offline:
        log.warning("offline mode: cache misses are reported, not fetched")

    summaries: dict[str, dict[str, int]] = {}
    try:
        if 1 in stages:
            from leadgen import stage1_websites
            log.info("=== stage 1: website discovery ===")
            summaries["stage1"] = stage1_websites.run(
                rows, fetcher, failures, checkpoint, args.limit)

        if 2 in stages:
            from leadgen import stage2_audit
            log.info("=== stage 2: site audit ===")
            summaries["stage2"] = stage2_audit.run(
                rows, fetcher, failures, checkpoint, args.limit)

        if 3 in stages:
            from leadgen import stage3_companies_house
            log.info("=== stage 3: Companies House ===")
            summaries["stage3"] = stage3_companies_house.run(
                rows, fetcher, failures, checkpoint, args.limit)

        if 4 in stages:
            from leadgen import stage4_score
            log.info("=== stage 4: rescore ===")
            summaries["stage4"] = stage4_score.run(
                rows, failures, checkpoint, args.limit)

    except KeyboardInterrupt:
        log.warning("interrupted - checkpointing before exit")
        checkpoint()
        return 130
    finally:
        checkpoint()
        if fetcher.proxy_errors:
            log.error(
                "%d requests failed at the proxy layer. That is a local egress "
                "problem, not a signal about these companies - affected rows "
                "are marked 'proxy_error'/'unknown', NOT 'unreachable'. Fix "
                "network access and re-run; cached successes are kept.",
                fetcher.proxy_errors,
            )
        for name, stats in summaries.items():
            log.info("%s: %s", name,
                     ", ".join(f"{k}={v}" for k, v in stats.items()))
        log.info("requests made: %d | cache hits: %d | cache: %s",
                 fetcher.request_count, fetcher.cache_hits, cache.stats())
        log.info("failures: %s", failures.summary())
        if failures.counts:
            log.info("failure detail: %s", config.FAILURE_LOG)
        failures.close()
        cache.close()

    print_report(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
