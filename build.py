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

e = html.escape


def local(iso):
    return datetime.fromisoformat(iso).astimezone(TZ)


def day_label(d):
    return f"יום {DAYS[d.weekday()]} · {d.day} ב{MONTHS[d.month - 1]} {d.year}"


def item_html(a):
    code, lang_he = lang_info(a["lang"])
    t = local(a["seen"])
    translated = bool(a.get("he")) and code != "he"
    head = a["he"] if a.get("he") else a["title"]
    orig = ""
    if translated:
        orig = f'<p class="orig" dir="auto" lang="{e(code)}">{e(a["title"])}</p>'
    note = f"תורגם מ{e(lang_he)}" if translated else ("עברית" if code == "he" else f"{e(lang_he)} · טרם תורגם")
    return (
        f'<article class="item" data-lang="{e(code or "xx")}" data-country="{e(a["country"])}">'
        f'<span class="lang" title="{e(lang_he)}">{e((code or "?").upper())}</span>'
        f'<div class="body"><a href="{e(a["url"])}" target="_blank" rel="noopener nofollow">'
        f'<h3 dir="auto">{e(head)}</h3></a>{orig}'
        f'<div class="meta"><span>{e(a["domain"])}</span><span class="sep">·</span>'
        f'<span>{e(country_he(a["country"]))}</span><span class="sep">·</span>'
        f'<time datetime="{e(a["seen"])}">{t:%H:%M}</time><span class="sep">·</span>'
        f'<span>{note}</span></div></div></article>'
    )


def days_html(items):
    groups = OrderedDict()
    for a in items:
        groups.setdefault(local(a["seen"]).date(), []).append(a)
    out = []
    for d, rows in groups.items():
        out.append(f'<section class="day"><h2>{day_label(d)}</h2>'
                   + "".join(item_html(a) for a in rows) + "</section>")
    return "".join(out)


def filters_html(items):
    langs = Counter(lang_info(a["lang"]) for a in items)
    countries = Counter(a["country"] for a in items if a["country"])
    chips = [f'<button type="button" class="chip" data-lang="all" aria-pressed="true">הכול<small>{len(items)}</small></button>']
    for (code, he), n in langs.most_common(10):
        chips.append(f'<button type="button" class="chip" data-lang="{e(code or "xx")}" aria-pressed="false">{e(he)}<small>{n}</small></button>')
    opts = ['<option value="">כל המדינות</option>']
    for c, n in countries.most_common(40):
        opts.append(f'<option value="{e(c)}">{e(country_he(c))} ({n})</option>')
    return (
        '<div class="controls">'
        '<input id="q" type="search" placeholder="חיפוש בכותרות, למשל: עזה, איראן, בחירות" aria-label="חיפוש בכותרות">'
        '<div class="row"><div class="chips" role="group" aria-label="שפת מקור">' + "".join(chips) + "</div>"
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@500;700;900&family=Assistant:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="{prefix}style.css">
{ads}
</head>
<body>
<div class="wrap">
<header>
  <div class="top"><a class="brand" href="{prefix}index.html">{e(config.SITE_NAME)}</a>
  <nav><a href="{prefix}index.html">עכשיו</a><a href="{prefix}archive.html">ארכיון</a><a href="{prefix}about.html">אודות</a></nav></div>
</header>
{body}
<footer>
  <div>הכותרות נאספות אוטומטית מכלי תקשורת ברחבי העולם ומתורגמות לעברית בתרגום מכונה. ייתכנו אי־דיוקים בתרגום. כל הזכויות על הכתבות שמורות למקורות; לחיצה על כותרת מובילה לכתבה המקורית.</div>
  <div>מקור הנתונים: <a href="https://www.gdeltproject.org/" target="_blank" rel="noopener">GDELT Project</a>.</div>
</footer>
</div>
<script src="{prefix}app.js" defer></script>
</body>
</html>
"""


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
    for fn in ("style.css", "app.js"):
        shutil.copy(os.path.join(ASSETS, fn), os.path.join(SITE, fn))

    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=config.HOME_HOURS)).isoformat()
    home = [a for a in items if a["seen"] >= cutoff][:config.HOME_MAX]
    if not home:
        home = items[:50]

    langs_n = len({a["lang"] for a in home})
    countries_n = len({a["country"] for a in home if a["country"]})
    updated = now.astimezone(TZ)
    hero = (
        '<section class="hero">'
        '<div class="kicker"><span class="dot"></span> מתעדכן כל 15 דקות</div>'
        f'<h1>{e(config.SITE_TAGLINE)}</h1>'
        '<div class="stats">'
        f'<div><b>{len(home)}</b>כותרות ב־{config.HOME_HOURS} שעות</div>'
        f'<div><b>{countries_n}</b>מדינות</div>'
        f'<div><b>{langs_n}</b>שפות מקור</div>'
        f'<div><b>{updated:%H:%M}</b>עדכון אחרון</div>'
        "</div></section>"
    )
    if items:
        body = hero + filters_html(home) + '<main id="list">' + days_html(home) + "</main>"
    else:
        body = hero + '<p class="empty">הכותרות הראשונות ייאספו בריצה הקרובה. חזרו בעוד כמה דקות.</p>'
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(config.SITE_NAME, config.SITE_TAGLINE, body))

    # עמוד לכל יום (טוב לגוגל) + ארכיון
    by_day = OrderedDict()
    for a in items:
        by_day.setdefault(local(a["seen"]).date(), []).append(a)
    arch = []
    for d, rows in by_day.items():
        slug = d.isoformat()
        title = f"מה כתבו על ישראל בעולם ב־{d.day} ב{MONTHS[d.month - 1]} {d.year}"
        body = (f'<section class="hero"><div class="kicker">ארכיון יומי</div><h1>{e(title)}</h1>'
                f'<p class="lede">{len(rows)} כותרות מתוך {len({r["country"] for r in rows})} מדינות, מתורגמות לעברית.</p></section>'
                + filters_html(rows) + '<main id="list">' + days_html(rows) + "</main>")
        with open(os.path.join(SITE, "day", slug + ".html"), "w", encoding="utf-8") as f:
            f.write(page(title, title, body, prefix="../", path=f"day/{slug}.html"))
        arch.append(f'<li><a href="day/{slug}.html">{day_label(d)}</a><span>{len(rows)} כותרות</span></li>')
    body = ('<section class="hero"><h1>ארכיון</h1><p class="lede">כל הכותרות, לפי ימים.</p></section>'
            '<ul class="archive">' + "".join(arch) + "</ul>")
    with open(os.path.join(SITE, "archive.html"), "w", encoding="utf-8") as f:
        f.write(page("ארכיון", "ארכיון יומי של כותרות על ישראל מהתקשורת העולמית", body, path="archive.html"))

    about = f"""<section class="hero"><h1>אודות</h1></section><div class="prose">
<p>{e(config.SITE_NAME)} מרכז במקום אחד את מה שכותבים על ישראל בתקשורת העולמית: עיתונים, אתרי חדשות וסוכנויות מעשרות מדינות ובעשרות שפות.</p>
<p>כל 15 דקות המערכת סורקת את פרויקט GDELT, שמנטר אתרי חדשות בכל העולם, בוחרת כותרות שעוסקות בישראל, מסירה כפילויות ומתרגמת אותן לעברית בתרגום מכונה.</p>
<p>האתר לא מעתיק כתבות. מוצגות רק הכותרות, עם קישור לכתבה המקורית ולשם כלי התקשורת. הבחירה אוטומטית ואינה מבטאת עמדה; אנחנו מציגים את מה שהעולם כותב, גם כשזה לא נעים לקרוא.</p>
</div>"""
    with open(os.path.join(SITE, "about.html"), "w", encoding="utf-8") as f:
        f.write(page("אודות", "על האתר ואיך הוא עובד", about, path="about.html"))

    # SEO
    if config.SITE_URL:
        base = config.SITE_URL.rstrip("/") + "/"
        urls = ["", "archive.html", "about.html"] + [f"day/{d.isoformat()}.html" for d in by_day]
        sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        sm += [f"<url><loc>{e(base + u)}</loc></url>" for u in urls]
        sm.append("</urlset>")
        with open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write("\n".join(sm))
        robots = f"User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n"
    else:
        robots = "User-agent: *\nAllow: /\n"
    with open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)
    if config.CUSTOM_DOMAIN:
        with open(os.path.join(SITE, "CNAME"), "w") as f:
            f.write(config.CUSTOM_DOMAIN.strip() + "\n")
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    print(f"נבנה האתר: {len(home)} כותרות בעמוד הראשי, {len(by_day)} ימים בארכיון")


if __name__ == "__main__":
    main()
