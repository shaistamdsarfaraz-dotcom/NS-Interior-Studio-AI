function togglePassword(id,icon){
  const f=document.getElementById(id), show=f.type==='password';
  f.type=show?'text':'password';
  icon.classList.toggle('fa-lock',!show);icon.classList.toggle('fa-lock-open',show);
}
function toast(msg,ok){
  let t=document.querySelector('.toast');
  if(!t){t=document.createElement('div');document.body.appendChild(t)}
  t.className='toast'+(ok?' ok':'');t.textContent=msg;
  requestAnimationFrame(()=>t.classList.add('show'));
  clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),3000);
}
(function(){
  const card=document.querySelector('.auth-card');if(!card)return;
  const still=matchMedia('(prefers-reduced-motion: reduce)').matches;
  card.addEventListener('mousemove',e=>{
    const r=card.getBoundingClientRect(), x=e.clientX-r.left, y=e.clientY-r.top;
    card.style.setProperty('--mx',x+'px');card.style.setProperty('--my',y+'px');
    if(!still)card.style.transform=`rotateY(${(x/r.width-.5)*6}deg) rotateX(${-(y/r.height-.5)*6}deg)`;
  });
  card.addEventListener('mouseleave',()=>card.style.transform='');
  document.querySelectorAll('.main-btn').forEach(b=>b.addEventListener('mousemove',e=>{
    const r=b.getBoundingClientRect();
    b.style.setProperty('--bx',(e.clientX-r.left)+'px');b.style.setProperty('--by',(e.clientY-r.top)+'px');
  }));
  document.querySelectorAll('.ghost-btn').forEach(a=>a.addEventListener('click',e=>{
    e.preventDefault();card.classList.add('leaving');
    setTimeout(()=>location.href=a.href,420);
  }));
  const stage=document.querySelector('.bg-stage');
  addEventListener('mousemove',e=>{if(!still)stage.style.transform=`translate(${(e.clientX/innerWidth-.5)*-14}px,${(e.clientY/innerHeight-.5)*-14}px)`});
})();
