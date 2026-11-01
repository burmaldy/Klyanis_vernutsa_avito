from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from functools import partial
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1];server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start();checks=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);p=b.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(f'http://127.0.0.1:{server.server_port}/Avito_Miry_v9_visual.html');p.evaluate("profile9().wish=Object.keys(DATA);save9()")
 for width in [390,768,1365,1920]:
  p.set_viewport_size({'width':width,'height':1000})
  for theme in ['scandi','loft','creative']:
   p.evaluate('(theme)=>{visualSettings.me.wish.theme=theme}',theme)
   for zone in ['room','garage','wardrobe','shelf','camping']:
    p.evaluate('(zone)=>go(zone==="room"?"house/me/wish":"storage/"+zone+"/me/wish")',zone)
    p.wait_for_selector('.visual-scene[data-layout-valid="true"]')
    for slot in [0,4,8]:
     p.evaluate('(slot)=>{for(const id of profile9().wish){const allowed=allowedSlotsVisual(id);profile9().positions["wish:"+zoneFor(id)+":"+id]=allowed.includes(slot)?slot:allowed[allowed.length-1]}render()}',slot)
     p.wait_for_function("document.querySelector('.visual-scene').dataset.layoutValid==='true'")
     failures=p.evaluate("""()=>{const s=document.querySelector('.visual-scene'),r=s.getBoundingClientRect(),poly=JSON.parse(s.dataset.floorPolygon),items=[...s.querySelectorAll('.scene-object')].map(el=>{const b=el.querySelector('.scene-cutout').getBoundingClientRect();return {id:el.dataset.id,x:b.left-r.left-s.clientLeft,y:b.top-r.top-s.clientTop,w:b.width,h:b.height}}),out=[];function inside(x,y){let value=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if(((a[1]>y)!==(b[1]>y))&&(x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]))value=!value}return value}for(const a of items){for(const [x,y] of [[a.x,a.y],[a.x+a.w,a.y],[a.x+a.w,a.y+a.h],[a.x,a.y+a.h]])if(!inside(x,y))out.push(['outside',a.id,x,y]);for(const b of items){if(a.id>=b.id)continue;if(!(a.x+a.w+5<=b.x||b.x+b.w+5<=a.x||a.y+a.h+5<=b.y||b.y+b.h+5<=a.y))out.push(['collision',a.id,b.id])}}return out}""")
     assert not failures,(width,theme,zone,slot,failures)
    checks.append({'width':width,'theme':theme,'zone':zone,'status':'PASS'})
    (ROOT/'tests/floor_collisions_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
    print(width,theme,zone,'PASS',flush=True)
    if width==1365 and theme=='creative' and zone in ['room','garage']:
     p.locator('[data-floor-toggle]').click();p.locator('.visual-scene').screenshot(path=str(ROOT/f'downloads/floor_{zone}_preview.png'));p.locator('[data-floor-toggle]').click()
 # Default positions must still allow selecting every item without forced pointer events.
 p.set_viewport_size({'width':390,'height':844});p.evaluate('profile9().positions={};render()')
 for zone in ['room','garage','wardrobe','shelf','camping']:
  p.evaluate('(zone)=>go(zone==="room"?"house/me/wish":"storage/"+zone+"/me/wish")',zone);p.wait_for_selector('.visual-scene[data-layout-valid="true"]')
  ids=p.locator('.scene-object').evaluate_all('(els)=>els.map(e=>e.dataset.id)')
  for item in ids:
   p.locator(f'.scene-object[data-id="{item}"]').click();assert p.locator('#sheetTitle').inner_text()==p.evaluate('(id)=>DATA[id].name',item);p.locator('#itemSheet [data-action="close-sheet"]').click()
 # Community photos use complete individual photographs, fitted with cover instead of stretching sprites.
 p.evaluate("go('community/all');app9.communityTab='all';render()")
 p.wait_for_selector('.community-photo-cover>img')
 assert p.locator('.community-photo-cover>img').count()>=20
 p.locator('.community-photo-cover>img').evaluate_all("ims=>ims.forEach(im=>im.loading='eager')")
 p.wait_for_function("[...document.querySelectorAll('.community-photo-cover>img')].every(im=>im.complete&&im.naturalWidth>1000)")
 assert p.locator('.community-photo-cover>img').evaluate_all("ims=>ims.every(im=>getComputedStyle(im).objectFit==='cover'&&im.naturalWidth/im.naturalHeight>2.5)")
 p.screenshot(path=str(ROOT/'downloads/community_covers_preview.png'),full_page=True)
 assert not errors,errors;b.close()
server.shutdown();(ROOT/'tests/floor_collisions_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print('PASS:60 floor/theme/viewport cases x3 positions; every texture corner inside boundary; minimum 5px gap; all items selectable on mobile;20 community covers preserve aspect ratio')
