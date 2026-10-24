# -*- coding: utf-8 -*-
"""בונה את האתר הסטטי בתיקייה site/ מתוך data/articles.json."""
import html
import json
import os
import shutil
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
<meta name="theme-color" content="#3a8fcd">
<meta property="og:image" content="{e(config.SITE_URL.rstrip("/") + "/icon-512.png") if config.SITE_URL else ""}">
{ads}
</head>
<body>
<header class="bar"><div class="bar-in">
  <a class="brand" href="{prefix}index.html">{e(config.SITE_NAME)}</a>
  <nav><a href="{prefix}index.html">ראשי</a><a href="{prefix}archive.html">ארכיון</a><a href="{prefix}about.html">אודות</a><a href="{prefix}contact.html">צור קשר</a></nav>
</div></header>
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
               "apple-touch-icon.png", "favicon.png"):
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
        f'<p class="stats"><b>{len(home)}</b> כותרות ב־{config.HOME_HOURS} שעות · '
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

    # SEO
    if config.SITE_URL:
        base = config.SITE_URL.rstrip("/") + "/"
        urls = ["", "archive.html", "about.html", "contact.html"] + [f"day/{d.isoformat()}.html" for d in by_day]
        sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        sm += [f"<url><loc>{e(base + u)}</loc></url>" for u in urls]
        sm.append("</urlset>")
        write(os.path.join(SITE, "sitemap.xml"), "\n".join(sm))
        robots = f"User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n"
    else:
        robots = "User-agent: *\nAllow: /\n"
    write(os.path.join(SITE, "robots.txt"), robots)
    if config.CUSTOM_DOMAIN:
        write(os.path.join(SITE, "CNAME"), config.CUSTOM_DOMAIN.strip() + "\n")
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    print(f"נבנה האתר: {len(home)} כותרות בעמוד הראשי, {len(by_day)} ימים בארכיון")


if __name__ == "__main__":
    main()
