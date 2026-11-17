"use strict";
// Reads index.json (docs/index-format.md, schema 1) and lists the machines. Plain DOM, no framework.
(function () {
  var BOARD_NAMES = { pi4: "Pi 4", pi5: "Pi 5", teensy: "Teensy" };
  var entries = [];
  var latest = {};
  var q = document.getElementById("q");
  var board = document.getElementById("board");
  var all = document.getElementById("all");
  var list = document.getElementById("list");
  var status = document.getElementById("status");

  function el(tag, text, cls) {
    var e = document.createElement(tag);
    if (text !== undefined) e.textContent = text;
    if (cls) e.className = cls;
    return e;
  }

  function link(href, text) {
    var a = el("a", text);
    a.href = href;
    return a;
  }

  function safeUrl(u) {
    return typeof u === "string" && /^https:\/\//.test(u) ? u : null;
  }

  function render() {
    var term = q.value.trim().toLowerCase();
    var b = board.value;
    var shown = entries.filter(function (e) {
      if (b && e.board !== b) return false;
      if (!all.checked && latest[e.id] && latest[e.id][e.board] !== e.version) return false;
      if (!term) return true;
      return [e.id, e.name, e.short, e.author, e.description, e.licence].join(" ").toLowerCase().indexOf(term) >= 0;
    });
    list.textContent = "";
    shown.forEach(function (e) {
      var li = el("li");
      var h = el("h2", e.name + " ");
      h.appendChild(el("span", e.version, "meta"));
      li.appendChild(h);
      var meta = el("p", "", "meta");
      meta.appendChild(el("span", BOARD_NAMES[e.board] || e.board, "badge"));
      meta.appendChild(el("span", e.kind === "effect" ? "Effect" : "Machine", "badge"));
      meta.appendChild(el("span", e.licence, "badge"));
      meta.appendChild(el("span", "community, not tested by Sidecar", "badge"));
      meta.appendChild(document.createTextNode(" " + e.id + " by " + e.author));
      li.appendChild(meta);
      li.appendChild(el("p", e.description));
      var act = el("p", "", "actions");
      act.appendChild(link(e.file, "Download .rmp (" + Math.ceil(e.size / 1024) + " KB)"));
      var src = safeUrl(e.source);
      act.appendChild(src ? link(src, "Source") : el("span", "No source given", "meta"));
      if (safeUrl(e.demo)) act.appendChild(link(e.demo, "Demo audio"));
      act.appendChild(link(e.readme, "Readme"));
      li.appendChild(act);
      var sha = el("p", "SHA-256 ", "meta");
      sha.appendChild(el("code", e.sha256));
      li.appendChild(sha);
      list.appendChild(li);
    });
    status.textContent = shown.length ? shown.length + " package(s)" : "Nothing matches.";
  }

  [q, board, all].forEach(function (c) { c.addEventListener("input", render); });

  fetch("index.json", { cache: "no-cache" })
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(function (idx) {
      if (idx.schema !== 1) throw new Error("unsupported index schema " + idx.schema);
      entries = idx.entries;
      latest = idx.latest;
      render();
    })
    .catch(function (err) {
      status.textContent = "Could not load index.json: " + err.message;
    });
})();
