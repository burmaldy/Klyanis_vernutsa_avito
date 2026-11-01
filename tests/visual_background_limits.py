from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1];server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start();checks=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);p=b.new_page(viewport={'width':1365,'height':1000});p.goto(f'http://127.0.0.1:{server.server_port}/Avito_Miry_v9_visual.html');p.evaluate("go('house/me/wish')");p.wait_for_selector('[data-visual="settings"]');p.locator('[data-visual="settings"]').click()
 p.locator('#visualBackgroundFile').set_input_files({'name':'too-large.png','mimeType':'image/png','buffer':b'x'*(1024*1024+1)})
 assert 'не более 1 МБ' in p.locator('#visualError').inner_text();assert p.evaluate('visualDraft.config.custom===null');checks.append({'check':'Oversize PNG rejected before replacement of background','status':'PASS'})
 p.locator('[data-visual="theme"][data-id="creative"]').click()
 p.evaluate("()=>{window.originalSetItem=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='avito-miry:visual:v1')throw new DOMException('Quota','QuotaExceededError');return window.originalSetItem.call(this,k,v)}}")
 p.locator('#visualSettingsForm button[type="submit"]').click();assert 'Не удалось сохранить' in p.locator('#visualError').inner_text();assert p.evaluate("cfgVisual().theme==='scandi'");assert p.locator('#v9Modal').is_visible();checks.append({'check':'Quota error leaves saved settings unchanged and keeps recoverable draft','status':'PASS'})
 p.evaluate('()=>{Storage.prototype.setItem=window.originalSetItem}');p.locator('#visualSettingsForm button[type="submit"]').click();assert p.evaluate("cfgVisual().theme==='creative'")
 p.wait_for_function("!document.querySelector('#toast').classList.contains('show')")
 p.locator('.visual-scene').screenshot(path=str(ROOT/'downloads/Avito_Miry_v9_visual_preview.png'))
 p.evaluate("go('house/me/real')");p.wait_for_selector('.visual-scene');assert p.evaluate("cfgVisual().theme==='scandi'");p.evaluate("go('house/me/wish')");p.wait_for_selector('.visual-scene');assert p.evaluate("cfgVisual().theme==='creative'");p.reload();assert p.evaluate("cfgVisual().theme==='creative'");checks.append({'check':'Interior settings are separate for real/wish and persist across reload','status':'PASS'})
 p.locator('[data-visual="settings"]').click();p.locator('#v9Modal').screenshot(path=str(ROOT/'downloads/Avito_Miry_v9_visual_gallery.png'));p.keyboard.press('Escape');assert p.locator('dialog[open]').count()==0
 b.close()
server.shutdown();(ROOT/'tests/visual_background_limits_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(json.dumps(checks,ensure_ascii=False))
