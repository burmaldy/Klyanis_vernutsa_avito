from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from functools import partial
from playwright.sync_api import sync_playwright
import json
root=Path(__file__).resolve().parents[1];s=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root)));Thread(target=s.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);p=b.new_page();p.goto(f'http://127.0.0.1:{s.server_port}/Avito_Miry_v9_visual.html');p.evaluate("go('house/me/wish')");p.wait_for_function("state.room==='wish'");p.evaluate("openVisualSettings()")
 p.locator('#visualFloor').select_option('walnut');assert p.evaluate("document.querySelector('.draft-preview img').getAttribute('src')===roomBackgroundVisual(visualDraft.config)")
 p.locator('#visualSettingsForm [type="submit"]').click();p.reload();p.evaluate("go('house/me/wish')");p.wait_for_function("state.room==='wish'");assert p.evaluate("cfgVisual().floor==='walnut'")
 p.evaluate("openVisualSettings();const c=document.createElement('canvas');c.width=100;c.height=100;visualDraft.config.custom=c.toDataURL();drawVisualSettings()")
 assert p.locator('#visualFloor').is_disabled();p.locator('[data-visual="cancel-settings"]').click()
 p.evaluate("go('house/anna/wish')");p.wait_for_function("activeOwner==='anna'");assert p.locator('[data-boundary-action="edit"]').count()==0
 b.close()
s.shutdown();(root/'tests/floor_settings_results.json').write_text(json.dumps({'material_selector_preview_and_reload':'PASS','custom_photo_material_disabled':'PASS','guest_boundary_edit_hidden':'PASS'},indent=2));print('PASS: floor selector preview/save/reload, custom photo notice, guest boundary protection')
