// Look only: reveal on scroll. The form itself (including the photo auto-submit) works exactly as before.
(function () {
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
  }, { threshold: .1 });
  document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });
})();