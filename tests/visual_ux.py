from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from functools import partial
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1];server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{server.server_port}/Avito_Miry_v9_visual.html'
checks=[]
def route(p,s):p.evaluate('(s)=>go(s)',s);p.wait_for_timeout(80)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);context=b.new_context();page=context.new_page();errors=[];external=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda req:external.append(req.url) if not req.url.startswith((f'http://127.0.0.1:{server.server_port}/','data:')) else None)
 page.goto(URL)
 for width in [390,768,1365,1920]:
  page.set_viewport_size({'width':width,'height':1000})
  for path in ['home','listing/tent2','community/all','community/tech','house/me/wish','storage/wardrobe/me','event/toyota']:
   route(page,path)
   overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
   assert not overflow,(width,path,page.evaluate("[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,8).map(e=>[e.tagName,e.className,e.getBoundingClientRect().right])"))
  route(page,'house/me/wish');page.screenshot(path=f'/tmp/visual-house-{width}.png',full_page=True)
  checks.append({'check':f'{width}px, 7 screens without horizontal overflow','status':'PASS'})
 # Migration from existing V8 keys without deleting favorites, wish products or posts.
 page.evaluate("""()=>{localStorage.clear();localStorage.setItem('avito-miry:favorites:v1',JSON.stringify(['laptop']));localStorage.setItem('avito-miry:wishes:v1',JSON.stringify(['sofa','jacket','laptop','bmw']));localStorage.setItem('avito-miry:community:v1',JSON.stringify({joined:['tech'],likes:[],comments:{},posts:[{id:'user-legacy',cat:'home',title:'Сохранённая публикация V8',text:'Не удалять существующие публикации',author:'Вы',tags:['#мой_дом'],house:true,homeOwner:'me',homeRoom:'wish'}]}))}""")
 page.reload();route(page,'favorites');assert page.locator('#app .heart[data-id="laptop"]').count()==1
 route(page,'storage/wardrobe/me');assert page.locator('.scene-object[data-id="jacket"]').count()==1
 route(page,'storage/shelf/me');assert page.locator('.scene-object[data-id="laptop"]').count()==1
 route(page,'storage/garage/me');assert page.locator('.scene-object[data-id="bmw"]').count()==1
 route(page,'discussion/user-legacy');assert 'Сохранённая публикация V8' in page.locator('.post-title').inner_text()
 checks.append({'check':'V8 favorites, wish items, publications migration','status':'PASS'})
 # Fallback without crypto.randomUUID; a real publication and comment must work.
 page.add_init_script("Object.defineProperty(crypto,'randomUUID',{value:undefined,configurable:true})")
 page.reload();route(page,'community/tech');page.locator('#postTitle').fill('Fallback публикация');page.locator('#postText').fill('<img src=x onerror=alert(1)> Безопасный текст');page.locator('#postForm button[type="submit"]').click();page.wait_for_selector('#commentForm');assert page.locator('.post-title').inner_text()=='Fallback публикация'
 page.locator('#commentText').fill('Сохранённый комментарий');page.locator('#commentForm button').click();page.reload();assert 'Сохранённый комментарий' in page.locator('.comments').inner_text();checks.append({'check':'UUID fallback, safe publication and saved comment','status':'PASS'})
 # Demo purchase changes both the inventory and the rendered scene.
 route(page,'listing/laptop');page.locator('[data-v9="demo-buy"]').click();assert page.locator('.scene-object[data-id="laptop"]').count()==1
 page.reload();assert page.locator('.scene-object[data-id="laptop"]').count()==1
 route(page,'storage/shelf/me');assert page.locator('.scene-object[data-id="laptop"]').count()==0
 checks.append({'check':'Demo purchase moves wish item to purchase scene','status':'PASS'})
 # Public sharing links to the correct owner and room, retains #мой_дом after reload.
 route(page,'house/me/wish');page.locator('[data-v9="privacy"][data-room="wish"]').click();page.locator('[data-v9="share-home"]').click();page.wait_for_selector('.post')
 assert page.locator('.post-actions [data-go="house/me/wish"]').count()==1
 page.reload();assert page.locator('.tag[data-tag="#мой_дом"]').count()==1
 page.locator('.post-actions [data-go="house/me/wish"]').click();assert page.locator('.scene').count()==1
 checks.append({'check':'Share selected public room, owner and hashtag survive reload','status':'PASS'})
 # Independently owned items, settings and walls.
 page.locator('#profileButton9').click();page.locator('#v9Modal [data-v9="profile"][data-id="anna"]').click();route(page,'house/anna/real')
 assert page.locator('.scene-object[data-id="laptop"]').count()==0
 page.locator('#wallMessage9').fill('Стена только Анны');page.locator('#wallForm9 button').click();page.locator('#profileButton9').click();page.locator('#v9Modal [data-v9="profile"][data-id="me"]').click();route(page,'house/me/real');assert 'Стена только Анны' not in page.locator('.wall').inner_text()
 checks.append({'check':'Independent profile inventories and walls','status':'PASS'})
 # No negative balances or duplicate charges; escape releases dialogs and scroll.
 page.locator('[data-v9="guard"]').click();wallet=page.evaluate("JSON.parse(localStorage.getItem('avito-miry:v9')).profiles.me.wallet");assert wallet['coins']==430
 page.locator('[data-v9="guard"]').click();assert page.evaluate("JSON.parse(localStorage.getItem('avito-miry:v9')).profiles.me.wallet.coins")==430
 page.locator('#walletButton9').click();page.keyboard.press('Escape');assert page.locator('dialog[open]').count()==0;assert page.evaluate("!document.body.classList.contains('sheet-open')")
 route(page,'house/me/real');page.locator('.scene-object[data-id="lamp"]').click();page.keyboard.press('Escape');assert page.locator('dialog[open]').count()==0;assert page.evaluate("!document.body.classList.contains('sheet-open')")
 checks.append({'check':'Single guard charge and accessible dialog closing','status':'PASS'})
 # Voluntary raids only: Anna enables the feature; guest gets at most one virtual trophy.
 page.locator('#profileButton9').click();page.locator('#v9Modal [data-v9="profile"][data-id="anna"]').click();route(page,'house/anna/real');page.locator('[data-v9="raid-consent"]').click()
 page.locator('#profileButton9').click();page.locator('#v9Modal [data-v9="profile"][data-id="me"]').click();route(page,'house/anna/real');page.locator('[data-v9="raid"]').click()
 assert page.evaluate("JSON.parse(localStorage.getItem('avito-miry:v9')).profiles.me.trophies")==1
 page.locator('[data-v9="raid"]').click();assert page.evaluate("JSON.parse(localStorage.getItem('avito-miry:v9')).profiles.me.trophies")==1
 checks.append({'check':'Opt-in raid and single virtual trophy without real property changes','status':'PASS'})
 route(page,'soon/test');assert page.locator('#app h1').inner_text()=='Эта вкладка будет доработана в вашей будущей версии!'
 assert not errors,errors;assert not external,external
 checks.append({'check':'Exact placeholder; no JS errors or external network requests','status':'PASS'})
 context.close();b.close()
server.shutdown();(ROOT/'tests/visual_ux_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(json.dumps(checks,ensure_ascii=False,indent=2))
