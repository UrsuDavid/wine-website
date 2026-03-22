(function () {
  'use strict';
  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  var siteHeader = document.querySelector('.site-header');
  var bannerHero = document.getElementById('bannerHero');
  var bannerContent = document.getElementById('bannerContent');
  var hasHeroBanner = !!(bannerHero && bannerContent);

  var bannerRaf = null;
  var winH = window.innerHeight || 1;
  var heroTopDoc = 0;

  function recacheHeroBannerGeometry() {
    if (!hasHeroBanner) return;
    winH = window.innerHeight || 1;
    var sy = window.pageYOffset || document.documentElement.scrollTop || 0;
    heroTopDoc = bannerHero.getBoundingClientRect().top + sy;
  }

  function tickBannerScroll() {
    bannerRaf = null;
    if (!hasHeroBanner) return;
    var sy = window.pageYOffset || document.documentElement.scrollTop || 0;
    var rectTop = heroTopDoc - sy;
    var raw = -rectTop / (winH * 0.85);
    if (raw < 0) raw = 0;
    if (raw > 1) raw = 1;
    var progress = 1 - raw;
    var y = (1 - progress) * 36;
    var opacity = 0.78 + 0.22 * progress;
    var scale = 0.94 + 0.06 * progress;
    bannerContent.style.transform = 'translate3d(0,' + y + 'px,0) scale(' + scale + ')';
    bannerContent.style.opacity = String(opacity);
  }

  function scheduleBannerScroll() {
    if (!hasHeroBanner) return;
    if (bannerRaf != null) return;
    bannerRaf = requestAnimationFrame(tickBannerScroll);
  }

  function onWindowScroll() {
    if (siteHeader) {
      var sy = window.scrollY || document.documentElement.scrollTop || 0;
      if (sy > 40) siteHeader.classList.add('scrolled');
      else siteHeader.classList.remove('scrolled');
    }
    scheduleBannerScroll();
  }

  if (hasHeroBanner) {
    recacheHeroBannerGeometry();
  }
  if (siteHeader || hasHeroBanner) {
    window.addEventListener('scroll', onWindowScroll, { passive: true });
    onWindowScroll();
  }

  if (hasHeroBanner) {
    function onHeroResize() {
      recacheHeroBannerGeometry();
      if (bannerRaf != null) cancelAnimationFrame(bannerRaf);
      bannerRaf = null;
      tickBannerScroll();
    }
    window.addEventListener('resize', onHeroResize, { passive: true });
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () {
        recacheHeroBannerGeometry();
        scheduleBannerScroll();
      });
    }
    requestAnimationFrame(function () {
      recacheHeroBannerGeometry();
      tickBannerScroll();
    });
  }
  function initScrollAnimations() {
    var triggers = document.querySelectorAll('.banner.scroll-trigger');
    if (!triggers.length) return;
    var observer = new IntersectionObserver(function (entries) { entries.forEach(function (entry) { if (entry.isIntersecting) { entry.target.classList.add('animation-triggered'); observer.unobserve(entry.target); } }); }, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });
    triggers.forEach(function (el) { observer.observe(el); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initScrollAnimations); else initScrollAnimations();
})();
