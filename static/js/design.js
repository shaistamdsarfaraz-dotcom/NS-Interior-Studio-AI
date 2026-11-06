/* Design Ideas: filters, gallery, lightbox, favourites, palettes.
   Needs design-data.js (styleGalleries + allPalettes) loaded first. */
(function () {
  var ROOMS = { 'living-room': 'Living Room', 'bedroom': 'Bedroom', 'kitchen': 'Kitchen', 'bathroom': 'Bathroom' };
  var STYLES = {
    Modern: 'Clean lines, neutral colours and minimal decor for a sleek look.',
    Minimalist: 'Less is more. Simple, functional and clutter-free spaces.',
    Scandinavian: 'Light colours, natural materials and cosy hygge vibes.',
    Luxury: 'Elegant, rich materials and sophisticated designs.'
  };
  var FEATURED = [
    { name: 'Warm Earth', colors: ['#7B4B2A', '#B5763F', '#D9B48F', '#4A3222'] },
    { name: 'Sage Green', colors: ['#3F5B45', '#6B8F71', '#A8C3A4', '#C9CBB8'] },
    { name: 'Ocean Blue', colors: ['#1B3A5C', '#2E6BA8', '#89B4D9', '#C7DDEC'] },
    { name: 'Terracotta Touch', colors: ['#8C3B23', '#C1613C', '#E0A17E', '#F0D3BC'] }
  ];
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var PAGE = 24;
  var state = { room: 'all', style: 'all', shown: PAGE, list: [] };
  var gallery = $('#gallery');
 
  function toast(t) {
    var el = $('#toast'); el.textContent = t; el.classList.add('show');
    clearTimeout(el._h); el._h = setTimeout(function () { el.classList.remove('show'); }, 1800);
  }
 
  /* ---------- data ---------- */
  var items = [];
  if (typeof styleGalleries === 'undefined') {
    gallery.innerHTML = '<p style="padding:40px;text-align:center">The image list was not found. Paste your <b>const styleGalleries = {...}</b> block into static/js/design-data.js.</p>';
    return;
  }
  var roomKeys = Object.keys(ROOMS), styleKeys = Object.keys(STYLES);
  for (var i = 0; i < 12; i++) {           // interleave so "All" shows a mix
    roomKeys.forEach(function (r) {
      styleKeys.forEach(function (s) {
        var url = styleGalleries[r] && styleGalleries[r][s] && styleGalleries[r][s][i];
        if (url) items.push({ room: r, style: s, url: url, broken: false });
      });
    });
  }
 
  /* ---------- favourites (same localStorage key as before) ---------- */
  function favs() { try { return JSON.parse(localStorage.getItem('favorites')) || []; } catch (e) { return []; } }
  function saveFavs(f) { localStorage.setItem('favorites', JSON.stringify(f)); updateFavCount(); }
  function isFav(url) { return favs().some(function (f) { return f.image === url; }); }
  function toggleFav(it) {
    var f = favs();
    if (isFav(it.url)) f = f.filter(function (x) { return x.image !== it.url; });
    else f.push({ title: it.style + ' · ' + ROOMS[it.room], image: it.url });
    saveFavs(f);
  }
  function updateFavCount() { $('#favCount').textContent = favs().length; }
 
  /* ---------- filtering + gallery ---------- */
  function filtered() {
    return items.filter(function (it) {
      return !it.broken && (state.room === 'all' || it.room === state.room) && (state.style === 'all' || it.style === state.style);
    });
  }
  function makeItem(it, n) {
    var d = document.createElement('div'); d.className = 'g-item'; d.style.setProperty('--d', n % 8);
    var img = document.createElement('img'); img.loading = 'lazy'; img.alt = it.style + ' ' + ROOMS[it.room] + ' interior'; img.src = it.url;
    img.onerror = function () { it.broken = true; d.remove(); count(); };
    var h = document.createElement('button'); h.className = 'heart' + (isFav(it.url) ? ' on' : ''); h.setAttribute('aria-label', 'Save to favourites');
    h.innerHTML = '<i class="fa-' + (isFav(it.url) ? 'solid' : 'regular') + ' fa-heart"></i>';
    h.onclick = function (e) { e.stopPropagation(); toggleFav(it); var on = isFav(it.url); h.classList.toggle('on', on); h.firstChild.className = 'fa-' + (on ? 'solid' : 'regular') + ' fa-heart'; };
    var cap = document.createElement('div'); cap.className = 'g-cap';
    cap.innerHTML = '<span class="tag">' + ROOMS[it.room] + '</span><span class="tag s">' + it.style + '</span>';
    d.appendChild(img); d.appendChild(cap); d.appendChild(h);
    d.onclick = function () { openLB(state.list.indexOf(it)); };
    return d;
  }
  function count() {
    var n = filtered().length;
    $('#count').textContent = 'Showing ' + n + ' design' + (n === 1 ? '' : 's');
    $('#empty').classList.toggle('show', n === 0);
    $('#moreWrap').style.display = n > state.shown ? '' : 'none';
  }
  function render(reset) {
    if (reset) { state.shown = PAGE; gallery.innerHTML = ''; }
    state.list = filtered();
    var from = gallery.children.length;
    state.list.slice(from, state.shown).forEach(function (it, n) { gallery.appendChild(makeItem(it, n)); });
    var banner = $('#styleBanner');
    if (state.style !== 'all') {
      $('#bannerTitle').innerHTML = state.style + (state.room !== 'all' ? ' <em>· ' + ROOMS[state.room] + '</em>' : '');
      $('#bannerDesc').textContent = STYLES[state.style];
      $('#bannerUse').href = studioLink(state.style);
      banner.classList.add('show');
    } else banner.classList.remove('show');
    $('#resetBtn').style.display = (state.room !== 'all' || state.style !== 'all') ? '' : 'none';
    count();
  }
  function studioLink(style) { return (window.STUDIO_URL || '/studio') + (window.STUDIO_URL === '/studio' ? '?style=' + encodeURIComponent(style) : ''); }
 
  $$('.chip[data-room]').forEach(function (c) { c.onclick = function () { state.room = c.dataset.room; $$('.chip[data-room]').forEach(function (x) { x.classList.toggle('active', x === c); }); render(true); }; });
  $$('.chip[data-style]').forEach(function (c) { c.onclick = function () { state.style = c.dataset.style; $$('.chip[data-style]').forEach(function (x) { x.classList.toggle('active', x === c); }); render(true); }; });
  $('#resetBtn').onclick = function () { $('.chip[data-room="all"]').click(); $('.chip[data-style="all"]').click(); };
  $('#moreBtn').onclick = function () { state.shown += PAGE; render(false); };
 
  /* ---------- lightbox ---------- */
  var lb = $('#lb'), cur = 0;
  function openLB(i) {
    if (i < 0 || !state.list.length) return;
    cur = (i + state.list.length) % state.list.length;
    var it = state.list[cur];
    $('#lbImg').src = it.url; $('#lbImg').alt = it.style + ' ' + ROOMS[it.room];
    $('#lbTags').innerHTML = '<span class="tag">' + ROOMS[it.room] + '</span><span class="tag s">' + it.style + '</span>';
    $('#lbDesc').textContent = STYLES[it.style];
    $('#lbUse').href = studioLink(it.style);
    var f = $('#lbFav'); f.classList.toggle('on', isFav(it.url)); f.firstElementChild.className = 'fa-' + (isFav(it.url) ? 'solid' : 'regular') + ' fa-heart';
    lb.classList.add('show'); document.body.style.overflow = 'hidden';
  }
  function closeLB() { lb.classList.remove('show'); document.body.style.overflow = ''; }
  $('#lbFav').onclick = function () { var it = state.list[cur]; toggleFav(it); openLB(cur); $$('.g-item').forEach(function (g, k) { var h = g.querySelector('.heart'), t = state.list[k]; if (t) { var on = isFav(t.url); h.classList.toggle('on', on); h.firstChild.className = 'fa-' + (on ? 'solid' : 'regular') + ' fa-heart'; } }); };
  $('#lbPrev').onclick = function () { openLB(cur - 1); }; $('#lbNext').onclick = function () { openLB(cur + 1); }; $('#lbClose').onclick = closeLB;
  lb.onclick = function (e) { if (e.target === lb) closeLB(); };
 
  /* ---------- favourites modal ---------- */
  function renderFavs() {
    var g = $('#favGrid'), f = favs(); g.innerHTML = '';
    if (!f.length) { g.innerHTML = '<div class="fav-empty"><i class="fa-regular fa-heart"></i>No favourites yet. Tap the heart on any design to save it here.</div>'; return; }
    f.forEach(function (x) {
      var d = document.createElement('div'); d.className = 'fav-item';
      var im = document.createElement('img'); im.src = x.image; im.alt = x.title;
      var t = document.createElement('div'); t.className = 'fav-title'; t.textContent = x.title;
      var b = document.createElement('button'); b.className = 'rm'; b.setAttribute('aria-label', 'Remove'); b.innerHTML = '<i class="fa-solid fa-xmark"></i>';
      b.onclick = function () { saveFavs(favs().filter(function (y) { return y.image !== x.image; })); renderFavs(); render(true); };
      d.appendChild(im); d.appendChild(t); d.appendChild(b); g.appendChild(d);
    });
  }
  function modal(id, open) { $(id).classList.toggle('show', open); document.body.style.overflow = open ? 'hidden' : ''; }
  $('#favBtn').onclick = function () { renderFavs(); modal('#favModal', true); };
 
  /* ---------- palettes ---------- */
  function paletteCard(p) {
    var c = document.createElement('div'); c.className = 'palette-card';
    c.innerHTML = '<div class="palette-name"></div><div class="swatch-row"></div>';
    c.firstChild.textContent = p.name;
    p.colors.forEach(function (hex) {
      var b = document.createElement('button'); b.style.background = hex; b.textContent = hex; b.title = 'Copy ' + hex; b.setAttribute('aria-label', 'Copy ' + hex);
      b.onclick = function () { (navigator.clipboard ? navigator.clipboard.writeText(hex) : Promise.reject()).then(function () { toast('Copied ' + hex); }).catch(function () { toast(hex); }); };
      c.lastChild.appendChild(b);
    });
    return c;
  }
  FEATURED.forEach(function (p) { $('#featured').appendChild(paletteCard(p)); });
  $('#allPalBtn').onclick = function () {
    var g = $('#allPalettes'); g.innerHTML = '';
    (typeof allPalettes !== 'undefined' ? allPalettes : FEATURED).forEach(function (p) { g.appendChild(paletteCard(p)); });
    modal('#palModal', true);
  };
  $$('[data-close]').forEach(function (b) { b.onclick = function () { modal('#' + b.dataset.close, false); }; });
  $$('.modal-overlay').forEach(function (m) { m.onclick = function (e) { if (e.target === m) modal('#' + m.id, false); }; });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeLB(); modal('#favModal', false); modal('#palModal', false); }
    if (lb.classList.contains('show')) { if (e.key === 'ArrowRight') openLB(cur + 1); if (e.key === 'ArrowLeft') openLB(cur - 1); }
  });
 
  /* ---------- slideshow, progress, reveal, start-up ---------- */
  var slides = $$('.slideshow .slide'), si = 0;
  if (slides.length > 1) setInterval(function () { slides[si].classList.remove('active'); si = (si + 1) % slides.length; slides[si].classList.add('active'); }, 4500);
  var bar = $('.progress');
  addEventListener('scroll', function () { bar.style.width = scrollY / (document.documentElement.scrollHeight - innerHeight) * 100 + '%'; }, { passive: true });
  var io = new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } }); }, { threshold: .14 });
  $$('.reveal').forEach(function (el) { io.observe(el); });
 
  var q = new URLSearchParams(location.search);   // e.g. /design-ideas?style=Modern&room=bedroom
  var qs = q.get('style'), qr = q.get('room');
  if (qs) { var cs = $('.chip[data-style="' + qs + '"]'); if (cs) { state.style = qs; $$('.chip[data-style]').forEach(function (x) { x.classList.toggle('active', x === cs); }); } }
  if (qr) { var cr = $('.chip[data-room="' + qr + '"]'); if (cr) { state.room = qr; $$('.chip[data-room]').forEach(function (x) { x.classList.toggle('active', x === cr); }); } }
  updateFavCount();
  render(true);
})();