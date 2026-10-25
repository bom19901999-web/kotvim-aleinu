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
