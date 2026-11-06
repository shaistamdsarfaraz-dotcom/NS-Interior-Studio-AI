/* Lumi, the little lamp chatbot. Keyword-based (no AI / no API keys). */
(function () {
  // ---- the mascot: one SVG, injected wherever needed ----
  function lumi(cls) {
    return '<svg class="lumi ' + (cls || '') + '" viewBox="0 0 120 140" aria-hidden="true">' +
      '<ellipse cx="60" cy="132" rx="30" ry="5" fill="#000" opacity=".22"/>' +
      '<ellipse cx="49" cy="127" rx="10" ry="5" fill="#29211D"/><ellipse cx="71" cy="127" rx="10" ry="5" fill="#29211D"/>' +
      '<rect x="42" y="98" width="36" height="28" rx="14" fill="#7A5C3C"/>' +
      '<circle cx="52" cy="112" r="2.6" fill="#F6F1E9"/><circle cx="68" cy="112" r="2.6" fill="#F6F1E9"/>' +
      '<path d="M35 98 Q22 100 19 111" stroke="#F6F1E9" stroke-width="7" stroke-linecap="round" fill="none"/>' +
      '<path class="arm-r" d="M85 98 Q98 94 102 82" stroke="#F6F1E9" stroke-width="7" stroke-linecap="round" fill="none"/>' +
      '<circle cx="60" cy="75" r="30" fill="#F6F1E9"/>' +
      '<path d="M32 60 L48 20 H72 L88 60 Z" fill="#AD8964"/><path d="M32 60 H88 L86 66 H34 Z" fill="#7A5C3C"/>' +
      '<path d="M54 24 L49 56" stroke="#fff" opacity=".3" stroke-width="3.5" stroke-linecap="round"/>' +
      '<ellipse class="eye" cx="49" cy="78" rx="3.8" ry="4.8" fill="#29211D"/><ellipse class="eye" cx="71" cy="78" rx="3.8" ry="4.8" fill="#29211D"/>' +
      '<circle cx="50.3" cy="76.2" r="1.3" fill="#fff"/><circle cx="72.3" cy="76.2" r="1.3" fill="#fff"/>' +
      '<circle cx="40" cy="87" r="5.2" fill="#E8A598" opacity=".65"/><circle cx="80" cy="87" r="5.2" fill="#E8A598" opacity=".65"/>' +
      '<path class="mouth" d="M53 87 Q60 94 67 87" stroke="#29211D" stroke-width="2.6" fill="none" stroke-linecap="round"/>' +
      '<ellipse class="mouth-open" cx="60" cy="89" rx="4.6" ry="4.2" fill="#29211D"/>' +
      '<path class="spark" d="M101 28 l2.6 6.4 6.4 2.6 -6.4 2.6 -2.6 6.4 -2.6 -6.4 -6.4 -2.6 6.4 -2.6z" fill="#89947A"/></svg>';
  }
  document.querySelectorAll('[data-lumi]').forEach(function (el) { el.innerHTML = lumi(); });
 
  // ---- Lumi is a website guide, not a general design-advice bot ----
  // Each response points the visitor to the NS Design AI feature that handles it.
  var R = [
    [/\b(hi+|hello|hey|hola|salam|assalam\w*)\b/, ["Hi! I'm Lumi, your NS Design AI guide. I can show you where to find room analysis, Design Ideas, budget planning, Gallery and more. What would you like to open?"]],
    [/(thank|thx|shukriya|jazak)/, ["You're welcome! Tell me what you want to do next and I'll guide you to the right page."]],
    [/\b(bye|goodbye|see you)\b/, ["Bye! Come back whenever you need help finding something in NS Design AI."]],
    [/(who are you|your name|what are you)/, ["I'm Lumi, the NS Design AI website guide. I help you find the right feature and explain how to use it."]],
    [/(free|\bpay\b|paid|payment|charge|charges|\bfees?\b|subscription|premium)/, ["For information about using the website and its available features, please continue through the NS Design AI pages. I can guide you to Studio, Budget Planner, Design Ideas or Gallery."]],

    // Budget-range questions must be checked before the general room/photo rule.
    // This catches both digits and words, including questions such as
    // “Can I renovate my room within fifteen to twenty thousand rupees?”
    [/((15|fifteen)\s*(000|thousand)|20\s*(000|thousand)|twenty\s*thousand|(50|fifty)\s*(000|thousand)|1\s*lakh|one\s*lakh|100\s*000|one\s*hundred\s*thousand|budget).*(room|space|renovat|redesign|photo|picture|rupee|inr|cost|money)|((room|space|renovat|redesign|photo|picture).*(15|fifteen|20|twenty|50|fifty|1\s*lakh|one\s*lakh|budget))/, ["To check whether your current room can be redesigned within a budget such as ₹15,000–₹20,000 or ₹50,000–₹1,00,000, open <a href='/studio'><b>AI Design Studio</b></a>. Upload your picture, choose the matching budget range, and click Analyse &amp; Redesign. Your result will show the planned estimate and shopping items."]],

    // Room photo, regeneration, room cost and selected budget all belong in Studio.
    [/(upload|photo|picture|image|analyse|analyze|analysis|regenerate|redesign|before|after|transform|existing room|current room|renovat|renovation)/, ["To analyse your current room, regenerate its interior and see the estimated renovation cost, go to <a href='/studio'><b>AI Design Studio</b></a>. Upload your room photo there, choose the room type, style and budget range, then click Analyse &amp; Redesign."]],

    // Style questions get a direct answer with the four available styles.
    // Keep this before the broad design and fallback rules so “suggest me some styles”
    // does not produce an unrelated generic response.
    [/\b(what|which|show|suggest|recommend|tell|give|available|different)?\s*(design\s*)?styles?\b/, ["We currently have four design styles: <b>Modern</b>, <b>Minimalist</b>, <b>Scandinavian</b> and <b>Luxury</b>. You can view and compare them on the <a href='/design-ideas'><b>Design Ideas</b></a> page. If you want one of these styles applied to your own uploaded room, use the <a href='/studio'><b>AI Design Studio</b></a>."]],

    // Design requests should go to the curated Design Ideas page.
    [/(suggest|recommend|show|give|find|choose|inspiration|idea|ideas|palette|colour|color|paint|wall|modern|minimal|scandi|scandinavian|luxury|luxurious|contemporary|traditional|accent).*(design|style|room|colour|color|colour palette|color palette|palette|interior|look)|(?:design|style|room|colour|color|colour palette|color palette|palette|interior|look).*(suggest|recommend|show|idea|modern|minimal|scandi|scandinavian|luxury|luxurious)/, ["For ready-made interior inspiration, styles and colour palettes, go to <a href='/design-ideas'><b>Design Ideas</b></a>. You can browse the available concepts there and choose the look you like."]],
    [/(design ideas|inspiration|inspire|browse designs|see designs|recommended designs|recommended palettes)/, ["You can browse recommended interiors and colour palettes on the <a href='/design-ideas'><b>Design Ideas</b></a> page."]],

    // Budget Planner is for planning and shopping allocations.
    [/(budget planner|plan.*budget|budget.*plan|shopping budget|shopping list|buy|buying list|items|furniture cost|cost breakdown|allocation)/, ["For a detailed budget plan, item allocations and shopping links, open the <a href='/budget-planner'><b>Budget Planner</b></a>. For a photo-based room estimate, use <a href='/studio'><b>AI Design Studio</b></a> first."]],
    [/(cost|price|estimate|estimated|how much|rupee|rupees|inr|afford|money).*(photo|picture|room|renovat|redesign|current|existing)/, ["To get a room-specific estimate from your uploaded picture, go to <a href='/studio'><b>AI Design Studio</b></a>. To organise the resulting items and shopping amounts, use the <a href='/budget-planner'><b>Budget Planner</b></a>."]],

    [/(gallery|save|saved|favour?ite|previous design|my design|before after)/, ["Open <a href='/gallery'><b>My Gallery</b></a> to view saved before-and-after designs. You need to be logged in for saved designs to appear there."]],
    [/(login|log in|register|sign up|account|password|forgot)/, ["Use <a href='/register'><b>Register</b></a> to create an account or log in to access your Studio results, Gallery and saved designs."]],
    [/(contact|support|human|instagram|team|founder|about)/, ["For the team, mission and contact information, open the <a href='/about'><b>About</b></a> page or visit <a href='/contact'><b>Contact</b></a>."]],
    [/(how.*use|where.*go|what.*do|help|feature|page|website|navigate|navigation)/, ["I can guide you: use <a href='/studio'><b>AI Design Studio</b></a> for photo analysis and redesign, <a href='/design-ideas'><b>Design Ideas</b></a> for inspiration, <a href='/budget-planner'><b>Budget Planner</b></a> for costs, and <a href='/gallery'><b>My Gallery</b></a> for saved designs."]]
  ];
  var FALLBACK = "I can guide you to the right NS Design AI feature. Use <a href='/studio'><b>AI Design Studio</b></a> for uploading, analysing and regenerating a room; <a href='/design-ideas'><b>Design Ideas</b></a> for suggested designs and palettes; <a href='/budget-planner'><b>Budget Planner</b></a> for costs; or <a href='/gallery'><b>My Gallery</b></a> for saved results.";
  function replyFor(text) {
    var t = (text || '').toLowerCase();
    for (var i = 0; i < R.length; i++) if (R[i][0].test(t)) { var a = R[i][1]; return a[Math.floor(Math.random() * a.length)]; }
    return FALLBACK;
  }
  if (typeof window !== 'undefined') window.lumiReply = replyFor;
 
  // ---- chat UI ----
  var box = document.getElementById('chatbotMessages');
  var win = document.getElementById('chatbotWindow');
  var input = document.getElementById('chatbotInput');
  var busy = false;
 
  function esc(s) { return s.replace(/[&<>"']/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
  function add(who, html) {
    if (!box) return null;
    var m = document.createElement('div'); m.className = 'msg ' + who;
    m.innerHTML = (who === 'bot' ? '<div class="av">' + lumi('mini') + '</div>' : '') + '<div class="bubble">' + html + '</div>';
    box.appendChild(m); box.scrollTop = box.scrollHeight; return m;
  }
  function talk(on) { document.querySelectorAll('.cb-avatar .lumi, .chatbot-bubble .lumi').forEach(function (s) { s.classList.toggle('talking', on); }); }
 
  window.toggleChatbot = function () {
    if (!win) return;
    var open = win.classList.toggle('open');
    var w = document.getElementById('chatbotWidget'); if (w) w.classList.toggle('is-open', open);
    if (open && input) setTimeout(function () { input.focus(); }, 350);
  };
  window.sendChatMessage = function () {
    if (!input || busy) return;
    var text = input.value.trim(); if (!text) return;
    add('user', esc(text)); input.value = ''; busy = true;
    var typing = add('bot', '<i></i><i></i><i></i>'); if (typing) typing.classList.add('typing');
    talk(true);
    var answer = replyFor(text);
    setTimeout(function () {
      if (typing) typing.remove();
      add('bot', answer); talk(false); busy = false;
    }, 650 + Math.min(answer.length * 6, 900));
  };
 
  // quick-reply chips (capture phase, so they work on every page without extra code)
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.chat-chips button[data-q]');
    if (!b) return;
    e.stopPropagation(); e.preventDefault();
    if (!win.classList.contains('open')) window.toggleChatbot();
    input.value = b.dataset.q; window.sendChatMessage();
  }, true);
 
  add('bot', "Hi, I'm <b>Lumi</b>! 💡 Ask me about designing a living room, bedroom, kitchen or bathroom, colour ideas, budgets, or how to use the studio.");
})();