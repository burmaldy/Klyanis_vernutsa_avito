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
    page.evaluate("location.hash='house/me'")
    page.wait_for_selector('.room-products .prod')
    assert page.locator('.room-products .prod').count() == 3
    assert page.locator('.room-photo').evaluate('(img)=>img.complete && img.naturalWidth >= 1000')
    for item in ['sofa', 'lamp', 'table']:
        page.locator(f'[data-item="{item}"]').click()
        assert page.locator('#itemSheet').is_visible()
        assert page.locator('[data-action="open-linked"]').get_attribute('data-link') == item
        if item != 'table':
            page.locator('[data-action="close-sheet"]').click()
    page.locator('[data-action="open-linked"]').click()
    page.wait_for_selector('.listing')
    assert page.url.endswith('#listing/table')
    page.evaluate("location.hash='house/me'")
    page.locator('[data-room="wish"]').click()
    assert page.locator('.room-products .prod').count() == 4
    page.locator('[data-item="plant"]').click()
    page.locator('[data-action="open-linked"]').click()
    assert page.locator('#modal').is_visible()
    page.locator('#modalClose').click()
    page.locator('[data-item="plant"]').click()
    page.locator('#itemSheet [data-action="fav"]').click()
    page.locator('[data-action="close-sheet"]').click()
    assert page.locator('.room-products .heart[data-id="plant"]').get_attribute('aria-pressed') == 'true'
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path='/tmp/avito-realistic-house-mobile.png', full_page=True)
    page.set_viewport_size({'width':1440,'height':1000})
    page.screenshot(path='/tmp/avito-realistic-house.png', full_page=True)
    # The list card and the sheet use the same unavailable-product guard.
    page.locator('.room-products [data-go="listing/plant"]').first.click()
    assert page.locator('#modal').is_visible()
    assert page.locator('#modal h3').is_visible()
    page.locator('#modalConfirm').click()
    page.wait_for_selector('#app .prod')
    assert page.url.endswith('#similar/plant')
    assert page.locator('#app [data-go="listing/plant"]').count() == 0
    page.evaluate("location.hash='listing/plant'")
    page.wait_for_selector('.favorites-empty')
    assert page.locator('#app h1').inner_text() == 'РАСКУПИЛИ'
    page.evaluate("location.hash='house/me'")
    page.wait_for_selector('.room-photo')
    assert not page.locator('#itemSheet').is_visible()
    page.locator('[data-item="sofa"]').click()
    assert page.locator('#itemSheet').is_visible()
    assert page.locator('#itemSheet').inner_text().find('Для отсевающих в продаже товаров будет предложена альтернатива') >= 0
    assert page.locator('#itemSheet').bounding_box()['y'] > 0
    page.keyboard.press('Escape')
    assert not page.locator('#itemSheet').is_visible()
    assert page.evaluate("!document.body.classList.contains('sheet-open')")
    # Every community supports joining, publishing, reactions and comments.
    for cat in ['home','car','tech','travel','pets','repair']:
        page.evaluate('(cat)=>{location.hash="community/"+cat}', cat)
        page.wait_for_selector('#postForm')
        assert page.locator('.post[data-post]').count() >= 1
        page.locator('[data-action="join"]').click()
        assert page.locator('[data-action="join"]').get_attribute('aria-pressed') == 'true'
        page.locator('#postTitle').fill('Проверка сообщества '+cat)
        page.locator('#postText').fill('Поделитесь опытом выбора товаров. <script>bad()</script>')
        page.locator('#postForm button[type="submit"]').click()
        page.wait_for_selector('#commentForm')
        page.locator('[data-action="post-like"]').click()
        assert page.locator('[data-action="post-like"]').get_attribute('aria-pressed') == 'true'
        page.locator('#commentText').fill('Полезное обсуждение — '+cat)
        page.locator('#commentForm button').click()
        assert page.locator('.comment').last.inner_text().endswith('Полезное обсуждение — '+cat)
        page.reload()
        assert page.locator('.post-title').inner_text() == 'Проверка сообщества '+cat
        assert page.locator('.comment').last.inner_text().endswith('Полезное обсуждение — '+cat)
        assert page.locator('[data-action="post-like"]').get_attribute('aria-pressed') == 'true'
    page.set_viewport_size({'width':390,'height':844})
    page.evaluate("location.hash='community/pets'")
    page.wait_for_selector('#postForm')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path='/tmp/avito-community-updated.png', full_page=True)
    page.evaluate("location.hash='house/me'")
    page.locator('[data-item="sofa"]').click()
    assert page.locator('#itemSheet').is_visible()
    page.wait_for_function("Math.abs(document.querySelector('#itemSheet').getBoundingClientRect().bottom-innerHeight)<=1")
    box=page.locator('#itemSheet').bounding_box()
    assert abs(box['y']+box['height']-844) <= 1
    page.screenshot(path='/tmp/avito-bottom-sheet.png')
    page.locator('[data-action="close-sheet"]').click()
    assert not errors, errors
    browser.close()
server.shutdown()
print('PASS: favorites, reload, invalid storage, mobile layout, scrolling, search, house bottom sheet, unavailable products and alternatives, all six communities (join, publish, comment, react, reload); no JS errors')
