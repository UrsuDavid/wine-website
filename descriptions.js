// Runtime description enhancer for Aiwine products.
// Generates a richer Romanian description for each product using its metadata.
(function () {
  if (!Array.isArray(window.WINE_PRODUCTS)) return;
  var typeLabel = {
    red: 'vin roșu',
    white: 'vin alb',
    sparkling: 'vin spumant',
    rose: 'vin rosé'
  };
  function tastingNotes(p, t, grape) {
    var g = (grape || '').toLowerCase();
    if (t === 'vin spumant') {
      return 'Un spumant cu perlaj fin, note de fructe albe și citrice, perfect pentru momente festive și aperitive lejere.';
    }
    if (t === 'vin rosé') {
      return 'Un rosé proaspăt, cu arome de fructe roșii de pădure și citrice, echilibrat între prospețime și eleganță.';
    }
    if (t === 'vin alb') {
      if (g.indexOf('sauvignon') !== -1 || g.indexOf('viorica') !== -1) {
        return 'Un alb aromatic, cu note de flori albe, ierburi fine și fructe exotice, cu aciditate crocantă.';
      }
      if (g.indexOf('chardonnay') !== -1) {
        return 'Un alb catifelat, cu note de fructe galbene coapte, vanilie discretă și o structură echilibrată.';
      }
      return 'Un alb curat și expresiv, cu note de flori de viță, fructe albe și citrice, ideal alături de pește și salate.';
    }
    // red
    if (g.indexOf('saperavi') !== -1 || g.indexOf('feteasca neagra') !== -1 || g.indexOf('rara neagra') !== -1) {
      return 'Un roșu intens, cu nuanțe de fructe negre coapte, condimente fine și taninuri coapte, specific terroir-ului din Moldova.';
    }
    if (g.indexOf('pinot noir') !== -1) {
      return 'Un roșu elegant, cu note de fructe roșii, condimente delicate și o textură suplă, ușor de băut.';
    }
    return 'Un roșu generos, cu arome de prune, vișine și condimente, structură bună și postgust persistent.';
  }
  function story(p, region) {
    var brand = p.brand || '';
    var reg = region || 'Moldova';
    if (brand) {
      return 'Eticheta face parte din selecția ' + brand + ', o cramă care îmbină tradiția locală cu tehnologii moderne, reprezentativă pentru ' + reg + '.';
    }
    return 'Acest vin reflectă tradiția vinicolă a regiunii ' + reg + ', unde clima și solurile dau naștere unor vinuri cu caracter și personalitate.';
  }
  window.WINE_PRODUCTS.forEach(function (p) {
    if (!p || !p.name) return;
    var t = typeLabel[p.type] || 'vin';
    var brand = p.brand || '';
    var region = p.region || 'Moldova';
    var grape = p.grape || 'asamblu de soiuri locale și internaționale';
    var abv = p.abv || 12;
    var base = brand ? (t.charAt(0).toUpperCase() + t.slice(1) + ' de la ' + brand) : (t.charAt(0).toUpperCase() + t.slice(1));
    var sentences = [];
    sentences.push(base + ', „' + p.name + '”, produs în ' + region + '.');
    sentences.push('Creat din ' + grape.toLowerCase() + ', cu o tărie alcoolică de aproximativ ' + abv + '%.');
    sentences.push(tastingNotes(p, t, grape));
    sentences.push(story(p, region));
    p.description = sentences.join(' ');
  });
})();
