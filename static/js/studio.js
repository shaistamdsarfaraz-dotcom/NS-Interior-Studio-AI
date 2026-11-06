document.addEventListener('DOMContentLoaded', function () {
  var $ = function (id) { return document.getElementById(id); };
  var form = $('uploadForm'), input = $('roomPhoto'), box = $('uploadBox'), preview = $('uploadPreview');
  var meta = $('fileMeta'), fileName = $('fileName'), clearBtn = $('clearFile'), button = $('analyzeButton');
  var busy = $('busy'), busyImg = $('busyImg'), busyStep = $('busyStep'), busyBar = $('busyBar');
  var MAX = 10 * 1024 * 1024, OK = ['image/jpeg', 'image/png', 'image/webp'];
  var still = matchMedia('(prefers-reduced-motion: reduce)').matches;
 
  function toast(msg) {
    var t = $('toast'); t.textContent = msg; t.classList.add('show');
    clearTimeout(t._h); t._h = setTimeout(function () { t.classList.remove('show'); }, 3600);
  }
 
  /* ---- photo chosen (click OR drag & drop) ---- */
  function showFile(file) {
    if (!file) return false;
    if (OK.indexOf(file.type) === -1) { toast('Please choose a JPG, PNG or WEBP image.'); return false; }
    if (file.size > MAX) { toast('Please choose an image smaller than 10 MB.'); return false; }
    var r = new FileReader();
    r.onload = function (e) {
      preview.src = e.target.result; busyImg.src = e.target.result;
      box.classList.add('has-file'); meta.classList.add('visible');
      fileName.textContent = file.name + '  ·  ' + (file.size / 1048576).toFixed(1) + ' MB';
    };
    r.readAsDataURL(file);
    return true;
  }
  function clearFile() { input.value = ''; preview.removeAttribute('src'); box.classList.remove('has-file'); meta.classList.remove('visible'); }
  input.addEventListener('change', function () { if (input.files[0] && !showFile(input.files[0])) clearFile(); });
  ['dragenter', 'dragover'].forEach(function (n) { box.addEventListener(n, function (e) { e.preventDefault(); box.classList.add('is-dragging'); }); });
  ['dragleave', 'drop'].forEach(function (n) { box.addEventListener(n, function (e) { e.preventDefault(); box.classList.remove('is-dragging'); }); });
  box.addEventListener('drop', function (e) {
    var f = e.dataTransfer.files[0];
    if (f && showFile(f)) input.files = e.dataTransfer.files;   // attach the dropped file to the form (it was only previewed before)
  });
  clearBtn.addEventListener('click', clearFile);
 
  /* ---- budget picker: ₹10,000 to ₹1,00,000 ---- */
  var cost = $('estimatedCost');
  var radios = form.querySelectorAll('input[name="budget_range"]');
  function words(n) {
    if (n >= 100000) return '₹' + (n / 100000).toFixed(2).replace(/\.00$/, '') + ' lakh';
    return '₹' + Number(n).toLocaleString('en-IN');
  }
  function indian(n) { return '₹' + Number(n).toLocaleString('en-IN'); }
  function pos(n) { return Math.max(0, Math.min(100, (Number(n) - 10000) / 90000 * 100)); }   // ₹10,000 .. ₹1,00,000
  radios.forEach(function (r) {
    var p = r.value.split('-').map(Number), tile = r.closest('.btile');
    tile.querySelector('.bt-main').textContent = '₹' + Number(p[0]).toLocaleString('en-IN') + ' – ₹' + Number(p[1]).toLocaleString('en-IN');
    tile.querySelector('.bt-sub').textContent = 'budget range';
  });
  function syncBudget() {
    var r = form.querySelector('input[name="budget_range"]:checked'); if (!r) return;
    var p = r.value.split('-').map(Number);
    cost.value = p[1] || p[0] || 300000;
    var ro = $('budgetReadout'), nx = ro.cloneNode(false);
    nx.textContent = words(p[0]) + ' – ' + words(p[1]); ro.parentNode.replaceChild(nx, ro);   // re-trigger the small slide-in
    $('budgetWords').textContent = indian(p[0]) + ' – ' + indian(p[1]);
    var l = pos(p[0]), h = pos(p[1]); var f = $('scaleFill'); f.style.left = l + '%'; f.style.width = Math.max(2.5, h - l) + '%';
  }
  radios.forEach(function (r) { r.addEventListener('change', syncBudget); });
  syncBudget();
 
  /* ---- ?style=Luxury&room=Bedroom links from Design Ideas / Home ---- */
  var q = new URLSearchParams(location.search);
  [['style', 'design_style'], ['room', 'room_type']].forEach(function (pair) {
    var v = q.get(pair[0]); if (!v) return;
    var el = form.querySelector('input[name="' + pair[1] + '"][value="' + v.replace(/"/g, '') + '"]');
    if (el) el.checked = true;
  });
 
  /* ---- progress overlay ---- */
  var STEPS = ['Reading the colours of your room…', 'Detecting furniture and objects…', 'Checking light, layout and materials…',
    'Planning your colour palette…', 'Generating your redesigned room…', 'Almost there, adding the finishing touches…'];
  var stepTimer, pct;
  function startBusy() {
    busy.classList.add('show'); document.body.style.overflow = 'hidden'; var i = 0; pct = 6;
    busyStep.textContent = STEPS[0]; busyBar.style.width = pct + '%';
    stepTimer = setInterval(function () {
      i = Math.min(i + 1, STEPS.length - 1); busyStep.textContent = STEPS[i];
      pct = Math.min(pct + 14, 92); busyBar.style.width = pct + '%';
    }, 4500);
  }
  function stopBusy() { clearInterval(stepTimer); busy.classList.remove('show'); document.body.style.overflow = ''; button.disabled = false; }
 
  /* ---- submit: same /upload route, result page is shown in place ---- */
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!input.files.length) { toast('Please choose a room photo first.'); box.scrollIntoView({ behavior: 'smooth', block: 'center' }); return; }
    syncBudget(); button.disabled = true; startBusy();
    var ctl = new AbortController(), killer = setTimeout(function () { ctl.abort(); }, 240000);
    fetch('/upload', { method: 'POST', body: new FormData(form), signal: ctl.signal })
      .then(function (r) {
        if (r.ok) return r.text().then(function (html) { document.open(); document.write(html); document.close(); });
        return r.json().catch(function () { return {}; }).then(function (d) { throw new Error(d.message || 'Upload failed. Please try again.'); });
      })
      .catch(function (err) {
        console.error(err); stopBusy();
        toast(err.name === 'AbortError' ? 'This is taking too long. Please try again.' : (err.message || 'Connection error. Please try again.'));
      })
      .then(function () { clearTimeout(killer); });
  });
 
  /* ---- motion: reveal + collage tilt ---- */
  var io = new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } }); }, { threshold: .12 });
  document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });
  var col = document.querySelector('.collage');
  if (col && !still) {
    col.addEventListener('mousemove', function (e) {
      var r = col.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
      col.querySelector('.c-before').style.transform = 'rotate(-6deg) translate(' + (x * -22) + 'px,' + (y * -16) + 'px)';
      col.querySelector('.c-after').style.transform = 'rotate(4deg) translate(' + (x * 26) + 'px,' + (y * 18) + 'px)';
    });
    col.addEventListener('mouseleave', function () {
      col.querySelector('.c-before').style.transform = ''; col.querySelector('.c-after').style.transform = '';
    });
  }
});
