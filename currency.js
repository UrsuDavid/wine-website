(function () {
  var STORAGE_KEY = 'aiwineCurrency';
  var CURRENCIES = ['MDL', 'USD', 'EUR'];
  var RATES = { MDL: 1, USD: 18, EUR: 19.5 };

  function getCurrency() {
    try {
      var c = (localStorage.getItem(STORAGE_KEY) || 'MDL').toUpperCase();
      return CURRENCIES.indexOf(c) !== -1 ? c : 'MDL';
    } catch (e) { return 'MDL'; }
  }

  function setCurrency(code) {
    code = (code || 'MDL').toUpperCase();
    if (CURRENCIES.indexOf(code) === -1) return;
    try {
      localStorage.setItem(STORAGE_KEY, code);
      window.dispatchEvent(new CustomEvent('currencychange', { detail: { currency: code } }));
    } catch (e) {}
  }

  function formatPrice(mdlAmount) {
    if (mdlAmount == null || isNaN(mdlAmount)) return '';
    var cur = getCurrency();
    if (cur === 'MDL') return Math.round(mdlAmount) + ' MDL';
    var rate = RATES[cur];
    if (!rate) return Math.round(mdlAmount) + ' MDL';
    var value = mdlAmount / rate;
    if (value >= 100) return value.toFixed(0) + ' ' + cur;
    if (value >= 10) return value.toFixed(1) + ' ' + cur;
    if (value >= 1) return value.toFixed(2) + ' ' + cur;
    return value.toFixed(2) + ' ' + cur;
  }

  window.getCurrency = getCurrency;
  window.setCurrency = setCurrency;
  window.formatPrice = formatPrice;
  window.CURRENCY_OPTIONS = CURRENCIES;
})();
