/* True when product.firstSeenAt (YYYY-MM-DD from scrape merge) is within the last 14 days. */
(function () {
  var MS_14_DAYS = 14 * 24 * 60 * 60 * 1000;
  window.isWineProductNew = function (p) {
    if (!p || p.firstSeenAt == null) return false;
    var raw = String(p.firstSeenAt).trim();
    if (!raw) return false;
    var m = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return false;
    var t0 = Date.UTC(parseInt(m[1], 10), parseInt(m[2], 10) - 1, parseInt(m[3], 10));
    if (isNaN(t0)) return false;
    return (Date.now() - t0) < MS_14_DAYS;
  };
})();
