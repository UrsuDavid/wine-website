(function () {
  function initHeader() {
    var labels = { ro: 'Română', ru: 'Русский', en: 'English' };
    var lang = localStorage.getItem('aiwineLanguage') || 'ro';
    var display = document.getElementById('currentLangDisplay');
    var displayMenu = document.getElementById('currentLangDisplayMenu');
    var menuLangTriggerText = document.getElementById('menuLanguageTriggerText');
    var menuCurrencyTriggerText = document.getElementById('menuCurrencyTriggerText');
    var currencyDisplay = document.getElementById('currentCurrencyDisplay');
    var currencyDisplayMenu = document.getElementById('currentCurrencyDisplayMenu');
    function updateLanguageUI() {
      var l = localStorage.getItem('aiwineLanguage') || 'ro';
      var text = labels[l] || labels.ro;
      if (display) display.textContent = text;
      if (menuLangTriggerText) menuLangTriggerText.textContent = text;
      if (window.BESSA_TRANSLATIONS && window.BESSA_TRANSLATIONS[l]) {
        if (displayMenu) displayMenu.textContent = window.BESSA_TRANSLATIONS[l]['nav-language'] || 'Limba';
        if (currencyDisplayMenu) currencyDisplayMenu.textContent = window.BESSA_TRANSLATIONS[l]['nav-currency'] || 'Monedă';
      }
      var dropdown = document.getElementById('languageDropdown');
      if (dropdown) dropdown.querySelectorAll('.language-option').forEach(function (opt) {
        opt.classList.toggle('active', opt.getAttribute('data-lang') === l);
      });
      document.querySelectorAll('.nav-menu-language-option.language-option').forEach(function (opt) {
        opt.classList.toggle('active', opt.getAttribute('data-lang') === l);
      });
    }
    updateLanguageUI();

    document.getElementById('languageBtn') && document.getElementById('languageBtn').addEventListener('click', function (e) {
      e.stopPropagation();
      document.querySelector('.language-selector').classList.toggle('active');
    });
    function onLanguageChoose(l) {
      localStorage.setItem('aiwineLanguage', l);
      if (typeof window.applyLanguageToWebsite === 'function') window.applyLanguageToWebsite(l);
      if (typeof window.updateWineDetailTranslations === 'function') window.updateWineDetailTranslations();
      updateLanguageUI();
      document.querySelectorAll('.language-selector').forEach(function (s) { s.classList.remove('active'); });
      if (navMenu && navMenu.classList.contains('open')) closeMenu();
    }
    document.getElementById('languageDropdown') && document.getElementById('languageDropdown').querySelectorAll('.language-option').forEach(function (opt) {
      opt.addEventListener('click', function () { onLanguageChoose(this.getAttribute('data-lang')); });
    });
    document.querySelectorAll('.nav-menu-language-option.language-option').forEach(function (opt) {
      opt.addEventListener('click', function () {
        onLanguageChoose(this.getAttribute('data-lang'));
        var wrap = document.getElementById('menuLanguageWrap');
        if (wrap) wrap.classList.remove('is-open');
      });
    });
    document.getElementById('menuLanguageTrigger') && document.getElementById('menuLanguageTrigger').addEventListener('click', function (e) {
      e.stopPropagation();
      var wrap = document.getElementById('menuLanguageWrap');
      var currencyWrap = document.getElementById('menuCurrencyWrap');
      if (currencyWrap) currencyWrap.classList.remove('is-open');
      if (wrap) wrap.classList.toggle('is-open');
      this.setAttribute('aria-expanded', wrap && wrap.classList.contains('is-open'));
    });
    document.addEventListener('click', function (e) {
      var s = document.querySelector('.language-selector');
      if (s && !s.contains(e.target)) s.classList.remove('active');
    });

    function updateCurrencyUI() {
      var c = (typeof window.getCurrency === 'function') ? window.getCurrency() : 'MDL';
      if (currencyDisplay) currencyDisplay.textContent = c;
      if (menuCurrencyTriggerText) menuCurrencyTriggerText.textContent = c;
      document.querySelectorAll('.currency-option').forEach(function (opt) {
        opt.classList.toggle('active', opt.getAttribute('data-currency') === c);
      });
    }
    if (typeof window.getCurrency === 'function') updateCurrencyUI();
    window.addEventListener('currencychange', updateCurrencyUI);

    function onCurrencyChoose(code) {
      if (typeof window.setCurrency === 'function') window.setCurrency(code);
      updateCurrencyUI();
      if (navMenu && navMenu.classList.contains('open')) closeMenu();
    }
    document.querySelectorAll('.nav-menu-currency-option.currency-option').forEach(function (opt) {
      opt.addEventListener('click', function () {
        onCurrencyChoose(this.getAttribute('data-currency'));
        var wrap = document.getElementById('menuCurrencyWrap');
        if (wrap) wrap.classList.remove('is-open');
      });
    });
    document.getElementById('menuCurrencyTrigger') && document.getElementById('menuCurrencyTrigger').addEventListener('click', function (e) {
      e.stopPropagation();
      var wrap = document.getElementById('menuCurrencyWrap');
      var langWrap = document.getElementById('menuLanguageWrap');
      if (langWrap) langWrap.classList.remove('is-open');
      if (wrap) wrap.classList.toggle('is-open');
      this.setAttribute('aria-expanded', wrap && wrap.classList.contains('is-open'));
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.nav-menu-select-wrap')) {
        var lw = document.getElementById('menuLanguageWrap');
        var cw = document.getElementById('menuCurrencyWrap');
        if (lw) lw.classList.remove('is-open');
        if (cw) cw.classList.remove('is-open');
        var lt = document.getElementById('menuLanguageTrigger');
        var ct = document.getElementById('menuCurrencyTrigger');
        if (lt) lt.setAttribute('aria-expanded', 'false');
        if (ct) ct.setAttribute('aria-expanded', 'false');
      }
    });
    var menuBtn = document.getElementById('menuBtn');
    var navMenu = document.getElementById('navMenu');
    var navMenuClose = document.getElementById('navMenuClose');
    function setMenuOpen(open) {
      if (!navMenu) return;
      navMenu.classList.toggle('open', open);
      if (menuBtn) menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (navMenuClose) navMenuClose.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.classList.toggle('nav-menu-open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    }
    function closeMenu() { setMenuOpen(false); }
    if (menuBtn && navMenu) {
      menuBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        setMenuOpen(!navMenu.classList.contains('open'));
      });
      if (navMenuClose) {
        navMenuClose.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          closeMenu();
        });
      }
      navMenu.querySelectorAll('.nav-menu-dropdown .nav-link').forEach(function (link) {
        link.addEventListener('click', function () {
          closeMenu();
        });
      });
      document.addEventListener('click', function (e) {
        if (!navMenu || !navMenu.classList.contains('open')) return;
        if (menuBtn && (e.target === menuBtn || menuBtn.contains(e.target))) return;
        if (!navMenu.contains(e.target)) closeMenu();
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && navMenu && navMenu.classList.contains('open')) { closeMenu(); menuBtn && menuBtn.focus(); }
      });
    }

    var searchBar = document.getElementById('headerSearchBar');
    var searchBtn = document.getElementById('headerSearchBtn');
    var siteHeader = document.querySelector('.site-header');
    function closeSearch() {
      if (searchBar) searchBar.classList.remove('is-open');
      if (searchBtn) searchBtn.setAttribute('aria-expanded', 'false');
      if (siteHeader) siteHeader.classList.remove('search-expanded');
      document.body.classList.remove('search-grid-open');
    }
    if (searchBar && searchBtn) {
      document.addEventListener('click', function (e) {
        if (!searchBar.classList.contains('is-open')) return;
        if (searchBar.contains(e.target) || searchBtn.contains(e.target)) return;
        closeSearch();
      });
      var closeSearchScrollRaf = 0;
      function closeSearchOnScroll() {
        if (!searchBar || !searchBar.classList.contains('is-open')) return;
        if (closeSearchScrollRaf) return;
        closeSearchScrollRaf = requestAnimationFrame(function () {
          closeSearchScrollRaf = 0;
          if (searchBar && searchBar.classList.contains('is-open')) closeSearch();
        });
      }
      var passive = { passive: true };
      window.addEventListener('scroll', closeSearchOnScroll, passive);
      window.addEventListener('wheel', closeSearchOnScroll, passive);
      window.addEventListener('touchmove', closeSearchOnScroll, passive);
    }

    if (typeof window.updateHeaderCartCount === 'function') window.updateHeaderCartCount();

    var searchInput = document.getElementById('headerSearchInput');
    var searchForm = document.querySelector('.header-search-form');
    if (searchInput) {
      var qParam = typeof URLSearchParams !== 'undefined' ? new URLSearchParams(window.location.search).get('q') : null;
      if (qParam) searchInput.value = qParam;
    }
    if (searchForm && searchInput) {
      searchForm.addEventListener('submit', function (e) {
        var q = (searchInput.value || '').trim();
        if (q) {
          e.preventDefault();
          window.location.href = 'wines-red.html?q=' + encodeURIComponent(q);
        }
      });
    }

    (function initSearchSuggestions() {
      var input = document.getElementById('headerSearchInput');
      var bar = document.getElementById('headerSearchBar');
      if (!input || !bar || !window.WINE_PRODUCTS || !Array.isArray(window.WINE_PRODUCTS)) return;
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
        if (/achitarea\s+transport|achitare\s+transport/i.test(name) || /achitarea\s+transport|achitare\s+transport/i.test(brand)) return false;
        if (id === 'transport' && /achitare/i.test(brand + name)) return false;
        return true;
      }
      var wrap = document.createElement('div');
      wrap.className = 'header-search-suggestions';
      wrap.setAttribute('role', 'listbox');
      wrap.setAttribute('aria-label', 'Search results');
      bar.appendChild(wrap);
      var debounceTimer;
      var maxSuggestions = 8;
      function showSuggestions(query) {
        query = (query || '').trim().toLowerCase();
        wrap.innerHTML = '';
        wrap.classList.remove('is-visible');
        if (query.length < 2) return;
        var list = window.WINE_PRODUCTS.filter(function (p) {
          if (!isBottleOnly(p)) return false;
          var text = ((p.name || '') + ' ' + (p.brand || '')).toLowerCase();
          return text.indexOf(query) !== -1;
        });
        if (list.length === 0) {
          wrap.classList.add('is-visible');
          var empty = document.createElement('div');
          empty.className = 'header-search-suggestions-empty';
          empty.textContent = 'No products found';
          wrap.appendChild(empty);
          return;
        }
        list.slice(0, maxSuggestions).forEach(function (p) {
          var a = document.createElement('a');
          a.href = 'wine-detail.html?id=' + encodeURIComponent(p.id || p.name || '');
          a.className = 'header-search-suggestions-item';
          a.setAttribute('role', 'option');
          a.textContent = p.name || '';
          a.addEventListener('mousedown', function (e) { e.preventDefault(); });
          a.addEventListener('click', function () { wrap.classList.remove('is-visible'); });
          wrap.appendChild(a);
        });
        if (list.length > 0) {
          var viewAll = document.createElement('a');
          viewAll.href = 'wines-red.html?q=' + encodeURIComponent(input.value.trim());
          viewAll.className = 'header-search-suggestions-viewall';
          viewAll.textContent = 'View all products';
          viewAll.addEventListener('mousedown', function (e) { e.preventDefault(); });
          viewAll.addEventListener('click', function () { wrap.classList.remove('is-visible'); });
          wrap.appendChild(viewAll);
        }
        wrap.classList.add('is-visible');
      }
      function hideSuggestions() {
        wrap.classList.remove('is-visible');
      }
      input.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () { showSuggestions(input.value); }, 180);
      });
      input.addEventListener('focus', function () {
        if ((input.value || '').trim().length >= 2) showSuggestions(input.value);
      });
      input.addEventListener('blur', function () {
        setTimeout(hideSuggestions, 280);
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') hideSuggestions();
      });
      bar.addEventListener('click', function (e) {
        if (e.target.closest('.header-search-suggestions-item') || e.target.closest('.header-search-suggestions-viewall')) return;
        if (!e.target.closest('.header-search-input-wrap')) hideSuggestions();
      });
    })();

    var lastScrollY = window.scrollY || window.pageYOffset;
    var ticking = false;
    var header = document.querySelector('.site-header');
    var scrollThreshold = 80;
    function updateHeaderScroll() {
      var scrollY = window.scrollY || window.pageYOffset;
      if (scrollY <= 60) {
        if (header) header.classList.remove('header--hidden');
        lastScrollY = scrollY;
        ticking = false;
        return;
      }
      if (scrollY > lastScrollY && scrollY > scrollThreshold) {
        if (header) header.classList.add('header--hidden');
        if (navMenu && navMenu.classList.contains('open')) closeMenu();
      } else if (scrollY < lastScrollY) {
        if (header) header.classList.remove('header--hidden');
      }
      lastScrollY = scrollY;
      ticking = false;
    }
    function onScroll() {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(updateHeaderScroll);
      }
    }
    window.addEventListener('scroll', onScroll, { passive: true });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initHeader);
  else initHeader();
})();
