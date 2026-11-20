"use strict";
// Runs inside the listing page in headless Chromium (tests/test_site.py). Writes {"ok":bool,"log":[...]} into #result.
(function () {
  var log = [], ok = true;
  function check(c, msg) { log.push((c ? "ok: " : "FAIL: ") + msg); if (!c) ok = false; }
  function done() {
    var pre = document.createElement("pre");
    pre.id = "result";
    pre.textContent = JSON.stringify({ ok: ok, log: log });
    document.body.appendChild(pre);
  }
  function wait(test, ms) {
    return new Promise(function (res) {
      var t0 = Date.now();
      (function poll() { if (test() || Date.now() - t0 > ms) res(test()); else setTimeout(poll, 50); })();
    });
  }
  wait(function () { return document.querySelector("#list li"); }, 5000).then(function () {
    var lis = document.querySelectorAll("#list > li");
    check(lis.length === 2, "two entries listed");
    var withPv = Array.prototype.filter.call(lis, function (l) { return l.querySelector(".toggle"); });
    check(withPv.length === 1, "only the entry with previews has a toggle");
    var li = withPv[0];
    var tog = li.querySelector(".toggle");
    var panel = document.getElementById(tog.getAttribute("aria-controls"));
    check(tog.textContent === "Previews (2)", "toggle label is Previews (2)");
    check(tog.getAttribute("aria-expanded") === "false" && panel.hidden, "closed at first");
    check(!!li.querySelector("a[href='https://example.org/demo.mp3']"), "demo link kept");
    check(document.querySelectorAll("audio").length === 0, "no <audio> element before play");
    tog.click();
    check(tog.getAttribute("aria-expanded") === "true" && !panel.hidden, "toggle opens the list");
    var rows = panel.querySelectorAll("li.track");
    check(rows.length === 2, "two tracks");
    check(rows[0].querySelector(".tname").textContent === "01 Kick" && rows[1].querySelector(".tname").textContent === "Pad #2 (long)",
          "names are the file names without .mp3, in order");
    check(rows[0].querySelector("button").tagName === "BUTTON" && rows[0].querySelector("input[type=range]"), "button and slider");
    var b0 = rows[0].querySelector("button"), b1 = rows[1].querySelector("button");
    var played = [];
    var origPlay = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () { played.push(this.getAttribute("src")); return origPlay.call(this); };
    b0.click();
    return wait(function () { return b0.getAttribute("aria-pressed") === "true"; }, 3000).then(function (r) {
      check(r, "track 1 plays (button says Pause)");
      check(played[0] === "machines/test.sine/1.0.0/preview/01%20Kick.mp3", "url is encoded: " + played[0]);
      b1.click();
      return wait(function () { return b1.getAttribute("aria-pressed") === "true"; }, 3000);
    }).then(function (r) {
      check(r, "track 2 plays");
      check(played[1] === "machines/test.sine/1.0.0/preview/Pad%20%232%20(long).mp3", "url with # is encoded: " + played[1]);
      check(b0.getAttribute("aria-pressed") === "false" && b0.textContent === "Play", "track 1 stopped when track 2 started");
      b1.click();
      return wait(function () { return b1.getAttribute("aria-pressed") === "false"; }, 3000);
    }).then(function (r) {
      check(r && b1.textContent === "Play", "pause works");
      var bar0 = rows[0].querySelector("input[type=range]");
      bar0.value = 500;
      bar0.dispatchEvent(new Event("input"));
      check(Number(bar0.value) === 0, "slider of a track that does not play goes back to 0");
      tog.click();
      check(panel.hidden && tog.getAttribute("aria-expanded") === "false", "toggle closes the list");
      done();
    });
  }).catch(function (e) { check(false, "exception " + e); done(); });
})();
