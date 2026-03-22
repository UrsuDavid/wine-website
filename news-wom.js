/**
 * Loads “Știrile Vinăriilor” from Wine of Moldova (WordPress REST API, category id 8).
 * List matches the source site: new posts appear and removed posts disappear on each visit.
 */
(function () {
  var WOM_CATEGORY_ID = 8;
  var API_BASE = 'https://wineofmoldova.com/wp-json/wp/v2/posts';

  function htmlToPlainText(html) {
    var d = document.createElement('div');
    d.innerHTML = html || '';
    return (d.textContent || d.innerText || '').replace(/\s+/g, ' ').trim();
  }

  function featuredImageUrl(post) {
    var emb = post._embedded || {};
    var media = (emb['wp:featuredmedia'] || [])[0];
    if (!media) return '';
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

  function fetchAllPostsSafe() {
    var all = [];
    function nextPage(page) {
      return fetchPage(page).then(function (res) {
        if (!res.ok) throw new Error('wom_http_' + res.status);
        var totalPages = parseInt(res.headers.get('X-WP-TotalPages') || '1', 10) || 1;
        return res.json().then(function (chunk) {
          all = all.concat(chunk);
          if (page >= totalPages) return all;
          return nextPage(page + 1);
        });
      });
    }
    return nextPage(1);
  }

  function fetchPage(page) {
    var url =
      API_BASE +
      '?categories=' +
      WOM_CATEGORY_ID +
      '&per_page=100&page=' +
      page +
      '&orderby=date&order=desc&_embed=1';
    return fetch(url, {
      credentials: 'omit',
      headers: { Accept: 'application/json' },
    });
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
    if (typeof window.applyLanguageToWebsite === 'function') {
      window.applyLanguageToWebsite(localStorage.getItem('aiwineLanguage') || 'ro');
    }
  }

  function run() {
    var list = document.getElementById('newsWomList');
    var status = document.getElementById('newsWomStatus');
    if (!list) return;

    setStatus(status, 'loading');
    list.innerHTML = '';

    fetchAllPostsSafe()
      .then(function (posts) {
        if (!posts || !posts.length) {
          setStatus(status, 'empty');
          return;
        }
        setStatus(status, 'hide');
        var frag = document.createDocumentFragment();
        posts.forEach(function (p) {
          frag.appendChild(buildItem(p));
        });
        list.appendChild(frag);
        if (typeof window.applyLanguageToWebsite === 'function') {
          window.applyLanguageToWebsite(localStorage.getItem('aiwineLanguage') || 'ro');
        }
      })
      .catch(function () {
        setStatus(status, 'error');
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
