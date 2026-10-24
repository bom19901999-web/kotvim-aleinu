# -*- coding: utf-8 -*-
"""הגדרות האתר. כאן משנים שם, דומיין והגבלות עלות — בלי לגעת בשאר הקוד."""

# ---- זהות האתר ----
SITE_NAME = "כותבים עלינו"
SITE_TAGLINE = "כל מה שהתקשורת בעולם כותבת על ישראל, מתורגם לעברית"
# הכתובת המלאה של האתר אחרי שיש דומיין, למשל "https://kotvim-aleinu.co.il"
SITE_URL = "https://kotvim-aleinu.com"
# הדומיין בלבד (בלי https), למשל "kotvim-aleinu.co.il". ריק = כתובת GitHub הרגילה
CUSTOM_DOMAIN = "kotvim-aleinu.com"
# מזהה Google AdSense (למשל "ca-pub-1234567890"). ריק = בלי פרסומות
ADSENSE_CLIENT = ""
# מונה מבקרים (goatcounter.com). ריק = בלי ספירה
GOATCOUNTER = "kotvim"
# מייל ליצירת קשר (מוצג באתר)
CONTACT_EMAIL = "kotvimaleinu@gmail.com"

# ---- תגובות (Cusdis) ----
# ה-App ID מ-cusdis.com. ריק = בלי כפתור תגובות
CUSDIS_APP_ID = ""

# ---- תרגום (Microsoft) ----
MICROSOFT_REGION = "swedencentral"

# ---- איסוף ----
# כמה זמן אחורה לחפש בכל ריצה. חפיפה בין ריצות לא מזיקה: כפילויות מסוננות.
TIMESPAN = "3h"
# שאילתות ל-GDELT. הראשונה כללית, השאר מבטיחות כיסוי בשפות חשובות.
_BASE = "(israel OR israeli OR netanyahu)"
# 4 שאילתות בלבד (GDELT מגביל פניות). כל אחת מכסה קבוצת שפות.
GDELT_QUERIES = [
    _BASE,
    _BASE + " (sourcelang:arabic OR sourcelang:persian OR sourcelang:turkish)",
    _BASE + " (sourcelang:french OR sourcelang:german OR sourcelang:spanish OR sourcelang:italian OR sourcelang:portuguese)",
    _BASE + " (sourcelang:russian OR sourcelang:ukrainian OR sourcelang:chinese OR sourcelang:japanese)",
]
# לא להציג כלי תקשורת ישראליים — הרעיון הוא מה כותבים עלינו *בחוץ*
EXCLUDE_SOURCE_COUNTRIES = {"Israel"}

# רק כותרות שמזכירות את ישראל בכותרת עצמה (ולא רק בגוף הכתבה).
# זה משאיר כתבות שבאמת עוסקות בישראל, וגם חוסך הרבה בעלות התרגום.
TITLE_FILTER = True
TITLE_KEYWORDS = [
    # אנגלית ושפות לטיניות
    "israel", "israël", "israele", "izrael", "israil", "i̇srail", "israeli",
    "netanyahu", "netanjahu", "netanyahou", "tel aviv", "tel-aviv", "jerusalem",
    "jérusalem", "gerusalemme", "jerusalén", "kudüs", "idf", "mossad", "knesset",
    "hamas", "hezbollah", "hizbullah", "gaza", "west bank", "cisjordanie", "westjordanland",
    # ערבית / פרסית
    "إسرائيل", "اسرائيل", "الإسرائيلي", "الاحتلال", "نتنياهو", "تل أبيب", "غزة", "القدس",
    "اسرائیل", "نتانیاهو", "غزه",
    # רוסית / אוקראינית
    "израил", "ізраїл", "нетаньяху", "нетаньягу", "тель-авив", "сектор газ", "секторі газ", "иерусалим", "хамас",
    # סינית / יפנית / קוריאנית / הינדי
    "以色列", "内塔尼亚胡", "加沙", "イスラエル", "ネタニヤフ", "ガザ", "이스라엘", "네타냐후", "가자",
    "इज़राइल", "इजराइल", "नेतन्याहू",
    # יוונית / אחרות
    "ισραήλ", "νετανιάχου",
]

# ---- הגבלות עלות ושמירה ----
# מקסימום כותרות חדשות שמתורגמות בריצה אחת (ריצה כל 15 דקות = 96 ריצות ביום)
MAX_NEW_PER_RUN = 60
# כמה ימים לשמור בארכיון
KEEP_DAYS = 30
# בעמוד הראשי: כותרות מ-X השעות האחרונות, עד Y כותרות
HOME_HOURS = 24
HOME_MAX = 400
