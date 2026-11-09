'use strict';
(function(){
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Каталог: поиск и фильтр */
  const search=document.getElementById('search'), instrument=document.getElementById('instrument');
  const cards=[...document.querySelectorAll('#catalog .card')];
  const norm=s=>s.toLocaleLowerCase().replaceAll('ё','е').trim();
  const countEl=document.getElementById('count');
  const extraFilters=[...document.querySelectorAll('[data-catalog-filter]')];
  function filterCatalog(){
    const q=norm(search.value); let n=0;
    for(const c of cards){const ok=norm(c.textContent).includes(q)&&(instrument.value==='all'||c.dataset.instrument===instrument.value)&&extraFilters.every(f=>f.value==='all'||c.dataset[f.dataset.catalogFilter]===f.value);c.hidden=!ok;if(ok)n++}
    countEl.textContent=(countEl.dataset.tpl||'Показано: {n} из {t}').replace('{n}',n).replace('{t}',cards.length);
    document.getElementById('empty').hidden=n!==0;
  }
  if(search&&instrument){search.addEventListener('input',filterCatalog); instrument.addEventListener('change',filterCatalog); extraFilters.forEach(f=>f.addEventListener('change',filterCatalog)); filterCatalog();}

  /* Свет на карточках за курсором */
  for(const c of cards){c.addEventListener('pointermove',e=>{const r=c.getBoundingClientRect();c.style.setProperty('--x',(e.clientX-r.left)+'px');c.style.setProperty('--y',(e.clientY-r.top)+'px')})}

  /* Шапка, кнопка «наверх», активный пункт меню */
  const bar=document.getElementById('top-bar'), totop=document.getElementById('totop');
  const onScroll=()=>{const y=scrollY;bar.classList.toggle('scrolled',y>10);totop.classList.toggle('show',y>700)};
  addEventListener('scroll',onScroll,{passive:true}); onScroll();
  totop.addEventListener('click',()=>{scrollTo({top:0,behavior:reduce?'auto':'smooth'});(document.querySelector('h1')||document.querySelector('.brand')).setAttribute('tabindex','-1');(document.querySelector('h1')||document.querySelector('.brand')).focus({preventScroll:true})});
  const links=[...document.querySelectorAll('nav a')];
  if('IntersectionObserver' in window){
    /* Подсветка пункта меню: на многостраничной версии — текущая страница, на одностраничной — раздел в поле зрения */
    const here=location.pathname.split('/').pop()||'index.html';
    const pageLink=links.find(a=>a.getAttribute('href')===here);
    if(pageLink) pageLink.classList.add('active');
    const spy=new IntersectionObserver(es=>{for(const e of es){if(e.isIntersecting){links.forEach(a=>{const h=a.getAttribute('href');if(h.includes('#'))a.classList.toggle('active',h.endsWith('#'+e.target.id))})}}},{rootMargin:'-45% 0px -50% 0px'});
    links.map(a=>a.getAttribute('href').split('#')[1]).filter(Boolean).forEach(id=>{const el=document.getElementById(id);if(el)spy.observe(el)});

    /* Плавное появление: прячем только то, что ниже первого экрана */
    if(!reduce){
      const els=[...document.querySelectorAll('.reveal')].filter(el=>el.getBoundingClientRect().top>innerHeight);
      els.forEach(el=>el.classList.add('pre'));
      const io=new IntersectionObserver(es=>{for(const e of es){if(e.isIntersecting){e.target.classList.remove('pre');io.unobserve(e.target)}}},{rootMargin:'0px 0px -8% 0px'});
      els.forEach(el=>io.observe(el));
    }
  }

  if(reduce || matchMedia('(max-width: 620px), (pointer: coarse)').matches) return;
  const hero=document.getElementById('hero'); if(!hero) return;
  const img=hero.querySelector('.portrait img');

  /* Луч света следует за курсором, лёгкий параллакс портрета */
  hero.addEventListener('pointermove',e=>{const r=hero.getBoundingClientRect();hero.style.setProperty('--mx',((e.clientX-r.left)/r.width*100).toFixed(1)+'%');hero.style.setProperty('--my',((e.clientY-r.top)/r.height*100).toFixed(1)+'%')});
  hero.addEventListener('pointerleave',()=>{hero.style.setProperty('--mx','50%');hero.style.setProperty('--my','38%')});
  addEventListener('scroll',()=>{const y=Math.min(scrollY,900);img.style.setProperty('--py',(y*.12).toFixed(1)+'px')},{passive:true});

  /* Пылинки в луче прожектора */
  const cv=document.getElementById('motes'); if(!cv) return; const ctx=cv.getContext('2d');
  let W=0,H=0,dpr=1,motes=[],running=true;
  function size(){dpr=Math.min(devicePixelRatio||1,2);W=hero.clientWidth;H=hero.clientHeight;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);
    const n=Math.round(Math.min(70,W/18));motes=Array.from({length:n},()=>spawn(true))}
  function spawn(any){return{x:W/2+(Math.random()-.5)*Math.min(W,760)*.8,y:any?Math.random()*H:H+10,r:Math.random()*1.6+.4,v:Math.random()*.25+.08,d:Math.random()*Math.PI*2,a:Math.random()*.5+.15}}
  function tick(t){if(!running)return;ctx.clearRect(0,0,W,H);
    for(const m of motes){m.y-=m.v;m.x+=Math.sin(t/2400+m.d)*.15;if(m.y<-10)Object.assign(m,spawn(false));
      const tw=.6+.4*Math.sin(t/900+m.d);ctx.beginPath();ctx.arc(m.x,m.y,m.r,0,6.283);ctx.fillStyle=`rgba(243,210,138,${(m.a*tw).toFixed(3)})`;ctx.fill()}
    requestAnimationFrame(tick)}
  size(); addEventListener('resize',size);
  new IntersectionObserver(([e])=>{const was=running;running=e.isIntersecting;if(running&&!was)requestAnimationFrame(tick)}).observe(hero);
  requestAnimationFrame(tick);
})();
