const {chromium}=require(process.argv[2]||'playwright');
const assert=require('node:assert/strict'),path=require('node:path');
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
 const p=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
 p.on('pageerror',e=>errors.push(e.message));await p.route('https://fonts.googleapis.com/**',r=>r.abort());
 await p.goto('http://127.0.0.1:5173/new?example=rounded');
 await p.locator('.upload-preview').waitFor();await p.getByRole('button',{name:'Create project →',exact:true}).click();
 const ready=()=>p.getByRole('status').filter({hasText:'Preview and exports up to date'}).waitFor({timeout:120000});
 await ready();const initial=await p.locator('.element-hit').count();
 await p.getByRole('button',{name:'Compare original',exact:true}).click();
 await p.getByLabel('Comparison mode',{exact:true}).selectOption('overlay');
 await p.getByRole('slider',{name:'Original opacity'}).fill('100');
 assert.equal(await p.locator('.comparison-overlay').evaluate(e=>getComputedStyle(e).opacity),'1');
 await p.getByRole('checkbox',{name:'Selection outlines'}).uncheck();
 assert.equal(await p.locator('.artboard.hide-outlines').count(),1);
 await p.getByRole('slider',{name:'Original opacity'}).fill('45');
 await p.screenshot({path:'reports/comparison-editor.png',fullPage:true});
 await p.getByRole('button',{name:'Compare original',exact:true}).click();
 for(const type of ['text','button','input','card']) {
  await p.getByRole('button',{name:'Add '+type,exact:true}).click();await ready();
 }
 await p.locator('input[aria-label="Image to insert"]').setInputFiles('tests/fixtures/login.png');await ready();
 await p.locator('.element-hit').nth(initial+4).waitFor();
 await ready();assert.equal(await p.locator('.element-hit').count(),initial+5);
 await p.getByRole('button',{name:'Undo',exact:true}).click();await ready();assert.equal(await p.locator('.element-hit').count(),initial+4);
 await p.getByRole('button',{name:'Redo',exact:true}).click();await ready();assert.equal(await p.locator('.element-hit').count(),initial+5);
 await p.frameLocator('iframe').getByText('Your text',{exact:true}).waitFor();
 for(const [name,file] of [['↓ HTML / CSS','tools-html.zip'],['↓ React project','tools-react.zip']]){
  await p.getByRole('button',{name:'Export ↓',exact:true}).click();const event=p.waitForEvent('download');await p.getByRole('button',{name,exact:true}).click();await(await event).saveAs(path.resolve('reports',file));
 }
 await p.reload();await ready();assert.equal(await p.locator('.element-hit').count(),initial+5);
 await p.setViewportSize({width:390,height:844});await p.getByRole('button',{name:'Compare original',exact:true}).click();
 assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await p.screenshot({path:'reports/tools-mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);console.log('PASS: overlay opacity, outlines, five inserted types, undo/redo, autosave/reload, downloads, mobile.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
