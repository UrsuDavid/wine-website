(function () {
  var STORAGE_KEY = 'aiwineCart';
  function getCart() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) { return []; }
  }
  function setCart(items) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(items)); } catch (e) {}
  }
  window.getCart = function () { return getCart(); };
  window.getCartCount = function () {
    return getCart().reduce(function (sum, item) { return sum + (item.qty || 1); }, 0);
  };
  window.addToCart = function (productId, qty) {
    qty = parseInt(qty, 10) || 1;
    var cart = getCart();
    var i = cart.findIndex(function (item) { return item.id === productId; });
    if (i >= 0) cart[i].qty = (cart[i].qty || 1) + qty;
    else cart.push({ id: productId, qty: qty });
    setCart(cart);
    if (typeof window.updateHeaderCartCount === 'function') window.updateHeaderCartCount();
  };
  window.removeFromCart = function (productId) {
    setCart(getCart().filter(function (item) { return item.id !== productId; }));
    if (typeof window.updateHeaderCartCount === 'function') window.updateHeaderCartCount();
  };
  window.updateHeaderCartCount = function () {
    var el = document.getElementById('headerCartCount');
    if (!el || typeof window.getCartCount !== 'function') return;
    var count = Math.max(0, parseInt(window.getCartCount(), 10) || 0);
    el.textContent = count;
    el.setAttribute('data-count', String(count));
  };
})();
