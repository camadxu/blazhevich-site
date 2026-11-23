'use strict';
// node tools/test_audio_player.js — exercises shipped JS; no packages or browser required.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../src/script.js'),'utf8');
class Element{
  constructor(){this.handlers={};this.attrs={};this.hidden=false;this.value=0;this.textContent=''}
  addEventListener(name,handler){(this.handlers[name]??=[]).push(handler)}
  emit(name){for(const handler of this.handlers[name]||[])handler({})}
  setAttribute(name,value){this.attrs[name]=value}
}
async function test(lang){
  const audio=new Element(),custom=new Element(),play=new Element(),seek=new Element(),volume=new Element(),status=new Element(),elapsed=new Element(),duration=new Element();
  let playCalls=0,rejectPlay=false;
  Object.assign(audio,{paused:true,currentTime:0,duration:NaN,volume:1,controls:true,ended:false,error:null});
  audio.play=()=>{playCalls++;if(rejectPlay)return Promise.reject(new Error('media failed'));audio.paused=false;audio.emit('play');audio.emit('playing');return Promise.resolve()};
  audio.pause=()=>{audio.paused=true;audio.emit('pause')};
  custom.hidden=true;
  const parts={'audio':audio,'.audio-custom':custom,'.audio-play':play,'.audio-seek':seek,'.audio-volume input':volume,'.audio-status':status,'.audio-elapsed':elapsed,'.audio-duration':duration};
  const box={dataset:{title:'Concerto',artist:'Viktor Batashev'},querySelector:s=>parts[s]};
  const document={documentElement:{lang,classList:{add(){},contains(){return false}}},querySelectorAll:s=>s==='.audio-player'?[box]:[],querySelector:()=>null,getElementById:()=>null};
  const session={metadata:null,handlers:{},setActionHandler(name,handler){this.handlers[name]=handler}};
  vm.runInNewContext(source,{document,navigator:{mediaSession:session},MediaMetadata:class{constructor(data){Object.assign(this,data)}},window:{},scrollY:0,addEventListener(){}});
  assert.equal(playCalls,0,'initial page must not start loading media');
  assert.equal(custom.hidden,false);assert.equal(audio.hidden,true);assert.equal(audio.controls,false);
  assert.equal(seek.disabled,true);assert.equal(play.attrs['aria-pressed'],'false');
  play.emit('click');await Promise.resolve();
  assert.equal(audio.paused,false);assert.equal(play.attrs['aria-pressed'],'true');
  assert.equal(play.attrs['aria-label'],lang==='en'?'Pause':'Пауза');
  assert.equal(session.metadata.artist,'Viktor Batashev');
  audio.duration=642.054979;audio.emit('loadedmetadata');
  assert.equal(seek.disabled,false);assert.equal(duration.textContent,'10:42');
  seek.value=321;seek.emit('input');assert.equal(audio.currentTime,321);assert.equal(elapsed.textContent,'5:21');
  seek.value=900;seek.emit('input');assert.equal(audio.currentTime,audio.duration);
  volume.value=.4;volume.emit('input');assert.equal(audio.volume,.4);
  audio.volume=.6;audio.emit('volumechange');assert.equal(volume.value,.6);
  play.emit('click');assert.equal(audio.paused,true);
  session.handlers.seekto({seekTime:-20});assert.equal(audio.currentTime,0);
  session.handlers.seekto({seekTime:5000});assert.equal(audio.currentTime,audio.duration);
  session.handlers.seekto({seekTime:NaN});assert.equal(audio.currentTime,audio.duration);
  audio.ended=true;audio.emit('ended');assert.equal(status.textContent,lang==='en'?'Recording ended':'Запись окончена');
  audio.ended=false;audio.error={code:2};audio.emit('error');
  const error=status.textContent;
  assert.match(error,lang==='en'?/Unable/:/Не удалось/);
  // Media failure also dispatches pause: it must not erase the useful error.
  audio.emit('pause');assert.equal(status.textContent,error);
  rejectPlay=true;play.emit('click');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(status.textContent,error,'rejected play must be handled');
}
(async()=>{await test('ru');await test('en');console.log('audio player JS regression: RU/EN passed (not a browser test)')})().catch(error=>{console.error(error);process.exitCode=1});
