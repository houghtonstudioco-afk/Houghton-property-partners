"""Synthetic pages representing the site archetypes in this dataset."""

MODERN_WELL_EQUIPPED = """
<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gregor Heating, Electrical &amp; Renewable Energy | Bristol</title>
<meta property="og:site_name" content="Gregor Heating">
<script src="/_next/static/chunks/main.js" type="module"></script>
<script src="https://js.hs-scripts.com/1234567.js"></script>
<script src="https://assets.calendly.com/assets/external/widget.js"></script>
</head><body>
<h1>Gregor Heating, Electrical &amp; Renewable Energy</h1>
<p>Serving Warmley, Bristol and the surrounding area since 1972. Call us on
<a href="tel:+441179352400">0117 935 2400</a> or
<a href="mailto:hello@gregor.co.uk">email the team</a>.</p>
<form action="/enquiry" method="post">
  <input name="your-name" placeholder="Your name">
  <input name="email" type="email" placeholder="Email">
  <textarea name="message"></textarea>
  <button type="submit">Send enquiry</button>
</form>
<div id="intercom-container"></div>
<script>window.Intercom = window.Intercom || function(){};
intercomSettings = {app_id: "ab12cd34"};</script>
<footer><p>&copy; 2026 Gregor Heating Ltd. Registered in England.</p></footer>
</body></html>
"""

DATED_JQUERY_SITE = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN">
<html><head><title>MCR Gas - Boiler Installation Bury Manchester</title>
<script src="js/jquery-1.7.2.min.js"></script>
<script src="js/jquery.cycle.js"></script>
</head><body bgcolor="#ffffff">
<table width="960" cellpadding="0" cellspacing="0" border="0">
<tr><td><table width="100%" cellpadding="4"><tr>
<td><font face="Arial" size="2"><center>MCR Gas</center></font></td>
<td>Bury, Manchester &mdash; Tel: 0161 660 6063</td>
</tr></table></td></tr>
<tr><td>Gas safety certificates and boiler servicing across Greater Manchester.
Email <a href="mailto:info@mcrgas.co.uk">info@mcrgas.co.uk</a></td></tr>
</table>
<p><embed src="banner.swf" type="application/x-shockwave-flash" width="468" height="60"></p>
<p>Copyright &copy; 2011 MCR Gas. All rights reserved.</p>
</body></html>
"""

PHONE_ONLY_MINIMAL = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width">
<title>The Gas Pro</title></head><body>
<h1>The Gas Pro - Bishopsworth, Bristol</h1>
<p>Gas Safe registered engineer covering Bristol. Boiler installation and
servicing. Ring <a href="tel:07830448127">07830 448127</a> for a quote.</p>
<p>Established 2019. We cover BS13 and surrounding postcodes.</p>
<footer>&copy; 2024 The Gas Pro</footer>
</body></html>
"""

PARKED_DOMAIN = """
<html><head><title>abcheating.co.uk</title></head><body>
<h1>This domain is parked</h1><p>Buy this domain.</p>
</body></html>
"""

TAWK_AND_BOOKING_ROUTE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Plumbco Heating Bristol</title>
<script src="https://embed.tawk.to/5f0a/default"></script>
</head><body>
<nav><a href="/about">About</a><a href="/book-a-service">Book a service</a></nav>
<h1>Plumbco Heating</h1><p>Bristol. 0117 901 2266</p>
<form><input name="email"><textarea name="enquiry"></textarea></form>
<p>&copy; 2026</p></body></html>
"""

ZOHO_AND_ACUITY = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aberdeen Oilfield Services Ltd</title>
<script src="https://salesiq.zoho.eu/widget"></script>
<script src="https://secure.acuityscheduling.com/embed.js"></script>
</head><body><h1>Aberdeen Oilfield Services</h1>
<p>Aberdeen, AB12 3XY. <a href="mailto:enquiries@example.co.uk">Email</a></p>
<p>&copy; 2026</p></body></html>
"""

DRIFT_PIPEDRIVE_SALESFORCE = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Industrial Pipe Fabrication Leeds</title>
<script src="https://js.driftt.com/include/abc/xyz.js"></script>
<script src="https://leadbooster-chat.pipedrive.com/assets/loader.js"></script>
<script>piAId = '12345'; piCId = '678';</script>
<script src="https://pi.pardot.com/pd.js"></script>
</head><body><h1>Fab Co Leeds</h1><p>&copy; 2026</p>
<form><input name="email"><textarea name="message"></textarea></form>
</body></html>
"""

CRISP_LIVECHAT_ZENDESK_CALCOM = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Test Multi Vendor</title>
<script src="https://client.crisp.chat/l.js"></script>
<script>window.$crisp=[];CRISP_WEBSITE_ID="abc";</script>
<script src="https://cdn.livechatinc.com/tracking.js"></script>
<script>window.__lc = {license: 123};</script>
<script src="https://static.zdassets.com/ekr/snippet.js"></script>
<script src="https://app.cal.com/embed/embed.js"></script>
<script src="https://widget.intercom.io/widget/abc"></script>
</head><body><p>&copy; 2026</p></body></html>
"""

SEARCH_FORM_ONLY = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Oil Distribution Devon</title></head><body>
<form role="search" action="/search"><input type="search" name="s"></form>
<h1>Devon Fuels</h1><p>Call 01392 000000</p>
<p>&copy; 2026 Devon Fuels</p></body></html>
"""

NO_CONTACT_AT_ALL = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nothing Here Engineering</title></head><body>
<h1>Nothing Here Engineering</h1>
<p>We are an engineering company based in Sheffield providing industrial
maintenance contracting services to clients across South Yorkshire and the
wider region, with over twenty years of experience in the sector.</p>
<p>&copy; 2026</p></body></html>
"""

WRONG_COMPANY_SAME_TRADE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Smith &amp; Sons Gas Engineers - Norwich</title></head><body>
<h1>Smith &amp; Sons Gas Engineers</h1>
<p>Norwich, NR1 1AA. Call 01603 111222.</p>
<p>Gas engineering across Norfolk for over thirty years, covering boilers,
servicing, and commercial gas work throughout the East of England region.</p>
<p>&copy; 2026</p></body></html>
"""

DIRECTORY_LISTING = """
<html><head><title>The Gas Pro, Bristol | Reviews | Yell</title></head>
<body><h1>The Gas Pro</h1><p>Bishopsworth, Bristol. 07830 448127</p>
<p>Find more gas engineers near you on Yell.com, the UK business directory
with millions of listings across every trade and region.</p></body></html>
"""


# --- Companies House search payloads -----------------------------------------

CH_GOOD_MATCH = {
    "items": [
        {
            "title": "MCR GAS LIMITED",
            "company_number": "09123456",
            "company_status": "active",
            "address_snippet": "12 Rochdale Road, Bury, Greater Manchester, BL9 7AA",
            "address": {"locality": "Bury", "postal_code": "BL9 7AA",
                        "address_line_1": "12 Rochdale Road"},
        },
        {
            "title": "MCR GAS SERVICES LTD",
            "company_number": "07777777",
            "company_status": "dissolved",
            "address_snippet": "9 High Street, Cardiff, CF10 1AA",
            "address": {"locality": "Cardiff", "postal_code": "CF10 1AA"},
        },
    ]
}

CH_WRONG_TOWN_ONLY = {
    "items": [
        {
            "title": "THE GAS PRO LIMITED",
            "company_number": "11111111",
            "company_status": "active",
            "address_snippet": "1 Sauchiehall Street, Glasgow, G2 3AA",
            "address": {"locality": "Glasgow", "postal_code": "G2 3AA"},
        }
    ]
}

CH_POSTCODE_ONLY_MATCH = {
    "items": [
        {
            "title": "THE GAS PRO LIMITED",
            "company_number": "12345678",
            "company_status": "active",
            # Town recorded as a suburb we don't have, but BS = Bristol.
            "address_snippet": "44 Hengrove Way, Hengrove, BS14 9BZ",
            "address": {"locality": "Hengrove", "postal_code": "BS14 9BZ"},
        }
    ]
}

CH_NO_NAME_MATCH = {
    "items": [
        {
            "title": "COMPLETELY DIFFERENT HOLDINGS PLC",
            "company_number": "22222222",
            "company_status": "active",
            "address_snippet": "1 Corn Street, Bristol, BS1 1AA",
            "address": {"locality": "Bristol", "postal_code": "BS1 1AA"},
        }
    ]
}

CH_SCOTTISH_NUMBER = {
    "items": [
        {
            "title": "ABERDEEN OILFIELD SERVICES LIMITED",
            "company_number": "SC123456",
            "company_status": "active",
            "address_snippet": "5 Union Street, Aberdeen, AB11 5BU",
            "address": {"locality": "Aberdeen", "postal_code": "AB11 5BU"},
        }
    ]
}
