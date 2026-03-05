(function () {
  function initHeader() {
    var labels = { ro: 'Română', ru: 'Русский', en: 'English' };
    var lang = localStorage.getItem('aiwineLanguage') || 'ro';
    var display = document.getElementById('currentLangDisplay');
    function updateLanguageUI() {
      var l = localStorage.getItem('aiwineLanguage') || 'ro';
      if (display) display.textContent = labels[l] || labels.ro;
      var dropdown = document.getElementById('languageDropdown');
      if (dropdown) dropdown.querySelectorAll('.language-option').forEach(function (opt) {
        opt.classList.toggle('active', opt.getAttribute('data-lang') === l);
      });
    }
    updateLanguageUI();

    document.getElementById('languageBtn') && document.getElementById('languageBtn').addEventListener('click', function (e) {
      e.stopPropagation();
      document.querySelector('.language-selector').classList.toggle('active');
    });
    document.getElementById('languageDropdown') && document.getElementById('languageDropdown').querySelectorAll('.language-option').forEach(function (opt) {
      opt.addEventListener('click', function () {
        var l = this.getAttribute('data-lang');
        localStorage.setItem('aiwineLanguage', l);
        if (typeof window.applyLanguageToWebsite === 'function') window.applyLanguageToWebsite(l);
        updateLanguageUI();
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

    var searchBar = document.getElementById('headerSearchBar');
    var searchBtn = document.getElementById('headerSearchBtn');
    var siteHeader = document.querySelector('.site-header');
    function closeSearch() {
      if (searchBar) searchBar.classList.remove('is-open');
      if (searchBtn) searchBtn.setAttribute('aria-expanded', 'false');
      if (siteHeader) siteHeader.classList.remove('search-expanded');
    }
    if (searchBar && searchBtn) {
      document.addEventListener('click', function (e) {
        if (!searchBar.classList.contains('is-open')) return;
        if (searchBar.contains(e.target) || searchBtn.contains(e.target)) return;
        closeSearch();
      });
      var closeSearchOnScroll = function () {
        if (searchBar && searchBar.classList.contains('is-open')) closeSearch();
      };
      var passive = { passive: true };
      window.addEventListener('scroll', closeSearchOnScroll, passive);
      window.addEventListener('wheel', closeSearchOnScroll, passive);
      window.addEventListener('touchmove', closeSearchOnScroll, passive);
      var scrollRoot = document.scrollingElement || document.documentElement || document.body;
      if (scrollRoot && scrollRoot !== window) scrollRoot.addEventListener('scroll', closeSearchOnScroll, passive);
    }

    if (typeof window.updateHeaderCartCount === 'function') window.updateHeaderCartCount();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initHeader);
  else initHeader();
})();
