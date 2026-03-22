(function () {
  function tr(k) { var L = window.BESSA_TRANSLATIONS, l = localStorage.getItem('aiwineLanguage') || 'ro'; return (L && L[l] && L[l][k]) || (L && L.ro && L.ro[k]) || k; }
  function starRating(v) { var f = Math.floor(v), h = v - f >= 0.5 ? 1 : 0, e = 5 - f - h, s = ''; for (var i = 0; i < f; i++) s += '<span class="wine-star wine-star--full">★</span>'; if (h) s += '<span class="wine-star wine-star--half">★</span>'; for (var j = 0; j < e; j++) s += '<span class="wine-star wine-star--empty">★</span>'; return s; }
  function render(p) {
    var useVivino = (typeof p.vivinoRating === 'number' && typeof p.vivinoReviewCount === 'number' && p.vivinoReviewCount >= 1);
    var r = useVivino ? p.vivinoRating : (typeof p.rating === 'number' ? p.rating : 4);
    var count = useVivino ? p.vivinoReviewCount : p.reviewCount;
    var lab = count ? count + ' ' + tr('detail-reviews') : tr('detail-reviews');
    var priceText = p.price ? (typeof window.formatPrice === 'function' ? window.formatPrice(p.price) : p.price + ' MDL') : tr('detail-price-request'), desc = (p.description || '').replace(/</g, '&lt;').replace(/\n/g, '<br>');
    var lang = localStorage.getItem('aiwineLanguage') || 'ro';
    var vintageLabel = (tr('detail-vintage') || 'an');
    if (lang === 'ro') vintageLabel = String(vintageLabel).toLowerCase();
    var volumeLiters = (p.volumeLiters && String(p.volumeLiters).trim()) ? String(p.volumeLiters).trim() : '0.75';
    var volumeVintageText = volumeLiters + ' l' + (p.vintage ? ' • ' + p.vintage + ' ' + vintageLabel : '');
    var details = [];
    if (p.region) details.push('<div class="wine-detail-meta-item"><span class="wine-detail-meta-label" data-translate="detail-region">' + tr('detail-region') + '</span><span>' + (p.region || '').replace(/</g, '&lt;') + '</span></div>');
    if (p.taste) details.push('<div class="wine-detail-meta-item"><span class="wine-detail-meta-label" data-translate="detail-taste">' + tr('detail-taste') + '</span><span>' + (p.taste || '').replace(/</g, '&lt;') + '</span></div>');
    if (p.grape) details.push('<div class="wine-detail-meta-item"><span class="wine-detail-meta-label" data-translate="detail-grape">' + tr('detail-grape') + '</span><span>' + (p.grape || '').replace(/</g, '&lt;') + '</span></div>');
    if (p.abv) details.push('<div class="wine-detail-meta-item"><span class="wine-detail-meta-label" data-translate="detail-abv">' + tr('detail-abv') + '</span><span>' + (p.abv || '') + '%</span></div>');
    if (p.awards && ((Array.isArray(p.awards) && p.awards.length) || (!Array.isArray(p.awards) && String(p.awards).trim()))) {
      var awardsText = Array.isArray(p.awards) ? p.awards.join(', ') : String(p.awards);
      details.push('<div class="wine-detail-meta-item"><span class="wine-detail-meta-label" data-translate="detail-awards">' + tr('detail-awards') + '</span><span>' + awardsText.replace(/</g, '&lt;') + '</span></div>');
    }
    if (p.vintage) details.push('<div class="wine-detail-meta-item"><span class="wine-detail-meta-label" data-translate="detail-vintage">' + tr('detail-vintage') + '</span><span>' + (p.vintage || '').replace(/</g, '&lt;') + '</span></div>');
    var detailsBlock = details.length ? '<div class="wine-detail-meta"><h3 class="wine-detail-meta-title" data-translate="detail-details">' + tr('detail-details') + '</h3><div class="wine-detail-meta-grid">' + details.join('') + '</div></div>' : '';
    var typeFallbacks = { red: 'https://images.unsplash.com/photo-1553361371-9b22f78e8b1d?w=400', white: 'https://images.unsplash.com/photo-1608270586620-248524c67de9?w=400', sparkling: 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=400', rose: 'https://images.unsplash.com/photo-1569529465841-dfecdab7503b?w=400' };
    var fallback = typeFallbacks[p.type] || typeFallbacks.red;
    var imgSrc = (p.imageUrl && p.imageUrl.trim()) ? p.imageUrl : fallback;
    var firstFallback = fallback;
    if (p.imageUrlSmall && p.imageUrlSmall.trim()) firstFallback = p.imageUrlSmall;
    if (imgSrc.indexOf('wine.md') !== -1 && imgSrc.indexOf('/small/') !== -1) {
      if (!firstFallback || firstFallback === fallback) firstFallback = imgSrc;
      imgSrc = imgSrc.replace('/small/', '/');
    }
    var useJpgOnly = {};
    if (!useJpgOnly[p.id] && p.type !== 'white' && p.type !== 'sparkling' && imgSrc.indexOf('wine.md') !== -1 && /\.jpe?g$/i.test(imgSrc)) {
      firstFallback = imgSrc;
      imgSrc = imgSrc.replace(/\.jpe?g$/i, '.png');
    }
    var typeClass = (p.type === 'red' || p.type === 'white' || p.type === 'rose' || p.type === 'sparkling') ? p.type : 'red';
    var wrapClass = 'wine-detail-image-wrap wine-detail-image-wrap--' + typeClass + (useJpgOnly[p.id] ? ' wine-detail-image-wrap--jpg' : '');
    var newBadge = (typeof window.isWineProductNew === 'function' && window.isWineProductNew(p))
      ? '<span class="wine-detail-new-badge" data-translate="card-new">' + tr('card-new') + '</span>'
      : '';
    return '<div class="wine-detail-grid"><div class="wine-detail-image-col"><div class="' + wrapClass + '"><img class="wine-detail-image" src="' + imgSrc.replace(/"/g, '&quot;') + '" alt="' + (p.name || '').replace(/"/g, '&quot;') + '" decoding="async" fetchpriority="high" data-fallback="' + firstFallback.replace(/"/g, '&quot;') + '" data-fallback2="' + fallback.replace(/"/g, '&quot;') + '" onerror="var t=this;var f=t.getAttribute(\'data-fallback\');var f2=t.getAttribute(\'data-fallback2\');if(f){t.onerror=function(){if(f2){t.onerror=null;t.src=f2;}};t.src=f;}"></div>' + newBadge + '</div><div class="wine-detail-info">' +
      '<h1 class="wine-detail-name">' + (p.name || '').replace(/</g, '&lt;') + '</h1>' +
      '<p class="wine-card-volume-vintage wine-detail-volume-vintage">' + volumeVintageText.replace(/</g, '&lt;') + '</p>' +
      '<div class="wine-detail-rating">' + starRating(r) + ' <strong class="wine-detail-rating-value">' + r.toFixed(1) + '</strong> <span class="wine-detail-rating-label">' + lab + '</span></div>' +
      '<div class="wine-detail-price-block"><p class="wine-detail-price-value">' + priceText + '</p><p class="wine-detail-tax-shipping" data-translate="detail-tax-shipping">' + tr('detail-tax-shipping') + '</p></div>' +
      '<div class="wine-detail-quantity"><label data-translate="detail-quantity">' + tr('detail-quantity') + '</label><div class="wine-detail-qty-wrap"><button type="button" class="wine-detail-qty-minus">−</button><input type="number" class="wine-detail-qty-input" value="1" min="1" max="99"><button type="button" class="wine-detail-qty-plus">+</button></div></div>' +
      '<div class="wine-detail-actions"><button type="button" class="btn btn-outline wine-detail-add-cart" data-id="' + (p.id || '').replace(/"/g, '&quot;') + '" data-translate="detail-add-cart">' + tr('detail-add-cart') + '</button><a href="cart.html" class="btn btn-primary wine-detail-buy-now" data-translate="detail-buy-now">' + tr('detail-buy-now') + '</a></div>' +
      detailsBlock +
      (desc ? '<div class="wine-detail-description"><h3 class="wine-detail-description-title" data-translate="detail-about">' + tr('detail-about') + '</h3><p class="wine-detail-description-text">' + desc + '</p></div>' : '') + '</div></div>';
  }
  function init() {
    var params = new URLSearchParams(window.location.search);
    var id = params.get('id');
    try {
      if (!id) {
        var lastId = sessionStorage.getItem('aiwineLastProductId');
        if (lastId) {
          id = lastId;
          if (window.history && window.history.replaceState) {
            var base = (window.location.pathname || '').split('/').pop() || 'wine-detail.html';
            var newUrl = base + '?id=' + encodeURIComponent(id);
            window.history.replaceState(null, '', newUrl);
          }
        }
      }
    } catch (e) {}
    var loading = document.getElementById('wineDetailLoading'), content = document.getElementById('wineDetailContent');
    if (!id || !window.WINE_PRODUCTS) { if (loading) loading.setAttribute('data-translate', 'detail-not-found'), loading.textContent = ''; if (typeof window.applyLanguageToWebsite === 'function') window.applyLanguageToWebsite(localStorage.getItem('aiwineLanguage') || 'ro'); return; }
    var product = window.WINE_PRODUCTS.find(function (p) { return (p.id || '') === id; });
    if (!product) { if (loading) loading.setAttribute('data-translate', 'detail-not-found'); if (typeof window.applyLanguageToWebsite === 'function') window.applyLanguageToWebsite(localStorage.getItem('aiwineLanguage') || 'ro'); return; }
    if (loading) loading.style.display = 'none';
    var catalogHref = (product.type === 'red') ? 'wines-red.html' : (product.type === 'sparkling') ? 'wines-sparkling.html' : 'wines-white.html';
    var backLink = document.getElementById('backToCatalogLink');
    if (backLink) backLink.href = catalogHref;
    if (content) {
      content.style.display = 'block'; content.innerHTML = render(product);
      document.title = (product.name || '') + ' – ' + (product.brand || '') + ' | Aiwine';
      if (typeof window.applyLanguageToWebsite === 'function') window.applyLanguageToWebsite(localStorage.getItem('aiwineLanguage') || 'ro');
      window.addEventListener('currencychange', function updateDetailPrice() {
        var el = content.querySelector('.wine-detail-price-value');
        if (el && product) el.textContent = product.price ? (typeof window.formatPrice === 'function' ? window.formatPrice(product.price) : product.price + ' MDL') : tr('detail-price-request');
      });
      var qtyInput = content.querySelector('.wine-detail-qty-input'), minus = content.querySelector('.wine-detail-qty-minus'), plus = content.querySelector('.wine-detail-qty-plus');
      if (minus) minus.addEventListener('click', function () { var v = parseInt(qtyInput.value, 10) || 1; if (v > 1) qtyInput.value = v - 1; });
      if (plus) plus.addEventListener('click', function () { var v = parseInt(qtyInput.value, 10) || 1; if (v < 99) qtyInput.value = v + 1; });
      var addBtn = content.querySelector('.wine-detail-add-cart');
      if (addBtn && typeof window.addToCart === 'function') addBtn.addEventListener('click', function () { var q = parseInt(content.querySelector('.wine-detail-qty-input').value, 10) || 1; window.addToCart(product.id, q); addBtn.textContent = 'Added'; addBtn.disabled = true; if (typeof window.updateHeaderCartCount === 'function') window.updateHeaderCartCount(); });
      var buyBtn = content.querySelector('.wine-detail-buy-now');
      if (buyBtn && typeof window.addToCart === 'function') buyBtn.addEventListener('click', function (e) { var q = parseInt(content.querySelector('.wine-detail-qty-input').value, 10) || 1; window.addToCart(product.id, q); if (typeof window.updateHeaderCartCount === 'function') window.updateHeaderCartCount(); e.preventDefault(); window.location.href = 'cart.html'; });
      if (typeof window.updateHeaderCartCount === 'function') window.updateHeaderCartCount();
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
