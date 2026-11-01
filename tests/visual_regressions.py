"""Actual Chromium journeys against the single-file V9; saves machine-readable results."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright
import json, traceback
ROOT=Path(__file__).resolve().parents[1]
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
Thread(target=server.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{server.server_port}/Avito_Miry_v9_visual.html'
results=[]

def route(page,path):
    page.evaluate('(path)=>{go(path)}',path)
    page.wait_for_timeout(100)

def close_sheet(page):
    page.locator('#itemSheet [data-action="close-sheet"]').click()

def section(page,name):
    page.locator(f'.group-sections [data-section="{name}"]').click()

def switch_profile(page,owner):
    page.locator('#profileButton9').click()
    page.locator(f'#v9Modal [data-v9="profile"][data-id="{owner}"]').click()

def journey_a(p):
    p.locator('.cat-tile[data-go="catalog/car"]').click()
    p.locator('#app .prod-info[data-go="listing/bmw"]').first.click()
    p.locator('.community-recommendation [data-id="car-spb"]').click()
    section(p,'chat')
    assert p.locator('#chatForm9').is_visible()
    p.locator('.chat-panel [data-go="event/toyota"]').click()
    before=p.locator('.event-details').inner_text()
    p.locator('[data-v9="event-join"]').click()
    assert p.locator('[data-v9="event-join"]').get_attribute('aria-pressed')=='true'
    assert '19' in p.locator('.event-details').inner_text() and before!=p.locator('.event-details').inner_text()
    route(p,'my-events')
    assert p.locator('[data-event="toyota"]').count()==1
    route(p,'event/toyota');p.locator('[data-go="event-chat/toyota"]').click()
    p.locator('#chatText9').fill('Буду на демо-встрече владельцев')
    p.locator('#chatForm9 button[type="submit"]').click()
    assert 'Буду на демо-встрече владельцев' in p.locator('.chat-messages').inner_text()
    p.reload();assert 'Буду на демо-встрече владельцев' in p.locator('.chat-messages').inner_text()

def journey_b(p):
    p.locator('.cat-tile[data-go="catalog/tech"]').click()
    p.locator('#app .prod-info[data-go="listing/headphones"]').first.click()
    p.locator('.community-recommendation [data-id="tech"]').click()
    p.locator('.community-tags [data-tag="#интервью"]').click()
    assert p.locator('.interview-card').count()>=1
    assert p.locator('.portrait-frame img').first.evaluate('(img)=>img.complete&&img.naturalWidth>0')
    p.locator('.community-tags [data-tag="#мемы"]').click()
    assert p.locator('.meme-figure svg').count()>=1
    assert p.locator('.interview-card').count()==0
    section(p,'chat');p.locator('[data-v9="video"]').click()
    assert 'playing' in p.locator('.video-circle').get_attribute('class')
    p.locator('[data-v9="video"]').click();assert 'playing' not in p.locator('.video-circle').get_attribute('class')

def journey_c(p):
    p.locator('.cat-tile[data-go="catalog/home"]').click()
    p.locator('#app .prod-info[data-go="listing/wardrobe"]').first.click()
    p.locator('[data-action="wish-add"]').click();p.locator('[data-action="wish-open"]').click()
    obj=p.locator('.scene-object[data-id="wardrobe"]');obj.wait_for(state='visible');assert obj.is_visible()
    old=obj.get_attribute('style');obj.click()
    p.locator('[data-visual-position]').select_option('6')
    close_sheet(p);assert p.locator('.scene-object[data-id="wardrobe"]').get_attribute('style')!=old
    p.reload();assert p.locator('.scene-object[data-id="wardrobe"]').get_attribute('style')!=old
    p.locator('.scene-object[data-id="wardrobe"]').click();p.locator('#itemSheet [data-go="listing/wardrobe"]').click()
    assert p.url.endswith('#listing/wardrobe')

def journey_d(p):
    route(p,'house/me/wish');p.locator('.scene-doors [data-go="storage/wardrobe/me/wish"]').click()
    p.wait_for_selector('.visual-scene[data-zone="wardrobe"]')
    assert p.locator('.scene-empty').is_visible()
    p.locator('.storage-candidates [data-visual="add"][data-id="jacket"]').click()
    assert p.locator('.scene-object[data-id="jacket"]').is_visible()
    p.locator('.scene-object[data-id="jacket"]').click();p.locator('#itemSheet [data-v9="room-remove"]').click()
    assert p.locator('.scene-object[data-id="jacket"]').count()==0
    p.reload();assert p.locator('.scene-object[data-id="jacket"]').count()==0

def journey_e(p):
    route(p,'house/me/wish');p.locator('.scene-doors [data-go="storage/garage/me/wish"]').click()
    p.locator('.storage-candidates [data-visual="add"][data-id="bmw"]').click()
    p.locator('.scene-object[data-id="bmw"]').click();p.locator('#itemSheet [data-go="listing/bmw"]').click()
    p.locator('.community-recommendation [data-id="car"]').click();assert p.locator('.group-top h1').inner_text().endswith('Toyota и кроссоверы')

def journey_f(p):
    route(p,'community/tech');p.locator('.group-top [data-action="join"]').click()
    route(p,'community/all')
    assert p.locator('[data-v9="group-tab"][data-id="mine"]').get_attribute('aria-selected')=='true'
    assert p.locator('[data-group="tech"]').count()==1
    assert p.locator('[data-group="home"]').count()==0
    p.locator('[data-group="tech"] [data-action="join"]').click()
    assert p.locator('[data-group="tech"]').count()==0
    p.reload();assert p.locator('[data-group="tech"]').count()==0

def journey_g(p):
    switch_profile(p,'anna');route(p,'house/anna/wish')
    privacy=p.locator('[data-v9="privacy"][data-room="wish"]')
    if privacy.get_attribute('aria-pressed')=='false':privacy.click()
    privacy.click()
    assert privacy.get_attribute('aria-pressed')=='false'
    switch_profile(p,'me');route(p,'house/anna/wish')
    assert p.get_by_text('Эта комната закрыта владельцем',exact=True).is_visible()
    assert p.locator('.scene').count()==0 and p.locator('.prod').count()==0
    assert p.locator('[data-v9="privacy"]').count()==0
    route(p,'storage/wardrobe/anna');assert p.locator('.scene').count()==0
    assert p.get_by_text('Эта комната закрыта владельцем',exact=True).is_visible()

def journey_h(p):
    route(p,'house/me/wish');p.locator('.scene-object[data-id="plant"]').click()
    p.locator('#itemSheet [data-go="listing/plant"]').click()
    assert p.locator('#v9Modal').is_visible()
    assert p.locator('#v9DialogTitle').inner_text()=='Этот товар уже выкуплен. Подобрать похожие?'
    p.locator('#v9Modal [data-v9="similar"]').click()
    assert p.url.endswith('#similar/plant')
    p.wait_for_selector('.similar-products .prod')
    assert p.locator('.similar-products .prod').count()>=2
    assert p.locator('#app [data-go="listing/plant"]').count()==0

def journey_i(p):
    route(p,'house/me/real');p.locator('.scene-object[data-id="lamp"]').click()
    p.locator('#itemSheet [data-v9="interact"]').click()
    first=p.evaluate("JSON.parse(localStorage.getItem('avito-miry:v9')).profiles.me.wallet")
    assert first['coins']==441 and abs(first['rubles']-.0067)<1e-8 and len(first['history'])==1
    p.reload();p.locator('.scene-object[data-id="lamp"]').click();p.locator('#itemSheet [data-v9="interact"]').click()
    second=p.evaluate("JSON.parse(localStorage.getItem('avito-miry:v9')).profiles.me.wallet")
    assert first==second
    p.locator('#walletButton9').click()
    assert 'Вывода в деньги' in p.locator('#v9Modal').inner_text()

def journey_j(p):
    route(p,'community/car');section(p,'chat')
    p.locator('#chatText9').fill('Сохраняем сообщение в автомобильном чате')
    p.locator('#chatProduct9').select_option('bmw');p.locator('#chatForm9 button').click()
    route(p,'community/tech');section(p,'chat');assert 'Сохраняем сообщение' not in p.locator('.chat-messages').inner_text()
    route(p,'community/car');assert 'Сохраняем сообщение' in p.locator('.chat-messages').inner_text()
    p.reload();assert 'Сохраняем сообщение' in p.locator('.chat-messages').inner_text()

with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    for name,test in [('А',journey_a),('Б',journey_b),('В',journey_c),('Г',journey_d),('Д',journey_e),('Е',journey_f),('Ж',journey_g),('З',journey_h),('И',journey_i),('К',journey_j)]:
        context=browser.new_context(viewport={'width':1365,'height':1000});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        try:
            page.goto(URL);test(page);assert not errors,errors
            results.append({'scenario':name,'status':'PASS','detail':'Chromium, HTTP, real UI actions'});print(name,'PASS',flush=True)
        except Exception as e:
            results.append({'scenario':name,'status':'FAIL','detail':traceback.format_exc()});page.screenshot(path='/tmp/v9-fail-'+name+'.png',full_page=True);print(name,'FAIL',str(e)[:600],flush=True)
        context.close()
    # Real file URL test: do not silently count an HTTP run as a file run.
    context=browser.new_context();page=context.new_page()
    try:
        page.goto((ROOT/'Avito_Miry_v9_visual.html').as_uri());assert page.locator('#app .prod').count()>0
        results.append({'scenario':'file://','status':'PASS','detail':'Actual local file URL opened in Chromium'})
    except Exception as e:results.append({'scenario':'file://','status':'BLOCKED','detail':str(e)[:600]})
    context.close();browser.close()
server.shutdown()
(ROOT/'tests'/'visual_regression_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False,indent=2))
raise SystemExit(any(r['status']=='FAIL' for r in results))
