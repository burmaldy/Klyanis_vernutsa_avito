from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread

server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).resolve().parents[1])))
Thread(target=server.serve_forever, daemon=True).start()
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
    assert page.locator('.cats-grid').is_visible()
    for key in ['sofa','lamp']:
        assert page.locator(f'.prod img[data-go="listing/{key}"]').evaluate('(img)=>img.naturalWidth') >= 900
    page.screenshot(path='/tmp/avito-home.png', full_page=True)
    page.evaluate('localStorage.clear()')
    page.reload()
    page.locator('.favorites-nav').click()
    assert page.locator('.cats-grid').is_hidden()
    assert page.get_by_text('В избранном пока пусто', exact=True).is_visible()
    page.locator('#app [data-go="home"]').first.click()
    page.locator('.heart[data-id="sofa"]').click()
    page.locator('.heart[data-id="bmw"]').click()
    assert page.locator('#favoritesCounter').inner_text() == '2'
    page.locator('.favorites-nav').click()
    assert page.locator('#app .prod').count() == 2
    assert page.locator('#app .heart[data-id="sofa"]').get_attribute('aria-pressed') == 'true'
    page.reload()
    assert page.locator('#app .prod').count() == 2
    page.locator('#app [data-go="listing/sofa"]').first.click()
    page.locator('[data-action="fav"]').click()
    page.locator('.favorites-nav').click()
    assert page.locator('#app .prod').count() == 1
    assert page.locator('#app .heart[data-id="bmw"]').count() == 1
    page.locator('#app .heart').click()
    assert page.get_by_text('В избранном пока пусто', exact=True).is_visible()
    page.evaluate("localStorage.setItem('avito-miry:favorites:v1', 'broken')")
    page.reload()
    assert page.locator('#favoritesCounter').inner_text() == '0'
    page.evaluate("localStorage.setItem('avito-miry:favorites:v1', JSON.stringify(['sofa','sofa','unknown',null]))")
    page.reload()
    assert page.locator('#app .prod').count() == 1
    page.set_viewport_size({'width':390,'height':844})
    assert page.locator('.favorites-nav').is_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), page.evaluate("[...document.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>[e.tagName,e.className,e.getBoundingClientRect().right]).slice(0,15)")
    for route, selector in [('community/all','.community-cards'),('house/me','.room-frame'),('catalog/tech','.grid5')]:
        page.evaluate('(route)=>{location.hash=route}', route)
        page.wait_for_selector(selector)
        assert page.locator('.cats-grid').is_hidden()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), route
        page.screenshot(path='/tmp/avito-'+route.split('/')[0]+'.png', full_page=True)
    page.locator('#searchInput').fill('наушники')
    page.locator('.search-submit').click()
    page.wait_for_selector('#app .prod')
    assert page.locator('#app .prod').count() == 1
    assert page.locator('#app .prod-name').inner_text() == 'Беспроводные наушники'
    assert page.locator('.cats-grid').is_hidden()
    page.locator('.logo').click()
    assert page.locator('.cats-grid').is_visible()
    page.screenshot(path='/tmp/avito-mobile-home.png', full_page=True)
    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    page.wait_for_function("document.querySelector('.cats-grid').getBoundingClientRect().bottom < 0")
    page.screenshot(path='/tmp/avito-mobile-scrolled.png')
    page.evaluate('window.scrollTo(0, 0)')
    page.wait_for_function("document.querySelector('.cats-grid').getBoundingClientRect().top >= 0")
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors, errors
    browser.close()
server.shutdown()
print('PASS: empty state, add/remove, listing sync, reload, invalid storage, mobile layout, existing routes; no JS errors')
