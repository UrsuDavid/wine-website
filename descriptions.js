// Runtime description enhancer for Aiwine products.
// Generates multilingual descriptions (ro/ru/en) using product metadata.
(function () {
  if (!Array.isArray(window.WINE_PRODUCTS)) return;
  var typeLabel = {
    ro: { red: 'vin rosu', white: 'vin alb', sparkling: 'vin spumant', rose: 'vin rose', fallback: 'vin' },
    ru: { red: 'красное вино', white: 'белое вино', sparkling: 'игристое вино', rose: 'розе', fallback: 'вино' },
    en: { red: 'red wine', white: 'white wine', sparkling: 'sparkling wine', rose: 'rose wine', fallback: 'wine' }
  };
  function tastingNotes(lang, t, grape) {
    var g = (grape || '').toLowerCase();
    if (lang === 'ru') {
      if (t === 'игристое вино') return 'Игристое вино с тонким перляжем, нотами белых фруктов и цитрусов, подходит для праздников и легких закусок.';
      if (t === 'розе') return 'Свежее розе с ароматами красных ягод и цитрусов, хорошо сбалансировано между легкостью и элегантностью.';
      if (t === 'белое вино') {
        if (g.indexOf('sauvignon') !== -1 || g.indexOf('viorica') !== -1) return 'Ароматичное белое вино с нотами белых цветов, трав и тропических фруктов, с хрустящей кислотностью.';
        if (g.indexOf('chardonnay') !== -1) return 'Мягкое белое вино с нотами спелых желтых фруктов, легкой ванили и хорошо сбалансированной структурой.';
        return 'Чистое и выразительное белое вино с нотами цветов лозы, белых фруктов и цитрусов, идеально к рыбе и салатам.';
      }
      if (g.indexOf('saperavi') !== -1 || g.indexOf('feteasca neagra') !== -1 || g.indexOf('rara neagra') !== -1) return 'Насыщенное красное вино с нотами спелых темных ягод, специй и зрелых танинов, характерное для терруара Молдовы.';
      if (g.indexOf('pinot noir') !== -1) return 'Элегантное красное вино с нотами красных ягод, нежных специй и мягкой текстурой.';
      return 'Щедрое красное вино с ароматами сливы, вишни и специй, с хорошей структурой и длительным послевкусием.';
    }
    if (lang === 'en') {
      if (t === 'sparkling wine') return 'A sparkling wine with fine bubbles, white fruit and citrus notes, ideal for celebrations and light appetizers.';
      if (t === 'rose wine') return 'A fresh rose with red berry and citrus aromas, balanced between crispness and elegance.';
      if (t === 'white wine') {
        if (g.indexOf('sauvignon') !== -1 || g.indexOf('viorica') !== -1) return 'An aromatic white with white flower, herb and tropical fruit notes, supported by bright acidity.';
        if (g.indexOf('chardonnay') !== -1) return 'A smooth white with ripe yellow fruit notes, subtle vanilla and a balanced structure.';
        return 'A clean and expressive white with vine blossom, white fruit and citrus notes, ideal with fish and salads.';
      }
      if (g.indexOf('saperavi') !== -1 || g.indexOf('feteasca neagra') !== -1 || g.indexOf('rara neagra') !== -1) return 'An intense red with ripe dark fruit, fine spice and ripe tannins, typical of Moldova terroir.';
      if (g.indexOf('pinot noir') !== -1) return 'An elegant red with red fruit notes, delicate spice and a silky texture.';
      return 'A generous red with plum, sour cherry and spice aromas, solid structure and a persistent finish.';
    }
    if (t === 'vin spumant') {
      return 'Un spumant cu perlaj fin, note de fructe albe si citrice, perfect pentru momente festive si aperitive lejere.';
    }
    if (t === 'vin rose') {
      return 'Un rose proaspat, cu arome de fructe rosii de padure si citrice, echilibrat intre prospetime si eleganta.';
    }
    if (t === 'vin alb') {
      if (g.indexOf('sauvignon') !== -1 || g.indexOf('viorica') !== -1) {
        return 'Un alb aromatic, cu note de flori albe, ierburi fine si fructe exotice, cu aciditate crocanta.';
      }
      if (g.indexOf('chardonnay') !== -1) {
        return 'Un alb catifelat, cu note de fructe galbene coapte, vanilie discreta si o structura echilibrata.';
      }
      return 'Un alb curat si expresiv, cu note de flori de vita, fructe albe si citrice, ideal alaturi de peste si salate.';
    }
    // red
    if (g.indexOf('saperavi') !== -1 || g.indexOf('feteasca neagra') !== -1 || g.indexOf('rara neagra') !== -1) {
      return 'Un rosu intens, cu nuante de fructe negre coapte, condimente fine si taninuri coapte, specific terroir-ului din Moldova.';
    }
    if (g.indexOf('pinot noir') !== -1) {
      return 'Un rosu elegant, cu note de fructe rosii, condimente delicate si o textura supla, usor de baut.';
    }
    return 'Un rosu generos, cu arome de prune, visine si condimente, structura buna si postgust persistent.';
  }
  function story(lang, p, region) {
    var brand = p.brand || '';
    var reg = region || 'Moldova';
    if (lang === 'ru') {
      if (brand) return 'Это вино из подборки ' + brand + ', винодельни, которая сочетает местные традиции и современные технологии, представляя регион ' + reg + '.';
      return 'Это вино отражает винодельческие традиции региона ' + reg + ', где климат и почвы формируют характерный стиль.';
    }
    if (lang === 'en') {
      if (brand) return 'This label is part of the ' + brand + ' selection, a winery that blends local tradition with modern methods and represents ' + reg + '.';
      return 'This wine reflects the winemaking tradition of ' + reg + ', where climate and soils create wines with clear character.';
    }
    if (brand) {
      return 'Eticheta face parte din selectia ' + brand + ', o crama care imbina traditia locala cu tehnologii moderne, reprezentativa pentru ' + reg + '.';
    }
    return 'Acest vin reflecta traditia vinicola a regiunii ' + reg + ', unde clima si solurile dau nastere unor vinuri cu caracter si personalitate.';
  }
  function createDescription(lang, p) {
    var labels = typeLabel[lang] || typeLabel.ro;
    var t = labels[p.type] || labels.fallback;
    var brand = p.brand || '';
    var region = p.region || 'Moldova';
    var grape = p.grape || (lang === 'en' ? 'a blend of local and international varieties' : lang === 'ru' ? 'купаж местных и международных сортов' : 'asamblu de soiuri locale si internationale');
    var abv = p.abv || 12;
    var base;
    if (lang === 'en') base = brand ? ('A ' + t + ' from ' + brand) : ('A ' + t);
    else if (lang === 'ru') base = brand ? (t.charAt(0).toUpperCase() + t.slice(1) + ' от ' + brand) : (t.charAt(0).toUpperCase() + t.slice(1));
    else base = brand ? (t.charAt(0).toUpperCase() + t.slice(1) + ' de la ' + brand) : (t.charAt(0).toUpperCase() + t.slice(1));
    var sentences = [];
    if (lang === 'en') {
      sentences.push(base + ', "' + p.name + '", produced in ' + region + '.');
      sentences.push('Made from ' + grape.toLowerCase() + ', with approximately ' + abv + '% alcohol.');
    } else if (lang === 'ru') {
      sentences.push(base + ', "' + p.name + '", произведено в регионе ' + region + '.');
      sentences.push('Сделано из ' + grape.toLowerCase() + ', с крепостью около ' + abv + '%.');
    } else {
      sentences.push(base + ', "' + p.name + '", produs in ' + region + '.');
      sentences.push('Creat din ' + grape.toLowerCase() + ', cu o tarie alcoolica de aproximativ ' + abv + '%.');
    }
    sentences.push(tastingNotes(lang, t, grape));
    sentences.push(story(lang, p, region));
    return sentences.join(' ');
  }
  window.getLocalizedProductDescription = function (product, lang) {
    if (!product) return '';
    var wanted = (lang || localStorage.getItem('aiwineLanguage') || 'ro');
    if (product.descriptionI18n && product.descriptionI18n[wanted]) return product.descriptionI18n[wanted];
    if (product.descriptionI18n && product.descriptionI18n.ro) return product.descriptionI18n.ro;
    return product.description || '';
  };
  window.WINE_PRODUCTS.forEach(function (p) {
    if (!p || !p.name) return;
    p.descriptionI18n = {
      ro: createDescription('ro', p),
      ru: createDescription('ru', p),
      en: createDescription('en', p)
    };
    p.description = p.descriptionI18n.ro;
  });
})();
