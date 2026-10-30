# -*- coding: utf-8 -*-
"""בונה את האתר הסטטי בתיקייה site/ מתוך data/articles.json."""
import html
import json
import os
import shutil
import csv
import io
import urllib.request
import urllib.parse
from collections import OrderedDict, Counter
from datetime import datetime, timedelta, timezone

import config
from names import lang_info, country_he

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
ASSETS = ROOT

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Jerusalem")
except Exception:  # pragma: no cover
    TZ = timezone(timedelta(hours=3))

MONTHS = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט",
          "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
DAYS = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]  # weekday(): Monday=0

CUSDIS = getattr(config, "CUSDIS_APP_ID", "").strip()
MAIL = getattr(config, "CONTACT_EMAIL", "").strip()
GOAT = getattr(config, "GOATCOUNTER", "").strip()

e = html.escape


def local(iso):
    return datetime.fromisoformat(iso).astimezone(TZ)


def day_label(d):
    return f"יום {DAYS[d.weekday()]} · {d.day} ב{MONTHS[d.month - 1]} {d.year}"


def headline(a):
    return a["he"] if a.get("he") else a["title"]


def item_html(a, prefix=""):
    code, lang_he = lang_info(a["lang"])
    t = local(a["seen"])
    translated = bool(a.get("he")) and code != "he"
    orig = ""
    if translated:
        orig = f'<p class="orig" dir="auto" lang="{e(code)}">{e(a["title"])}</p>'
    country = country_he(a["country"])
    src = e(a["domain"]) + (f" ({e(country)})" if country else "")
    tag = f"תורגם מ{e(lang_he)}" if translated else ("עברית" if code == "he" else f"{e(lang_he)}, טרם תורגם")
    comments = (f'<a class="cm" href="{prefix}a/{e(a["id"])}.html">💬 תגובות</a>' if CUSDIS else "")
    return (
        f'<article class="item" data-lang="{e(code or "xx")}" data-country="{e(a["country"])}">'
        f'<a class="hl" href="{e(a["url"])}" target="_blank" rel="noopener nofollow">'
        f'<h3 dir="auto">{e(headline(a))}</h3></a>{orig}'
        f'<div class="meta"><span>מאת <b>{src}</b> בתאריך</span> '
        f'<time datetime="{e(a["seen"])}"><span class="date">{t:%d/%m}</span> <span class="time">{t:%H:%M}</span></time>'
        f'<span class="tag">{tag}</span>{comments}</div></article>'
    )


def days_html(items, prefix=""):
    groups = OrderedDict()
    for a in items:
        groups.setdefault(local(a["seen"]).date(), []).append(a)
    out = []
    for d, rows in groups.items():
        out.append(f'<section class="day"><h2>{day_label(d)}</h2>'
                   + "".join(item_html(a, prefix) for a in rows) + "</section>")
    return "".join(out)


def filters_html(items):
    langs = Counter(lang_info(a["lang"]) for a in items)
    countries = Counter(a["country"] for a in items if a["country"])
    tabs = [f'<button type="button" class="tab" data-lang="all" aria-pressed="true">הכול</button>']
    for (code, he), n in langs.most_common(8):
        tabs.append(f'<button type="button" class="tab" data-lang="{e(code or "xx")}" aria-pressed="false">{e(he)}</button>')
    opts = ['<option value="">כל המדינות</option>']
    for c, n in countries.most_common(40):
        opts.append(f'<option value="{e(c)}">{e(country_he(c))} ({n})</option>')
    return (
        '<div class="controls">'
        '<div class="tabs" role="group" aria-label="שפת מקור">' + "".join(tabs) + "</div>"
        '<div class="row"><input id="q" type="search" placeholder="חיפוש: עזה, איראן, בחירות…" aria-label="חיפוש בכותרות">'
        '<select id="country" aria-label="מדינת המקור">' + "".join(opts) + "</select></div>"
        '<p id="empty" class="empty" hidden>אין כותרות שמתאימות לסינון. נסו מילה אחרת או בחרו "הכול".</p>'
        "</div>"
    )


def page(title, desc, body, prefix="", path=""):
    full_title = f"{title} | {config.SITE_NAME}" if title != config.SITE_NAME else title
    canon = f'<link rel="canonical" href="{e(config.SITE_URL.rstrip("/") + "/" + path)}">' if config.SITE_URL else ""
    ads = ""
    if config.ADSENSE_CLIENT:
        ads = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={e(config.ADSENSE_CLIENT)}" '
               'crossorigin="anonymous"></script>')
    return f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="he_IL">
{canon}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;600;700;800&display=swap">
<link rel="stylesheet" href="{prefix}style.css">
<link rel="icon" type="image/png" href="{prefix}favicon.png">
<link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png">
<link rel="manifest" href="{prefix}manifest.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{e(config.SITE_NAME)}" href="{prefix}feed.xml">
<meta name="theme-color" content="#3a8fcd">
<meta property="og:image" content="{e(config.SITE_URL.rstrip("/") + "/og-image.png") if config.SITE_URL else ""}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:site_name" content="{e(config.SITE_NAME)}">
<meta name="twitter:card" content="summary_large_image">
{ads}
</head>
<body>
<header class="bar"><div class="bar-in">
  <a class="brand" href="{prefix}index.html">{e(config.SITE_NAME)}</a>
  <nav><a href="{prefix}index.html">ראשי</a><a href="{prefix}archive.html">ארכיון</a><a href="{prefix}about.html">אודות</a><a href="{prefix}contact.html">צור קשר</a><a class="jc" href="{prefix}community.html" lang="en" dir="ltr">🌍 Jewish Community</a><button type="button" id="install" class="inst" hidden>📲 התקן אפליקציה</button></nav>
</div></header>
<div id="install-help" class="install-help" hidden><div class="ih-in"><span class="tip"></span><button type="button" class="close" aria-label="סגור">✕</button></div></div>
<div class="wrap">
{body}
<footer>
  <div>הכותרות נאספות אוטומטית מכלי תקשורת ברחבי העולם ומתורגמות לעברית בתרגום מכונה. ייתכנו אי־דיוקים בתרגום. כל הזכויות על הכתבות שמורות למקורות; לחיצה על כותרת מובילה לכתבה המקורית.</div>
  <div>מקור הנתונים: <a href="https://www.gdeltproject.org/" target="_blank" rel="noopener">GDELT Project</a>.</div>
  {('<div>יצירת קשר: <a href="mailto:' + e(MAIL) + '">' + e(MAIL) + '</a></div>') if MAIL else ''}
</footer>
</div>
<script src="{prefix}app.js" defer></script>
{('<script data-goatcounter="https://' + e(GOAT) + '.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>') if GOAT else ''}
</body>
</html>
"""


def article_page(a):
    code, lang_he = lang_info(a["lang"])
    t = local(a["seen"])
    translated = bool(a.get("he")) and code != "he"
    country = country_he(a["country"])
    orig = f'<p class="orig big" dir="auto" lang="{e(code)}">{e(a["title"])}</p>' if translated else ""
    page_url = (config.SITE_URL.rstrip("/") + f"/a/{a['id']}.html") if config.SITE_URL else ""
    body = (
        '<section class="art">'
        f'<h1 dir="auto">{e(headline(a))}</h1>{orig}'
        f'<div class="meta"><span>מאת <b>{e(a["domain"])}{(" (" + e(country) + ")") if country else ""}</b> בתאריך</span> '
        f'<span class="date">{t:%d/%m/%Y}</span> <span class="time">{t:%H:%M}</span>'
        f'{("<span class=tag>תורגם מ" + e(lang_he) + "</span>") if translated else ""}</div>'
        f'<a class="go" href="{e(a["url"])}" target="_blank" rel="noopener nofollow">לכתבה המלאה ב־{e(a["domain"])} ↗</a>'
        "</section>"
        '<section class="comments"><h2>תגובות</h2>'
        '<p class="note">התגובות מתפרסמות אחרי אישור. אנא שמרו על שיח מכבד.</p>'
        f'<div id="cusdis_thread" data-host="https://cusdis.com" data-app-id="{e(CUSDIS)}" '
        f'data-page-id="{e(a["id"])}" data-page-url="{e(page_url)}" data-page-title="{e(headline(a))}" data-theme="auto"></div>'
        '<script async defer src="https://cusdis.com/js/cusdis.es.js"></script>'
        '</section>'
        '<p><a class="back" href="../index.html">→ חזרה לכל הכותרות</a></p>'
    )
    return page(headline(a), headline(a), body, prefix="../", path=f"a/{a['id']}.html")


# ---------- סיכום כל 3 שעות (לפרסום אוטומטי בפייסבוק דרך feed.xml) ----------
ISO2 = {
    "United States": "US", "United Kingdom": "GB", "France": "FR", "Germany": "DE", "Spain": "ES", "Italy": "IT",
    "Russia": "RU", "Ukraine": "UA", "Turkey": "TR", "Iran": "IR", "Qatar": "QA", "Egypt": "EG",
    "Saudi Arabia": "SA", "United Arab Emirates": "AE", "Jordan": "JO", "Lebanon": "LB", "Syria": "SY",
    "Iraq": "IQ", "Kuwait": "KW", "Morocco": "MA", "Algeria": "DZ", "Tunisia": "TN", "China": "CN", "Japan": "JP",
    "South Korea": "KR", "India": "IN", "Pakistan": "PK", "Indonesia": "ID", "Malaysia": "MY", "Australia": "AU",
    "Canada": "CA", "Mexico": "MX", "Brazil": "BR", "Argentina": "AR", "Chile": "CL", "Colombia": "CO",
    "Netherlands": "NL", "Belgium": "BE", "Switzerland": "CH", "Austria": "AT", "Poland": "PL", "Greece": "GR",
    "Portugal": "PT", "Ireland": "IE", "Sweden": "SE", "Norway": "NO", "Denmark": "DK", "Finland": "FI",
    "South Africa": "ZA", "Nigeria": "NG", "Serbia": "RS", "Romania": "RO", "Hungary": "HU", "Czech Republic": "CZ",
    "Philippines": "PH", "Singapore": "SG", "Venezuela": "VE", "Peru": "PE", "Cyprus": "CY",
}


def flag(country):
    c = ISO2.get(country)
    return "".join(chr(0x1F1E6 + ord(ch) - 65) for ch in c) if c else "🌍"


def build_feed(items, now):
    """feed.xml: פריט אחד לכל חלון של 3 שעות שהסתיים, עם עד 5 כותרות ממדינות שונות."""
    loc_now = now.astimezone(TZ)
    end = loc_now.replace(minute=0, second=0, microsecond=0, hour=(loc_now.hour // 3) * 3)
    base = (config.SITE_URL or "").rstrip("/")
    link = base + "/?utm_source=facebook&utm_campaign=auto"
    entries = []
    for k in range(8):
        w_end = end - timedelta(hours=3 * k)
        w_start = w_end - timedelta(hours=3)
        rows = [a for a in items if a.get("he") and w_start <= local(a["seen"]) < w_end
                and lang_info(a["lang"])[0] != "he"]
        picked, seen_c = [], set()
        for a in rows:  # קודם מדינה אחת לכל כותרת, לגיוון
            if a["country"] not in seen_c:
                picked.append(a); seen_c.add(a["country"])
            if len(picked) == 5:
                break
        if len(picked) < 2:
            continue
        lines = ["🌍 מה כתבו עלינו בעולם בשעות האחרונות:", ""]
        for a in picked:
            c = country_he(a["country"]) or a["domain"]
            lines.append(f"{flag(a['country'])} {c}: \"{a['he'].strip()}\"")
        lines += ["", f"כל הכותרות, מתורגמות לעברית ומתעדכנות כל רבע שעה 👇", link]
        text = "\n".join(lines)
        gid = w_end.strftime("%Y-%m-%dT%H")
        entries.append(
            "<item>"
            f"<title>{e(f'מה כתבו עלינו בעולם, {w_start:%H:%M}-{w_end:%H:%M}')}</title>"
            f"<link>{e(link)}</link>"
            f'<guid isPermaLink="false">kotvim-{gid}</guid>'
            f"<pubDate>{w_end.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>"
            f"<description>{e(text)}</description>"
            "</item>"
        )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f"<title>{e(config.SITE_NAME)}</title><link>{e(base + '/')}</link>"
            f"<description>{e(config.SITE_TAGLINE)}</description><language>he</language>"
            + "".join(entries) + "</channel></rss>\n")


# ---------- Jewish Community: מדריך עסקים יהודיים בעולם ----------
CATS = ["Real Estate", "Lawyers", "Doctors & Health", "Accounting & Finance", "Kosher Food & Restaurants",
        "Contractors & Home", "Tech & IT", "Travel & Tourism", "Education & Tutors", "Beauty & Fashion",
        "Events & Judaica", "Other"]


def _pick(row, *words):
    """מוצא עמודה לפי מילה בכותרת שלה (כדי שזה יעבוד עם כל טופס גוגל)."""
    for k, v in row.items():
        kl = (k or "").lower()
        if any(w in kl for w in words):
            return (v or "").strip()
    return ""


def load_community():
    url = getattr(config, "COMMUNITY_SHEET_CSV", "").strip()
    if not url:
        return []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "kotvim-aleinu"})
        raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8-sig")
    except Exception as ex:
        print("מדריך הקהילה: לא הצלחתי לקרוא את הגיליון:", ex)
        return []
    out = []
    for row in csv.DictReader(io.StringIO(raw)):
        ok = _pick(row, "approved", "אושר", "מאושר").lower()
        if ok not in ("yes", "y", "כן", "v", "✓", "✔", "true", "1"):
            continue
        name = _pick(row, "business name", "name", "שם")
        if not name:
            continue
        site = _pick(row, "website", "site", "אתר")
        if site and not site.startswith(("http://", "https://")):
            site = "https://" + site
        out.append({
            "name": name,
            "cat": _pick(row, "category", "תחום") or "Other",
            "country": _pick(row, "country", "מדינה"),
            "city": _pick(row, "city", "עיר"),
            "desc": _pick(row, "description", "about", "תיאור")[:300],
            "phone": _pick(row, "phone", "whatsapp", "טלפון"),
            "site": site,
        })
    out.sort(key=lambda r: (r["country"].lower(), r["city"].lower(), r["name"].lower()))
    return out


def community_page():
    rows = load_community()
    form = getattr(config, "COMMUNITY_FORM_URL", "").strip()
    if form:
        add_href = e(form)
    else:
        body_txt = ("Business name:\nCategory:\nCountry:\nCity:\nPhone / WhatsApp:\nWebsite:\n"
                    "Short description:\n\nI agree that this business will be listed publicly on kotvim-aleinu.com")
        add_href = e("mailto:" + MAIL + "?subject=" + urllib.parse.quote("Add my business - Jewish Community")
                     + "&body=" + urllib.parse.quote(body_txt))
    cards = []
    for r in rows:
        tel = "".join(ch for ch in r["phone"] if ch.isdigit() or ch == "+")
        links = []
        if tel:
            links.append(f'<a href="tel:{e(tel)}">📞 {e(r["phone"])}</a>')
            links.append(f'<a href="https://wa.me/{e(tel.lstrip("+"))}" target="_blank" rel="noopener">💬 WhatsApp</a>')
        if r["site"]:
            links.append(f'<a href="{e(r["site"])}" target="_blank" rel="noopener nofollow">🌐 Website</a>')
        cards.append(
            f'<article class="biz" data-country="{e(r["country"])}" data-city="{e(r["city"])}" data-cat="{e(r["cat"])}">'
            f'<h3>{e(r["name"])}</h3><p class="bmeta"><b>{e(r["cat"])}</b> · {e(r["city"])}{", " if r["city"] and r["country"] else ""}{e(r["country"])}</p>'
            + (f'<p class="bdesc">{e(r["desc"])}</p>' if r["desc"] else "")
            + (f'<p class="blinks">{" ".join(links)}</p>' if links else "") + "</article>")
    countries = sorted({r["country"] for r in rows if r["country"]})
    cats = [c for c in CATS if c in {r["cat"] for r in rows}] + sorted({r["cat"] for r in rows} - set(CATS))
    opt = lambda vals, first: f'<option value="">{first}</option>' + "".join(f'<option>{e(v)}</option>' for v in vals)
    if rows:
        listing = (
            '<div class="controls"><div class="row">'
            '<input id="bq" type="search" placeholder="Search: lawyer, Paris, kosher…" aria-label="Search">'
            f'<select id="bcountry" aria-label="Country">{opt(countries, "All countries")}</select>'
            f'<select id="bcat" aria-label="Category">{opt(cats, "All categories")}</select>'
            '</div></div>'
            f'<p class="stats"><b id="bn">{len(rows)}</b> businesses in <b>{len(countries)}</b> countries</p>'
            '<main id="blist" class="blist">' + "".join(cards) + "</main>"
            '<p id="bempty" class="empty" hidden>No businesses match. Try another search.</p>')
    else:
        listing = ('<div class="bfirst"><p><b>The directory is just starting.</b></p>'
                   '<p>Are you a Jewish professional or business owner anywhere in the world? '
                   'Be among the first to join, it is free.</p></div>')
    body = f"""<div lang="en" dir="ltr" class="community">
<section class="hero"><h1>🌍 Jewish Community</h1>
<p class="tagline">Jewish professionals &amp; businesses around the world, by country, city and field.</p>
<p class="stats">Real estate, lawyers, doctors, kosher food, contractors and more. Find a member of the community wherever you are.</p>
<p><a class="go addbiz" href="{add_href}" target="_blank" rel="noopener">➕ Add your business (free)</a></p></section>
{listing}
<div class="prose bnote"><p>Every listing is added only at the request of the business itself and checked by us before publishing. We never publish private home addresses.
To update or remove a listing, email <a href="mailto:{e(MAIL)}">{e(MAIL)}</a>.</p></div>
</div>
<script>
(function(){{
  var q=document.getElementById('bq'); if(!q) return;
  var c=document.getElementById('bcountry'), k=document.getElementById('bcat');
  var cards=[].slice.call(document.querySelectorAll('.biz')), n=document.getElementById('bn'), em=document.getElementById('bempty');
  function run(){{
    var t=q.value.trim().toLowerCase(), shown=0;
    cards.forEach(function(x){{
      var ok=(!c.value||x.dataset.country===c.value)&&(!k.value||x.dataset.cat===k.value)&&(!t||x.textContent.toLowerCase().indexOf(t)>-1);
      x.hidden=!ok; if(ok) shown++;
    }});
    n.textContent=shown; em.hidden=shown>0;
  }}
  q.addEventListener('input',run); c.addEventListener('change',run); k.addEventListener('change',run);
}})();
</script>"""
    return page("Jewish Community", "Directory of Jewish professionals and businesses around the world, by country, city and field.",
                body, path="community.html")


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    try:
        with open(os.path.join(ROOT, "data", "articles.json"), encoding="utf-8") as f:
            items = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        items = []
    items.sort(key=lambda x: x["seen"], reverse=True)

    if os.path.isdir(SITE):
        shutil.rmtree(SITE)
    os.makedirs(os.path.join(SITE, "day"))
    os.makedirs(os.path.join(SITE, "a"))
    for fn in ("style.css", "app.js", "manifest.webmanifest", "icon-192.png", "icon-512.png",
               "apple-touch-icon.png", "favicon.png", "og-image.png", "sw.js"):
        if not os.path.exists(os.path.join(ASSETS, fn)):
            continue
        shutil.copy(os.path.join(ASSETS, fn), os.path.join(SITE, fn))

    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=config.HOME_HOURS)).isoformat()
    home = [a for a in items if a["seen"] >= cutoff][:config.HOME_MAX]
    if not home:
        home = items[:50]

    countries_n = len({a["country"] for a in home if a["country"]})
    langs_n = len({a["lang"] for a in home})
    updated = now.astimezone(TZ)
    hero = (
        '<section class="hero">'
        f'<p class="tagline">{e(config.SITE_TAGLINE)}</p>'
        + (f'<div class="cta-box"><p class="cta1">{e(config.SITE_CTA_TITLE)}</p>'
           f'<p class="cta2">{e(config.SITE_CTA_TEXT)}</p></div>' if getattr(config, "SITE_CTA_TITLE", "") else "")
        + f'<p class="stats"><b>{len(home)}</b> כותרות ב־{config.HOME_HOURS} שעות · '
        f'<b>{countries_n}</b> מדינות · <b>{langs_n}</b> שפות · עודכן ב־<b class="time">{updated:%H:%M}</b></p>'
        "</section>"
    )
    if items:
        body = hero + filters_html(home) + '<main id="list">' + days_html(home) + "</main>"
    else:
        body = hero + '<p class="empty">הכותרות הראשונות ייאספו בריצה הקרובה. חזרו בעוד כמה דקות.</p>'
    write(os.path.join(SITE, "index.html"), page(config.SITE_NAME, config.SITE_TAGLINE, body))

    # עמוד תגובות לכל כותרת
    if CUSDIS:
        for a in items:
            write(os.path.join(SITE, "a", a["id"] + ".html"), article_page(a))

    # עמוד לכל יום + ארכיון
    by_day = OrderedDict()
    for a in items:
        by_day.setdefault(local(a["seen"]).date(), []).append(a)
    arch = []
    for d, rows in by_day.items():
        slug = d.isoformat()
        title = f"מה כתבו על ישראל בעולם ב־{d.day} ב{MONTHS[d.month - 1]} {d.year}"
        body = (f'<section class="hero"><h1>{e(title)}</h1>'
                f'<p class="stats"><b>{len(rows)}</b> כותרות מ־<b>{len({r["country"] for r in rows})}</b> מדינות</p></section>'
                + filters_html(rows) + '<main id="list">' + days_html(rows, "../") + "</main>")
        write(os.path.join(SITE, "day", slug + ".html"), page(title, title, body, prefix="../", path=f"day/{slug}.html"))
        arch.append(f'<li><a href="day/{slug}.html">{day_label(d)}</a><span>{len(rows)} כותרות</span></li>')
    body = ('<section class="hero"><h1>ארכיון</h1></section>'
            '<ul class="archive">' + "".join(arch) + "</ul>")
    write(os.path.join(SITE, "archive.html"), page("ארכיון", "ארכיון יומי של כותרות על ישראל מהתקשורת העולמית", body, path="archive.html"))

    about = f"""<section class="hero"><h1>אודות</h1></section><div class="prose">
<p>{e(config.SITE_NAME)} מרכז במקום אחד את מה שכותבים על ישראל בתקשורת העולמית: עיתונים, אתרי חדשות וסוכנויות מעשרות מדינות ובעשרות שפות.</p>
<p>כל 15 דקות המערכת סורקת את פרויקט GDELT, שמנטר אתרי חדשות בכל העולם, בוחרת כותרות שעוסקות בישראל, מסירה כפילויות ומתרגמת אותן לעברית בתרגום מכונה.</p>
<p>האתר לא מעתיק כתבות. מוצגות רק הכותרות, עם קישור לכתבה המקורית ולשם כלי התקשורת. הבחירה אוטומטית ואינה מבטאת עמדה; אנחנו מציגים את מה שהעולם כותב, גם כשזה לא נעים לקרוא.</p>
</div>"""
    write(os.path.join(SITE, "about.html"), page("אודות", "על האתר ואיך הוא עובד", about, path="about.html"))

    contact = f"""<section class="hero"><h1>צור קשר</h1></section><div class="prose">
<p>נשמח לשמוע מכם.</p>
<ul>
<li>מצאתם טעות בתרגום, או כותרת שלא שייכת לכאן?</li>
<li>רוצים להציע כלי תקשורת שכדאי לעקוב אחריו?</li>
<li>מעוניינים לפרסם באתר או לשתף פעולה?</li>
</ul>
<p>כתבו לנו: <a class="mail" href="mailto:{e(MAIL)}">{e(MAIL)}</a></p>
<p>אנחנו משתדלים לענות לכל פנייה.</p>
</div>"""
    write(os.path.join(SITE, "contact.html"), page("צור קשר", "יצירת קשר עם " + config.SITE_NAME, contact, path="contact.html"))
    write(os.path.join(SITE, "community.html"), community_page())

    # SEO
    if config.SITE_URL:
        base = config.SITE_URL.rstrip("/") + "/"
        urls = ["", "archive.html", "about.html", "contact.html", "community.html"] + [f"day/{d.isoformat()}.html" for d in by_day]
        sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        sm += [f"<url><loc>{e(base + u)}</loc></url>" for u in urls]
        sm.append("</urlset>")
        write(os.path.join(SITE, "sitemap.xml"), "\n".join(sm))
        robots = f"User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n"
    else:
        robots = "User-agent: *\nAllow: /\n"
    write(os.path.join(SITE, "robots.txt"), robots)
    write(os.path.join(SITE, "feed.xml"), build_feed(items, now))
    if config.CUSTOM_DOMAIN:
        write(os.path.join(SITE, "CNAME"), config.CUSTOM_DOMAIN.strip() + "\n")
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    print(f"נבנה האתר: {len(home)} כותרות בעמוד הראשי, {len(by_day)} ימים בארכיון")


if __name__ == "__main__":
    main()
