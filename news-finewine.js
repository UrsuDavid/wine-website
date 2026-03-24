/**
 * Loads news from Fine Wine (finewine.md) WordPress REST API — category “Important” (id 59).
 * List is always built from a live request (no HTTP cache): new posts show and removed posts
 * disappear on the next load or when the tab becomes visible again (throttled).
 */
(function () {
  var FINEWINE_CATEGORY_ID = 59;
  var API_BASE = 'https://finewine.md/wp-json/wp/v2/posts';
  var PER_PAGE = 100;
  var lastFetchTime = 0;
  var BACKGROUND_REFRESH_MIN_MS = 45000;

  function htmlToPlainText(html) {
    var d = document.createElement('div');
    d.innerHTML = html || '';
    return (d.textContent || d.innerText || '').replace(/\s+/g, ' ').trim();
  }

  function featuredImageUrl(post) {
    var emb = post._embedded || {};
    var media = (emb['wp:featuredmedia'] || [])[0];
    if (!media || media.code) return '';
    return media.source_url || '';
  }

  function buildItem(post) {
    var link = post.link || '#';
    var title = htmlToPlainText(post.title && post.title.rendered);
    var excerpt = htmlToPlainText(post.excerpt && post.excerpt.rendered);
    var img = featuredImageUrl(post);

    var li = document.createElement('li');
    li.className = 'news-wom-item';

    if (img) {
      var aMedia = document.createElement('a');
      aMedia.className = 'news-wom-item-media';
      aMedia.href = link;
      aMedia.target = '_blank';
      aMedia.rel = 'noopener noreferrer';
      aMedia.tabIndex = -1;
      aMedia.setAttribute('aria-hidden', 'true');
      var im = document.createElement('img');
      im.src = img;
      im.alt = '';
      im.width = 400;
      im.height = 300;
      im.loading = 'lazy';
      im.decoding = 'async';
      im.referrerPolicy = 'no-referrer';
      aMedia.appendChild(im);
      li.appendChild(aMedia);
    }

    var body = document.createElement('div');
    body.className = 'news-wom-item-body';

    var h2 = document.createElement('h2');
    h2.className = 'news-wom-item-title';
    var aTitle = document.createElement('a');
    aTitle.href = link;
    aTitle.target = '_blank';
    aTitle.rel = 'noopener noreferrer';
    aTitle.textContent = title;
    h2.appendChild(aTitle);

    var p = document.createElement('p');
    p.className = 'news-wom-item-excerpt';
    p.textContent = excerpt;

    var aRead = document.createElement('a');
    aRead.className = 'news-wom-item-read';
    aRead.href = link;
    aRead.target = '_blank';
    aRead.rel = 'noopener noreferrer';
    aRead.setAttribute('data-translate', 'news-wom-read');

    body.appendChild(h2);
    body.appendChild(p);
    body.appendChild(aRead);
    li.appendChild(body);
    return li;
  }

  function fetchLatestPosts() {
    var url =
      API_BASE +
      '?categories=' +
      FINEWINE_CATEGORY_ID +
      '&per_page=' +
      PER_PAGE +
      '&page=1&orderby=date&order=desc&_embed=1';
    return fetch(url, {
      cache: 'no-store',
      credentials: 'omit',
      headers: { Accept: 'application/json' },
    }).then(function (res) {
      if (!res.ok) throw new Error('finewine_http_' + res.status);
      return res.json();
    });
  }

  function applyLang() {
    if (typeof window.applyLanguageToWebsite === 'function') {
      window.applyLanguageToWebsite(localStorage.getItem('aiwineLanguage') || 'ro');
    }
  }

  function setStatus(el, mode) {
    if (!el) return;
    if (mode === 'hide') {
      el.hidden = true;
      el.removeAttribute('data-translate');
      return;
    }
    el.hidden = false;
    el.removeAttribute('data-translate');
    if (mode === 'loading') {
      el.setAttribute('data-translate', 'news-wom-loading');
    } else if (mode === 'error') {
      el.setAttribute('data-translate', 'news-wom-error');
    } else if (mode === 'empty') {
      el.setAttribute('data-translate', 'news-wom-empty');
    }
    applyLang();
  }

  function mountPosts(list, status, posts, silent) {
    lastFetchTime = Date.now();
    if (!posts || !posts.length) {
      setStatus(status, 'empty');
      list.innerHTML = '';
      applyLang();
      return;
    }
    setStatus(status, 'hide');
    list.innerHTML = '';
    var frag = document.createDocumentFragment();
    posts.forEach(function (p) {
      frag.appendChild(buildItem(p));
    });
    list.appendChild(frag);
    applyLang();
  }

  /**
   * @param {boolean} silent If true, keep existing list on network error; do not show loading state.
   */
  function loadNews(silent) {
    var list = document.getElementById('newsWomList');
    var status = document.getElementById('newsWomStatus');
    if (!list || !status) return Promise.resolve();

    if (!silent) {
      setStatus(status, 'loading');
      list.innerHTML = '';
    }

    return fetchLatestPosts()
      .then(function (posts) {
        mountPosts(list, status, posts, silent);
      })
      .catch(function () {
        if (!silent) {
          setStatus(status, 'error');
        }
      });
  }

  function maybeRefreshFromFinewine() {
    if (document.hidden) return;
    var now = Date.now();
    if (now - lastFetchTime < BACKGROUND_REFRESH_MIN_MS) return;
    loadNews(true);
  }

  function run() {
    loadNews(false);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }

  window.addEventListener('pageshow', function (e) {
    if (e.persisted) {
      loadNews(true);
    }
  });

  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) {
      maybeRefreshFromFinewine();
    }
  });
})();
