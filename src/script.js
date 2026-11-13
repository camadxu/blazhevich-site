'use strict';
(function(){
  document.documentElement.classList.add('js');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Плеер: внешний iframe (Яндекс Музыка) подгружается только по нажатию кнопки */
  document.querySelectorAll('.player').forEach(box=>{const btn=box.querySelector('button');
    btn.addEventListener('click',()=>{const f=document.createElement('iframe');f.src=box.dataset.src;f.title=box.dataset.title;f.loading='lazy';f.allow='clipboard-write';box.replaceChildren(f)})});

  /* Меню-поповер: после перехода к разделу закрывается, чтобы не висеть над текстом */
  const menu=document.getElementById('menu');
  if(menu&&menu.hidePopover)menu.addEventListener('click',e=>{if(e.target.closest('a'))menu.hidePopover()});

  /* Шапка, кнопка «наверх», активный пункт меню */
  const bar=document.getElementById('top-bar'), totop=document.getElementById('totop'), hero=document.getElementById('hero');
  if(!totop)return;
  /* главная — одна длинная страница: боковое меню и кнопка «Меню» появляются, когда первый экран ушёл вверх */
  const onScroll=()=>{const y=scrollY;if(bar)bar.classList.toggle('scrolled',y>10);totop.classList.toggle('show',y>700);
    if(hero)document.documentElement.classList.toggle('past-hero',y>hero.offsetHeight*.6)};
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

})();
