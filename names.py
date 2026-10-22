# -*- coding: utf-8 -*-
"""שמות שפות ומדינות בעברית (GDELT מחזיר אותם באנגלית)."""

# GDELT language name -> (ISO code, Hebrew name)
LANGS = {
    "English": ("en", "אנגלית"), "Arabic": ("ar", "ערבית"), "French": ("fr", "צרפתית"),
    "German": ("de", "גרמנית"), "Spanish": ("es", "ספרדית"), "Russian": ("ru", "רוסית"),
    "Turkish": ("tr", "טורקית"), "Italian": ("it", "איטלקית"), "Persian": ("fa", "פרסית"),
    "Chinese": ("zh", "סינית"), "Portuguese": ("pt", "פורטוגזית"), "Ukrainian": ("uk", "אוקראינית"),
    "Japanese": ("ja", "יפנית"), "Korean": ("ko", "קוריאנית"), "Polish": ("pl", "פולנית"),
    "Dutch": ("nl", "הולנדית"), "Hindi": ("hi", "הינדי"), "Indonesian": ("id", "אינדונזית"),
    "Greek": ("el", "יוונית"), "Swedish": ("sv", "שוודית"), "Norwegian": ("no", "נורווגית"),
    "Danish": ("da", "דנית"), "Finnish": ("fi", "פינית"), "Czech": ("cs", "צ'כית"),
    "Hungarian": ("hu", "הונגרית"), "Romanian": ("ro", "רומנית"), "Bulgarian": ("bg", "בולגרית"),
    "Serbian": ("sr", "סרבית"), "Croatian": ("hr", "קרואטית"), "Urdu": ("ur", "אורדו"),
    "Bengali": ("bn", "בנגלית"), "Malay": ("ms", "מלאית"), "Thai": ("th", "תאית"),
    "Vietnamese": ("vi", "וייטנאמית"), "Hebrew": ("he", "עברית"), "Catalan": ("ca", "קטלאנית"),
    "Slovak": ("sk", "סלובקית"), "Slovenian": ("sl", "סלובנית"), "Lithuanian": ("lt", "ליטאית"),
    "Latvian": ("lv", "לטבית"), "Estonian": ("et", "אסטונית"), "Azerbaijani": ("az", "אזרית"),
    "Georgian": ("ka", "גאורגית"), "Armenian": ("hy", "ארמנית"), "Kazakh": ("kk", "קזחית"),
    "Albanian": ("sq", "אלבנית"), "Tamil": ("ta", "טמילית"), "Swahili": ("sw", "סוואהילית"),
}

COUNTRIES = {
    "United States": "ארה\"ב", "United Kingdom": "בריטניה", "France": "צרפת", "Germany": "גרמניה",
    "Spain": "ספרד", "Italy": "איטליה", "Russia": "רוסיה", "Ukraine": "אוקראינה", "Turkey": "טורקיה",
    "Iran": "איראן", "Qatar": "קטאר", "Egypt": "מצרים", "Saudi Arabia": "ערב הסעודית",
    "United Arab Emirates": "איחוד האמירויות", "Jordan": "ירדן", "Lebanon": "לבנון", "Syria": "סוריה",
    "Iraq": "עיראק", "Kuwait": "כווית", "Bahrain": "בחריין", "Oman": "עומאן", "Yemen": "תימן",
    "Morocco": "מרוקו", "Algeria": "אלג'יריה", "Tunisia": "תוניסיה", "Libya": "לוב",
    "Occupied Palestinian Territory": "השטחים הפלסטיניים", "Palestine": "השטחים הפלסטיניים",
    "China": "סין", "Japan": "יפן", "South Korea": "דרום קוריאה", "India": "הודו", "Pakistan": "פקיסטן",
    "Indonesia": "אינדונזיה", "Malaysia": "מלזיה", "Australia": "אוסטרליה", "New Zealand": "ניו זילנד",
    "Canada": "קנדה", "Mexico": "מקסיקו", "Brazil": "ברזיל", "Argentina": "ארגנטינה", "Chile": "צ'ילה",
    "Colombia": "קולומביה", "Peru": "פרו", "Venezuela": "ונצואלה", "Uruguay": "אורוגוואי",
    "Netherlands": "הולנד", "Belgium": "בלגיה", "Switzerland": "שווייץ", "Austria": "אוסטריה",
    "Poland": "פולין", "Czech Republic": "צ'כיה", "Hungary": "הונגריה", "Romania": "רומניה",
    "Greece": "יוון", "Cyprus": "קפריסין", "Portugal": "פורטוגל", "Ireland": "אירלנד",
    "Sweden": "שוודיה", "Norway": "נורווגיה", "Denmark": "דנמרק", "Finland": "פינלנד",
    "South Africa": "דרום אפריקה", "Nigeria": "ניגריה", "Kenya": "קניה", "Ethiopia": "אתיופיה",
    "Azerbaijan": "אזרבייג'ן", "Georgia": "גאורגיה", "Armenia": "ארמניה", "Kazakhstan": "קזחסטן",
    "Belarus": "בלארוס", "Serbia": "סרביה", "Croatia": "קרואטיה", "Bulgaria": "בולגריה",
    "Philippines": "הפיליפינים", "Thailand": "תאילנד", "Vietnam": "וייטנאם", "Singapore": "סינגפור",
    "Bangladesh": "בנגלדש", "Afghanistan": "אפגניסטן", "Hong Kong": "הונג קונג", "Taiwan": "טאיוואן",
}


def lang_info(gdelt_lang):
    code, he = LANGS.get(gdelt_lang or "", ("", gdelt_lang or "לא ידוע"))
    return code, he


def country_he(gdelt_country):
    return COUNTRIES.get(gdelt_country or "", gdelt_country or "")
