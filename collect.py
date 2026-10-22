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
from datetime import datetime, timedelta, timezone

import config
from names import lang_info

ROOT = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(ROOT, "data", "articles.json")
UA = "Mozilla/5.0 (compatible; IsraelWorldHeadlines/1.0)"


# ---------- עזרים ----------
def log(*a):
    print(*a, flush=True)


def http_json(url, data=None, timeout=40):
    body = None
    headers = {"User-Agent": UA}
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
    for attempt in range(3):
        try:
            return http_json(url).get("articles", []) or []
        except Exception as e:  # GDELT לפעמים איטי או מחזיר שגיאה זמנית
            log(f"  GDELT error ({attempt + 1}/3): {e}")
            time.sleep(8)
    return []


def gather():
    fixture = os.environ.get("GDELT_FIXTURE")
    if fixture:
        with open(fixture, encoding="utf-8") as f:
            return json.load(f)
    out = []
    for i, q in enumerate(config.GDELT_QUERIES):
        arts = fetch_gdelt(q)
        log(f"  {q}: {len(arts)}")
        out.extend(arts)
        if i < len(config.GDELT_QUERIES) - 1:
            time.sleep(6)  # GDELT מבקש לא יותר מבקשה אחת ל-5 שניות
    return out


# ---------- תרגום ----------
def translate(titles, src_codes):
    """מחזיר רשימת תרגומים (או None לכל כותרת שלא תורגמה)."""
    if not titles:
        return []
    if os.environ.get("TRANSLATE_MOCK"):
        return ["[תרגום] " + t for t in titles]
    key = os.environ.get("GOOGLE_TRANSLATE_KEY", "").strip()
    if not key:
        log("  אין GOOGLE_TRANSLATE_KEY: הכותרות יישמרו בשפת המקור")
        return [None] * len(titles)
    url = "https://translation.googleapis.com/language/translate/v2?key=" + urllib.parse.quote(key)
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
    log(f"התקבלו מ-GDELT: {len(raw)}")

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
        fresh = fresh[:config.MAX_NEW_PER_RUN]

    todo = [x for x in fresh if x["he"] is None]
    # כותרות שלא תורגמו בריצות קודמות (למשל לפני שהוגדר מפתח) — מנסים שוב, בתוך אותה מגבלה
    recent = (datetime.now(timezone.utc) - timedelta(hours=config.HOME_HOURS)).isoformat()
    room = max(0, config.MAX_NEW_PER_RUN - len(todo))
    todo += [x for x in store if x.get("he") is None and x["seen"] >= recent][:room]
    tr = translate([x["title"] for x in todo], [lang_info(x["lang"])[0] for x in todo])
    chars = sum(len(x["title"]) for x in todo)
    for x, t in zip(todo, tr):
        x["he"] = t

    cutoff = (datetime.now(timezone.utc) - timedelta(days=config.KEEP_DAYS)).isoformat()
    items = [x for x in store + fresh if x["seen"] >= cutoff]
    items.sort(key=lambda x: x["seen"], reverse=True)
    save_store(items)
    log(f"נוספו: {len(fresh)} | נשלחו לתרגום: {len(todo)} ({chars} תווים) | "
        f"דולגו: {skipped} | סה\"כ במאגר: {len(items)}")


if __name__ == "__main__":
    sys.exit(main())
