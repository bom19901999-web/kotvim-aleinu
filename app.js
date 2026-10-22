// סינון לפי שפה, מדינה וחיפוש חופשי — הכול בדפדפן, בלי שרת
(function () {
  var list = document.getElementById("list");
  if (!list) return;
  var items = Array.prototype.slice.call(list.querySelectorAll(".item"));
  var days = Array.prototype.slice.call(list.querySelectorAll(".day"));
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
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
