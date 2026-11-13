// node tools/media/og_shot.js  → /tmp/og.png (затем tools/media: Pillow сохраняет assets/og-image.jpg)
const {chromium}=require('playwright');const path=require('path');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:630}});
await p.goto('file://'+path.resolve(__dirname,'og.html'));await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(400);
await p.screenshot({path:process.argv[2]||'/tmp/og.png'});await b.close()})();
