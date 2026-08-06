"""Offline test suite for the enrichment pipeline.

Every stage is exercised without network access: HTTP responses are seeded
directly into the cache, so the full pipeline (including checkpointing and the
never-overwrite rule) runs end to end against known inputs.

Run with:  python -m pytest tests/ -q      (or: python tests/test_pipeline.py)
"""
from __future__ import annotations

import csv
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leadgen import config, stage1_websites, stage2_audit, stage3_companies_house, stage4_score  # noqa: E402
from leadgen.fetcher import Fetcher, diagnose_ssl, normalise_url, registrable_host  # noqa: E402
from leadgen.schema import ORIGINAL_COLUMNS, OUTPUT_COLUMNS  # noqa: E402
from leadgen.store import Cache, CachedResponse, FailureLog, read_rows, set_if_blank, write_rows_atomic  # noqa: E402
from leadgen.textutil import (  # noqa: E402
    location_city,
    name_similarity,
    phone_digits,
    phone_matches,
    postcode_area,
    town_matches,
)
from tests import fixtures  # noqa: E402


def seed(cache: Cache, url: str, body: str = "", status: int = 200,
         error: str | None = None, ssl_status: str | None = "valid",
         final_url: str | None = None) -> None:
    cache.put_response(CachedResponse(
        url=normalise_url(url),
        status=status if error is None else None,
        final_url=final_url or normalise_url(url),
        body=body,
        error=error,
        ssl_status=ssl_status,
    ))


def blank_row(**overrides) -> dict[str, str]:
    row = {c: "" for c in OUTPUT_COLUMNS}
    row.update(overrides)
    return row


class TempMixin:
    def setUp(self) -> None:
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.cache = Cache(self.tmp / "cache.sqlite")
        self.failures = FailureLog(self.tmp / "failures.log")
        self.fetcher = Fetcher(self.cache, offline=True, respect_robots=False)

    def tearDown(self) -> None:
        self.failures.close()
        self.cache.close()
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)


# ------------------------------------------------------------- text utils ----

class TestTextUtil(unittest.TestCase):
    def test_phone_digits_normalises_uk_formats(self):
        for variant in ["0117 964 0078", "+44 117 964 0078", "(0117) 9640078",
                        "0044 117 964 0078", "0117-964-0078"]:
            self.assertEqual(phone_digits(variant), "1179640078", variant)

    def test_phone_digits_handles_mobile(self):
        self.assertEqual(phone_digits("07830 448127"), "7830448127")
        self.assertEqual(phone_digits("+447830448127"), "7830448127")

    def test_phone_matches_across_markup(self):
        html = '<a href="tel:+441179352400">0117 <b>935</b> 2400</a>'
        self.assertTrue(phone_matches("0117 935 2400", html))

    def test_phone_matches_rejects_different_number(self):
        self.assertFalse(phone_matches("0117 935 2400", "Call 0161 660 6063"))

    def test_phone_matches_ignores_short_numbers(self):
        self.assertFalse(phone_matches("999", "999"))

    def test_name_similarity_ignores_legal_suffix(self):
        self.assertGreater(name_similarity("MCR Gas", "MCR GAS LIMITED"), 0.85)
        self.assertGreater(name_similarity("The Gas Pro", "GAS PRO LTD"), 0.85)

    def test_name_similarity_rejects_generic_trade_overlap(self):
        # Two unrelated firms sharing only 'gas'/'engineering' must not match.
        self.assertLess(
            name_similarity("Smith & Sons Gas Engineers",
                            "Jones Gas Engineers"), 0.72)

    def test_name_similarity_distinct_companies(self):
        self.assertLess(name_similarity("The Gas Pro", "Gregor Heating"), 0.5)

    def test_postcode_area_extraction(self):
        self.assertEqual(postcode_area("Bristol, BS13 8AB"), "BS")
        self.assertEqual(postcode_area("Aberdeen AB11 5BU"), "AB")
        self.assertEqual(postcode_area("London EC1A 1BB"), "EC")
        self.assertIsNone(postcode_area("no postcode here"))

    def test_location_city_takes_broadest_part(self):
        self.assertEqual(location_city("Bishopsworth, Bristol"), "bristol")
        self.assertEqual(location_city("Bristol"), "bristol")

    def test_town_matches_direct_hit(self):
        ok, basis = town_matches("Bury, Manchester", "12 Rochdale Road, Bury, BL9 7AA")
        self.assertTrue(ok)
        self.assertEqual(basis, "town")

    def test_town_matches_via_postcode_area(self):
        ok, basis = town_matches("Bishopsworth, Bristol", "44 Hengrove Way, BS14 9BZ")
        self.assertTrue(ok)
        self.assertEqual(basis, "postcode-area")

    def test_town_matches_rejects_wrong_city(self):
        ok, _ = town_matches("Bishopsworth, Bristol", "1 Sauchiehall Street, Glasgow, G2 3AA")
        self.assertFalse(ok)

    def test_town_match_respects_word_boundary(self):
        # 'Bury' must not match inside 'Canterbury'.
        ok, _ = town_matches("Bury, Manchester", "1 High Street, Canterbury, CT1 2AA")
        self.assertFalse(ok)


# ------------------------------------------------------ SSL classification ---

class TestSSL(unittest.TestCase):
    def test_expired(self):
        self.assertEqual(
            diagnose_ssl("certificate verify failed: certificate has expired"),
            "expired")

    def test_hostname_mismatch(self):
        self.assertEqual(
            diagnose_ssl("hostname 'x.co.uk' doesn't match 'y.co.uk'"),
            "hostname_mismatch")

    def test_self_signed(self):
        self.assertEqual(
            diagnose_ssl("certificate verify failed: self signed certificate"),
            "self_signed")

    def test_untrusted_chain(self):
        self.assertEqual(
            diagnose_ssl("unable to get local issuer certificate"),
            "untrusted_chain")

    def test_registrable_host_strips_www(self):
        self.assertEqual(registrable_host("https://www.Example.co.uk/x"), "example.co.uk")


# ----------------------------------------------------- stage 2 detection -----

class TestSignalDetection(unittest.TestCase):
    def test_detects_intercom_hubspot_calendly(self):
        html = fixtures.MODERN_WELL_EQUIPPED
        self.assertIn("Intercom", stage2_audit._find(stage2_audit.LIVE_CHAT_SIGNATURES, html))
        self.assertIn("Calendly", stage2_audit._find(stage2_audit.BOOKING_SIGNATURES, html))
        self.assertIn("HubSpot", stage2_audit._find(stage2_audit.CRM_SIGNATURES, html))

    def test_detects_all_seven_requested_chat_vendors(self):
        cases = {
            "Intercom": '<script src="https://widget.intercom.io/widget/x"></script>',
            "Drift": '<script src="https://js.driftt.com/include/a/b.js"></script>',
            "Tawk.to": '<script src="https://embed.tawk.to/abc/default"></script>',
            "Crisp": '<script src="https://client.crisp.chat/l.js"></script>',
            "LiveChat": '<script src="https://cdn.livechatinc.com/tracking.js"></script>',
            "Zendesk Chat": '<script src="https://static.zdassets.com/ekr/snippet.js"></script>',
            "HubSpot Chat": '<script src="https://js.hs-scripts.com/1.js"></script>',
        }
        for vendor, html in cases.items():
            found = stage2_audit._find(stage2_audit.LIVE_CHAT_SIGNATURES, html)
            self.assertIn(vendor, found, f"{vendor} not detected")

    def test_detects_all_four_requested_crm_vendors(self):
        cases = {
            "HubSpot": '<script src="https://js.hs-analytics.net/analytics/1.js"></script>',
            "Salesforce": "<script>piAId='123';</script><script src='https://pi.pardot.com/pd.js'></script>",
            "Pipedrive": '<script src="https://leadbooster-chat.pipedrive.com/a.js"></script>',
            "Zoho": '<script src="https://salesiq.zoho.eu/w"></script>',
        }
        for vendor, html in cases.items():
            self.assertIn(vendor, stage2_audit._find(stage2_audit.CRM_SIGNATURES, html), vendor)

    def test_detects_requested_booking_vendors(self):
        cases = {
            "Calendly": '<script src="https://assets.calendly.com/w.js"></script>',
            "Acuity": '<script src="https://secure.acuityscheduling.com/e.js"></script>',
            "Cal.com": '<script src="https://app.cal.com/embed/embed.js"></script>',
            "SimplyBook": '<iframe src="https://company.simplybook.it/v2/"></iframe>',
        }
        for vendor, html in cases.items():
            self.assertIn(vendor, stage2_audit._find(stage2_audit.BOOKING_SIGNATURES, html), vendor)

    def test_booking_route_detected_without_vendor(self):
        self.assertTrue(stage2_audit.BOOKING_ROUTE.search(fixtures.TAWK_AND_BOOKING_ROUTE))
        self.assertFalse(stage2_audit.BOOKING_ROUTE.search(fixtures.PHONE_ONLY_MINIMAL))

    def test_multi_vendor_page_finds_all(self):
        found = stage2_audit._find(stage2_audit.LIVE_CHAT_SIGNATURES,
                                   fixtures.CRISP_LIVECHAT_ZENDESK_CALCOM)
        for vendor in ("Crisp", "LiveChat", "Zendesk Chat", "Intercom"):
            self.assertIn(vendor, found)

    def test_no_false_positive_chat_on_plain_page(self):
        self.assertEqual(
            stage2_audit._find(stage2_audit.LIVE_CHAT_SIGNATURES,
                               fixtures.PHONE_ONLY_MINIMAL), [])


class TestOutdatedScore(unittest.TestCase):
    def score(self, html, url="https://example.co.uk", ssl="valid", year=2026):
        return stage2_audit.score_outdated(html, url, ssl, now_year=year)

    def test_modern_site_scores_low(self):
        score, signals = self.score(fixtures.MODERN_WELL_EQUIPPED)
        self.assertLessEqual(score, 2, signals)

    def test_dated_site_scores_high(self):
        score, signals = self.score(fixtures.DATED_JQUERY_SITE)
        self.assertGreaterEqual(score, 8, signals)
        joined = " ".join(signals)
        self.assertIn("no-responsive-viewport", joined)
        self.assertIn("jquery", joined)
        self.assertIn("table-based-layout", joined)
        self.assertIn("flash-remnants", joined)
        self.assertIn("legacy-html-tags", joined)

    def test_score_is_clamped_to_1_10(self):
        low, _ = self.score(fixtures.MODERN_WELL_EQUIPPED)
        self.assertGreaterEqual(low, 1)
        high, _ = self.score(fixtures.DATED_JQUERY_SITE, url="http://x.co.uk", ssl=None)
        self.assertLessEqual(high, 10)

    def test_http_only_penalised(self):
        secure, _ = self.score(fixtures.PHONE_ONLY_MINIMAL, "https://x.co.uk")
        plain, signals = self.score(fixtures.PHONE_ONLY_MINIMAL, "http://x.co.uk")
        self.assertGreater(plain, secure)
        self.assertIn("no-https", signals)

    def test_expired_cert_penalised(self):
        _, signals = self.score(fixtures.PHONE_ONLY_MINIMAL, ssl="expired")
        self.assertIn("tls-expired", signals)

    def test_stale_copyright_year(self):
        _, signals = self.score(fixtures.DATED_JQUERY_SITE)
        self.assertTrue(any("copyright-2011" in s for s in signals), signals)

    def test_copyright_year_range_takes_latest(self):
        self.assertEqual(
            stage2_audit.copyright_year("<footer>&copy; 2009-2024 Someone</footer>"), 2024)

    def test_jquery_with_modern_stack_not_penalised(self):
        html = ('<meta name="viewport" content="width=device-width">'
                '<script src="jquery-3.6.0.min.js"></script>'
                '<script src="/_next/static/x.js"></script><p>&copy; 2026</p>')
        _, signals = self.score(html)
        self.assertNotIn("jquery-only-stack", signals)


class TestContactMethod(unittest.TestCase):
    def test_real_form_detected(self):
        method, channels = stage2_audit.detect_contact_method(fixtures.MODERN_WELL_EQUIPPED)
        self.assertEqual(method, "form")
        self.assertIn("mailto", channels)
        self.assertIn("tel", channels)

    def test_search_form_is_not_a_contact_form(self):
        method, channels = stage2_audit.detect_contact_method(fixtures.SEARCH_FORM_ONLY)
        self.assertNotEqual(method, "form")
        self.assertNotIn("form", channels)

    def test_mailto_only(self):
        method, _ = stage2_audit.detect_contact_method(
            '<a href="mailto:a@b.co.uk">email</a>')
        self.assertEqual(method, "mailto")

    def test_phone_only(self):
        method, channels = stage2_audit.detect_contact_method(fixtures.PHONE_ONLY_MINIMAL)
        self.assertEqual(method, "phone")
        self.assertEqual(channels, ["tel"])

    def test_no_contact_route(self):
        method, channels = stage2_audit.detect_contact_method(fixtures.NO_CONTACT_AT_ALL)
        self.assertEqual(method, "none")
        self.assertEqual(channels, [])

    def test_embedded_third_party_form(self):
        method, _ = stage2_audit.detect_contact_method(
            '<iframe src="https://docs.google.com/forms/d/e/x/viewform"></iframe>')
        self.assertEqual(method, "form")


class TestCircuitBreakerPropagates(TempMixin, unittest.TestCase):
    """The breaker is useless if a per-row handler swallows it.

    This is a regression test for a real failure: a 51-row run kept going
    through all 51 rows and 61 requests after the breaker had fired, because
    stage 1's 'one bad row must not kill the run' handler caught EgressBlocked
    along with everything else and logged it as an ordinary row failure.
    """

    def _blocked_fetcher(self):
        from requests.exceptions import ProxyError
        f = Fetcher(self.cache, offline=False, respect_robots=False)
        f._sleep = lambda host: None

        def boom(*a, **kw):
            raise ProxyError("CONNECT tunnel failed, response 403")

        f.session.get = boom
        f.session.post = boom
        return f

    def test_stage1_run_aborts_rather_than_logging_every_row(self):
        from leadgen.fetcher import EgressBlocked
        rows = [blank_row(**{"Company Name": f"Co {i}", "Location": "Bristol",
                             "Phone Number": "0117 000 0000"})
                for i in range(40)]
        fetcher = self._blocked_fetcher()
        with self.assertRaises(EgressBlocked):
            stage1_websites.run(rows, fetcher, self.failures, lambda: None)
        # Must not have written a per-row failure for every company.
        self.assertNotIn("unhandled_exception", self.failures.counts)

    def test_stage2_run_aborts(self):
        from leadgen.fetcher import EgressBlocked
        rows = [blank_row(**{"Company Name": f"Co {i}",
                             "Website": f"https://co{i}.co.uk"})
                for i in range(40)]
        fetcher = self._blocked_fetcher()
        with self.assertRaises(EgressBlocked):
            stage2_audit.run(rows, fetcher, self.failures, lambda: None)
        self.assertNotIn("unhandled_exception", self.failures.counts)


class TestEmailExtraction(unittest.TestCase):
    HTML = ('<a href="mailto:info@clinic.co.uk">Email</a>'
            '<p>reception@clinic.co.uk careers@clinic.co.uk</p>'
            '<p>Dr Smith: j.smith@clinic.co.uk</p>'
            '<footer>Site by <a href="mailto:hello@webagency.com">Agency</a> '
            'noreply@clinic.co.uk logo@2x.png</footer>')

    def test_extracts_and_ranks_role_addresses_first(self):
        got = stage2_audit.extract_emails(self.HTML, "clinic.co.uk")
        self.assertEqual(got[0], "info@clinic.co.uk")
        self.assertIn("reception@clinic.co.uk", got)

    def test_excludes_other_domains(self):
        # The web designer's footer address is the commonest false positive,
        # and emailing a company's agency is worse than finding nothing.
        got = stage2_audit.extract_emails(self.HTML, "clinic.co.uk")
        self.assertNotIn("hello@webagency.com", got)

    def test_excludes_noreply_and_image_filenames(self):
        got = stage2_audit.extract_emails(self.HTML, "clinic.co.uk")
        self.assertNotIn("noreply@clinic.co.uk", got)
        self.assertNotIn("logo@2x.png", got)

    def test_careers_ranked_last_but_kept(self):
        got = stage2_audit.extract_emails(self.HTML, "clinic.co.uk")
        self.assertIn("careers@clinic.co.uk", got)
        self.assertEqual(got[-1], "careers@clinic.co.uk")

    def test_subdomain_of_site_is_accepted(self):
        html = '<a href="mailto:info@mail.clinic.co.uk">x</a>'
        self.assertIn("info@mail.clinic.co.uk",
                      stage2_audit.extract_emails(html, "clinic.co.uk"))

    def test_no_emails_returns_empty(self):
        self.assertEqual(stage2_audit.extract_emails("<p>call us</p>", "x.co.uk"), [])

    def test_deduplicates(self):
        html = "info@a.co.uk INFO@a.co.uk <a href='mailto:info@a.co.uk'>x</a>"
        self.assertEqual(stage2_audit.extract_emails(html, "a.co.uk"),
                         ["info@a.co.uk"])


class TestClassify(unittest.TestCase):
    def make(self, **kw):
        return CachedResponse(url="https://x.co.uk/", **kw)

    def test_200_https_is_ok(self):
        status, health = stage2_audit.classify(
            self.make(status=200, final_url="https://x.co.uk/", ssl_status="valid"))
        self.assertEqual((status, health), ("200", "ok"))

    def test_404_is_broken(self):
        _, health = stage2_audit.classify(self.make(status=404, final_url="https://x.co.uk/"))
        self.assertEqual(health, "broken")

    def test_500_is_broken(self):
        _, health = stage2_audit.classify(self.make(status=503, final_url="https://x.co.uk/"))
        self.assertEqual(health, "broken")

    def test_http_only_is_insecure(self):
        _, health = stage2_audit.classify(self.make(status=200, final_url="http://x.co.uk/"))
        self.assertEqual(health, "insecure")

    def test_expired_ssl_is_insecure(self):
        status, health = stage2_audit.classify(
            self.make(error="ssl_error: certificate has expired", ssl_status="expired"))
        self.assertEqual(health, "insecure")
        self.assertEqual(status, "ssl_expired")

    def test_dns_error_is_unreachable(self):
        status, health = stage2_audit.classify(self.make(error="dns_error: nope"))
        self.assertEqual((status, health), ("dns_error", "unreachable"))

    def test_timeout_is_unreachable(self):
        status, health = stage2_audit.classify(self.make(error="timeout: too slow"))
        self.assertEqual((status, health), ("timeout", "unreachable"))

    def test_circuit_breaker_trips_on_sustained_proxy_failure(self):
        from leadgen.fetcher import PROXY_ERROR_CIRCUIT_BREAK, EgressBlocked
        import tempfile
        from requests.exceptions import ProxyError

        tmp = Path(tempfile.mkdtemp())
        cache = Cache(tmp / "c.sqlite")
        fetcher = Fetcher(cache, offline=False, respect_robots=False)
        fetcher._sleep = lambda host: None          # no delays in the test

        def always_proxy_error(*a, **kw):
            raise ProxyError("CONNECT tunnel failed, response 403")

        fetcher.session.get = always_proxy_error

        for i in range(PROXY_ERROR_CIRCUIT_BREAK - 1):
            resp = fetcher.get(f"https://host{i}.co.uk", check_robots=False)
            self.assertTrue(resp.error.startswith("proxy_error"))

        with self.assertRaises(EgressBlocked):
            fetcher.get("https://final.co.uk", check_robots=False)

        cache.close()
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    def test_proxy_error_is_not_blamed_on_the_site(self):
        # A local egress failure must never present as a dead company site,
        # or every row scores as a hot prospect for the wrong reason.
        status, health = stage2_audit.classify(
            self.make(error="proxy_error: CONNECT tunnel failed, 403"))
        self.assertEqual(status, "proxy_error")
        self.assertEqual(health, "unknown")
        self.assertNotEqual(health, "unreachable")

    def test_proxy_error_scores_below_a_confirmed_dead_site(self):
        proxied = blank_row(**{"Website": "https://x.co.uk", "HTTP Status": "proxy_error",
                               "Site Health": "unknown", "Contact Method": "",
                               "Website Outdated Score (unverified)": ""})
        dead = blank_row(**{"Website": "https://x.co.uk", "HTTP Status": "dns_error",
                            "Site Health": "unreachable", "Contact Method": "none",
                            "Website Outdated Score (unverified)": "10"})
        self.assertLess(stage4_score.score_row(proxied)[0],
                        stage4_score.score_row(dead)[0])


# ------------------------------------------------------ stage 1 discovery ----

class TestDiscoveryGate(TempMixin, unittest.TestCase):
    def test_accepts_on_phone_match(self):
        seed(self.cache, "https://thegaspro.co.uk", fixtures.PHONE_ONLY_MINIMAL)
        row = blank_row(**{"Company Name": "The Gas Pro",
                           "Location": "Bishopsworth, Bristol",
                           "Phone Number": "07830 448127"})
        verdict = stage1_websites.verify_candidate(
            stage1_websites.Candidate("https://thegaspro.co.uk", "test"), row, self.fetcher)
        self.assertTrue(verdict.accepted, verdict)
        self.assertIn("phone-match", verdict.evidence)
        self.assertEqual(verdict.confidence, "high")

    def test_rejects_directory_host(self):
        row = blank_row(**{"Company Name": "The Gas Pro", "Phone Number": "07830 448127"})
        verdict = stage1_websites.verify_candidate(
            stage1_websites.Candidate("https://www.yell.com/biz/the-gas-pro", "test"),
            row, self.fetcher)
        self.assertFalse(verdict.accepted)
        self.assertIn("directory_host", verdict.reason)

    def test_rejects_wrong_company_with_same_trade(self):
        seed(self.cache, "https://gasengineers.co.uk", fixtures.WRONG_COMPANY_SAME_TRADE)
        row = blank_row(**{"Company Name": "Jones Gas Engineers",
                           "Location": "Sheffield",
                           "Phone Number": "0114 555 1234"})
        verdict = stage1_websites.verify_candidate(
            stage1_websites.Candidate("https://gasengineers.co.uk", "test"),
            row, self.fetcher)
        self.assertFalse(verdict.accepted, verdict)

    def test_rejects_parked_domain(self):
        seed(self.cache, "https://abcheating.co.uk", fixtures.PARKED_DOMAIN)
        row = blank_row(**{"Company Name": "ABC Heating", "Location": "Leeds",
                           "Phone Number": "0113 000 0000"})
        verdict = stage1_websites.verify_candidate(
            stage1_websites.Candidate("https://abcheating.co.uk", "test"),
            row, self.fetcher)
        self.assertFalse(verdict.accepted)
        self.assertIn("parked-page", verdict.evidence)

    def test_rejects_404_from_a_blind_domain_guess(self):
        # A guessed domain that 404s proves nothing - the guess was just wrong.
        seed(self.cache, "https://deadco.co.uk", "", status=404)
        row = blank_row(**{"Company Name": "Dead Co", "Phone Number": "0113 000 0000"})
        verdict = stage1_websites.verify_candidate(
            stage1_websites.Candidate("https://deadco.co.uk", "domain_guess"),
            row, self.fetcher)
        self.assertFalse(verdict.accepted)
        self.assertEqual(verdict.reason, "http_404")

    def test_accepts_404_from_search_when_domain_matches_name(self):
        # A search engine returning deadco.co.uk for "Dead Co" means the company
        # has a site and it is broken - the strongest prospect in the dataset.
        seed(self.cache, "https://deadco.co.uk", "", status=404)
        row = blank_row(**{"Company Name": "Dead Co", "Phone Number": "0113 000 0000"})
        verdict = stage1_websites.verify_candidate(
            stage1_websites.Candidate("https://deadco.co.uk", "brave"),
            row, self.fetcher)
        self.assertTrue(verdict.accepted, verdict)
        self.assertEqual(verdict.confidence, "medium")
        self.assertTrue(any("unreachable" in e for e in verdict.evidence), verdict.evidence)

    def test_rejects_unreachable_when_domain_does_not_match_name(self):
        seed(self.cache, "https://unrelated-domain.co.uk", "", status=404)
        row = blank_row(**{"Company Name": "Dead Co", "Phone Number": "0113 000 0000"})
        verdict = stage1_websites.verify_candidate(
            stage1_websites.Candidate("https://unrelated-domain.co.uk", "brave"),
            row, self.fetcher)
        self.assertFalse(verdict.accepted)

    def test_dns_failure_from_search_is_captured(self):
        self.cache.put_response(CachedResponse(
            url="https://ghostgas.co.uk/", error="dns_error: not found"))
        row = blank_row(**{"Company Name": "Ghost Gas", "Phone Number": "0113 000 0000"})
        verdict = stage1_websites.verify_candidate(
            stage1_websites.Candidate("https://ghostgas.co.uk", "brave"),
            row, self.fetcher)
        self.assertTrue(verdict.accepted, verdict)
        self.assertIn("unreachable(dns_error)", verdict.evidence)

    def test_rejects_redirect_to_facebook(self):
        seed(self.cache, "https://someheating.co.uk", "<html>hi</html>",
             final_url="https://www.facebook.com/someheating")
        row = blank_row(**{"Company Name": "Some Heating", "Phone Number": "0113 000 0000"})
        verdict = stage1_websites.verify_candidate(
            stage1_websites.Candidate("https://someheating.co.uk", "test"),
            row, self.fetcher)
        self.assertFalse(verdict.accepted)
        self.assertIn("redirects_to_directory", verdict.reason)

    def test_name_and_town_without_phone_can_still_pass(self):
        seed(self.cache, "https://mcrgas.co.uk", fixtures.DATED_JQUERY_SITE)
        row = blank_row(**{"Company Name": "MCR Gas", "Location": "Bury, Manchester",
                           "Phone Number": "0161 999 9999"})   # deliberately wrong
        verdict = stage1_websites.verify_candidate(
            stage1_websites.Candidate("https://mcrgas.co.uk", "test"), row, self.fetcher)
        self.assertTrue(verdict.accepted, verdict)
        self.assertEqual(verdict.confidence, "medium")

    def test_domain_guess_stems(self):
        stems = stage1_websites.DomainGuessProvider._stems("The Gas Pro")
        self.assertIn("thegaspro", stems)
        stems2 = stage1_websites.DomainGuessProvider._stems("Gregor Heating, Electrical & Renewable Energy")
        self.assertTrue(any("gregor" in s for s in stems2), stems2)

    def test_ddg_url_unwrapping(self):
        wrapped = "/l/?uddg=https%3A%2F%2Fthegaspro.co.uk%2F&rut=abc"
        self.assertEqual(
            stage1_websites.DuckDuckGoProvider._unwrap(wrapped),
            "https://thegaspro.co.uk/")

    def test_looks_parked(self):
        self.assertTrue(stage1_websites.looks_parked(fixtures.PARKED_DOMAIN))
        self.assertFalse(stage1_websites.looks_parked(fixtures.MODERN_WELL_EQUIPPED))


# --------------------------------------------------- stage 3 CH matching -----

class TestCompaniesHouseMatching(unittest.TestCase):
    def test_accepts_town_match_and_prefers_active(self):
        item, basis, reason = stage3_companies_house.pick_match(
            "MCR Gas", "Bury, Manchester", fixtures.CH_GOOD_MATCH["items"])
        self.assertIsNotNone(item)
        self.assertEqual(item["company_number"], "09123456")
        self.assertEqual(basis, "town")
        self.assertEqual(reason, "")

    def test_rejects_right_name_wrong_town(self):
        item, _, reason = stage3_companies_house.pick_match(
            "The Gas Pro", "Bishopsworth, Bristol", fixtures.CH_WRONG_TOWN_ONLY["items"])
        self.assertIsNone(item)
        self.assertIn("none registered", reason)

    def test_accepts_postcode_area_match(self):
        item, basis, _ = stage3_companies_house.pick_match(
            "The Gas Pro", "Bishopsworth, Bristol",
            fixtures.CH_POSTCODE_ONLY_MATCH["items"])
        self.assertIsNotNone(item)
        self.assertEqual(basis, "postcode-area")

    def test_rejects_unrelated_name_in_right_town(self):
        item, _, reason = stage3_companies_house.pick_match(
            "The Gas Pro", "Bristol", fixtures.CH_NO_NAME_MATCH["items"])
        self.assertIsNone(item)
        self.assertIn("no name match", reason)

    def test_empty_results(self):
        item, _, reason = stage3_companies_house.pick_match("X", "Bristol", [])
        self.assertIsNone(item)
        self.assertEqual(reason, "no search results")

    def test_number_zero_padded(self):
        self.assertEqual(stage3_companies_house.normalise_number("123456"), "00123456")
        self.assertEqual(stage3_companies_house.normalise_number("09123456"), "09123456")

    def test_scottish_prefix_preserved(self):
        self.assertEqual(stage3_companies_house.normalise_number("SC123456"), "SC123456")
        item, _, _ = stage3_companies_house.pick_match(
            "Aberdeen Oilfield Services", "Aberdeen",
            fixtures.CH_SCOTTISH_NUMBER["items"])
        self.assertEqual(
            stage3_companies_house.normalise_number(item["company_number"]), "SC123456")

    def test_address_blob_includes_postcode(self):
        blob = stage3_companies_house.address_blob(
            fixtures.CH_POSTCODE_ONLY_MATCH["items"][0])
        self.assertIn("BS14 9BZ", blob)


# ------------------------------------------------------- stage 4 scoring -----

class TestScoring(unittest.TestCase):
    def test_well_equipped_site_scores_low(self):
        row = blank_row(**{
            "Website": "https://gregor.co.uk", "HTTP Status": "200",
            "Site Health": "ok", "Live Chat Vendor": "Intercom",
            "Online Booking Vendor": "Calendly", "CRM Vendor": "HubSpot",
            "Contact Method": "form", "Website Outdated Score (unverified)": "1",
        })
        score, breakdown, confidence = stage4_score.score_row(row)
        self.assertLessEqual(score, 15, breakdown)
        self.assertEqual(confidence, "high")

    def test_dead_site_with_nothing_scores_near_max(self):
        row = blank_row(**{
            "Website": "https://dead.co.uk", "HTTP Status": "dns_error",
            "Site Health": "unreachable", "Contact Method": "none",
            "Website Outdated Score (unverified)": "10",
        })
        score, breakdown, _ = stage4_score.score_row(row)
        self.assertGreaterEqual(score, 95, breakdown)

    def test_no_website_scores_high_with_low_confidence(self):
        row = blank_row(**{"Company Name": "No Site Ltd", "Phone Number": "0117 000 0000"})
        score, breakdown, confidence = stage4_score.score_row(row)
        self.assertGreater(score, 70, breakdown)
        self.assertEqual(confidence, "low")

    def test_expired_ssl_scores_above_healthy_site(self):
        base = {"Website": "https://x.co.uk", "HTTP Status": "200",
                "Contact Method": "form", "Website Outdated Score (unverified)": "5"}
        healthy, _, _ = stage4_score.score_row(blank_row(**base, **{"Site Health": "ok"}))
        expired, _, _ = stage4_score.score_row(blank_row(**base, **{"Site Health": "insecure"}))
        self.assertGreater(expired, healthy)

    def test_chat_absence_adds_weight(self):
        base = {"Website": "https://x.co.uk", "HTTP Status": "200", "Site Health": "ok",
                "Contact Method": "form", "Website Outdated Score (unverified)": "5"}
        with_chat, _, _ = stage4_score.score_row(
            blank_row(**base, **{"Live Chat Vendor": "Tawk.to"}))
        without, _, _ = stage4_score.score_row(blank_row(**base))
        self.assertEqual(without - with_chat, stage4_score.W_CHAT)

    def test_form_only_beats_phone_route(self):
        base = {"Website": "https://x.co.uk", "HTTP Status": "200", "Site Health": "ok",
                "Website Outdated Score (unverified)": "5"}
        form, _, _ = stage4_score.score_row(blank_row(**base, **{"Contact Method": "form"}))
        phone, _, _ = stage4_score.score_row(blank_row(**base, **{"Contact Method": "phone"}))
        self.assertGreater(form, phone)

    def test_outdated_score_scales_monotonically(self):
        base = {"Website": "https://x.co.uk", "HTTP Status": "200", "Site Health": "ok",
                "Contact Method": "form"}
        scores = [stage4_score.score_row(
            blank_row(**base, **{"Website Outdated Score (unverified)": str(n)}))[0]
            for n in range(1, 11)]
        self.assertEqual(scores, sorted(scores))
        self.assertLess(scores[0], scores[-1])

    def test_score_bounded_0_100(self):
        for health in stage4_score.PRESENCE_POINTS:
            row = blank_row(**{"Website": "https://x.co.uk", "HTTP Status": "200",
                               "Site Health": health, "Contact Method": "none",
                               "Website Outdated Score (unverified)": "10"})
            score, _, _ = stage4_score.score_row(row)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)

    def test_falls_back_to_unverified_yes_no_columns(self):
        row = blank_row(**{"Website": "https://x.co.uk", "HTTP Status": "200",
                           "Site Health": "ok", "Contact Method": "form",
                           "Live Chat (unverified)": "Yes",
                           "Website Outdated Score (unverified)": "5"})
        _, breakdown, _ = stage4_score.score_row(row)
        self.assertIn("chat=0/", breakdown)


# --------------------------------------------- store / never-overwrite -------

class TestWebDevClassification(unittest.TestCase):
    """The critical property: 'we never looked' must never be reported as
    'they have no website'."""

    def test_confirmed_no_website_is_priority_1(self):
        row = blank_row(**{"Company Name": "No Site Ltd", "Website": "",
                           "Website Confidence": "none",
                           "Website Evidence": "name-moderate(0.61)+parked-page"})
        opportunity, priority = stage4_score.classify_webdev(row)
        self.assertEqual(priority, "1")
        self.assertIn("needs one built", opportunity)

    def test_discovery_never_run_is_not_a_prospect(self):
        row = blank_row(**{"Company Name": "Unknown Ltd", "Website": ""})
        opportunity, priority = stage4_score.classify_webdev(row)
        self.assertEqual(priority, "")
        self.assertIn("not run", opportunity)

    def test_all_lookups_failed_is_flagged_unconfirmed_not_no_website(self):
        row = blank_row(**{"Company Name": "Blocked Ltd", "Website": "",
                           "Website Confidence": "none",
                           "Website Evidence": "no-evidence"})
        opportunity, priority = stage4_score.classify_webdev(row)
        self.assertEqual(priority, "")
        self.assertIn("unconfirmed", opportunity)
        self.assertNotIn("needs one built", opportunity)

    def test_proxy_blocked_discovery_is_unconfirmed(self):
        row = blank_row(**{"Company Name": "Proxied Ltd", "Website": "",
                           "Website Confidence": "none",
                           "Website Evidence": "proxy_error"})
        _, priority = stage4_score.classify_webdev(row)
        self.assertEqual(priority, "")

    def test_dead_site_is_priority_2(self):
        for health, status in (("unreachable", "dns_error"), ("broken", "404")):
            row = blank_row(**{"Website": "https://x.co.uk", "Site Health": health,
                               "HTTP Status": status})
            _, priority = stage4_score.classify_webdev(row)
            self.assertEqual(priority, "2", health)

    def test_placeholder_is_priority_3(self):
        row = blank_row(**{"Website": "https://x.co.uk", "Site Health": "placeholder",
                           "HTTP Status": "200"})
        _, priority = stage4_score.classify_webdev(row)
        self.assertEqual(priority, "3")

    def test_insecure_is_priority_4(self):
        row = blank_row(**{"Website": "https://x.co.uk", "Site Health": "insecure",
                           "HTTP Status": "200_ssl_expired"})
        _, priority = stage4_score.classify_webdev(row)
        self.assertEqual(priority, "4")

    def test_dated_tiers(self):
        for score, expected in (("10", "5"), ("8", "5"), ("6", "6"), ("5", "6")):
            row = blank_row(**{"Website": "https://x.co.uk", "Site Health": "ok",
                               "HTTP Status": "200",
                               "Website Outdated Score (unverified)": score})
            _, priority = stage4_score.classify_webdev(row)
            self.assertEqual(priority, expected, score)

    def test_healthy_modern_site_is_not_a_prospect(self):
        row = blank_row(**{"Website": "https://x.co.uk", "Site Health": "ok",
                           "HTTP Status": "200",
                           "Website Outdated Score (unverified)": "2"})
        opportunity, priority = stage4_score.classify_webdev(row)
        self.assertEqual((opportunity, priority), ("", ""))

    def test_unchecked_site_is_not_a_prospect(self):
        row = blank_row(**{"Website": "https://x.co.uk", "HTTP Status": "proxy_error",
                           "Site Health": "unknown"})
        opportunity, priority = stage4_score.classify_webdev(row)
        self.assertEqual(priority, "")
        self.assertIn("not successfully checked", opportunity)

    def test_export_sorts_confirmed_first_then_by_reviews(self):
        import enrich_leads
        import tempfile
        rows = [
            blank_row(**{"Company Name": "Unconfirmed", "Website": "",
                         "Website Confidence": "none", "Website Evidence": "no-evidence"}),
            blank_row(**{"Company Name": "Dated", "Website": "https://d.co.uk",
                         "Site Health": "ok", "HTTP Status": "200",
                         "Website Outdated Score (unverified)": "9"}),
            blank_row(**{"Company Name": "NoSiteQuiet", "Website": "",
                         "Website Confidence": "none", "Website Evidence": "town-town",
                         "Google Reviews (verified)": "10"}),
            blank_row(**{"Company Name": "NoSiteBusy", "Website": "",
                         "Website Confidence": "none", "Website Evidence": "town-town",
                         "Google Reviews (verified)": "500"}),
            blank_row(**{"Company Name": "Healthy", "Website": "https://h.co.uk",
                         "Site Health": "ok", "HTTP Status": "200",
                         "Website Outdated Score (unverified)": "1"}),
        ]
        for r in rows:
            r["Web Dev Opportunity"], r["Web Dev Priority"] = \
                stage4_score.classify_webdev(r)

        tmp = Path(tempfile.mkdtemp()) / "webdev.csv"
        total, confirmed = enrich_leads.export_webdev(rows, tmp)

        out = read_rows(tmp)
        names = [r["Company Name"] for r in out]
        # Healthy site excluded entirely; busiest no-site first; unconfirmed last.
        self.assertNotIn("Healthy", names)
        self.assertEqual(names[0], "NoSiteBusy")
        self.assertEqual(names[1], "NoSiteQuiet")
        self.assertEqual(names[-1], "Unconfirmed")
        self.assertEqual((total, confirmed), (4, 3))
        import shutil
        shutil.rmtree(tmp.parent, ignore_errors=True)


class TestOutreachRanking(unittest.TestCase):
    def row(self, **kw):
        base = {"Company Name": "X", "Industry": "", "Services": "",
                "Phone Number": "0117 000 0000", "Location": "Bristol",
                "Google Reviews (verified)": "", "Google Rating (verified)": ""}
        base.update(kw)
        return blank_row(**base)

    def test_phone_kind(self):
        from leadgen.outreach import phone_kind
        self.assertEqual(phone_kind("07830 448127"), "mobile")
        self.assertEqual(phone_kind("+447830448127"), "mobile")
        self.assertEqual(phone_kind("0117 964 0078"), "landline")
        self.assertEqual(phone_kind("01224 651250"), "landline")
        self.assertEqual(phone_kind("0800 069 9404"), "non-geographic")
        self.assertEqual(phone_kind("0845 456 0639"), "non-geographic")

    def test_segments(self):
        from leadgen import outreach
        cases = [
            ("Oil & Gas Exploration/Production", "", outreach.ENERGY_MAJOR),
            ("Offshore Engineering", "", outreach.ENERGY_MAJOR),
            ("Commercial Gas Engineering", "", outreach.COMMERCIAL),
            ("Oil Distribution", "Domestic heating oil", outreach.DOMESTIC),
            ("Precision Engineering", "CNC machining", outreach.INDUSTRIAL),
            ("Industrial Pipe Fabrication", "", outreach.INDUSTRIAL),
            ("Gas Engineering", "Boiler installation", outreach.DOMESTIC),
        ]
        for industry, services, expected in cases:
            got = outreach.segment_of(self.row(Industry=industry, Services=services))
            self.assertEqual(got, expected, f"{industry} / {services}")

    def test_consumer_trade_beats_pipe_keyword(self):
        # "gas pipe replacement" must not read as pipe fabrication.
        from leadgen import outreach
        row = self.row(Industry="Gas & Pipework Engineering",
                       Services="Gas line install, boiler fitting, pipework",
                       **{"Phone Number": "07869 837241",
                          "Google Reviews (verified)": "409"})
        self.assertEqual(outreach.segment_of(row), outreach.DOMESTIC)

    def test_review_evidence_overrides_industry_label(self):
        from leadgen import outreach
        row = self.row(Industry="Oil Infrastructure Services",
                       Services="Oil tank replacement and decommissioning",
                       **{"Phone Number": "07875 639214",
                          "Google Reviews (verified)": "180"})
        self.assertEqual(outreach.segment_of(row), outreach.DOMESTIC)

    def test_low_review_industrial_stays_industrial(self):
        # A pipe fabricator with 3 reviews is not a weak business, and must not
        # be reclassified as consumer-facing either.
        from leadgen import outreach
        row = self.row(Industry="Industrial Pipe Fabrication",
                       **{"Phone Number": "0114 000 0000",
                          "Google Reviews (verified)": "3"})
        self.assertEqual(outreach.segment_of(row), outreach.INDUSTRIAL)

    def test_demand_is_percentile_within_segment_not_absolute(self):
        """The core property: a 4-review industrial firm at the top of its
        segment must beat a 4-review industrial firm at the bottom, and low
        absolute reviews must not doom an industrial lead."""
        from leadgen import outreach
        rows = [
            self.row(Company_Name="IndTop", Industry="Precision Engineering",
                     **{"Company Name": "IndTop",
                        "Google Reviews (verified)": "20"}),
            self.row(**{"Company Name": "IndLow", "Industry": "Precision Engineering",
                        "Google Reviews (verified)": "1"}),
            self.row(**{"Company Name": "DomLow", "Industry": "Gas Engineering",
                        "Services": "Boiler repair",
                        "Google Reviews (verified)": "20"}),
        ]
        outreach.rank(rows)
        by = {r["Company Name"]: r for r in rows}
        self.assertGreater(int(by["IndTop"]["Outreach Score /100"]),
                           int(by["IndLow"]["Outreach Score /100"]))

        # The property that matters: the SAME review count lands at a different
        # demand percentile depending on the segment it is compared against.
        # 20 reviews is top-of-pack among these industrial firms (75th, mid-rank
        # convention) but merely median among the domestic ones (50th).
        self.assertIn("75% of b2b industrial", by["IndTop"]["Outreach Breakdown"])
        self.assertIn("50% of domestic trade", by["DomLow"]["Outreach Breakdown"])

        def demand(row):
            return int(re.search(r"demand=(\d+)/30", row["Outreach Breakdown"]).group(1))

        self.assertNotEqual(demand(by["IndTop"]), demand(by["DomLow"]),
                            "identical review counts must not score identically "
                            "across segments")

    def test_energy_major_is_deprioritised_and_told_not_to_cold_call(self):
        from leadgen import outreach
        rows = [self.row(**{"Company Name": "Ithaca",
                            "Industry": "Oil & Gas Exploration/Production",
                            "Phone Number": "01224 460100",
                            "Google Reviews (verified)": "3"})]
        outreach.rank(rows)
        self.assertEqual(rows[0]["Segment"], outreach.ENERGY_MAJOR)
        self.assertIn("do not cold call", rows[0]["Contact Channel"].lower())
        self.assertIn("LinkedIn", rows[0]["Contact Approach"])

    def test_mobile_domestic_gets_direct_call_and_out_of_hours_timing(self):
        from leadgen import outreach
        rows = [self.row(**{"Company Name": "Solo Gas",
                            "Industry": "Gas Engineering",
                            "Services": "Boiler installation",
                            "Phone Number": "07830 448127",
                            "Google Reviews (verified)": "259",
                            "Google Rating (verified)": "5.0"})]
        outreach.rank(rows)
        r = rows[0]
        self.assertIn("mobile", r["Contact Channel"].lower())
        self.assertIn("07:30", r["Best Time To Call"])
        self.assertIn("259 Google reviews", r["Contact Approach"])

    def test_non_geographic_number_routes_away_from_phone(self):
        from leadgen import outreach
        rows = [self.row(**{"Company Name": "Switchboard Ltd",
                            "Industry": "Pipeline Contracting",
                            "Phone Number": "0800 069 9404"})]
        outreach.rank(rows)
        self.assertIn("not the phone", rows[0]["Contact Channel"])

    def test_industrial_approach_avoids_review_talk(self):
        from leadgen import outreach
        rows = [self.row(**{"Company Name": "Fab Co",
                            "Industry": "Industrial Pipe Fabrication",
                            "Phone Number": "0114 000 0000",
                            "Google Reviews (verified)": "3"})]
        outreach.rank(rows)
        self.assertIn("does not collect", rows[0]["Contact Approach"])

    def test_ranks_are_dense_and_ordered(self):
        from leadgen import outreach
        rows = [
            self.row(**{"Company Name": "A", "Industry": "Gas Engineering",
                        "Services": "Boiler repair", "Phone Number": "07000 000000",
                        "Google Reviews (verified)": "500",
                        "Google Rating (verified)": "4.9"}),
            self.row(**{"Company Name": "B",
                        "Industry": "Oil & Gas Exploration/Production",
                        "Phone Number": "01224 000000",
                        "Google Reviews (verified)": "1"}),
        ]
        ordered = outreach.rank(rows)
        self.assertEqual([r["Company Name"] for r in ordered], ["A", "B"])
        self.assertEqual([r["Outreach Rank"] for r in ordered], ["1", "2"])
        self.assertGreater(int(ordered[0]["Outreach Score /100"]),
                           int(ordered[1]["Outreach Score /100"]))

    def test_missing_review_data_does_not_crash_or_zero_out(self):
        from leadgen import outreach
        rows = [self.row(**{"Company Name": "NoData",
                            "Industry": "Offshore Engineering"})]
        outreach.rank(rows)
        self.assertTrue(rows[0]["Outreach Score /100"].isdigit())
        self.assertIn("no review data", rows[0]["Outreach Breakdown"])

    def test_pitch_copy_stays_trade_neutral(self):
        # The domestic segment also holds structural engineers and tank
        # fitters; boiler-specific copy must not leak onto them.
        from leadgen import outreach
        rows = [self.row(**{"Company Name": "Peter Foster Engineering",
                            "Industry": "Structural Engineering",
                            "Services": "Structural calculations and design",
                            "Phone Number": "07725 986933",
                            "Google Reviews (verified)": "95"})]
        outreach.rank(rows)
        pitch = outreach.pitch_sheet(rows)[0]["What To Pitch"]
        self.assertNotIn("boiler", pitch.lower())

    def test_pitch_leads_with_confirmed_site_problem(self):
        from leadgen import outreach
        cases = [
            ({"Web Dev Opportunity": "no website - needs one built"}, "Website build"),
            ({"Website": "https://x.co.uk", "Site Health": "broken"}, "Urgent rebuild"),
            ({"Website": "https://x.co.uk", "Site Health": "placeholder"}, "Real website"),
            ({"Website": "https://x.co.uk", "Site Health": "insecure"}, "HTTPS fix"),
        ]
        for extra, expected in cases:
            row = self.row(Industry="Gas Engineering", Services="Boiler repair",
                           **{"Phone Number": "07000 000000", **extra})
            outreach.rank([row])
            pitch = outreach.pitch_sheet([row])[0]["What To Pitch"]
            self.assertIn(expected, pitch, extra)

    def test_website_cell_never_implies_an_unchecked_site_is_absent(self):
        from leadgen import outreach
        row = self.row()
        self.assertEqual(outreach.website_cell(row), "not checked yet")
        row["Web Dev Opportunity"] = "no website - needs one built"
        self.assertIn("NONE FOUND", outreach.website_cell(row))
        row2 = self.row(**{"Website": "https://x.co.uk", "Site Health": "broken"})
        self.assertIn("DEAD", outreach.website_cell(row2))

    def test_pitch_sheet_has_the_six_requested_columns(self):
        from leadgen import outreach
        rows = [self.row(Industry="Gas Engineering", Services="Boiler repair",
                         **{"Company Name": "A", "Phone Number": "07000 000000"})]
        outreach.rank(rows)
        sheet = outreach.pitch_sheet(rows)
        self.assertEqual(list(sheet[0].keys()), outreach.PITCH_COLUMNS)
        for field in ("Company", "Score", "What They Do", "Phone", "Website",
                      "What To Pitch"):
            self.assertTrue(str(sheet[0][field]).strip(), field)

    def test_what_they_do_is_short(self):
        from leadgen import outreach
        row = self.row(Services="Boiler install, AC, heating systems, more, extra")
        self.assertEqual(outreach.what_they_do(row), "Boiler install, AC")

    def test_score_bounded(self):
        from leadgen import outreach
        rows = [self.row(**{"Company Name": "Max", "Industry": "Gas Engineering",
                            "Services": "Boiler", "Phone Number": "07000 000000",
                            "Google Reviews (verified)": "9999",
                            "Google Rating (verified)": "5.0"})]
        outreach.rank(rows)
        self.assertLessEqual(int(rows[0]["Outreach Score /100"]), 100)


class TestStore(TempMixin, unittest.TestCase):
    def test_set_if_blank_writes_only_when_empty(self):
        row = {"Website": ""}
        self.assertTrue(set_if_blank(row, "Website", "https://a.co.uk"))
        self.assertFalse(set_if_blank(row, "Website", "https://b.co.uk"))
        self.assertEqual(row["Website"], "https://a.co.uk")

    def test_set_if_blank_treats_whitespace_as_filled(self):
        row = {"Website": "   existing  "}
        self.assertFalse(set_if_blank(row, "Website", "https://b.co.uk"))

    def test_set_if_blank_ignores_empty_values(self):
        row = {"Website": ""}
        self.assertFalse(set_if_blank(row, "Website", ""))
        self.assertFalse(set_if_blank(row, "Website", None))
        self.assertFalse(set_if_blank(row, "Website", "   "))

    def test_cache_round_trip_including_errors(self):
        seed(self.cache, "https://a.co.uk", "<p>hi</p>")
        got = self.cache.get_response("https://a.co.uk/")
        self.assertIsNotNone(got)
        self.assertEqual(got.body, "<p>hi</p>")
        self.assertTrue(got.from_cache)

        self.cache.put_response(CachedResponse(url="https://b.co.uk/", error="dns_error: x"))
        err = self.cache.get_response("https://b.co.uk/")
        self.assertEqual(err.error, "dns_error: x")
        self.assertFalse(err.ok)

    def test_cache_ttl_expiry(self):
        stale = Cache(self.tmp / "stale.sqlite", ttl_days=0)
        stale.put_response(CachedResponse(url="https://a.co.uk/", status=200, body="x"))
        self.assertIsNone(stale.get_response("https://a.co.uk/"))
        stale.close()

    def test_offline_fetcher_reports_cache_miss(self):
        resp = self.fetcher.get("https://never-seen.co.uk")
        self.assertEqual(resp.error, "offline_cache_miss")

    def test_offline_fetcher_serves_hit(self):
        seed(self.cache, "https://seen.co.uk", "<p>ok</p>")
        resp = self.fetcher.get("https://seen.co.uk")
        self.assertTrue(resp.ok)
        self.assertEqual(self.fetcher.request_count, 0)

    def test_atomic_write_and_read_round_trip(self):
        rows = [blank_row(**{"Company Name": "A, Inc \"quoted\"", "Website": "https://a.co.uk"})]
        out = self.tmp / "out.csv"
        write_rows_atomic(out, rows, OUTPUT_COLUMNS)
        back = read_rows(out)
        self.assertEqual(back[0]["Company Name"], 'A, Inc "quoted"')
        self.assertEqual(list(back[0].keys()), OUTPUT_COLUMNS)

    def test_failure_log_format_is_greppable(self):
        self.failures.record("stage1", 7, "A|B Ltd", "website_not_found", "no\ncandidates")
        text = (self.tmp / "failures.log").read_text()
        line = [l for l in text.splitlines() if not l.startswith("#")][0]
        self.assertEqual(len(line.split(" | ")), 6)
        self.assertIn("A/B Ltd", line)          # pipe sanitised
        self.assertNotIn("\n", line.strip())
        self.assertEqual(self.failures.counts["website_not_found"], 1)


# ---------------------------------------------------- end-to-end pipeline ----

class TestEndToEnd(TempMixin, unittest.TestCase):
    """Full pipeline over a seeded cache, verifying the real CSV plumbing."""

    def _input_csv(self) -> Path:
        path = self.tmp / "leads.csv"
        rows = [
            {"Company Name": "The Gas Pro", "Location": "Bishopsworth, Bristol",
             "Phone Number": "07830 448127", "Industry": "Gas Engineering",
             "Lead Score /100": "90"},
            {"Company Name": "MCR Gas", "Location": "Bury, Manchester",
             "Phone Number": "0161 660 6063", "Industry": "Gas Engineering",
             "Lead Score /100": "90"},
            {"Company Name": "Gregor Heating, Electrical & Renewable Energy",
             "Location": "Warmley, Bristol", "Phone Number": "0117 935 2400",
             "Industry": "Gas Engineering", "Lead Score /100": "90"},
            {"Company Name": "Ghost Engineering Ltd", "Location": "Sheffield",
             "Phone Number": "0114 000 0000", "Industry": "Industrial Engineering",
             "Lead Score /100": "73"},
            # Pre-filled website must be preserved verbatim by stage 1.
            {"Company Name": "Prefilled Ltd", "Location": "Leeds",
             "Phone Number": "0113 000 0000", "Industry": "Precision Engineering",
             "Website": "https://prefilled.example.co.uk", "Lead Score /100": "68"},
        ]
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=ORIGINAL_COLUMNS)
            writer.writeheader()
            for r in rows:
                writer.writerow({c: r.get(c, "") for c in ORIGINAL_COLUMNS})
        return path

    def _seed_web(self) -> None:
        seed(self.cache, "https://thegaspro.co.uk", fixtures.PHONE_ONLY_MINIMAL)
        seed(self.cache, "https://mcrgas.co.uk", fixtures.DATED_JQUERY_SITE)
        seed(self.cache, "https://gregor.co.uk", fixtures.MODERN_WELL_EQUIPPED)
        seed(self.cache, "https://prefilled.example.co.uk",
             fixtures.TAWK_AND_BOOKING_ROUTE)
        # Ghost Engineering: every guessed domain fails DNS.
        for stem in ("ghostengineering", "ghost", "ghost-engineering"):
            for tld in config.GUESS_TLDS:
                self.cache.put_response(CachedResponse(
                    url=f"https://{stem}{tld}/", error="dns_error: not found"))

    def test_full_pipeline(self):
        from leadgen.schema import OUTPUT_COLUMNS as COLS
        input_csv = self._input_csv()
        self._seed_web()
        output_csv = self.tmp / "out.csv"

        rows = read_rows(input_csv)
        for row in rows:
            for column in COLS:
                row.setdefault(column, "")

        checkpoints = []

        def checkpoint():
            write_rows_atomic(output_csv, rows, COLS)
            checkpoints.append(len(read_rows(output_csv)))

        # -- stage 1, using only the domain guesser (no network) --
        providers = [stage1_websites.DomainGuessProvider()]
        for row_num, row in enumerate(rows, start=2):
            if str(row.get("Website", "")).strip():
                continue
            verdict = stage1_websites.discover_website(
                row, providers, self.fetcher, self.failures, row_num)
            if verdict.accepted:
                set_if_blank(row, "Website", verdict.url)
                row["Website Confidence"] = verdict.confidence
                row["Website Evidence"] = "+".join(verdict.evidence)
        checkpoint()

        by_name = {r["Company Name"]: r for r in rows}
        self.assertEqual(by_name["The Gas Pro"]["Website"], "https://thegaspro.co.uk/")
        self.assertEqual(by_name["MCR Gas"]["Website"], "https://mcrgas.co.uk/")
        self.assertEqual(by_name["Ghost Engineering Ltd"]["Website"], "")
        # never-overwrite held
        self.assertEqual(by_name["Prefilled Ltd"]["Website"],
                         "https://prefilled.example.co.uk")

        # -- stage 2 --
        stage2_audit.run(rows, self.fetcher, self.failures, checkpoint)

        gaspro = by_name["The Gas Pro"]
        self.assertEqual(gaspro["Site Health"], "ok")
        self.assertEqual(gaspro["Contact Method"], "phone")
        self.assertEqual(gaspro["Live Chat (unverified)"], "No")

        mcr = by_name["MCR Gas"]
        self.assertGreaterEqual(int(mcr["Website Outdated Score (unverified)"]), 8)
        self.assertEqual(mcr["Contact Method"], "mailto")

        gregor = by_name["Gregor Heating, Electrical & Renewable Energy"]
        self.assertIn("Intercom", gregor["Live Chat Vendor"])
        self.assertIn("Calendly", gregor["Online Booking Vendor"])
        self.assertIn("HubSpot", gregor["CRM Vendor"])
        self.assertEqual(gregor["Contact Method"], "form")
        self.assertLessEqual(int(gregor["Website Outdated Score (unverified)"]), 2)

        prefilled = by_name["Prefilled Ltd"]
        self.assertIn("Tawk.to", prefilled["Live Chat Vendor"])
        self.assertIn("own booking route", prefilled["Online Booking Vendor"])

        ghost = by_name["Ghost Engineering Ltd"]
        self.assertEqual(ghost["HTTP Status"], "")   # no site to check

        # -- stage 4 --
        stage4_score.run(rows, self.failures, checkpoint)

        self.assertEqual(gregor["Lead Score (Original)"], "90")
        gregor_score = int(gregor["Lead Score /100"])
        ghost_score = int(ghost["Lead Score /100"])
        mcr_score = int(mcr["Lead Score /100"])

        self.assertLess(gregor_score, 20,
                        f"well-equipped site should score low: {gregor['Lead Score Breakdown']}")
        # MCR Gas has a live but ancient site: it forfeits the presence points a
        # dead domain would earn, so it must sit below Ghost (no site at all)
        # while still being firmly in prospect territory.
        self.assertGreater(mcr_score, 60, mcr["Lead Score Breakdown"])
        self.assertGreater(ghost_score, 70, ghost["Lead Score Breakdown"])
        self.assertGreater(ghost_score, mcr_score,
                           "a missing site should outrank a merely dated one")
        self.assertGreater(mcr_score, gregor_score + 40,
                           "dated site must rank far above a well-equipped one")
        self.assertEqual(ghost["Lead Score Confidence"], "low")
        self.assertEqual(gregor["Lead Score Confidence"], "high")

        # Checkpoints all wrote a complete file.
        self.assertTrue(checkpoints)
        self.assertTrue(all(n == 5 for n in checkpoints), checkpoints)

        # Output retains all original columns plus the appended ones.
        final = read_rows(output_csv)
        self.assertEqual(list(final[0].keys()), COLS)
        for col in ORIGINAL_COLUMNS:
            self.assertIn(col, final[0])

        # Original file untouched.
        self.assertEqual(list(read_rows(input_csv)[0].keys()), ORIGINAL_COLUMNS)

    def test_rerun_is_idempotent(self):
        input_csv = self._input_csv()
        self._seed_web()
        rows = read_rows(input_csv)
        for row in rows:
            for column in OUTPUT_COLUMNS:
                row.setdefault(column, "")

        noop = lambda: None  # noqa: E731
        stage2_audit.run(rows, self.fetcher, self.failures, noop)
        stage4_score.run(rows, self.failures, noop)
        first = [dict(r) for r in rows]

        stage2_audit.run(rows, self.fetcher, self.failures, noop)
        stage4_score.run(rows, self.failures, noop)

        for before, after in zip(first, rows):
            self.assertEqual(before, after,
                             f"re-run changed {before['Company Name']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
