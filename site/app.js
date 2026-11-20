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

  // Previews: one shared audio element, so only one track plays at a time. preload="none": nothing is fetched until play.
  var audio = null;
  var playing = null;   // { btn, bar, time } of the track that is loaded

  function previewUrl(f) {
    return typeof f === "string" && /^machines\/[^\\]+\.mp3$/.test(f) && f.indexOf("..") < 0
      ? f.split("/").map(encodeURIComponent).join("/") : null;
  }

  function clock(s) {
    if (!isFinite(s)) s = 0;
    s = Math.floor(s);
    return Math.floor(s / 60) + ":" + (s % 60 < 10 ? "0" : "") + (s % 60);
  }

  function resetTrack(t) {
    t.btn.textContent = "Play";
    t.btn.setAttribute("aria-label", "Play " + t.name);
    t.btn.setAttribute("aria-pressed", "false");
    t.bar.value = 0;
    t.bar.setAttribute("aria-valuetext", "0:00");
    t.time.textContent = "0:00";
  }

  function stopPreview() {
    if (!audio) return;
    audio.pause();
    audio.removeAttribute("src");
    audio.load();
    if (playing) resetTrack(playing);
    playing = null;
  }

  function getAudio() {
    if (audio) return audio;
    audio = new Audio();
    audio.preload = "none";
    audio.autoplay = false;
    audio.addEventListener("timeupdate", function () {
      if (!playing || !audio.duration) return;
      playing.bar.value = Math.round(1000 * audio.currentTime / audio.duration);
      playing.bar.setAttribute("aria-valuetext", clock(audio.currentTime) + " of " + clock(audio.duration));
      playing.time.textContent = clock(audio.currentTime) + " / " + clock(audio.duration);
    });
    audio.addEventListener("pause", function () {
      if (playing && audio.paused && !audio.ended && audio.getAttribute("src")) {
        playing.btn.textContent = "Play";
        playing.btn.setAttribute("aria-label", "Play " + playing.name);
        playing.btn.setAttribute("aria-pressed", "false");
      }
    });
    audio.addEventListener("play", function () {
      if (!playing) return;
      playing.btn.textContent = "Pause";
      playing.btn.setAttribute("aria-label", "Pause " + playing.name);
      playing.btn.setAttribute("aria-pressed", "true");
    });
    audio.addEventListener("ended", function () { if (playing) resetTrack(playing); playing = null; });
    audio.addEventListener("error", function () {
      if (!playing || !audio.getAttribute("src")) return;
      playing.time.textContent = "could not play";
      playing.btn.textContent = "Play";
      playing.btn.setAttribute("aria-pressed", "false");
      playing = null;
    });
    return audio;
  }

  function track(p, url) {
    var li = el("li", "", "track");
    var t = { name: String(p.name), btn: el("button", "Play", "play"), bar: el("input"), time: el("span", "0:00", "meta time") };
    t.btn.type = "button";
    t.btn.setAttribute("aria-pressed", "false");
    t.btn.setAttribute("aria-label", "Play " + t.name);
    t.bar.type = "range";
    t.bar.min = 0;
    t.bar.max = 1000;
    t.bar.value = 0;
    t.bar.setAttribute("aria-label", "Position in " + t.name);
    t.bar.setAttribute("aria-valuetext", "0:00");
    t.btn.addEventListener("click", function () {
      var a = getAudio();
      if (playing === t) {
        if (a.paused) a.play(); else a.pause();
        return;
      }
      stopPreview();
      playing = t;
      a.src = url;
      a.play().catch(function () { /* the error event reports it */ });
    });
    t.bar.addEventListener("input", function () {
      if (playing === t && audio.duration) audio.currentTime = audio.duration * t.bar.value / 1000;
    });
    li.appendChild(t.btn);
    li.appendChild(el("span", t.name, "tname"));
    li.appendChild(t.bar);
    li.appendChild(t.time);
    li._track = t;
    return li;
  }

  function previewBlock(e, n) {
    var items = (Array.isArray(e.previews) ? e.previews : []).map(function (p) {
      var url = p && previewUrl(p.file);
      return url && typeof p.name === "string" ? track(p, url) : null;
    }).filter(Boolean);
    if (!items.length) return null;
    var wrap = el("div", "", "previews");
    var tog = el("button", "Previews (" + items.length + ")", "toggle");
    var panel = el("ul", "", "tracks");
    var id = "pv" + n;
    tog.type = "button";
    tog.setAttribute("aria-expanded", "false");
    tog.setAttribute("aria-controls", id);
    panel.id = id;
    panel.hidden = true;
    items.forEach(function (i) { panel.appendChild(i); });
    tog.addEventListener("click", function () {
      var open = panel.hidden;
      panel.hidden = !open;
      tog.setAttribute("aria-expanded", open ? "true" : "false");
      if (!open && playing && panel.contains(playing.btn)) stopPreview();
    });
    wrap.appendChild(tog);
    wrap.appendChild(panel);
    return wrap;
  }

  function render() {
    stopPreview();
    var term = q.value.trim().toLowerCase();
    var b = board.value;
    var shown = entries.filter(function (e) {
      if (b && e.board !== b) return false;
      if (!all.checked && latest[e.id] && latest[e.id][e.board] !== e.version) return false;
      if (!term) return true;
      return [e.id, e.name, e.short, e.author, e.description, e.licence].join(" ").toLowerCase().indexOf(term) >= 0;
    });
    list.textContent = "";
    shown.forEach(function (e, n) {
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
      var pv = previewBlock(e, n);
      if (pv) li.appendChild(pv);
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
