# Downloads the page's three typefaces from Google Fonts once and stores them in fonts/,
# with their licences, so the live page loads nothing from outside the site.
# Run by .github/workflows/pages.yml; does nothing once fonts/fonts.css exists.
import pathlib, re, sys, urllib.request

root = pathlib.Path(__file__).resolve().parent.parent
out = root / 'fonts'
if (out / 'fonts.css').exists():
    print('fonts already stored')
    sys.exit(0)
CSS = ('https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;1,400'
       '&family=Red+Hat+Text:wght@400..700&family=B612+Mono:wght@400;700&display=swap')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60).read()

css = get(CSS).decode()
out.mkdir(exist_ok=True)
faces = []
for subset, block in re.findall(r'/\* ([\w-]+) \*/\s*(@font-face\s*\{[^}]*\})', css):
    if subset not in ('latin', 'latin-ext'):
        continue
    family = re.search(r"font-family:\s*'([^']+)'", block).group(1)
    style = re.search(r'font-style:\s*(\w+)', block).group(1)
    weight = re.search(r'font-weight:\s*([\d ]+);', block).group(1).strip().replace(' ', '-')
    src = re.search(r'url\((https://[^)]+\.woff2)\)', block).group(1)
    name = f"{family.lower().replace(' ', '-')}-{weight}-{style}-{subset}.woff2"
    (out / name).write_bytes(get(src))
    faces.append(block.replace(src, name))
    print('saved', name)
if not faces:
    sys.exit('no font faces found')
for folder in ('spectral', 'redhattext', 'b612mono'):
    try:
        (out / f'OFL-{folder}.txt').write_bytes(get(f'https://raw.githubusercontent.com/google/fonts/main/ofl/{folder}/OFL.txt'))
    except Exception as e:
        print('licence not fetched for', folder, e)
(out / 'fonts.css').write_text('/* Spectral, Red Hat Text and B612 Mono, SIL Open Font License (OFL-*.txt), stored here so the page loads nothing from outside the site. */\n' + '\n'.join(faces) + '\n', encoding='utf-8')
print(len(faces), 'faces stored')
