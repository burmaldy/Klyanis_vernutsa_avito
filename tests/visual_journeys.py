"""12 required Visual-edition journeys, executed in Chromium, not inferred from code."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright
import json,traceback,base64,io
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{server.server_port}/Avito_Miry_v9_visual.html';results=[]

def route(p,path):p.evaluate('(path)=>go(path)',path);p.wait_for_timeout(100)
def add(p,item):
 route(p,'listing/'+item);p.locator('[data-action="wish-add"]').click()
def close_sheet(p):p.locator('#itemSheet [data-action="close-sheet"]').click()
def zone(p,name,room='wish'):route(p,f'storage/{name}/me/{room}');p.wait_for_selector('.visual-scene')
def select(p,item):p.locator(f'.scene-object[data-id="{item}"]').click();p.wait_for_selector('#itemSheet[open]')

def t1(p):
 add(p,'boots');zone(p,'wardrobe');p.locator('.scene-object[data-id="boots"]').wait_for(state='visible');assert p.locator('.room-products .heart[data-id="boots"]').count()==1
 assert p.locator('.storage-candidates .heart[data-id="tent2"]').count()==0

def t2(p):
 add(p,'bmw');zone(p,'garage');assert p.locator('.scene-object[data-id="bmw"]').is_visible();assert p.locator('.scene-object[data-id="tent2"]').count()==0

def t3(p):
 add(p,'headphones');zone(p,'shelf');assert p.locator('.scene-object[data-id="headphones"]').is_visible();assert p.locator('.room-products .heart[data-id="headphones"]').count()==1

def t4(p):
 add(p,'tent2')
 for z in ['wardrobe','garage','shelf']:
  zone(p,z);assert p.locator('.scene-object[data-id="tent2"]').count()==0;assert p.locator('.room-products .heart[data-id="tent2"]').count()==0
 zone(p,'camping');assert p.locator('.scene-object[data-id="tent2"]').is_visible()
 # An explicit wrong target is rejected and offers the correct zone without mutating saved goods.
 route(p,'listing/tent3');p.locator('[data-visual="choose-storage"]').click();p.locator('#placeZone').select_option('garage');p.locator('#placeProductForm button').click();assert p.locator('#v9DialogTitle').inner_text()=='Это место не подходит'
 assert p.evaluate("!profile9().wish.includes('tent3')")
 p.locator('[data-visual="add-correct"]').click();zone(p,'camping');assert p.locator('.scene-object[data-id="tent3"]').is_visible()

def t5(p):
 route(p,'house/me/wish');select(p,'sofa');p.locator('#itemSheet [data-v9="room-remove"]').click();assert p.locator('.scene-object[data-id="sofa"]').count()==0
 add(p,'sofa');route(p,'house/me/wish');assert p.locator('.scene-object[data-id="sofa"]').is_visible()

def t6(p):
 add(p,'jacket');zone(p,'wardrobe');select(p,'jacket');p.locator('#itemSheet [data-v9="room-remove"]').click();assert p.locator('.scene-object[data-id="jacket"]').count()==0;assert p.locator('.room-products .heart[data-id="jacket"]').count()==0;p.reload();assert p.locator('.scene-object[data-id="jacket"]').count()==0

def choose_theme(p,name):
 p.locator('[data-visual="settings"]').click();p.locator(f'[data-visual="theme"][data-id="{name}"]').click();p.locator('#visualSettingsForm button[type="submit"]').click()

def t7(p):
 add(p,'wardrobe');route(p,'house/me/wish');ids=p.locator('.scene-object').evaluate_all('(els)=>els.map(e=>e.dataset.id).sort()')
 for name in ['loft','creative','scandi']:
  choose_theme(p,name);assert f'theme-{name}' in p.locator('.visual-scene').get_attribute('class');assert ids==p.locator('.scene-object').evaluate_all('(els)=>els.map(e=>e.dataset.id).sort()')
  select(p,'wardrobe');assert p.locator('#sheetTitle').inner_text()=='Деревянный шкаф для одежды';close_sheet(p)
 p.screenshot(path='/tmp/visual-final-scandi.png',full_page=True)

def t8(p):
 route(p,'house/me/wish');p.locator('[data-visual="settings"]').click()
 # Invalid file must not replace the preview.
 p.locator('#visualBackgroundFile').set_input_files({'name':'bad.svg','mimeType':'image/svg+xml','buffer':b'<svg></svg>'});assert 'не более 1 МБ' in p.locator('#visualError').inner_text()
 out=io.BytesIO();Image.new('RGB',(400,300),(136,181,203)).save(out,format='PNG');data=out.getvalue()
 p.locator('#visualBackgroundFile').set_input_files({'name':'room.png','mimeType':'image/png','buffer':data});p.wait_for_function("document.querySelector('.draft-preview img').src.startsWith('data:image/png;base64,') && visualDraft.config.custom!==null")
 p.locator('#visualSettingsForm button[type="submit"]').click();assert p.locator('.scene-background img').get_attribute('src')=='data:image/png;base64,'+base64.b64encode(data).decode()
 p.reload();assert p.locator('.scene-background img').get_attribute('src')=='data:image/png;base64,'+base64.b64encode(data).decode()
 p.locator('[data-visual="settings"]').click();p.locator('[data-visual="reset-background"]').click();p.locator('#visualSettingsForm button[type="submit"]').click();assert p.evaluate('cfgVisual().custom===null')

def t9(p):
 add(p,'laptop');route(p,'house/me/wish');choose_theme(p,'loft');p.locator('[data-visual="settings"]').click();p.locator('#visualLighting').select_option('evening');p.locator('#visualFloor').select_option('stone');p.locator('#visualWall').evaluate("el=>{el.value='#aaccee';el.dispatchEvent(new Event('change',{bubbles:true}))}");p.locator('#visualDecor').uncheck();p.locator('#visualSettingsForm button[type="submit"]').click();p.reload()
 assert p.evaluate("cfgVisual().theme==='loft'&&cfgVisual().wall==='#aaccee'&&cfgVisual().floor==='stone'&&cfgVisual().lighting==='evening'&&!cfgVisual().decor")
 assert p.locator('.ambient-decoration').count()==0
 zone(p,'shelf');assert p.locator('.scene-object[data-id="laptop"]').is_visible()

def t10(p):
 for item in ['boots','backpack','jacket','headphones','laptop','speaker','bmw','sedan','hatchback','cartools','tent2']:
  add(p,item)
 for z in ['room','wardrobe','shelf','garage','camping']:
  route(p,'house/me/wish') if z=='room' else zone(p,z)
  ids=p.locator('.scene-object').evaluate_all('(els)=>els.map(e=>e.dataset.id)')
  for item in ids:
   select(p,item);assert p.locator('#sheetTitle').inner_text()==p.evaluate('(id)=>DATA[id].name',item)
   assert p.locator('#itemSheet [data-go="listing/'+item+'"]').count()==1
   assert p.locator('.item-details').inner_text().find(p.evaluate('(id)=>DATA[id].seller',item))>=0
   close_sheet(p)

def t11(p):
 route(p,'house/me/wish');select(p,'plant');p.locator('#itemSheet [data-go="listing/plant"]').click();p.locator('#v9Modal [data-v9="similar"]').click();p.wait_for_selector('.similar-products')
 ids=p.locator('.similar-products .heart').evaluate_all('(els)=>els.map(e=>e.dataset.id)');assert len(ids)>=2
 assert p.evaluate("ids=>ids.every(id=>DATA[id].subcategory===DATA.plant.subcategory&&DATA[id].available&&numericPrice9(DATA[id])>=900&&numericPrice9(DATA[id])<=2700)",ids)

def t12(p):
 for z in ['wardrobe','shelf','garage']:
  route(p,'house/me/wish');p.locator(f'.storage-portal[data-zone="{z}"]').click();p.wait_for_selector(f'.visual-scene[data-zone="{z}"]')
  assert p.url.endswith('/'+z+'/me/wish')
  p.locator('.return-home').click();p.wait_for_selector('.visual-scene[data-zone="room"]')
 zone(p,'camping');p.locator('.return-home').click();p.wait_for_selector('.visual-scene[data-zone="room"]')

with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for n,test in enumerate([t1,t2,t3,t4,t5,t6,t7,t8,t9,t10,t11,t12],1):
  context=b.new_context(viewport={'width':1365,'height':1000});p=context.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
  try:
   p.goto(URL);test(p);assert not errors,errors;results.append({'scenario':n,'status':'PASS'});print(n,'PASS',flush=True)
  except Exception:
   detail=traceback.format_exc();results.append({'scenario':n,'status':'FAIL','detail':detail});p.screenshot(path=f'/tmp/visual-fail-{n}.png',full_page=True);print(n,'FAIL',detail[-1300:],flush=True)
  context.close()
 b.close()
server.shutdown();(ROOT/'tests/visual_journeys_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False));raise SystemExit(any(r['status']=='FAIL' for r in results))
