(function () {
  function t(key) {
    var L = window.BESSA_TRANSLATIONS, l = localStorage.getItem('aiwineLanguage') || 'ro';
    return (L && L[l] && L[l][key]) || (L && L.ro && L.ro[key]) || key;
  }
  window._winePageState = { resultCountId: null, lastCount: 0 };
  function isBottleOnly(p) {
    var url = (p.productPageUrl || '').toLowerCase();
    var name = (p.name || '').toLowerCase();
    var id = (p.id || '').toLowerCase();
    var brand = (p.brand || '').toLowerCase();
    if (/cutie|box|cu-cutie|in-cutie/.test(id) || /cutie|in cutie| box/.test(name)) return false;
    if (/spirtoase|accesorii|vacuvin|gifts|suvenire|produse-gourmet/.test(url)) return false;
    if (/vacu vin|vacuvin/.test(brand)) return false;
    if (/cognac|coniac|decanter|conus|lichior|vodka|whiskey|spirtoase/.test(name) || /cognac|coniac|decanter|conus|lichior|spirtoase/.test(id)) return false;
    if (/ciocolata|chocolate/.test(name) || /ciocolata|chocolate/.test(id)) return false;
    return true;
  }
  function getFilterFn(typeFilter, filters) {
    return function (p) {
      if (!isBottleOnly(p)) return false;
      if (!typeFilter(p)) return false;
      if (filters.brandLabels && filters.brandLabels.length && filters.brandLabels.indexOf(prettyBrandLabel(p.brand)) === -1) return false;
      if (filters.priceMin != null && (p.price == null || p.price < filters.priceMin)) return false;
      if (filters.priceMax != null && (p.price == null || p.price > filters.priceMax)) return false;
      if (filters.ratingMin != null) { var pr = (typeof p.vivinoRating === 'number' ? p.vivinoRating : null) ?? p.rating; if (pr == null || pr < filters.ratingMin) return false; }
      if (filters.discountOnly && !p.discount) return false;
      return true;
    };
  }
  function getSortFn(sortKey) {
    if (sortKey === 'rating') return function (a, b) { var ra = (typeof a.vivinoRating === 'number' ? a.vivinoRating : null) ?? a.rating; var rb = (typeof b.vivinoRating === 'number' ? b.vivinoRating : null) ?? b.rating; return (rb || 0) - (ra || 0); };
    if (sortKey === 'price_asc') return function (a, b) { return (a.price || 0) - (b.price || 0); };
    if (sortKey === 'price_desc') return function (a, b) { return (b.price || 0) - (a.price || 0); };
    if (sortKey === 'name') return function (a, b) { return (a.name || '').localeCompare(b.name || ''); };
    return null;
  }
  function starRating(v) {
    var f = Math.floor(v), h = v - f >= 0.5 ? 1 : 0, e = 5 - f - h, s = '';
    for (var i = 0; i < f; i++) s += '<span class="wine-star wine-star--full">★</span>';
    if (h) s += '<span class="wine-star wine-star--half">★</span>';
    for (var j = 0; j < e; j++) s += '<span class="wine-star wine-star--empty">★</span>';
    return s;
  }
  function getVivinoSearchUrl(p) {
    var q = ((p.brand || '') + ' ' + (p.name || '')).trim();
    if (!q) return 'https://www.vivino.com/search/wines';
    return 'https://www.vivino.com/search/wines?q=' + encodeURIComponent(q);
  }
  function prettyBrandLabel(brand) {
    var s = (brand || '').trim();
    if (!s) return '';
    var lower = s.toLowerCase();
    var canonical = {
      carlevana: 'Carlevana',
      basavin: 'Basavin',
      bahu: 'Bahu',
      aurelius: 'Aurelius',
      'castel mimi': 'Castel Mimi',
      'château vartely': 'Château Vartely',
      'chateau vartely': 'Château Vartely',
      'château purcari': 'Château Purcari',
      'chateau purcari': 'Château Purcari'
    };
    for (var key in canonical) {
      if (canonical.hasOwnProperty(key) && lower.indexOf(key) !== -1) return canonical[key];
    }
    var words = s.split(/\s+/);
    if (words.length >= 2) {
      var grapes = ['CABERNET', 'MERLOT', 'FETEASCA', 'FETEASCA', 'PINOT', 'SAUVIGNON', 'BLANC', 'ROSE', 'ROȘU', 'NOIR', 'NEAGRA', 'NEAGRĂ'];
      if (grapes.indexOf(words[1].toUpperCase()) !== -1) {
        return words[0].charAt(0).toUpperCase() + words[0].slice(1).toLowerCase();
      }
    }
    return s;
  }
  function createCard(doc, p) {
    var a = doc.createElement('a');
    a.className = 'wine-card wine-card--product';
    a.href = 'wine-detail.html?id=' + encodeURIComponent(p.id || p.name);
    if (p.id) a.setAttribute('data-product-id', p.id);
    var useJpgOnly = {};
    var wrap = doc.createElement('div');
    wrap.className = 'wine-card-img wine-card-img--' + (p.type === 'red' ? 'red' : p.type === 'sparkling' ? 'sparkling' : p.type === 'rose' ? 'rose' : 'white') + (useJpgOnly[p.id] ? ' wine-card-img--jpg' : '');
    var img = doc.createElement('img');
    var fallbacks = { red: 'https://images.unsplash.com/photo-1553361371-9b22f78e8b1d?w=500&q=80', white: 'https://images.unsplash.com/photo-1608270586620-248524c67de9?w=500&q=80', sparkling: 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500&q=80', rose: 'https://images.unsplash.com/photo-1569529465841-dfecdab7503b?w=500&q=80' };
    var typeKey = p.type === 'red' ? 'red' : p.type === 'sparkling' ? 'sparkling' : p.type === 'rose' ? 'rose' : 'white';
    var safeUrl = (p.imageUrl && typeof p.imageUrl === 'string' && p.imageUrl.trim()) ? p.imageUrl : (fallbacks[typeKey] || fallbacks.red);
    if (safeUrl.indexOf('wine.md') !== -1 && safeUrl.indexOf('/small/') !== -1) safeUrl = safeUrl.replace('/small/', '/');
    var pngUrl = (!useJpgOnly[p.id] && safeUrl.indexOf('wine.md') !== -1 && /\.jpe?g$/i.test(safeUrl)) ? safeUrl.replace(/\.jpe?g$/i, '.png') : null;
    img.src = pngUrl || safeUrl;
    img.alt = p.name;
    img.loading = 'lazy';
    img.decoding = 'async';
    var fallbackUrl = fallbacks[typeKey] || fallbacks.red;
    var smallUrl = (p.imageUrlSmall && p.imageUrlSmall.trim()) ? p.imageUrlSmall : ((p.imageUrl && p.imageUrl.indexOf('wine.md') !== -1 && p.imageUrl.indexOf('/small/') !== -1) ? p.imageUrl : null);
    img.onerror = function () {
      this.onerror = null;
      if (pngUrl && this.src === pngUrl) { this.src = safeUrl; return; }
      if (smallUrl && this.src !== smallUrl) { this.src = smallUrl; return; }
      this.src = fallbackUrl;
    };
    wrap.appendChild(img);
    a.appendChild(wrap);
    var body = doc.createElement('div');
    body.className = 'wine-card-body';
    var winery = doc.createElement('div');
    winery.className = 'wine-card-winery';
    winery.textContent = p.brand;
    body.appendChild(winery);
    var productName = doc.createElement('h3');
    productName.className = 'wine-card-name wine-card-product-name';
    productName.textContent = p.name;
    body.appendChild(productName);
    var volumeVintage = doc.createElement('p');
    volumeVintage.className = 'wine-card-volume-vintage';
    volumeVintage.textContent = '0.75 l' + (p.vintage ? ' • ' + p.vintage + ' ' + (t('detail-vintage') || 'an') : '');
    body.appendChild(volumeVintage);
    var r = (typeof p.vivinoRating === 'number' ? p.vivinoRating : null) ?? (typeof p.rating === 'number' ? p.rating : 4);
    var count = (typeof p.vivinoReviewCount === 'number' ? p.vivinoReviewCount : null) ?? p.reviewCount;
    var reviewText = count ? count + ' ' + t('detail-reviews') : t('detail-reviews');
    var vivinoUrl = p.vivinoUrl || getVivinoSearchUrl(p);
    var rating = doc.createElement('div');
    rating.className = 'wine-card-rating';
    rating.innerHTML = starRating(r) + ' <span class="wine-card-rating-value">' + r.toFixed(1) + '</span> <span class="wine-card-rating-label">' + reviewText + '</span> <span class="wine-card-vivino-link" role="link" tabindex="0" data-vivino-url="' + vivinoUrl.replace(/"/g, '&quot;') + '" title="' + (t('detail-see-on-vivino') || 'Vivino').replace(/"/g, '&quot;') + '">Vivino</span>';
    body.appendChild(rating);
    var vivinoEl = rating.querySelector('.wine-card-vivino-link');
    if (vivinoEl) vivinoEl.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); window.open(vivinoEl.getAttribute('data-vivino-url') || 'https://www.vivino.com/search/wines', '_blank', 'noopener'); });
    if (vivinoEl) vivinoEl.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); window.open(vivinoEl.getAttribute('data-vivino-url') || 'https://www.vivino.com/search/wines', '_blank', 'noopener'); } });
    var price = doc.createElement('div');
    price.className = 'wine-card-price';
    price.textContent = p.price ? p.price + ' MDL' : t('detail-price-request');
    body.appendChild(price);
    var cta = doc.createElement('span');
    cta.className = 'wine-card-cta btn btn-primary';
    cta.textContent = t('card-add-to-cart') || t('card-view-details');
    body.appendChild(cta);
    a.appendChild(body);
    return a;
  }
  window.renderWineGrid = function (containerId, typeFilter, sortKey, filters) {
    var container = document.getElementById(containerId);
    if (!container || !Array.isArray(window.WINE_PRODUCTS)) return 0;
    var list = window.WINE_PRODUCTS.filter(getFilterFn(typeFilter, filters || {}));
    var sortFn = getSortFn(sortKey || '');
    if (sortFn) list = list.slice().sort(sortFn);
    container.innerHTML = '';
    list.forEach(function (p) { container.appendChild(createCard(document, p)); });
    return list.length;
  };
  window.initWineExplorer = function (opts) {
    var gridId = opts.gridId, typeFilter = opts.typeFilter, resultCountId = opts.resultCountId, sortSelectId = opts.sortSelectId;
    var filterBrandId = opts.filterBrandId, filterPriceMinId = opts.filterPriceMinId, filterPriceMaxId = opts.filterPriceMaxId;
    var priceRangeDisplayId = opts.priceRangeDisplayId, filterDiscountId = opts.filterDiscountId, filterRatingId = opts.filterRatingId;
    if (!gridId || !typeFilter) return;

    (function restoreCatalogScroll() {
      try {
        var raw = sessionStorage.getItem('aiwineCatalogScroll');
        if (!raw) return;
        var data = JSON.parse(raw);
        var currentPage = (window.location.pathname || '').split('/').pop() || window.location.href;
        if (data.page !== currentPage || typeof data.scroll !== 'number') return;
        sessionStorage.removeItem('aiwineCatalogScroll');
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            window.scrollTo(0, data.scroll);
          });
        });
      } catch (e) {}
    })();

    var state = { sort: '', brandLabels: [], priceMin: null, priceMax: null, ratingMin: null, discountOnly: false };
    var products = window.WINE_PRODUCTS.filter(function (p) { return isBottleOnly(p) && typeFilter(p); });
    var priceBounds = { min: 0, max: 2000 };
    products.forEach(function (p) { if (p.price != null) { if (p.price < priceBounds.min) priceBounds.min = p.price; if (p.price > priceBounds.max) priceBounds.max = p.price; } });
    priceBounds.min = Math.floor(priceBounds.min / 10) * 10 || 0;
    priceBounds.max = Math.ceil(priceBounds.max / 10) * 10 || 2000;
    function updateGrid() {
      var n = window.renderWineGrid(gridId, typeFilter, state.sort, { brandLabels: state.brandLabels.length ? state.brandLabels : null, priceMin: state.priceMin, priceMax: state.priceMax, ratingMin: state.ratingMin, discountOnly: state.discountOnly });
      window._winePageState.resultCountId = resultCountId;
      window._winePageState.lastCount = n;
      var countEl = resultCountId ? document.getElementById(resultCountId) : null;
      if (countEl) countEl.textContent = n + ' ' + (n === 1 ? t('wines-count-one') : t('wines-count'));
    }
    var brandEl = filterBrandId ? document.getElementById(filterBrandId) : null;
    if (brandEl) {
      var labelSet = {};
      products.forEach(function (p) {
        var label = prettyBrandLabel(p.brand);
        if (!label) return;
        labelSet[label] = true;
      });
      var labels = Object.keys(labelSet).sort();
      brandEl.innerHTML = labels.map(function (label) {
        var ch = state.brandLabels.indexOf(label) !== -1; // default: all unchecked
        return '<label class="wine-filter-check"><input type="checkbox" data-label="' + label.replace(/"/g, '&quot;') + '" ' + (ch ? 'checked' : '') + '> ' + label + '</label>';
      }).join('');
      brandEl.querySelectorAll('input').forEach(function (cb) {
        cb.addEventListener('change', function () {
          state.brandLabels = Array.from(brandEl.querySelectorAll('input:checked')).map(function (c) { return c.getAttribute('data-label'); });
          updateGrid(); // when none selected, all brands are shown
        });
      });
    }
    var priceMinEl = filterPriceMinId ? document.getElementById(filterPriceMinId) : null;
    var priceMaxEl = filterPriceMaxId ? document.getElementById(filterPriceMaxId) : null;
    var priceDisplayEl = priceRangeDisplayId ? document.getElementById(priceRangeDisplayId) : null;
    if (priceMinEl && priceMaxEl) {
      priceMinEl.min = priceMaxEl.min = priceBounds.min;
      priceMinEl.max = priceMaxEl.max = priceBounds.max;
      priceMinEl.value = priceBounds.min;
      priceMaxEl.value = priceBounds.max;
      state.priceMin = priceBounds.min;
      state.priceMax = priceBounds.max;
      function up() { var lo = parseInt(priceMinEl.value, 10), hi = parseInt(priceMaxEl.value, 10); if (lo > hi) priceMaxEl.value = lo; state.priceMin = parseInt(priceMinEl.value, 10); state.priceMax = parseInt(priceMaxEl.value, 10); if (priceDisplayEl) priceDisplayEl.textContent = state.priceMin + ' – ' + state.priceMax + ' MDL'; updateGrid(); }
      priceMinEl.addEventListener('input', up);
      priceMaxEl.addEventListener('input', up);
      if (priceDisplayEl) priceDisplayEl.textContent = priceBounds.min + ' – ' + priceBounds.max + ' MDL';
    }
    if (filterDiscountId) { var de = document.getElementById(filterDiscountId); if (de) de.addEventListener('change', function () { state.discountOnly = this.checked; updateGrid(); }); }
    if (filterRatingId) { var re = document.getElementById(filterRatingId); if (re) re.addEventListener('change', function () { state.ratingMin = this.value === '' ? null : parseFloat(this.value); updateGrid(); }); }
    if (sortSelectId) { var se = document.getElementById(sortSelectId); if (se) se.addEventListener('change', function () { state.sort = this.value || ''; updateGrid(); }); }
    updateGrid();

    var gridEl = document.getElementById(gridId);
    if (gridEl && !gridEl._aiwineClickBound) {
      gridEl._aiwineClickBound = true;
      gridEl.addEventListener('click', function (e) {
        var a = e.target.closest('a[href*="wine-detail.html"]');
        if (!a) return;
        var scrollY = window.scrollY || document.documentElement.scrollTop;
        var page = (window.location.pathname || '').split('/').pop() || window.location.href;
        try {
          sessionStorage.setItem('aiwineCatalogScroll', JSON.stringify({ scroll: scrollY, page: page }));
        } catch (err) {}
        try {
          var pid = a.getAttribute('data-product-id');
          if (!pid) {
            var href = a.getAttribute('href') || '';
            var qIndex = href.indexOf('?');
            if (qIndex !== -1) {
              var qs = href.substring(qIndex + 1);
              var params = new URLSearchParams(qs);
              pid = params.get('id') || '';
            }
          }
          if (pid) sessionStorage.setItem('aiwineLastProductId', pid);
        } catch (err2) {}
      });
    }
  };
  window.updateWinePageTranslations = function () { var s = window._winePageState; if (s && s.resultCountId) { var el = document.getElementById(s.resultCountId); if (el) el.textContent = s.lastCount + ' ' + (s.lastCount === 1 ? t('wines-count-one') : t('wines-count')); } };
})();
