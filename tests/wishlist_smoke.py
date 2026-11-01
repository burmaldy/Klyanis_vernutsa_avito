from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright

server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).resolve().parents[1])))
Thread(target=server.serve_forever, daemon=True).start()
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
    page.evaluate('localStorage.clear()')
    page.reload()
    for cat in ['home','car','tech','travel','clothes']:
        page.evaluate('(cat)=>{location.hash="catalog/"+cat}', cat)
        page.wait_for_selector('#app .prod')
        assert page.locator('#app .prod').count() >= 3, cat
        assert page.locator('#app .prod img').evaluate_all('(imgs)=>imgs.every(img=>img.complete && img.naturalWidth>1000)'), cat
    # Each target category offers three relevant, existing communities.
    for item in ['tent2','jacket','laptop','sedan','shelf']:
        page.evaluate('(id)=>{location.hash="listing/"+id}', item)
        page.wait_for_selector('.listing')
        assert page.locator('.community-choice').count() >= 3
    # Add from the listing and open the appropriate place; choices survive reloads.
    for item, zone in [('jacket','wardrobe'),('laptop','shelf'),('sedan','garage'),('tent2','wardrobe')]:
        page.evaluate('(id)=>{location.hash="listing/"+id}', item)
        page.wait_for_selector('.listing')
        page.locator('[data-action="wish-add"]').click()
        assert page.locator('[data-action="wish-add"]').inner_text() == '✓ В комнате желаний'
        page.locator('[data-action="wish-add"]').click()
        page.locator('[data-action="wish-open"]').click()
        page.wait_for_selector('.storage-products')
        assert page.url.endswith('#storage/'+zone)
        assert page.locator(f'.storage-products .heart[data-id="{item}"]').count()==1
        page.reload()
        assert page.locator(f'.storage-products .heart[data-id="{item}"]').count()==1
        page.locator(f'[data-action="wish-preview"][data-id="{item}"]').click()
        assert page.locator('#itemSheet').is_visible()
        assert page.locator('[data-action="open-linked"]').get_attribute('data-link') == item
        page.locator('[data-action="close-sheet"]').click()
    # Candidate buttons add another device to the shelf; removing affects only that wish.
    page.evaluate("location.hash='storage/shelf'")
    page.wait_for_selector('.storage-candidates')
    page.locator('[data-action="wish-add"][data-id="speaker"]').click()
    assert page.locator('.storage-products .prod').count()==2
    page.locator('[data-action="wish-remove"][data-id="speaker"]').click()
    assert page.locator('.storage-products .prod').count()==1
    page.reload()
    assert page.locator('.storage-products .prod').count()==1
    # Furniture can also be saved and removed from the room.
    page.evaluate("location.hash='listing/shelf'")
    page.locator('[data-action="wish-add"]').click()
    page.locator('[data-action="wish-open"]').click()
    page.wait_for_selector('.room-products')
    assert page.locator('.room-products .heart[data-id="shelf"]').count()==1
    assert page.locator('.room-zone').count()==3
    page.locator('[data-action="wish-remove"][data-id="shelf"]').click()
    assert page.locator('.room-products .heart[data-id="shelf"]').count()==0
    page.screenshot(path='/tmp/avito-wish-storage.png', full_page=True)
    # The expert question includes the actual tent listing and works as a discussion.
    page.evaluate("location.hash='listing/tent2'")
    page.locator('[data-action="ask-expert"]').click()
    page.wait_for_selector('#postForm')
    assert page.url.endswith('#community/experts')
    assert 'Палатка двухместная' in page.locator('#postTitle').input_value()
    assert page.locator('.attached-product [data-go="listing/tent2"]').count()==1
    page.locator('#postText').fill('Подойдёт ли эта палатка для двух человек в летнем походе?')
    page.locator('#postForm button[type="submit"]').click()
    page.wait_for_selector('#commentForm')
    assert page.locator('.post-actions [data-go="listing/tent2"]').count()==1
    page.reload()
    assert page.locator('.post-actions [data-go="listing/tent2"]').count()==1
    # Mobile layout and entering all storage zones from the wish room.
    page.set_viewport_size({'width':390,'height':844})
    for zone in ['wardrobe','shelf','garage']:
        page.evaluate('(zone)=>{location.hash="storage/"+zone}', zone)
        page.wait_for_selector('.storage-section')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), zone
    page.locator('[data-action="wish-room"]').click()
    page.wait_for_selector('.storage-grid')
    assert page.locator('.room-switch [data-room="wish"]').get_attribute('class')=='active'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path='/tmp/avito-wish-storage-mobile.png', full_page=True)
    # An empty room and invalid stored IDs are safe.
    page.evaluate("localStorage.setItem('avito-miry:wishes:v1', JSON.stringify(['unknown',null]))")
    page.reload()
    page.locator('[data-room="wish"]').click()
    assert page.locator('.room-products .prod').count()==0
    assert not errors, errors
    browser.close()
server.shutdown()
print('PASS: 5 catalog categories, related communities, saved wardrobe/shelf/garage inventory, add/remove/reload, expert product context, mobile layout, empty storage; no JS errors')
