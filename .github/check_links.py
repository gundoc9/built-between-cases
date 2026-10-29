# Opens every tool link listed in index.html and reports any that no longer open.
# Run on the 1st of each month by .github/workflows/links.yml. If a link is dead the run fails,
# which makes GitHub send an email, and an issue is opened listing the tools affected.
import json, os, pathlib, re, sys, time, urllib.error, urllib.request

root = pathlib.Path(__file__).resolve().parent.parent
html = (root / 'index.html').read_text(encoding='utf-8')
data = json.loads(re.search(r'<script id="hub-data" type="application/json">(.*?)</script>', html, re.S).group(1))
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
# Answers that mean the site is there but turned the checker away (sign-in walls, bot blocks): not counted as dead.
STILL_THERE = {401, 403, 405, 406, 429}


def check(url):
    problem = None
    for attempt in range(2):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8', 'Accept-Language': 'en-GB,en;q=0.9'})
            with urllib.request.urlopen(request, timeout=30) as response:
                response.read(65536)
                return None
        except urllib.error.HTTPError as e:
            if e.code in STILL_THERE or (e.code == 503 and 'cloudflare' in (e.headers.get('Server') or '').lower()):
                return None
            if e.code in (404, 410):
                return f'page not found ({e.code})'
            problem = f'the site answered with an error ({e.code})'
        except urllib.error.URLError as e:
            reason = str(getattr(e, 'reason', e))
            problem = 'the web address no longer exists' if ('Name or service not known' in reason or 'nodename' in reason) else f'no answer ({reason[:80]})'
        except Exception as e:
            problem = f'no answer ({type(e).__name__})'
        time.sleep(20)
    return problem


links = []
for t in data['tools']:
    links.append((t['name'], t['maker'], t['url']))
    for extra in t.get('more') or []:
        links.append((f"{t['name']}: {extra['label']}", t['maker'], extra['url']))
    if t.get('code') and t['code'] != t['url']:
        links.append((f"{t['name']}: code", t['maker'], t['code']))

problems = []
for name, maker, url in links:
    result = check(url)
    print(('OK   ' if result is None else 'DEAD ') + name + ' | ' + url + ('' if result is None else ' | ' + result), flush=True)
    if result:
        problems.append((name, maker, url, result))

lines = [f'Checked {len(links)} links for {len(data["tools"])} tools on {time.strftime("%d %B %Y", time.gmtime())}.', '']
if problems:
    lines.append(f'{len(problems)} no longer open:')
    lines.append('')
    lines += [f'- **{name}** by {maker}: {result}. {url}' for name, maker, url, result in problems]
    lines += ['', 'The page still lists them. Send this to Claude to check each one and update the list.']
else:
    lines.append('All of them opened.')
report = '\n'.join(lines) + '\n'
(root / 'links-report.md').write_text(report, encoding='utf-8')
summary = os.environ.get('GITHUB_STEP_SUMMARY')
if summary:
    with open(summary, 'a', encoding='utf-8') as f:
        f.write(report)
print(report)
if problems and os.environ.get('REPORT_ONLY', 'false') != 'true':
    sys.exit(1)
