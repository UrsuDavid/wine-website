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
    function setMenuOpen(open) {
      if (!navMenu) return;
      navMenu.classList.toggle('open', open);
      if (menuBtn) menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
    }
    function closeMenu() { setMenuOpen(false); }
    if (menuBtn && navMenu) {
      menuBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        setMenuOpen(!navMenu.classList.contains('open'));
      });
      document.addEventListener('click', function (e) {
        if (navMenu && navMenu.classList.contains('open') && !navMenu.contains(e.target)) closeMenu();
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
