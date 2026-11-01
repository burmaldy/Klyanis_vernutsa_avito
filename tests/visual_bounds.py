from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from functools import partial
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1];server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start();checks=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);p=b.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(f'http://127.0.0.1:{server.server_port}/Avito_Miry_v9_visual.html')
 p.evaluate("profile9().wish=Object.keys(DATA);save9()")
 for width in [390,768,1365,1920]:
  p.set_viewport_size({'width':width,'height':1000})
  for theme in ['scandi','loft','creative']:
   p.evaluate('(theme)=>{visualSettings.me.wish.theme=theme;go("house/me/wish")}',theme)
   for zone in ['room','wardrobe','shelf','garage','camping']:
    p.evaluate('(zone)=>go(zone==="room"?"house/me/wish":"storage/"+zone+"/me/wish")',zone)
    p.wait_for_selector('.visual-scene[data-bounds-ready="true"]')
    for slot in [0,4,8]:
     p.evaluate('(slot)=>{for(const id of profile9().wish){const allowed=allowedSlotsVisual(id);profile9().positions["wish:"+zoneFor(id)+":"+id]=allowed.includes(slot)?slot:allowed[allowed.length-1]}render()}',slot)
     p.wait_for_timeout(70)
     violations=p.evaluate("""()=>{const s=document.querySelector('.visual-scene'),r=s.getBoundingClientRect(),out=[];for(const el of s.querySelectorAll('.scene-object .scene-cutout,.scene-label,.storage-portal,.ambient-decoration')){const b=el.getBoundingClientRect();if(b.left<r.left-1||b.right>r.right+1||b.top<r.top-1||b.bottom>r.bottom+1)out.push([el.className,{left:b.left-r.left,top:b.top-r.top,right:b.right-r.left,bottom:b.bottom-r.top},r.width,r.height])}return out}""")
     assert not violations,(width,theme,zone,slot,violations)
    checks.append({'width':width,'theme':theme,'zone':zone,'status':'PASS'})
  p.evaluate("go('house/me/wish')");p.wait_for_selector('.visual-scene');p.locator('.visual-scene').screenshot(path=f'/tmp/room-bounds-{width}.png')
 # Actual selection and resize must not move or clip a sprite after its label appears.
 p.set_viewport_size({'width':390,'height':844});p.evaluate("profile9().positions={};profile9().wish=['sofa','lamp','table','plant'];go('house/me/wish');render()")
 p.locator('.scene-object[data-id="plant"]').click();assert p.locator('#itemSheet').is_visible();p.locator('#itemSheet [data-action="close-sheet"]').click()
 p.locator('.visual-scene').screenshot(path='/tmp/room-bounds-final.png')
 assert not errors,errors;b.close()
server.shutdown();(ROOT/'tests/visual_bounds_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print('PASS:',len(checks),'viewport/theme/zone combinations, three extreme slots each; selection and resize; no JS errors')
