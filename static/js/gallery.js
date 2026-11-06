(function () {
  var still = matchMedia('(prefers-reduced-motion: reduce)').matches;
 
  // show costs like "₹3,00,000" (your page printed the raw number); leaves the text alone if it isn't a number
  document.querySelectorAll('.design-budget').forEach(function (el) {
    var n = Number(String(el.textContent).replace(/[₹,\s]/g, ''));
    if (isFinite(n) && n > 0) el.textContent = '₹' + Math.round(n).toLocaleString('en-IN');
  });
 
  // reveal on scroll
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
  }, { threshold: .12 });
  document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });
 
  // 3D tilt + cursor light on the cards
  if (!still) document.querySelectorAll('.design-card').forEach(function (c) {
    c.addEventListener('mousemove', function (e) {
      var r = c.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
      c.style.setProperty('--mx', x + 'px'); c.style.setProperty('--my', y + 'px');
      c.style.transform = 'perspective(1000px) rotateY(' + ((x / r.width - .5) * 4) + 'deg) rotateX(' + (-(y / r.height - .5) * 4) + 'deg) translateY(-6px)';
    });
    c.addEventListener('mouseleave', function () { c.style.transform = ''; });
  });
})();
 
/* ===== View Design opens inside the page, with a close button ===== */
(function () {
  var viewer, lastFocus;
  function build() {
    viewer = document.createElement('div');
    viewer.className = 'viewer'; viewer.setAttribute('role', 'dialog'); viewer.setAttribute('aria-modal', 'true'); viewer.setAttribute('aria-label', 'Design preview');
    viewer.innerHTML = '<button type="button" class="viewer-close" aria-label="Close preview"><i class="fa-solid fa-xmark"></i></button>' +
      '<div class="viewer-box"><div class="viewer-head"></div><div class="viewer-pair"></div><p class="viewer-note"></p><p class="viewer-hint">Press Esc or click outside to close</p></div>';
    document.body.appendChild(viewer);
    viewer.addEventListener('click', function (e) {
      if (e.target === viewer || e.target.classList.contains('viewer-box') || e.target.closest('.viewer-close')) close();
    });
  }
  function pane(src, label, cls, alt) {
    var d = document.createElement('div'); d.className = 'viewer-pane ' + cls;
    var t = document.createElement('span'); t.className = 'tag'; t.textContent = label;
    var i = document.createElement('img'); i.src = src; i.alt = alt;
    d.appendChild(t); d.appendChild(i); return d;
  }
  function open(card) {
    if (!viewer) build();
    var imgs = card.querySelectorAll('.comparison-image img');
    var room = card.querySelector('.design-info h2').textContent.trim();
    var date = (card.querySelector('.design-date') || {}).textContent || '';
    var cost = (card.querySelector('.design-budget') || {}).textContent || '';
    var head = viewer.querySelector('.viewer-head'), pair = viewer.querySelector('.viewer-pair'), note = viewer.querySelector('.viewer-note');
    head.innerHTML = ''; pair.innerHTML = ''; note.textContent = '';
    var h = document.createElement('h3'); h.textContent = room; head.appendChild(h);
    if (date.trim()) { var sd = document.createElement('span'); sd.textContent = date.trim(); head.appendChild(sd); }
    if (cost.trim()) { var sc = document.createElement('span'); sc.className = 'cost'; sc.textContent = cost.trim(); head.appendChild(sc); }
    pair.appendChild(pane(imgs[0].src, 'BEFORE', 'before', 'Original ' + room));
    if (imgs[1]) { pair.classList.remove('single'); pair.appendChild(pane(imgs[1].src, 'AI CONCEPT', 'after', 'AI redesigned ' + room)); }
    else { pair.classList.add('single'); note.textContent = 'The AI redesign could not be created for this room.'; }
    lastFocus = document.activeElement;
    viewer.classList.add('show'); document.body.classList.add('viewer-open');
    viewer.querySelector('.viewer-close').focus();
  }
  function close() {
    if (!viewer) return;
    viewer.classList.remove('show'); document.body.classList.remove('viewer-open');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  document.addEventListener('click', function (e) {
    var trigger = e.target.closest('a[data-view], .comparison-image img');
    if (!trigger) return;
    var card = trigger.closest('.design-card'); if (!card) return;
    e.preventDefault(); e.stopPropagation(); open(card);
  }, true);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') close();
    if (e.key === 'Enter' && e.target.matches && e.target.matches('.comparison-image img')) open(e.target.closest('.design-card'));
  });
  document.querySelectorAll('.comparison-image img').forEach(function (i) { i.setAttribute('tabindex', '0'); i.setAttribute('role', 'button'); i.setAttribute('aria-label', 'View full size'); });
})();