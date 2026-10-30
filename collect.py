# -*- coding: utf-8 -*-
"""
איסוף כותרות על ישראל מ-GDELT, סינון כפילויות, תרגום לעברית ושמירה ל-data/articles.json.
רץ אוטומטית כל 15 דקות ב-GitHub Actions. אין צורך בספריות חיצוניות.

משתני סביבה:
  GOOGLE_TRANSLATE_KEY  מפתח Google Cloud Translation. בלעדיו הכותרות נשמרות בשפת המקור.
  GDELT_FIXTURE         (לבדיקות) נתיב לקובץ JSON במקום פנייה ל-GDELT.
  TRANSLATE_MOCK=1      (לבדיקות) תרגום מדומה, בלי עלות.
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone

import config
from names import lang_info

ROOT = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(ROOT, "data", "articles.json")
UA = "Mozilla/5.0 (compatible; IsraelWorldHeadlines/1.0)"


# ---------- עזרים ----------
def log(*a):
    print(*a, flush=True)


def http_json(url, data=None, timeout=25, extra_headers=None):
    body = None
    headers = {"User-Agent": UA}
    if extra_headers:
        headers.update(extra_headers)
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace").strip()
    if not raw:
        return {}
    return json.loads(raw, strict=False)


_SUFFIX = re.compile(r"\s+[|\-–—:]\s+[^|\-–—]{2,40}$")


def clean_title(t):
    t = re.sub(r"\s+", " ", (t or "")).strip()
    # מסיר סיומות כמו " | CNN" או " - Le Monde"
    t2 = _SUFFIX.sub("", t)
    return t2 if len(t2) >= 15 else t


def title_key(t):
    t = t.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def relevant(title):
    if not config.TITLE_FILTER:
        return True
    low = title.lower()
    return any(k in low for k in config.TITLE_KEYWORDS)


def parse_seen(s):
    try:
        return datetime.strptime(s, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


# ---------- GDELT ----------
def fetch_gdelt(query):
    params = {
        "query": query,
        "mode": "artlist",
        "maxrecords": "250",
        "format": "json",
        "sort": "datedesc",
        "timespan": config.TIMESPAN,
    }
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(params)
    for attempt in range(2):
        try:
            return http_json(url).get("articles", []) or []
        except Exception as e:  # GDELT לפעמים איטי או מגביל פניות (429)
            log(f"  GDELT error ({attempt + 1}/2): {e}")
            time.sleep(15 if "429" in str(e) else 6)
    return []


# ---------- Google News (מקור גיבוי) ----------
_TLD_COUNTRY = {
    "fr": "France", "de": "Germany", "es": "Spain", "it": "Italy", "ru": "Russia", "ua": "Ukraine",
    "tr": "Turkey", "uk": "United Kingdom", "br": "Brazil", "ar": "Argentina", "mx": "Mexico",
    "cl": "Chile", "co": "Colombia", "pt": "Portugal", "jp": "Japan", "cn": "China", "in": "India",
    "au": "Australia", "ca": "Canada", "ch": "Switzerland", "at": "Austria", "be": "Belgium",
    "nl": "Netherlands", "pl": "Poland", "gr": "Greece", "eg": "Egypt", "qa": "Qatar", "sa": "Saudi Arabia",
    "ae": "United Arab Emirates", "jo": "Jordan", "lb": "Lebanon", "ir": "Iran", "ma": "Morocco",
    "za": "South Africa", "ie": "Ireland", "se": "Sweden", "no": "Norway", "dk": "Denmark", "fi": "Finland",
    "il": "Israel", "pk": "Pakistan", "kr": "South Korea", "ro": "Romania", "hu": "Hungary", "cz": "Czech Republic",
    "ng": "Nigeria", "ke": "Kenya", "gh": "Ghana", "tz": "Tanzania", "ug": "Uganda", "zw": "Zimbabwe",
    "et": "Ethiopia", "sg": "Singapore", "ph": "Philippines", "my": "Malaysia", "id": "Indonesia",
    "nz": "New Zealand", "pe": "Peru", "ve": "Venezuela", "tw": "Taiwan", "hk": "Hong Kong", "kw": "Kuwait",
    "om": "Oman", "bh": "Bahrain", "iq": "Iraq", "dz": "Algeria", "tn": "Tunisia", "sn": "Senegal",
    "gr": "Greece", "bg": "Bulgaria", "rs": "Serbia", "hr": "Croatia", "sk": "Slovakia", "si": "Slovenia",
    "lt": "Lithuania", "lv": "Latvia", "ee": "Estonia", "th": "Thailand", "vn": "Vietnam", "bd": "Bangladesh",
}
_ISRAELI = ("timesofisrael.com", "jpost.com", "ynetnews.com", "israelhayom.com", "i24news.tv", "haaretz.com",
            "jns.org", "israelnationalnews.com", "allisrael.com", "israel21c.org", "jewishpress.com",
            "unitedwithisrael.org", "tps.co.il", "kan.org.il", "israelheute.com")


def _country_for(domain, fallback):
    d = domain.lower()
    if any(d == x or d.endswith("." + x) for x in _ISRAELI):
        return "Israel"
    tld = d.rsplit(".", 1)[-1]
    return _TLD_COUNTRY.get(tld, fallback)


def fetch_gnews(q, hl, gl, ceid, lang, country):
    url = ("https://news.google.com/rss/search?" +
           urllib.parse.urlencode({"q": q + " when:1d", "hl": hl, "gl": gl, "ceid": ceid}))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            root = ET.fromstring(r.read())
    except Exception as e:
        log(f"  Google News error ({hl}): {e}")
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=getattr(config, "GNEWS_MAX_AGE_HOURS", 6))
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        src = it.find("source")
        src_name = (src.text or "").strip() if src is not None else ""
        src_url = src.get("url", "") if src is not None else ""
        if src_name and title.endswith(" - " + src_name):
            title = title[: -len(src_name) - 3]
        try:
            when = parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc)
        except Exception:
            continue
        if when < cutoff or not link or not title:
            continue
        domain = urllib.parse.urlparse(src_url).netloc.replace("www.", "") or src_name
        out.append({
            "url": link, "title": title, "language": lang,
            "sourcecountry": _country_for(domain, country), "domain": domain,
            "seendate": when.strftime("%Y%m%dT%H%M%SZ"),
        })
    return out


def gather():
    fixture = os.environ.get("GDELT_FIXTURE")
    if fixture:
        with open(fixture, encoding="utf-8") as f:
            return json.load(f)
    out = []
    for i, q in enumerate(config.GDELT_QUERIES):
        arts = fetch_gdelt(q)
        log(f"  GDELT {q}: {len(arts)}")
        out.extend(arts)
        if i < len(config.GDELT_QUERIES) - 1:
            time.sleep(8)  # GDELT מבקש לא יותר מבקשה אחת ל-5 שניות
    feeds = list(getattr(config, "GNEWS_FEEDS", []))
    extra = list(getattr(config, "GNEWS_EXTRA", []))
    if extra:  # סבב: בכל ריצה חלק אחר מהמהדורות הנוספות
        k = max(1, getattr(config, "GNEWS_EXTRA_PER_RUN", 10))
        rounds = (len(extra) + k - 1) // k
        start = (int(time.time() // 900) % rounds) * k
        feeds += extra[start:start + k]
    for feed in feeds:
        arts = fetch_gnews(*feed)
        log(f"  Google News {feed[1]}: {len(arts)}")
        out.extend(arts)
        time.sleep(1)
    return out


# ---------- מגבלת תרגום יומית (כדי להישאר במכסה החינמית) ----------
USAGE = os.path.join(ROOT, "data", "usage.json")


def _load_usage():
    try:
        with open(USAGE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def char_budget_today(store):
    """כמה תווים מותר לתרגם עכשיו.
    התקציב החודשי (מתחת ל-2 מיליון התווים החינמיים) מתחלק שווה בין הימים שנשארו בחודש,
    כך שביום עמוס (בחירות, מלחמה) אפשר לתרגם הרבה יותר, בלי לחרוג מהחינם."""
    now = datetime.now(timezone.utc)
    today, month = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")
    u = _load_usage()
    if u.get("month") == month:
        month_chars = u.get("chars", 0)
        day_chars = u.get("day_chars", 0) if u.get("date") == today else 0
    else:  # חודש חדש, או מעבר מהשיטה הישנה: מעריכים לפי מה שכבר תורגם החודש
        month_chars = sum(len(x["title"]) for x in store
                          if x.get("he") and x["he"] != x["title"] and x["seen"][:7] == month)
        day_chars = 0
    nxt = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
    days_left = (nxt.date() - now.date()).days  # כולל היום
    budget = getattr(config, "MONTHLY_CHAR_BUDGET", 1_900_000)
    per_day = max(0, budget - (month_chars - day_chars)) / max(1, days_left)
    left = int(max(0, min(per_day - day_chars, budget - month_chars)))
    return left, {"date": today, "month": month, "chars": month_chars, "day_chars": day_chars}


def add_usage(state, chars):
    os.makedirs(os.path.dirname(USAGE), exist_ok=True)
    state = dict(state, chars=state["chars"] + chars, day_chars=state["day_chars"] + chars)
    with open(USAGE, "w", encoding="utf-8") as f:
        json.dump(state, f)


# ---------- תרגום ----------
def translate(titles, src_codes):
    """מחזיר רשימת תרגומים (או None לכל כותרת שלא תורגמה)."""
    if not titles:
        return []
    if os.environ.get("TRANSLATE_MOCK"):
        return ["[תרגום] " + t for t in titles]
    # מפתח התרגום נשמר ב-GitHub בסוד בשם GOOGLE_TRANSLATE_KEY (או TRANSLATOR_KEY).
    # מפתח של גוגל מתחיל ב-"AIza"; כל מפתח אחר נחשב מפתח של Microsoft Translator.
    key = (os.environ.get("TRANSLATOR_KEY") or os.environ.get("GOOGLE_TRANSLATE_KEY") or "").strip()
    if not key:
        log("  אין מפתח תרגום: הכותרות יישמרו בשפת המקור")
        return [None] * len(titles)
    if not key.startswith("AIza"):
        return translate_microsoft(titles, key)
    url ="https://translation.googleapis.com/language/translate/v2?key=" + urllib.parse.quote(key)
    result = [None] * len(titles)
    # מקבצים לפי שפת מקור כדי לעזור לתרגום, עד 100 כותרות בבקשה
    groups = {}
    for i, code in enumerate(src_codes):
        groups.setdefault(code or "", []).append(i)
    for code, idxs in groups.items():
        for s in range(0, len(idxs), 100):
            chunk = idxs[s:s + 100]
            payload = {"q": [titles[i] for i in chunk], "target": "he", "format": "text"}
            if code:
                payload["source"] = code
            try:
                data = http_json(url, payload)
                tr = data["data"]["translations"]
                for i, t in zip(chunk, tr):
                    result[i] = t.get("translatedText")
            except Exception as e:
                log(f"  שגיאת תרגום ({code}): {e}")
    return result


def translate_microsoft(titles, key):
    """Microsoft (Azure) Translator. שפת המקור מזוהה אוטומטית."""
    url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=he"
    headers = {"Ocp-Apim-Subscription-Key": key}
    region = getattr(config, "MICROSOFT_REGION", "swedencentral").strip()  # האזור שנבחר ב-Azure
    if region:
        headers["Ocp-Apim-Subscription-Region"] = region
    result = [None] * len(titles)
    for s in range(0, len(titles), 50):
        chunk = list(range(s, min(s + 50, len(titles))))
        payload = [{"Text": titles[i]} for i in chunk]
        try:
            data = http_json(url, payload, extra_headers=headers)
            for i, item in zip(chunk, data):
                tr = item.get("translations") or []
                if tr:
                    result[i] = tr[0].get("text")
        except urllib.error.HTTPError as e:
            log(f"  שגיאת תרגום (Microsoft): {e.code} {e.read()[:300]!r}")
            break
        except Exception as e:
            log(f"  שגיאת תרגום (Microsoft): {e}")
    return result


# ---------- אחסון ----------
def load_store():
    try:
        with open(STORE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_store(items):
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, STORE)


def main():
    store = load_store()
    by_id = {a["id"]: a for a in store}
    known_keys = {a["key"] for a in store}
    log(f"במאגר: {len(store)} כותרות")

    raw = gather()
    log(f"התקבלו מכל המקורות: {len(raw)}")

    fresh, seen_now = [], set()
    skipped = {"dup": 0, "country": 0, "irrelevant": 0}
    for a in raw:
        url = (a.get("url") or "").strip()
        if not url:
            continue
        aid = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
        if aid in by_id or aid in seen_now:
            skipped["dup"] += 1
            continue
        if a.get("sourcecountry") in config.EXCLUDE_SOURCE_COUNTRIES:
            skipped["country"] += 1
            continue
        title = clean_title(a.get("title"))
        if not title or not relevant(title):
            skipped["irrelevant"] += 1
            continue
        key = title_key(title)
        if key in known_keys:  # אותה כותרת בדיוק באתר אחר (למשל ידיעת סוכנות)
            skipped["dup"] += 1
            continue
        seen_now.add(aid)
        known_keys.add(key)
        code, _ = lang_info(a.get("language"))
        fresh.append({
            "id": aid,
            "key": key,
            "url": url,
            "title": title,
            "he": title if code == "he" else None,
            "lang": a.get("language") or "",
            "country": a.get("sourcecountry") or "",
            "domain": a.get("domain") or urllib.parse.urlparse(url).netloc,
            "seen": parse_seen(a.get("seendate")).isoformat(),
            "image": a.get("socialimage") or "",
        })

    fresh.sort(key=lambda x: x["seen"], reverse=True)
    if len(fresh) > config.MAX_NEW_PER_RUN:
        log(f"מגבלת עלות: מתרגמים רק {config.MAX_NEW_PER_RUN} מתוך {len(fresh)}")
        # גיוון: לוקחים לסירוגין מכל מדינה, כדי שמדינות גדולות לא ישתלטו על הרשימה
        by_c = {}
        for x in fresh:
            by_c.setdefault(x["country"], []).append(x)
        queues, picked = list(by_c.values()), []
        while len(picked) < config.MAX_NEW_PER_RUN and queues:
            for q in list(queues):
                if q:
                    picked.append(q.pop(0))
                if not q:
                    queues.remove(q)
                if len(picked) >= config.MAX_NEW_PER_RUN:
                    break
        fresh = sorted(picked, key=lambda x: x["seen"], reverse=True)

    todo = [x for x in fresh if x["he"] is None]
    # כותרות שלא תורגמו בריצות קודמות (למשל לפני שהוגדר מפתח) — מנסים שוב, בתוך אותה מגבלה
    recent = (datetime.now(timezone.utc) - timedelta(hours=config.HOME_HOURS)).isoformat()
    room = max(0, config.MAX_NEW_PER_RUN - len(todo))
    todo += [x for x in store if x.get("he") is None and x["seen"] >= recent][:room]
    left, state = char_budget_today(store)
    picked, total = [], 0
    for x in todo:
        if total + len(x["title"]) > left:
            continue
        picked.append(x)
        total += len(x["title"])
    if len(picked) < len(todo):
        log(f"תקציב תרגום: נשארו היום {left} תווים, {len(todo) - len(picked)} כותרות יחכו לריצה הבאה")
    todo = picked
    tr = translate([x["title"] for x in todo], [lang_info(x["lang"])[0] for x in todo])
    chars = sum(len(x["title"]) for x, t in zip(todo, tr) if t)
    for x, t in zip(todo, tr):
        x["he"] = t
    add_usage(state, chars)
    log(f"תווים החודש: {state['chars'] + chars} | היום: {state['day_chars'] + chars}")

    cutoff = (datetime.now(timezone.utc) - timedelta(days=config.KEEP_DAYS)).isoformat()
    items = [x for x in store + fresh if x["seen"] >= cutoff]
    items.sort(key=lambda x: x["seen"], reverse=True)
    save_store(items)
    log(f"נוספו: {len(fresh)} | נשלחו לתרגום: {len(todo)} ({chars} תווים) | "
        f"דולגו: {skipped} | סה\"כ במאגר: {len(items)}")


if __name__ == "__main__":
    sys.exit(main())
