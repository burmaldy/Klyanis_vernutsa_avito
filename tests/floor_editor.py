from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from functools import partial
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1]
s=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)));Thread(target=s.serve_forever,daemon=True).start()
checks=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);p=b.new_page(viewport={'width':1365,'height':1000});errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 url=f'http://127.0.0.1:{s.server_port}/Avito_Miry_v9_visual.html';p.goto(url);p.evaluate("profile9().wish=Object.keys(DATA);save9();go('house/me/wish')")
 for theme in ['scandi','loft','creative']:
  sources=[]
  for floor in ['oak','walnut','stone']:
   p.evaluate('([theme,floor])=>{visualSettings.me.wish.theme=theme;visualSettings.me.wish.floor=floor;render()}',[theme,floor]);p.wait_for_selector('.visual-scene[data-layout-valid="true"]');p.wait_for_function("document.querySelector('.scene-background>img').complete")
   assert p.evaluate("document.querySelectorAll('.floor-overlay').length===0")
   sources.append(p.evaluate("roomBackgroundVisual(cfgVisual()).slice(-100)"))
  assert len(set(sources))==3;checks.append(theme+': three distinct complete floor images, valid packing')
 p.locator('[data-boundary-action="edit"]').click();assert p.locator('#boundaryEditorShell').is_visible()
 initial=p.evaluate('boundaryDraft.points.map(p=>p.slice())')
 h=p.locator('[data-boundary-point="0"]');h.focus();h.press('ArrowRight');assert p.evaluate('boundaryDraft.points[0][0]')>initial[0][0]
 box=h.bounding_box();p.mouse.move(box['x']+22,box['y']+22);p.mouse.down();p.mouse.move(box['x']+27,box['y']+22,steps=3);p.mouse.up()
 p.locator('[data-boundary-action="add-point"]').click();assert p.locator('[data-boundary-point]').count()==5
 p.locator('[data-boundary-action="remove-point"]').click();assert p.locator('[data-boundary-point]').count()==4
 p.locator('[data-boundary-action="reset"]').click()
 inp=p.locator('[data-boundary-coordinate="x"][data-index="0"]');inp.fill('4');inp.press('Tab')
 assert p.locator('[data-boundary-action="save"]').is_enabled()
 p.evaluate("localStorage.setItem('avito-miry:visual:v1',JSON.stringify(visualSettings))");saved=p.evaluate('boundaryDraft.points');p.locator('[data-boundary-action="save"]').click();assert p.evaluate('userBoundaries[boundaryKey("me","wish","room")]')==saved
 p.reload();p.evaluate("go('house/me/wish')");p.wait_for_selector('.visual-scene[data-layout-valid="true"]');assert p.evaluate('userBoundaries[boundaryKey("me","wish","room")]')==saved;checks.append('pointer, keyboard, numeric input, add/remove/reset, save and reload')
 p.locator('[data-boundary-action="edit"]').click();p.evaluate('boundaryDraft.points=[[.1,.1],[.9,.9],[.9,.1],[.1,.9]];buildBoundaryHandles();updateBoundaryPreview(true)');assert p.locator('[data-boundary-action="save"]').is_disabled();p.keyboard.press('Escape');assert p.evaluate('boundaryDraft===null');assert p.evaluate('userBoundaries[boundaryKey("me","wish","room")]')==saved;checks.append('crossed contour blocked; Escape discards draft')
 p.locator('[data-boundary-action="edit"]').click();p.screenshot(path=str(ROOT/'downloads/floor_editor_preview.png'));p.locator('[data-boundary-action="cancel"]').click()
 assert p.evaluate('boundaryKey("me","wish","room")!==boundaryKey("me","real","room")&&boundaryKey("me","wish","room")!==boundaryKey("anna","wish","room")')
 for width in [390,768,1365,1920]:
  p.set_viewport_size({'width':width,'height':1000})
  for zone in ['room','garage','wardrobe','shelf','camping']:
   p.evaluate('(z)=>go(z==="room"?"house/me/wish":"storage/"+z+"/me/wish")',zone);p.wait_for_selector('.visual-scene[data-layout-valid="true"]');p.locator('[data-boundary-action="edit"]').click();assert p.locator('[data-boundary-action="save"]').is_enabled();p.locator('[data-boundary-action="cancel"]').click()
 checks.append('20 viewport/zone cases: editable, valid packing; profile and room keys separate')
 assert p.evaluate("!!boundaryGeometryError([[.5,.05],[.78,.86],[.05,.36],[.95,.36],[.22,.86]])");checks.append('self-intersecting star rejected');assert not errors,errors
 b.close()
s.shutdown();(ROOT/'tests/floor_editor_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(json.dumps(checks,ensure_ascii=False,indent=2))
