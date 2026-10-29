# Draws the link-preview card (og-card.png) and the phone picture used on the My work page (phone.webp).
# Run by .github/workflows/pages.yml on every upload; the pages are served over a local web server so the stored fonts in fonts/ load.
import functools, http.server, json, pathlib, re, sys, threading
from playwright.sync_api import sync_playwright
from PIL import Image

root = pathlib.Path(__file__).resolve().parent.parent
page = root / 'index.html'
data = json.loads(re.search(r'<script id="hub-data" type="application/json">(.*?)</script>', page.read_text(encoding='utf-8'), re.S).group(1))
tools = data['tools']
AREAS = [('airway', 'Airway', '#076772'), ('regional', 'Regional & access', '#735603'), ('drugs', 'Drugs & TIVA', '#863F61'),
         ('eeg', 'EEG & monitors', '#6E4885'), ('vent', 'Ventilation', '#195F91'), ('heart', 'Heart, blood & echo', '#8C4039'),
         ('icu', 'Intensive care', '#505294'), ('safety', 'Crisis & safety', '#85490F'), ('periop', 'Before & after surgery', '#5D6002'),
         ('learning', 'Learning & practice', '#216B3C')]
summary = {
    'tools': len(tools),
    'makers': len({t['maker'] for t in tools}),
    'countries': len({t['cc'] for t in tools if t.get('cc')}),
    'areas': [[label, n, colour] for key, label, colour in AREAS if (n := sum(1 for t in tools if t['areas'][0] == key))],
}
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_address[1]}/'
with sync_playwright() as p:
    browser = p.chromium.launch()
    card = browser.new_page(viewport={'width': 1200, 'height': 630})
    card.goto(base + '.github/og.html', wait_until='networkidle')
    print('card', card.evaluate('d => window.render(d)', summary))
    card.wait_for_timeout(300)
    card.screenshot(path=str(root / 'og-card.png'))
    phone = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, color_scheme='light').new_page()
    phone.goto(base + 'index.html', wait_until='networkidle')
    phone.evaluate('document.fonts.ready.then(() => 0)')
    phone.add_style_tag(content='.controls{display:none!important}')
    phone.wait_for_timeout(400)
    shot = root / '.github' / 'phone.png'
    phone.screenshot(path=str(shot), clip={'x': 0, 'y': 0, 'width': 390, 'height': 487.5})
    Image.open(shot).convert('RGB').resize((592, 740), Image.LANCZOS).save(root / 'phone.webp', 'WEBP', quality=86, method=6)
    browser.close()
server.shutdown()
print('done', summary['tools'], 'tools')
