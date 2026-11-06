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
KC_URL = getattr(config, "SUPABASE_URL", "").strip().rstrip("/")
WA_PAGE = "wa-k7q2.html"  # עמוד פרטי: לא מקושר, וחסום למנועי חיפוש
import hashlib as _h
ASSET_VER = _h.md5(b"".join(open(os.path.join(ROOT, f), "rb").read() for f in ("style.css", "app.js")
                            if os.path.exists(os.path.join(ROOT, f)))).hexdigest()[:8]
KC_KEY = getattr(config, "SUPABASE_KEY", "").strip()

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
        f'<article class="item" data-id="{e(a["id"])}" data-lang="{e(code or "xx")}" data-country="{e(a["country"])}">'
        f'<a class="hl" href="{e(a["url"])}" target="_blank" rel="noopener nofollow">'
        f'<h3 dir="auto">{e(headline(a))}</h3></a>{orig}'
        f'<div class="meta"><span>מאת <b>{src}</b> בתאריך</span> '
        f'<time datetime="{e(a["seen"])}"><span class="date">{t:%d/%m}</span> <span class="time">{t:%H:%M}</span></time>'
        f'<span class="tag">{tag}</span>{comments}'
        + ('<button type="button" class="kcb">💬 תגובות</button>' if KC_URL else '')
        + f'<button type="button" class="amb">✍️ הגיבו בשפה שלהם</button></div></article>'
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


def page(title, desc, body, prefix="", path="", og_image=""):
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
<link rel="stylesheet" href="{prefix}style.css?v={ASSET_VER}">
<link rel="icon" type="image/png" href="{prefix}favicon.png">
<link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png">
<link rel="manifest" href="{prefix}manifest.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{e(config.SITE_NAME)}" href="{prefix}feed.xml">
<meta name="theme-color" content="#3a8fcd">
<meta property="og:image" content="{e(og_image or (config.SITE_URL.rstrip("/") + "/og-image.png")) if config.SITE_URL else ""}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:site_name" content="{e(config.SITE_NAME)}">
<meta name="twitter:card" content="summary_large_image">
{ads}
</head>
<body>
<header class="bar"><div class="bar-in">
  <a class="brand" href="{prefix}index.html">{e(config.SITE_NAME)}</a>
  <nav><a href="{prefix}index.html">ראשי</a><a href="{prefix}videos.html">🎬 וידאו</a><a href="{prefix}archive.html">ארכיון</a><a href="{prefix}about.html">אודות</a><a href="{prefix}contact.html">צור קשר</a><a class="jc" href="{prefix}community.html" lang="en" dir="ltr">🌍 Jewish Community</a><button type="button" id="install" class="inst" hidden>📲 התקן אפליקציה</button></nav>
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
{('<script>window.KC=' + json.dumps({"url": KC_URL, "key": KC_KEY}) + ';</script>') if KC_URL else ''}
<script src="{prefix}app.js?v={ASSET_VER}" defer></script>
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


# ---------- תמונה לכל סיכום בפייסבוק ----------
_FONT = None


def _font_path():
    """פונט עברי: מהתיקייה, או הורדה חד-פעמית מ-Google Fonts (בשרת של GitHub)."""
    for p in (os.environ.get("KC_FONT", ""), os.path.join(ROOT, "Heebo.ttf"), "/tmp/Heebo.ttf"):
        if p and os.path.exists(p):
            return p
    try:
        url = "https://raw.githubusercontent.com/google/fonts/main/ofl/heebo/Heebo%5Bwght%5D.ttf"
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "kotvim"}), timeout=30).read()
        with open("/tmp/Heebo.ttf", "wb") as f:
            f.write(data)
        return "/tmp/Heebo.ttf"
    except Exception as ex:
        print("פונט לתמונות: לא הורד", ex)
        return None


_MIRROR = str.maketrans("()[]{}<>", ")(][}{><")


def _visual(s):
    """סידור פשוט של טקסט עברי (עם מילים לועזיות ומספרים) מימין לשמאל, לציור בתמונה."""
    import re as _re
    parts = _re.split(r"([A-Za-z0-9][A-Za-z0-9 .,:%'’/&+\-–]*[A-Za-z0-9%]|[A-Za-z0-9])", s)
    out = []
    for i, part in enumerate(parts):
        if not part:
            continue
        out.append(part if i % 2 else part[::-1].translate(_MIRROR))
    return "".join(reversed(out))


def digest_image(path, title, sub, rows):
    """1200x630: כותרת, עד 3 כותרות מהעולם עם שם המדינה, וכתובת האתר."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        try:  # בשרת של GitHub: התקנה חד-פעמית
            import subprocess, sys as _sys
            subprocess.run([_sys.executable, "-m", "pip", "install", "-q", "pillow"], check=True, timeout=180)
            from PIL import Image, ImageDraw, ImageFont
        except Exception as ex:
            print("תמונות לפייסבוק: אין Pillow", ex)
            return False
    fp = _font_path()
    if not fp:
        return False

    def F(size, w):
        f = ImageFont.truetype(fp, size, layout_engine=ImageFont.Layout.BASIC)
        try:
            f.set_variation_by_axes([w])
        except Exception:
            pass
        return f

    W, H = 1200, 630
    im = Image.new("RGB", (W, H), "#18208a")
    d = ImageDraw.Draw(im)
    for y in range(H):  # מעבר צבע עדין
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(0x2a + (0x0d - 0x2a) * t), int(0x63 + (0x12 - 0x63) * t), int(0xb8 + (0x50 - 0xb8) * t)))
    R = W - 50
    ft, fs, fc, fh, fu = F(54, 900), F(28, 600), F(26, 800), F(36, 800), F(30, 800)
    d.text((R, 38), _visual(title), font=ft, fill="#ffd84d", anchor="ra")
    d.text((R, 104), _visual(sub), font=fs, fill="#dfe6ff", anchor="ra")
    try:
        logo = Image.open(os.path.join(ROOT, "icon-192.png")).convert("RGBA").resize((96, 96))
        im.paste(logo, (50, 36), logo)
    except Exception:
        pass
    y = 160
    for country, head in rows[:3]:
        words, lines, cur = head.split(), [], ""
        for w_ in words:
            cand = (cur + " " + w_).strip()
            if fh.getlength(cand) <= W - 160:
                cur = cand
            else:
                lines.append(cur)
                cur = w_
        lines.append(cur)
        if len(lines) > 2:
            lines = lines[:2]
            while fh.getlength(lines[1] + "…") > W - 160 and " " in lines[1]:
                lines[1] = lines[1].rsplit(" ", 1)[0]
            lines[1] += "…"
        box_h = 50 + 44 * len(lines)
        d.rounded_rectangle([50, y, W - 50, y + box_h], radius=18, fill="#ffffff")
        d.rectangle([W - 62, y, W - 50, y + box_h], fill="#d2131a")
        d.text((R - 30, y + 12), _visual(country), font=fc, fill="#d2131a", anchor="ra")
        for i, ln in enumerate(lines):
            d.text((R - 30, y + 46 + 44 * i), _visual(ln), font=fh, fill="#18208a", anchor="ra")
        y += box_h + 14
        if y > H - 110:
            break
    url = "kotvim-aleinu.com"
    tw = fu.getlength(url)
    d.rounded_rectangle([50, H - 80, 50 + tw + 44, H - 26], radius=27, fill="#ffd84d")
    d.text((72, H - 53), url, font=fu, fill="#18208a", anchor="lm")
    d.text((R, H - 53), _visual("כל הכותרות מהעולם, בעברית"), font=fs, fill="#ffffff", anchor="rm")
    im.save(path, optimize=True)
    return True


_INTROS = ["🌍 מה כתבו עלינו בעולם בשעות האחרונות:", "📰 עוד מהעיתונות העולמית על ישראל:",
           "🗞️ ככה העולם מדבר עלינו עכשיו:", "🌐 כותרות על ישראל מרחבי העולם:"]


def build_feed(items, now):
    """feed.xml: פריט אחד לכל חלון של 3 שעות שהסתיים, עם עד 5 כותרות ממדינות שונות,
    ועמוד + תמונה ייחודיים לכל סיכום (התמונה מופיעה בפוסט בפייסבוק)."""
    loc_now = now.astimezone(TZ)
    end = loc_now.replace(minute=0, second=0, microsecond=0, hour=(loc_now.hour // 3) * 3)
    base = (config.SITE_URL or "").rstrip("/")
    os.makedirs(os.path.join(SITE, "p"), exist_ok=True)
    entries = []
    for k in range(56):  # עמודים לשבוע אחורה (קישורים בפוסטים ישנים), בפיד רק 8 האחרונים
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
        gid = w_end.strftime("%Y-%m-%dT%H")
        slug = w_end.strftime("%Y-%m-%d-%H")
        link = f"{base}/p/{slug}.html?utm_source=facebook&utm_campaign=auto"
        # הטקסט: השורה הראשונה היא כותרת מושכת (רק היא נראית לפני "עוד")
        h0 = picked[0]
        c0 = country_he(h0["country"]) or h0["domain"]
        lines = [f"{flag(h0['country'])} ב{c0} כותבים: \"{h0['he'].strip()}\"", "",
                 _INTROS[w_end.hour // 3 % len(_INTROS)]]
        for a in picked[1:]:
            c = country_he(a["country"]) or a["domain"]
            lines.append(f"{flag(a['country'])} {c}: \"{a['he'].strip()}\"")
        lines += ["", "כל הכותרות, מתורגמות לעברית ומתעדכנות כל רבע שעה 👇", link, "",
                  "#ישראל #חדשות #כולנו_שגרירים"]
        text = "\n".join(lines)
        day = "היום" if w_end.date() == loc_now.date() else f"{w_end:%d/%m}"
        title = "מה כתבו עלינו בעולם"
        sub = f"{day} · {w_start:%H:%M}–{w_end:%H:%M} · {len(picked)} כותרות מ־{len(picked)} מדינות"
        img_ok = digest_image(os.path.join(SITE, "p", slug + ".png"), title, sub,
                              [(country_he(a["country"]) or a["domain"], a["he"].strip()) for a in picked])
        sub_html = (f'{e(day)} · <span dir="ltr">{w_start:%H:%M}–{w_end:%H:%M}</span> · '
                    f'{len(picked)} כותרות מ־{len(picked)} מדינות')
        body = (f'<section class="hero"><h1>🌍 {e(title)}</h1><p class="stats">{sub_html}</p>'
                '<a class="go allbtn" href="../index.html">📰 לכל הכותרות של היום, מעשרות מדינות ←</a></section>'
                '<main id="list">' + "".join(item_html(a, "../") for a in picked) + "</main>"
                '<p><a class="go allbtn" href="../index.html">📰 לכל הכותרות של היום ←</a></p>')
        write(os.path.join(SITE, "p", slug + ".html"),
              page(f"{title} · {w_start:%H:%M}–{w_end:%H:%M}", h0["he"].strip(), body, prefix="../",
                   path=f"p/{slug}.html", og_image=(f"{base}/p/{slug}.png" if img_ok else "")))
        if k >= 8:
            continue
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


def video_teaser():
    """ריבוע בולט בראש העמוד הראשי: הסרטון האחרון + קישור לעמוד הווידאו"""
    try:
        with open(os.path.join(ROOT, "data", "videos.json"), encoding="utf-8") as f:
            vids = [v for v in json.load(f) if v.get("he")]
    except (FileNotFoundError, json.JSONDecodeError):
        vids = []
    if not vids:
        return ""
    v = vids[0]
    chans = len({x["channel"] for x in vids})
    return (f'<a class="vteaser" href="videos.html">'
            f'<div class="vt-img"><img src="https://i.ytimg.com/vi/{e(v["id"])}/hqdefault.jpg" alt=""><span class="vplay">▶</span>'
            f'<span class="vt-live">🎬 וידאו</span></div>'
            f'<div class="vt-txt"><p class="vt-k">צפו: מה משדרים עלינו עכשיו בעולם</p>'
            f'<p class="vt-h">״{e(v["he"])}״</p>'
            f'<p class="vt-m">{e(v["channel"])} · {len(vids)} סרטונים מ־{chans} ערוצי חדשות, עם תקציר בעברית ←</p></div></a>')


# ---------- הודעה מוכנה לערוץ הוואטסאפ (עמוד פרטי, לא מקושר מהאתר) ----------
def _words(t):
    import re as _re
    return {w for w in _re.findall(r"[֐-׿a-zA-Z0-9]{3,}", t or "")}


def whatsapp_page(items, now):
    since = now - timedelta(hours=12)
    rows = [a for a in items if a.get("he") and lang_info(a["lang"])[0] != "he"
            and local(a["seen"]) >= local(since.isoformat())]
    picked, seen_c, seen_w = [], set(), []
    for a in rows:  # מדינה אחת לכל כותרת, ונושאים שונים (בלי כותרות כמעט זהות)
        if a["country"] in seen_c:
            continue
        w = _words(a["he"])
        if any(len(w & o) / max(1, len(w | o)) > 0.35 for o in seen_w):
            continue
        picked.append(a); seen_c.add(a["country"]); seen_w.append(w)
        if len(picked) == 6:
            break
    try:
        with open(os.path.join(ROOT, "data", "videos.json"), encoding="utf-8") as f:
            vids = [v for v in json.load(f) if v.get("he")]
    except (FileNotFoundError, json.JSONDecodeError):
        vids = []
    base = (config.SITE_URL or "").rstrip("/")
    loc = now.astimezone(TZ)
    n24 = sum(1 for a in items if a.get("he") and local(a["seen"]) >= local((now - timedelta(hours=24)).isoformat()))
    nc = len({a["country"] for a in items if a.get("he") and local(a["seen"]) >= local((now - timedelta(hours=24)).isoformat())})
    part = "בוקר" if loc.hour < 12 else ("צהריים" if loc.hour < 17 else "ערב")
    lines = [f"🌍 *מה כתבו עלינו בעולם* | {part} {loc:%d.%m}",
             f"{n24} כותרות מ־{nc} מדינות ב־24 השעות האחרונות. הנה המעניינות:", ""]
    for a in picked:
        c = country_he(a["country"]) or a["domain"]
        lines.append(f"{flag(a['country'])} *{c}:* \"{a['he'].strip()}\"")
    if vids:
        v = vids[0]
        lines += ["", f"🎬 *וידאו:* {v['channel']}: \"{v['he'].strip()}\"",
                  f"👉 {base}/videos.html?utm_source=whatsapp&utm_campaign=channel"]
    lines += ["", "✍️ ראיתם כותרת שמעוותת את המציאות? הגיבו בשפה שלהם, ישר מהאתר.", "",
              "📰 כל הכותרות בעברית 👇", f"{base}/?utm_source=whatsapp&utm_campaign=channel", "",
              "כולנו שגרירים 🇮🇱"]
    text = "\n".join(lines)
    body = ('<section class="hero"><h1>📱 הודעה מוכנה לערוץ הוואטסאפ</h1>'
            f'<p class="stats">עודכן ב־<b>{loc:%H:%M}</b> · מתעדכן לבד כל רבע שעה, מהכותרות של 12 השעות האחרונות</p></section>'
            '<p><button type="button" id="wacopy" class="go wabtn">📋 העתק את ההודעה</button> '
            '<span id="wadone" class="wadone" hidden>✓ הועתק! עכשיו הדבק בערוץ</span></p>'
            f'<textarea id="watext" class="watext" rows="22" dir="rtl">{e(text)}</textarea>'
            '<p class="note">אפשר לערוך את הטקסט לפני ההעתקה. הכוכביות (*) מודגשות בוואטסאפ.</p>'
            """<script>document.getElementById('wacopy').onclick=function(){var t=document.getElementById('watext');
t.select();var ok=function(){var d=document.getElementById('wadone');d.hidden=false;setTimeout(function(){d.hidden=true},4000)};
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t.value).then(ok,function(){document.execCommand('copy');ok()})}
else{document.execCommand('copy');ok()}};</script>""")
    return page("הודעה לערוץ הוואטסאפ", "עמוד פנימי", body, path=WA_PAGE)


def videos_page():
    try:
        with open(os.path.join(ROOT, "data", "videos.json"), encoding="utf-8") as f:
            vids = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        vids = []
    if getattr(config, "HIDE_UNTRANSLATED", True):
        vids = [v for v in vids if v.get("he")] or vids
    cards = []
    for v in vids:
        try:
            t = local(v["seen"])
            when = f'<span class="date">{t:%d/%m}</span> <span class="time">{t:%H:%M}</span>'
        except Exception:
            when = ""
        code, _ = lang_info(v.get("lang"))
        orig = (f'<p class="orig" dir="auto" lang="{e(code)}">{e(v["title"])}</p>' if v.get("he") else "")
        cards.append(
            f'<article class="vcard"><button type="button" class="vthumb" data-id="{e(v["id"])}" aria-label="נגן">'
            f'<img loading="lazy" src="https://i.ytimg.com/vi/{e(v["id"])}/hqdefault.jpg" alt=""><span class="vplay">▶</span></button>'
            f'<h3 dir="auto">{e(v.get("he") or v["title"])}</h3>{orig}'
            + (f'<p class="vdesc">📝 <b>על מה הסרטון:</b> {e(v["desc_he"])}</p>' if v.get("desc_he") else "") +
            f'<div class="meta"><b>{e(v["channel"])}</b> ({e(country_he(v.get("country", "")))}) {when}</div></article>')
    if cards:
        listing = f'<p class="stats"><b>{len(cards)}</b> סרטונים מהשבוע האחרון</p><main class="vgrid">' + "".join(cards) + "</main>"
    else:
        listing = '<p class="empty">הסרטונים הראשונים ייאספו בשעה הקרובה. חזרו בקרוב.</p>'
    body = ('<section class="hero"><h1>🎬 וידאו: מה משדרים עלינו בעולם</h1>'
            '<p class="tagline">סרטוני חדשות על ישראל מערוצי החדשות הגדולים בעולם, עם כותרת מתורגמת לעברית.</p>'
            '<p class="vtip">📝 מתחת לכל סרטון יש <b>תקציר בעברית</b>. 💬 אם לסרטון יש כתוביות, אפשר לנסות: ⚙️ ← כתוביות ← תרגום אוטומטי ← עברית (לא בכל סרטון זה זמין).</p></section>'
            + listing +
            """<script>
document.addEventListener('click',function(ev){var b=ev.target.closest&&ev.target.closest('.vthumb');if(!b)return;
var f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+b.dataset.id+'?autoplay=1&rel=0&cc_load_policy=1&cc_lang_pref=iw&hl=iw';
f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';f.allowFullscreen=true;f.className='vframe';b.replaceWith(f);});
</script>""")
    return page("וידאו", "סרטוני חדשות על ישראל מערוצי החדשות בעולם, עם כותרות מתורגמות לעברית", body, path="videos.html")


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
    if getattr(config, "HIDE_UNTRANSLATED", True):
        # מציגים רק כותרות שתורגמו לעברית, כדי שהאתר יישאר כולו בעברית
        shown = [a for a in items if a.get("he")]
        items = shown or items

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
        + video_teaser() +
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
    write(os.path.join(SITE, "videos.html"), videos_page())
    write(os.path.join(SITE, WA_PAGE), whatsapp_page(items, now))

    # SEO
    if config.SITE_URL:
        base = config.SITE_URL.rstrip("/") + "/"
        urls = ["", "archive.html", "about.html", "contact.html", "community.html", "videos.html"] + [f"day/{d.isoformat()}.html" for d in by_day]
        sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        sm += [f"<url><loc>{e(base + u)}</loc></url>" for u in urls]
        sm.append("</urlset>")
        write(os.path.join(SITE, "sitemap.xml"), "\n".join(sm))
        robots = f"User-agent: *\nDisallow: /{WA_PAGE}\nAllow: /\nSitemap: {base}sitemap.xml\n"
    else:
        robots = f"User-agent: *\nDisallow: /{WA_PAGE}\nAllow: /\n"
    write(os.path.join(SITE, "robots.txt"), robots)
    write(os.path.join(SITE, "feed.xml"), build_feed(items, now))
    # עמוד שלא קיים (למשל קישור ישן מפייסבוק) מוביל לעמוד הראשי
    write(os.path.join(SITE, "404.html"), page("העמוד לא נמצא", config.SITE_TAGLINE,
          '<section class="hero"><h1>העמוד הזה כבר לא קיים</h1><p class="tagline">מעבירים אתכם לכותרות העדכניות…</p></section>'
          '<script>setTimeout(function(){location.replace("/")},1200)</script>', prefix="/"))
    if config.CUSTOM_DOMAIN:
        write(os.path.join(SITE, "CNAME"), config.CUSTOM_DOMAIN.strip() + "\n")
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    print(f"נבנה האתר: {len(home)} כותרות בעמוד הראשי, {len(by_day)} ימים בארכיון")


if __name__ == "__main__":
    main()
