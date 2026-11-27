'use strict';
(function(){
  document.documentElement.classList.add('js');
  /* Своя запись: native controls остаются доступны без JavaScript. */
  document.querySelectorAll('.audio-player').forEach(box=>{
    const audio=box.querySelector('audio'),custom=box.querySelector('.audio-custom'),
      play=box.querySelector('.audio-play'),seek=box.querySelector('.audio-seek'),
      volume=box.querySelector('.audio-volume input'),status=box.querySelector('.audio-status');
    const en=document.documentElement.lang==='en';
    const text=en?{play:'Play',pause:'Pause',loading:'Loading…',playing:'Playing',ended:'Recording ended',error:'Unable to play. Try again or open the audio file.'}
      :{play:'Воспроизвести',pause:'Пауза',loading:'Загрузка…',playing:'Воспроизведение',ended:'Запись окончена',error:'Не удалось воспроизвести. Повторите или откройте аудиофайл.'};
    const fmt=n=>{n=Number.isFinite(n)?Math.max(0,Math.floor(n)):0;return `${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`};
    const update=()=>{
      const finite=Number.isFinite(audio.duration);
      seek.disabled=!finite;
      if(finite){seek.max=audio.duration;box.querySelector('.audio-duration').textContent=fmt(audio.duration)}
      seek.value=audio.currentTime;seek.setAttribute('aria-valuetext',fmt(audio.currentTime));
      box.querySelector('.audio-elapsed').textContent=fmt(audio.currentTime);
      play.textContent=audio.paused?'▶':'Ⅱ';play.setAttribute('aria-label',audio.paused?text.play:text.pause);
      play.setAttribute('aria-pressed',String(!audio.paused));volume.value=audio.volume;
    };
    const start=async()=>{status.textContent=text.loading;try{await audio.play()}catch(e){status.textContent=text.error}};
    play.addEventListener('click',()=>{if(audio.paused)start();else audio.pause()});
    seek.addEventListener('input',()=>{if(Number.isFinite(audio.duration))audio.currentTime=Math.max(0,Math.min(audio.duration,Number(seek.value)));update()});
    volume.addEventListener('input',()=>{audio.volume=Number(volume.value)});
    ['loadedmetadata','durationchange','timeupdate','play','pause','ended','volumechange'].forEach(e=>audio.addEventListener(e,update));
    audio.addEventListener('waiting',()=>status.textContent=text.loading);
    audio.addEventListener('playing',()=>status.textContent=text.playing);
    audio.addEventListener('pause',()=>status.textContent=audio.error?text.error:audio.ended?text.ended:text.pause);
    audio.addEventListener('ended',()=>status.textContent=text.ended);
    audio.addEventListener('error',()=>status.textContent=text.error);
    if('mediaSession' in navigator&&typeof MediaMetadata==='function'){
      audio.addEventListener('play',()=>{
        navigator.mediaSession.metadata=new MediaMetadata({title:box.dataset.title,artist:box.dataset.artist});
        for(const [name,handler] of [['play',start],['pause',()=>audio.pause()],['seekto',e=>{
          if(Number.isFinite(audio.duration)&&Number.isFinite(e.seekTime))audio.currentTime=Math.max(0,Math.min(audio.duration,e.seekTime));
        }]]){try{navigator.mediaSession.setActionHandler(name,handler)}catch(e){}}
      });
    }
    update();custom.hidden=false;audio.hidden=true;audio.controls=false;
  });
  /* Плеер: внешний iframe (Яндекс Музыка) подгружается только по нажатию кнопки */
  document.querySelectorAll('.player').forEach(box=>{const btn=box.querySelector('button');
    btn.addEventListener('click',()=>{const f=document.createElement('iframe');f.src=box.dataset.src;f.title=box.dataset.title;f.loading='lazy';f.allow='clipboard-write';box.replaceChildren(f)})});

  /* Снимок в статье: клик открывает крупный просмотр. Без JS ссылка ведёт на сам файл */
  const zooms=[...document.querySelectorAll('.plate-zoom')];
  if(zooms.length&&typeof HTMLDialogElement==='function'&&HTMLDialogElement.prototype.showModal){
    const isEnglish=document.documentElement.lang==='en';
    const dlg=document.createElement('dialog');dlg.className='plate-view';
    dlg.setAttribute('aria-label',isEnglish?'Image viewer':'Просмотр снимка');
    const close=document.createElement('button');close.className='plate-close';close.type='button';
    close.textContent=isEnglish?'Close image':'Закрыть снимок';
    close.addEventListener('click',()=>dlg.close());
    const view=document.createElement('figure'),pic=document.createElement('img'),cap=document.createElement('figcaption');
    view.append(close,pic,cap);dlg.append(view);document.body.append(dlg);
    let opener=null;
    zooms.forEach(a=>a.addEventListener('click',e=>{
      if(e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;
      const inner=a.querySelector('img'),cap0=a.parentElement.querySelector('figcaption');
      e.preventDefault();
      pic.src=a.getAttribute('href');pic.alt=inner?inner.alt:'';
      cap.innerHTML=cap0?cap0.innerHTML:'';
      opener=a;dlg.showModal();
    }));
    dlg.addEventListener('click',e=>{if(e.target===dlg)dlg.close()});
    dlg.addEventListener('close',()=>{pic.removeAttribute('src');cap.textContent='';if(opener){opener.focus({preventScroll:true});opener=null}});
  }
  /* Меню-поповер: после перехода к разделу закрывается, чтобы не висеть над текстом */
  const menu=document.getElementById('menu');
  if(menu&&menu.hidePopover)menu.addEventListener('click',e=>{if(e.target.closest('a'))menu.hidePopover()});
  /* кнопка «Меню» сообщает экранному диктору, открыто меню или закрыто */
  const fab=document.querySelector('.fab');
  if(fab&&menu&&menu.hidePopover){fab.setAttribute('aria-controls','menu');fab.setAttribute('aria-expanded','false');
    menu.addEventListener('toggle',e=>fab.setAttribute('aria-expanded',String(e.newState==='open')))}

  /* «Лента»: фильтр по инструментам для выпуска, запечённого в страницу при сборке. */
  document.querySelectorAll('[data-agent-list]').forEach(list=>{
    const chips=list.parentNode.querySelector('[data-agent-chips]'), limit=+list.dataset.agentLimit||Infinity;
    let filter='';
    const show=()=>{let n=0,last=null;list.querySelectorAll('.news-item').forEach(li=>{
        const ok=(!filter||li.dataset.agentInstruments.split(' ').includes(filter))&&n<limit;if(ok){n++;last=li}
        li.classList.toggle('is-on',ok);li.classList.remove('is-last')});
      if(last)last.classList.add('is-last');
      let empty=list.querySelector('.news-empty');
      if(!n&&!empty){empty=document.createElement('li');empty.className='news-empty';empty.textContent='В этом выпуске таких заметок нет.';list.append(empty)}
      if(empty)empty.hidden=n>0;
      list.setAttribute('data-agent-ready','')};
    if(chips){chips.hidden=false;chips.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;filter=b.dataset.agentFilter;
      chips.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));show()})}
    show();
  });

  /* Витрина: старые якоря одностраничника (#scores, #concertos, …) ведут на страницы разделов.
     Биография теперь имеет отдельный адрес; страницы английской версии лежат рядом с en/index.html. */
  if(document.getElementById('hero')){
    const R={'#scores':'works.html','#concertos':'works.html#concertos','#listen':'listen.html',
             '#usa':'us-schools.html#usa','#schools':'schools.html','#about':'about.html'};
    const to=R[location.hash];if(to)location.replace(to);
  }

  /* Шапка и активный пункт меню */
  const bar=document.getElementById('top-bar'), hero=document.getElementById('hero');
  /* витрина: кнопка «Меню» и шапка появляются, когда первый экран ушёл вверх */
  let pastHero=document.documentElement.classList.contains('past-hero');
  const onScroll=()=>{const y=scrollY;if(bar)bar.classList.toggle('scrolled',y>10);
    if(hero){const edge=hero.offsetHeight*.6;if(!pastHero&&y>edge+40)pastHero=true;else if(pastHero&&y<edge-40)pastHero=false;
      document.documentElement.classList.toggle('past-hero',pastHero)}};
  addEventListener('scroll',onScroll,{passive:true}); onScroll();
  const links=[...document.querySelectorAll('nav a')];
  if('IntersectionObserver' in window){
    /* Подсветка пункта меню: на многостраничной версии — текущая страница, на одностраничной — раздел в поле зрения */
    const here=location.pathname.split('/').pop()||'index.html';
    const pageLink=links.find(a=>a.getAttribute('href')===here);
    if(pageLink) pageLink.classList.add('active');
    const spy=new IntersectionObserver(es=>{for(const e of es){if(e.isIntersecting){links.forEach(a=>{const h=a.getAttribute('href');if(h.includes('#'))a.classList.toggle('active',h.endsWith('#'+e.target.id))})}}},{rootMargin:'-45% 0px -50% 0px'});
    links.map(a=>a.getAttribute('href').split('#')[1]).filter(Boolean).forEach(id=>{const el=document.getElementById(id);if(el)spy.observe(el)});
  }

})();
