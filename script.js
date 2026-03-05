(function () {
  'use strict';
  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();
  var siteHeader = document.querySelector('.site-header');
  if (siteHeader) {
    function onScroll() { if (window.scrollY > 40) siteHeader.classList.add('scrolled'); else siteHeader.classList.remove('scrolled'); }
    window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  }
  var bannerHero = document.getElementById('bannerHero');
  var bannerContent = document.getElementById('bannerContent');
  if (bannerHero && bannerContent) {
    function updateBannerScroll() {
      var rect = bannerHero.getBoundingClientRect();
      var windowH = window.innerHeight;
      var progress = 1 - Math.max(0, Math.min(1, -rect.top / (windowH * 0.85)));
      var y = (1 - progress) * 36;
      var opacity = 0.78 + 0.22 * progress;
      var scale = 0.94 + 0.06 * progress;
      bannerContent.style.transform = 'translate3d(0, ' + y + 'px, 0) scale(' + scale + ')';
      bannerContent.style.opacity = String(opacity);
    }
    window.addEventListener('scroll', updateBannerScroll, { passive: true });
    window.addEventListener('resize', updateBannerScroll);
    updateBannerScroll();
  }
  function initScrollAnimations() {
    var triggers = document.querySelectorAll('.banner.scroll-trigger');
    if (!triggers.length) return;
    var observer = new IntersectionObserver(function (entries) { entries.forEach(function (entry) { if (entry.isIntersecting) { entry.target.classList.add('animation-triggered'); observer.unobserve(entry.target); } }); }, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });
    triggers.forEach(function (el) { observer.observe(el); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initScrollAnimations); else initScrollAnimations();
  var searchBtn = document.getElementById('headerSearchBtn');
  var searchBar = document.getElementById('headerSearchBar');
  var searchInput = document.getElementById('headerSearchInput');
  if (searchBtn && searchBar) {
    searchBtn.addEventListener('click', function () {
      var open = searchBar.hidden;
      searchBar.hidden = !open;
      searchBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open && searchInput) searchInput.focus();
    });
  }
})();
