// Shared by every page: mobile menu, scrolled navbar, smooth page transitions.
(function(){
  const nav=document.getElementById('navbar'), btn=document.getElementById('nav-toggle');
  if(btn&&nav){
    btn.addEventListener('click',()=>{const o=nav.classList.toggle('nav-open');btn.setAttribute('aria-expanded',o)});
    document.addEventListener('keydown',e=>{if(e.key==='Escape')nav.classList.remove('nav-open')});
  }
  const onScroll=()=>nav&&nav.classList.toggle('scrolled',scrollY>40);
  addEventListener('scroll',onScroll,{passive:true});onScroll();
  // user menu (logged-in pages)
  var chip=document.getElementById('userChip'), dd=document.getElementById('userDropdown');
  if(chip&&dd){
    chip.addEventListener('click',function(e){e.stopPropagation();var o=dd.classList.toggle('show');chip.setAttribute('aria-expanded',o)});
    document.addEventListener('click',function(e){if(!dd.contains(e.target)&&!chip.contains(e.target)){dd.classList.remove('show');chip.setAttribute('aria-expanded','false')}});
  }
  // fade out before navigating to another page of this site
  document.addEventListener('click',e=>{
    const a=e.target.closest&&e.target.closest('a[href]');
    if(!a||e.defaultPrevented||e.metaKey||e.ctrlKey||e.shiftKey||a.target==='_blank')return;
    const u=new URL(a.href,location.href);
    if(u.origin!==location.origin||u.pathname===location.pathname||a.hasAttribute('download'))return;
    e.preventDefault();document.body.classList.add('page-leave');
    setTimeout(()=>location.href=a.href,260);
  });
  addEventListener('pageshow',()=>document.body.classList.remove('page-leave'));
})();