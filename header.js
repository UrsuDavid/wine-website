(function () {
  function initHeader() {
    var labels = { ro: 'RO', ru: 'RU', en: 'EN' };
    var lang = localStorage.getItem('aiwineLanguage') || 'ro';
    var display = document.getElementById('currentLangDisplay');
    if (display) display.textContent = labels[lang] || 'RO';

    document.getElementById('languageBtn') && document.getElementById('languageBtn').addEventListener('click', function (e) {
      e.stopPropagation();
      document.querySelector('.language-selector').classList.toggle('active');
    });
    document.getElementById('languageDropdown') && document.getElementById('languageDropdown').querySelectorAll('.language-option').forEach(function (opt) {
      opt.addEventListener('click', function () {
        var l = this.getAttribute('data-lang');
        localStorage.setItem('aiwineLanguage', l);
        if (typeof window.applyLanguageToWebsite === 'function') window.applyLanguageToWebsite(l);
        var d = document.getElementById('currentLangDisplay');
        if (d) d.textContent = labels[l] || l.toUpperCase();
        document.querySelector('.language-selector').classList.remove('active');
      });
    });
    document.addEventListener('click', function (e) {
      var s = document.querySelector('.language-selector');
      if (s && !s.contains(e.target)) s.classList.remove('active');
    });

    var menuBtn = document.getElementById('menuBtn');
    var navMenu = document.getElementById('navMenu');
    if (menuBtn && navMenu) menuBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      navMenu.classList.toggle('open');
    });
    document.addEventListener('click', function (e) {
      if (navMenu && !navMenu.contains(e.target)) navMenu.classList.remove('open');
    });

    var searchBtn = document.getElementById('headerSearchBtn');
    var searchBar = document.getElementById('headerSearchBar');
    if (searchBtn && searchBar) {
      searchBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        var hidden = searchBar.hidden;
        searchBar.hidden = !hidden;
        searchBtn.setAttribute('aria-expanded', !hidden);
        if (!hidden && document.getElementById('headerSearchInput')) document.getElementById('headerSearchInput').focus();
      });
      document.addEventListener('click', function (e) {
        if (searchBar && !searchBar.contains(e.target) && !searchBtn.contains(e.target)) searchBar.hidden = true;
      });
    }

    var cartCount = document.getElementById('headerCartCount');
    if (cartCount && typeof window.getCartCount === 'function') cartCount.textContent = window.getCartCount();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initHeader);
  else initHeader();
})();
