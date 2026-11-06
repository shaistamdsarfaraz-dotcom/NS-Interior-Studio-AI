(function () {
  var still = matchMedia('(prefers-reduced-motion: reduce)').matches;
 
  // scroll progress + reveal
  var bar = document.querySelector('.progress');
  addEventListener('scroll', function () {
    if (bar) bar.style.width = scrollY / (document.documentElement.scrollHeight - innerHeight) * 100 + '%';
  }, { passive: true });
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
  }, { threshold: .14 });
  document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });
 
  // cursor spotlight (+ light 3D tilt on the help cards and form)
  document.querySelectorAll('.info-card, .help-card, .contact-right').forEach(function (c) {
    var tilt = !still && !c.classList.contains('info-card');
    c.addEventListener('mousemove', function (e) {
      var r = c.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
      c.style.setProperty('--mx', x + 'px'); c.style.setProperty('--my', y + 'px');
      if (tilt) c.style.transform = 'perspective(900px) rotateY(' + ((x / r.width - .5) * (c.classList.contains('contact-right') ? 3 : 8)) + 'deg) rotateX(' + (-(y / r.height - .5) * (c.classList.contains('contact-right') ? 3 : 8)) + 'deg)' + (c.classList.contains('help-card') ? ' translateY(-6px)' : '');
    });
    c.addEventListener('mouseleave', function () { c.style.transform = ''; });
  });
  var sb = document.querySelector('.send-btn');
  if (sb) sb.addEventListener('mousemove', function (e) {
    var r = sb.getBoundingClientRect(); sb.style.setProperty('--bx', (e.clientX - r.left) + 'px'); sb.style.setProperty('--by', (e.clientY - r.top) + 'px');
  });
 
  // support topics (chips in the form + the four help cards) fill in the subject
  var subject = document.getElementById('subject');
  var chips = document.querySelectorAll('.topics button');
  function pick(topic) {
    chips.forEach(function (c) { c.classList.toggle('on', c.dataset.topic === topic); });
    subject.value = topic;
  }
  chips.forEach(function (c) { c.addEventListener('click', function () { pick(c.dataset.topic); }); });
  document.querySelectorAll('.help-card[data-topic]').forEach(function (c) {
    c.addEventListener('click', function () {
      pick(c.dataset.topic);
      document.getElementById('contactForm').scrollIntoView({ behavior: 'smooth', block: 'center' });
      setTimeout(function () { document.getElementById('message').focus(); }, 700);
    });
  });
  subject.addEventListener('input', function () {
    chips.forEach(function (c) { c.classList.toggle('on', c.dataset.topic === subject.value); });
  });
 
  // copy email
  var copy = document.getElementById('copyEmail');
  if (copy) copy.addEventListener('click', function (e) {
    e.preventDefault(); e.stopPropagation();
    var mail = copy.dataset.email;
    (navigator.clipboard ? navigator.clipboard.writeText(mail) : Promise.reject()).then(function () {
      copy.textContent = 'Copied ✓'; setTimeout(function () { copy.textContent = 'Copy'; }, 1800);
    }).catch(function () { copy.textContent = 'Press Ctrl+C'; });
  });
 
  // send message (same backend call as before)
  var form = document.getElementById('contactForm');
  var status = document.getElementById('formStatus');
  function say(text, cls) { status.textContent = text; status.className = cls; }
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var name = document.getElementById('name').value.trim();
    var email = document.getElementById('email').value.trim();
    var sub = subject.value.trim();
    var message = document.getElementById('message').value.trim();
    if (!name || !email || !sub || !message) { say('Please fill in all fields.', 'err'); return; }
    var btn = form.querySelector('.send-btn');
    btn.disabled = true; say('Sending message…', 'wait');
    fetch('/send-message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ name: name, email: email, subject: sub, message: message })
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          say(data.message, 'ok'); form.reset(); chips.forEach(function (c) { c.classList.remove('on'); });
          btn.classList.add('sent'); setTimeout(function () { btn.classList.remove('sent'); }, 900);
        } else say(data.message, 'err');
      })
      .catch(function (err) { console.error('Error:', err); say('Could not send message. Please try again.', 'err'); })
      .then(function () { btn.disabled = false; });
  });
})();