// התקנה כאפליקציה (PWA)
(function () {
  if ("serviceWorker" in navigator) {
    var base = (document.querySelector('link[rel="manifest"]') || {}).href || "";
    var swUrl = base ? base.replace(/manifest\.webmanifest$/, "sw.js") : "sw.js";
    navigator.serviceWorker.register(swUrl).catch(function () {});
  }
  var btn = document.getElementById("install");
  var help = document.getElementById("install-help");
  if (!btn) return;
  var standalone = (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches) || window.navigator.standalone;
  if (standalone) return; // כבר פתוח כאפליקציה
  btn.hidden = false;
  var deferred = null;
  window.addEventListener("beforeinstallprompt", function (e) { e.preventDefault(); deferred = e; });
  btn.addEventListener("click", function () {
    if (deferred) {
      deferred.prompt();
      deferred.userChoice.finally(function () { deferred = null; });
      return;
    }
    if (help) {
      var ua = navigator.userAgent;
      var tip = /iPhone|iPad|iPod/.test(ua)
        ? "באייפון: לחצו על כפתור השיתוף <b>⬆️</b> בתחתית המסך, ואז <b>הוסף למסך הבית</b>."
        : /SamsungBrowser/.test(ua)
        ? "בדפדפן סמסונג: לחצו על התפריט <b>☰</b>, ואז <b>הוסף דף אל</b> ← <b>מסך הבית</b>."
        : /FBAN|FBAV|Instagram/.test(ua)
        ? "פתחו קודם את האתר בדפדפן: לחצו על <b>⋯</b> למעלה ← <b>פתח בדפדפן</b>, ואז לחצו שוב על התקן אפליקציה."
        : "בכרום: לחצו על התפריט <b>⋮</b> למעלה, ואז <b>התקן אפליקציה</b> או <b>הוסף למסך הבית</b>.";
      help.querySelector(".tip").innerHTML = tip;
      help.hidden = !help.hidden;
    }
  });
  if (help) help.querySelector(".close").addEventListener("click", function () { help.hidden = true; });
  window.addEventListener("appinstalled", function () { btn.hidden = true; if (help) help.hidden = true; });
})();

// סינון לפי שפה, מדינה וחיפוש חופשי — הכול בדפדפן, בלי שרת
(function () {
  var list = document.getElementById("list");
  if (!list) return;
  var items = Array.prototype.slice.call(list.querySelectorAll(".item"));
  var days = Array.prototype.slice.call(list.querySelectorAll(".day"));
  var chips = Array.prototype.slice.call(document.querySelectorAll(".tab"));
  var q = document.getElementById("q");
  var country = document.getElementById("country");
  var empty = document.getElementById("empty");
  var lang = "all";

  function apply() {
    var term = (q.value || "").trim().toLowerCase();
    var c = country.value;
    var shown = 0;
    items.forEach(function (el) {
      var ok = (lang === "all" || el.dataset.lang === lang) &&
               (!c || el.dataset.country === c) &&
               (!term || el.textContent.toLowerCase().indexOf(term) !== -1);
      el.hidden = !ok;
      if (ok) shown++;
    });
    days.forEach(function (d) { d.hidden = !d.querySelector(".item:not([hidden])"); });
    empty.hidden = shown !== 0;
  }

  chips.forEach(function (b) {
    b.addEventListener("click", function () {
      lang = b.dataset.lang;
      chips.forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      apply();
    });
  });
  q.addEventListener("input", apply);
  country.addEventListener("change", apply);
})();

/* כלי שגריר: כותבים תגובה בעברית, מתרגמים לשפת הכתבה ומדביקים בכתבה המקורית */
(function () {
  var LANGS = [["en","אנגלית"],["ar","ערבית"],["fr","צרפתית"],["es","ספרדית"],["de","גרמנית"],["ru","רוסית"],
    ["tr","טורקית"],["it","איטלקית"],["pt","פורטוגזית"],["nl","הולנדית"],["pl","פולנית"],["el","יוונית"],
    ["uk","אוקראינית"],["fa","פרסית"],["ur","אורדו"],["hi","הינדי"],["id","אינדונזית"],["ja","יפנית"],
    ["ko","קוריאנית"],["zh-CN","סינית"],["vi","וייטנאמית"],["th","תאית"],["sv","שוודית"],["no","נורווגית"],
    ["da","דנית"],["fi","פינית"],["cs","צ'כית"],["hu","הונגרית"],["ro","רומנית"],["bg","בולגרית"],
    ["hr","קרואטית"],["sr","סרבית"],["sk","סלובקית"],["ms","מלאית"],["sw","סוואהילית"]];
  function gt(code) { return code === "zh" ? "zh-CN" : code; }
  document.addEventListener("click", function (ev) {
    var btn = ev.target.closest && ev.target.closest(".amb");
    if (!btn) return;
    var art = btn.closest(".item");
    var open = art.querySelector(".amb-box");
    if (open) { open.remove(); return; }
    var link = art.querySelector(".hl");
    var code = art.dataset.lang;
    if (!code || code === "he" || code === "xx") code = "en";
    code = gt(code);
    var box = document.createElement("div");
    box.className = "amb-box";
    var opts = LANGS.map(function (l) {
      return '<option value="' + l[0] + '"' + (l[0] === code ? " selected" : "") + ">" + l[1] + "</option>";
    }).join("");
    if (!LANGS.some(function (l) { return l[0] === code; })) opts = '<option value="' + code + '" selected>' + code + "</option>" + opts;
    box.innerHTML =
      '<p class="amb-t"><b>כולנו שגרירים 🇮🇱</b> כתבו תגובה בעברית, תרגמו לשפת הכתבה, והדביקו אותה בכתבה המקורית.</p>' +
      '<textarea rows="4" dir="rtl" placeholder="מה הייתם רוצים להגיד לקוראים של הכתבה הזו? עובדות ומילים מכבדות משכנעות יותר."></textarea>' +
      '<div class="amb-row"><label>לתרגם ל: <select>' + opts + "</select></label></div>" +
      '<div class="amb-row"><button type="button" class="amb-go">1. תרגמו</button>' +
      '<a class="amb-open" href="' + link.href + '" target="_blank" rel="noopener nofollow">2. פתחו את הכתבה והדביקו</a></div>' +
      '<p class="amb-n">התרגום נפתח ב־Google Translate. שם לחצו על כפתור ההעתקה, ואז פתחו את הכתבה והדביקו בתגובות.</p>';
    btn.closest(".meta").after(box);
    var ta = box.querySelector("textarea");
    ta.focus();
    box.querySelector(".amb-go").addEventListener("click", function () {
      var t = ta.value.trim();
      if (!t) { ta.focus(); ta.placeholder = "קודם כתבו כאן את התגובה שלכם בעברית"; return; }
      var to = box.querySelector("select").value;
      window.open("https://translate.google.com/?sl=iw&tl=" + encodeURIComponent(to) +
        "&text=" + encodeURIComponent(t) + "&op=translate", "_blank", "noopener");
      if (window.goatcounter && window.goatcounter.count) {
        try { window.goatcounter.count({ path: "ambassador-translate", event: true }); } catch (e) {}
      }
    });
  });
})();
