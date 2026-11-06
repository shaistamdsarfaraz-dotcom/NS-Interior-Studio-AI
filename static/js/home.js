(function(){
  const still=matchMedia('(prefers-reduced-motion: reduce)').matches;
 
  /* hero slideshow: the four allowed rooms */
  const slides=[...document.querySelectorAll('.hero-slide')];
  const ticks=[...document.querySelectorAll('.hero-ticks button')];
  const label=document.getElementById('hero-name');
  let cur=0,timer;
  function show(i){
    cur=(i+slides.length)%slides.length;
    slides.forEach((s,k)=>s.classList.toggle('active',k===cur));
    ticks.forEach((t,k)=>{t.classList.remove('on');void t.offsetWidth;t.classList.toggle('on',k===cur)});
    label.innerHTML='<b>0'+(cur+1)+'</b>'+slides[cur].dataset.room;
    clearTimeout(timer);timer=setTimeout(()=>show(cur+1),6000);
  }
  ticks.forEach((t,k)=>t.addEventListener('click',()=>show(k)));
  if(slides.length)show(0);
 
  /* hero mouse parallax + scroll depth */
  const bg=document.querySelector('.hero-bg'),content=document.querySelector('.hero-content');
  addEventListener('mousemove',e=>{
    if(still||scrollY>innerHeight)return;
    const x=e.clientX/innerWidth-.5,y=e.clientY/innerHeight-.5;
    bg.style.transform='translate('+(x*-26)+'px,'+(y*-18)+'px)';
    content.style.transform='translate('+(x*14)+'px,'+(y*10)+'px)';
  });
 
  /* progress bar */
  const bar=document.querySelector('.progress');
  addEventListener('scroll',()=>{bar.style.width=scrollY/(document.documentElement.scrollHeight-innerHeight)*100+'%'},{passive:true});
 
  /* reveals */
  const io=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target)}}),{threshold:.14});
  document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
 
  /* 3D tilt + spotlight on capability cards */
  if(!still)document.querySelectorAll('.cap').forEach(c=>{
    c.addEventListener('mousemove',e=>{
      const r=c.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;
      c.style.setProperty('--mx',x+'px');c.style.setProperty('--my',y+'px');
      c.style.transform='perspective(900px) rotateY('+((x/r.width-.5)*7)+'deg) rotateX('+(-(y/r.height-.5)*7)+'deg) translateY(-6px)';
    });
    c.addEventListener('mouseleave',()=>c.style.transform='');
  });
 
  /* before/after slider with room tabs (images are the project's own AI concept renders) */
  const rooms={
    'Living Room':['living-room-before.jpeg','living-room-after.png'],
    'Bedroom':['bedroom-before.jpeg','bedroom-after.png'],
    'Kitchen':['kitchen-before.jpeg','kitchen-after.png'],
    'Bathroom':['Bathroom-before.jpeg','Bathroom-after.png']
  };
  const cmp=document.getElementById('compare');
  if(cmp){
    const base=cmp.dataset.base,imgB=cmp.querySelector('.before'),imgA=cmp.querySelector('.after');
    function setPos(p){cmp.style.setProperty('--pos',Math.max(0,Math.min(100,p))+'%')}
    function move(e){const r=cmp.getBoundingClientRect();setPos((e.clientX-r.left)/r.width*100)}
    let drag=false;
    cmp.addEventListener('pointerdown',e=>{drag=true;cmp.setPointerCapture(e.pointerId);move(e)});
    cmp.addEventListener('pointermove',e=>{if(drag||e.pointerType==='mouse')move(e)});
    cmp.addEventListener('pointerup',()=>drag=false);
    document.querySelectorAll('.tabs button').forEach(b=>b.addEventListener('click',()=>{
      document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x===b));
      const [bf,af]=rooms[b.dataset.room];
      imgB.src=base+bf;imgA.src=base+af;
      imgB.alt=b.dataset.room+' before';imgA.alt=b.dataset.room+' after AI redesign concept';
    }));
    if(!still){ // gentle intro sweep
      let t=0;const run=setInterval(()=>{t+=.04;setPos(50+Math.sin(t)*22);if(t>6.3){clearInterval(run);setPos(50)}},16);
      cmp.addEventListener('pointerdown',()=>clearInterval(run),{once:true});
    }
  }
 
  /* chatbot starter chips (uses the existing sendChatMessage from chatbot.js) */
  document.querySelectorAll('.chat-chips button').forEach(b=>b.addEventListener('click',()=>{
    document.getElementById('chatbotInput').value=b.dataset.q;
    if(typeof sendChatMessage==='function')sendChatMessage();
  }));
})();
