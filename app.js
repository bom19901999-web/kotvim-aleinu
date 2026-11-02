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

/* תגובות באתר: לכל כותרת, עם סינון מילים בשרת */
(function () {
  var KC = window.KC;
  if (!KC || !KC.url) return;
  var admin = null;
  try {
    var m = location.search.match(/[?&]admin=([^&]+)/);
    if (m) { localStorage.setItem("kc_admin", decodeURIComponent(m[1])); }
    admin = localStorage.getItem("kc_admin");
  } catch (e) {}
  function rpc(fn, args) {
    return fetch(KC.url + "/rest/v1/rpc/" + fn, {
      method: "POST",
      headers: KC.key.indexOf("sb_") === 0 ? { "apikey": KC.key, "Content-Type": "application/json" }
        : { "apikey": KC.key, "Authorization": "Bearer " + KC.key, "Content-Type": "application/json" },
      body: JSON.stringify(args)
    }).then(function (r) {
      return r.text().then(function (t) {
        var d = t ? JSON.parse(t) : null;
        if (!r.ok) { var err = new Error((d && d.message) || "error"); throw err; }
        return d;
      });
    });
  }
  var MSG = { kc_blocked: "התגובה לא פורסמה: יש בה מילים לא מכבדות. נסו לנסח אחרת 🙏",
    kc_link: "אי אפשר לפרסם קישורים בתגובות.", kc_rate: "יותר מדי תגובות בזמן קצר. נסו שוב בעוד שעה.",
    kc_dup: "כבר פרסמתם את התגובה הזו.", kc_length: "השם צריך להיות 2–30 תווים, והתגובה 2–500 תווים." };
  function when(iso) {
    var d = new Date(iso), s = (Date.now() - d) / 1000;
    if (s < 60) return "עכשיו";
    if (s < 3600) return "לפני " + Math.floor(s / 60) + " דק׳";
    if (s < 86400) return "לפני " + Math.floor(s / 3600) + " שע׳";
    return d.toLocaleDateString("he-IL");
  }
  function el(tag, cls, text) { var x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; }
  function row(c) {
    var li = el("li", "kc-c");
    var h = el("div", "kc-h"); h.appendChild(el("b", null, c.name)); h.appendChild(el("span", "kc-t", " · " + when(c.created_at)));
    var rep = el("button", "kc-r", "🚩"); rep.type = "button"; rep.title = "דווחו על תגובה פוגענית";
    rep.onclick = function () { rpc("report_comment", { p_id: c.id }).then(function () { rep.textContent = "✓ דווח"; rep.disabled = true; }); };
    h.appendChild(rep);
    if (admin) {
      var del = el("button", "kc-r", "🗑️"); del.type = "button";
      del.onclick = function () { if (confirm("להסתיר את התגובה?")) rpc("admin_hide", { p_key: admin, p_id: c.id }).then(function () { li.remove(); }); };
      h.appendChild(del);
    }
    li.appendChild(h); li.appendChild(el("p", "kc-b", c.body));
    return li;
  }
  // מונה תגובות לכל הכותרות בעמוד
  var arts = [].slice.call(document.querySelectorAll(".item[data-id]"));
  if (arts.length) {
    rpc("get_counts", { p_ids: arts.map(function (a) { return a.dataset.id; }) }).then(function (rows) {
      var map = {}; (rows || []).forEach(function (r) { map[r.article_id] = r.n; });
      arts.forEach(function (a) { var n = map[a.dataset.id]; var b = a.querySelector(".kcb"); if (b && n) { b.textContent = "💬 תגובות (" + n + ")"; b.classList.add("has"); } });
    }).catch(function () {});
  }
  document.addEventListener("click", function (ev) {
    var btn = ev.target.closest && ev.target.closest(".kcb");
    if (!btn) return;
    var art = btn.closest(".item"), open = art.querySelector(".kc-box");
    if (open) { open.remove(); return; }
    var box = el("div", "kc-box"), list = el("ul", "kc-list"), st = el("p", "kc-n", "טוען תגובות…");
    box.appendChild(list); box.appendChild(st);
    var f = el("form", "kc-f");
    var name = el("input"); name.placeholder = "השם שלכם"; name.maxLength = 30; name.required = true;
    try { name.value = localStorage.getItem("kc_name") || ""; } catch (e) {}
    var ta = el("textarea"); ta.rows = 3; ta.maxLength = 500; ta.required = true; ta.placeholder = "מה דעתכם על הכותרת? שמרו על שפה מכבדת.";
    var send = el("button", "kc-send", "פרסום תגובה"); send.type = "submit";
    var note = el("p", "kc-n", "תגובות עם מילים פוגעניות או קישורים לא יתפרסמו. 🚩 לדיווח על תגובה.");
    f.appendChild(name); f.appendChild(ta); f.appendChild(send); f.appendChild(note);
    box.appendChild(f);
    btn.closest(".meta").after(box);
    rpc("get_comments", { p_article: art.dataset.id }).then(function (rows) {
      st.textContent = rows && rows.length ? "" : "אין עדיין תגובות. היו הראשונים!";
      (rows || []).forEach(function (c) { list.appendChild(row(c)); });
    }).catch(function () { st.textContent = "לא הצלחנו לטעון תגובות כרגע."; });
    f.onsubmit = function (e2) {
      e2.preventDefault();
      send.disabled = true; note.textContent = "שולח…";
      try { localStorage.setItem("kc_name", name.value.trim()); } catch (e) {}
      rpc("add_comment", { p_article: art.dataset.id, p_name: name.value, p_body: ta.value }).then(function (rows) {
        var c = rows && rows[0];
        if (c) { list.appendChild(row(c)); st.textContent = ""; }
        ta.value = ""; note.textContent = "✓ התגובה פורסמה. תודה!";
        var n = list.children.length; btn.textContent = "💬 תגובות (" + n + ")"; btn.classList.add("has");
        if (window.goatcounter && window.goatcounter.count) { try { window.goatcounter.count({ path: "comment", event: true }); } catch (x) {} }
      }).catch(function (err) {
        var k = Object.keys(MSG).filter(function (m) { return String(err.message).indexOf(m) !== -1; })[0];
        note.textContent = k ? MSG[k] : "משהו השתבש. נסו שוב.";
      }).then(function () { send.disabled = false; });
    };
  });
})();
