#!/usr/bin/env python3
"""Build the Takes section from _takes/*.md.

Writes takes/index.html, takes/<slug>.html, feed.xml, images/takes/<slug>.png (share images)
and the takes entries in sitemap.xml. Standard library only.

  python3 _tools/build_takes.py            build everything
  python3 _tools/build_takes.py --number   print a fresh random take number
"""
import datetime, html, os, random, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://jonesco.com'
CSS_V = 39
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'


# ---------- reading ----------
def parse(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', raw, re.S)
    if not m:
        sys.exit(f'{path}: missing frontmatter')
    meta = {}
    for line in m.group(1).splitlines():
        line = re.sub(r'\s+#.*$', '', line)
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    for k in ('title', 'date', 'slug', 'number'):
        if not meta.get(k):
            sys.exit(f'{path}: frontmatter needs {k}')
    meta['tags'] = [t.strip() for t in meta.get('tags', '').strip('[]').split(',') if t.strip()]
    meta['date'] = datetime.date.fromisoformat(meta['date'])
    meta['body_md'] = m.group(2).strip()
    meta['path'] = path
    if '\u2014' in raw:
        sys.exit(f'{path}: contains an em dash')
    return meta


def curl(s):
    """Curly quotes and apostrophes in text (not inside tags)."""
    s = re.sub(r"(^|[\s(\[])'", '\\1\u2018', s)
    s = s.replace("'", '\u2019')
    s = re.sub(r'(^|[\s(\[])"', '\\1\u201c', s)
    return s.replace('"', '\u201d')


def inline(s):
    links = []
    def keep(m):
        links.append((m.group(1), m.group(2)))
        return f'\x00{len(links) - 1}\x00'
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', keep, s)
    s = curl(html.escape(s, quote=False))
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
    def put(m):
        text, url = links[int(m.group(1))]
        return f'<a href="{html.escape(url)}">{curl(html.escape(text, quote=False))}</a>'
    return re.sub(r'\x00(\d+)\x00', put, s)


def to_html(md):
    return '\n'.join(f'<p>{inline(" ".join(p.split()))}</p>' for p in re.split(r'\n\s*\n', md) if p.strip())


def plain(md):
    return curl(re.sub(r'\*|\[([^\]]+)\]\([^)]+\)', lambda m: m.group(1) or '', ' '.join(md.split())))


def long_date(d):
    return f'{d.strftime("%B")} {d.day}, {d.year}'


# ---------- page frame (same as the case study pages) ----------
def page(title, desc, url, body, og_image=None, extra_head=''):
    t, d = html.escape(title), html.escape(desc)
    img = f'\n    <meta property="og:image" content="{og_image}" />\n    <meta name="twitter:card" content="summary_large_image" />\n    <meta name="twitter:image" content="{og_image}" />' if og_image else ''
    return f'''<!doctype html>
<html lang="en" dir="ltr" class="compact-header">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png" />
    <link rel="manifest" href="/manifest.json" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#000000" />
    <title>{t}</title>
    <meta name="description" content="{d}" />
    <meta name="author" content="Wes Jones" />
    <link rel="canonical" href="{url}" />
    <meta property="og:title" content="{t}" />
    <meta property="og:description" content="{d}" />
    <meta property="og:type" content="article" />
    <meta property="og:url" content="{url}" />{img}
    <link rel="alternate" type="application/rss+xml" title="Takes by Wes Jones" href="/feed.xml" />
    <link rel="apple-touch-icon" sizes="180x180" href="/jonesco-bug180.png" />
    <link rel="apple-touch-icon" sizes="152x152" href="/jonesco-bug152.png" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Libre+Franklin:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/jonesco/system@1.0.0/system.css" />
    <link rel="stylesheet" href="/css/jonesco.css?v={CSS_V}" />{extra_head}
  </head>
  <body>
    <header class="site-header">
      <div class="bar">
        <a class="brand" href="/" aria-label="Jonesco, home">
          <img src="/images/jonesco-logo.svg" alt="Jonesco" />
        </a>
        <nav>
          <a href="/#work">Work</a>
          <a href="/#contact">Contact</a>
          <a href="/images/Wes_Jones_Resume.pdf" class="opt">Resumé</a>
        </nav>
      </div>
    </header>
{body}
    <footer class="site-footer">
      <div class="bar">
        <div class="links">
          <a href="mailto:wes@jonesco.com">wes@jonesco.com</a>
          <a href="https://www.linkedin.com/in/wes-jones-a0914312/" target="_blank" rel="noreferrer">LinkedIn</a>
          <a href="/feed.xml">RSS</a>
        </div>
        <small>© <span class="yr">2026</span> Wes Jones</small>
      </div>
    </footer>
    <script>document.querySelectorAll('.yr').forEach(e => e.textContent = new Date().getFullYear());</script>
  </body>
</html>
'''


def take_page(t, nxt):
    also = [(k, n) for k, n in (('linkedin', 'LinkedIn'), ('x', 'X'), ('bluesky', 'Bluesky')) if t.get(k)]
    also_html = ''
    if also:
        links = ' · '.join(f'<a href="{html.escape(t[k])}" target="_blank" rel="noreferrer">{n}</a>' for k, n in also)
        also_html = f'\n          <p class="take-also">Also on {links}</p>'
    band = ''
    if nxt:
        band = f'''
    <a class="next-band" href="/takes/{nxt["slug"]}">
      <div class="bar">
        <span class="next-label">Next take &gt;</span>
        <span class="next-title">{html.escape(curl(nxt["title"]))}</span>
      </div>
    </a>'''
    body = f'''    <div id="root">
      <div class="page take">
        <div><article>
          <h5 id="rcorners1">Take #{t["number"]}</h5>
          <h1>{html.escape(curl(t["title"]))}</h1>
          <div class="take-body">
{to_html(t["body_md"])}
          </div>
          <p class="take-meta"><time datetime="{t["date"]}">{long_date(t["date"])}</time> · <a href="/takes/">All takes</a></p>{also_html}
        </article></div>
      </div>
    </div>{band}'''
    url = f'{SITE}/takes/{t["slug"]}'
    desc = plain(t['body_md'])
    desc = desc if len(desc) <= 200 else desc[:desc.rfind(' ', 0, 197)] + '…'
    jsonld = ('\n    <script type="application/ld+json">{"@context":"https://schema.org","@type":"BlogPosting",'
              f'"headline":{json_str(curl(t["title"]))},"datePublished":"{t["date"]}","url":"{url}",'
              '"author":{"@type":"Person","name":"Wes Jones","url":"https://jonesco.com"}}</script>')
    return page(f'{curl(t["title"])} | Jonesco', desc, url, body, f'{SITE}/images/takes/{t["slug"]}.png', jsonld)


def json_str(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def index_page(takes):
    items = '\n'.join(f'''          <li>
            <a href="/takes/{t["slug"]}">
              <span class="take-num">Take #{t["number"]}</span>
              <span class="take-title">{html.escape(curl(t["title"]))}</span>
              <span class="take-date">{long_date(t["date"])}</span>
            </a>
          </li>''' for t in takes)
    body = f'''    <div id="root">
      <div class="page takes">
        <div>
        <h1>Takes</h1>
        <p class="takes-intro">Short takes on design, AI and product.</p>
        <ul class="takes-list">
{items}
        </ul>
        </div>
      </div>
    </div>'''
    return page('Takes | Jonesco', 'Short takes on design, AI and product by Wes Jones.', f'{SITE}/takes/', body,
                f'{SITE}/images/takes/{takes[0]["slug"]}.png' if takes else None)


def feed(takes):
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    items = ''.join(f'''
    <item>
      <title>{html.escape(curl(t["title"]))}</title>
      <link>{SITE}/takes/{t["slug"]}</link>
      <guid isPermaLink="true">{SITE}/takes/{t["slug"]}</guid>
      <pubDate>{t["date"].strftime("%a, %d %b %Y")} 12:00:00 -0500</pubDate>
      <description>{html.escape(to_html(t["body_md"]))}</description>
    </item>''' for t in takes)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Takes by Wes Jones</title>
    <link>{SITE}/takes/</link>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml" />
    <description>Short takes on design, AI and product.</description>
    <language>en-us</language>
    <lastBuildDate>{now}</lastBuildDate>{items}
  </channel>
</rss>
'''


def share_card(t):
    """1200×630 share image: the take in big Trade Gothic on black."""
    return f'''<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/jonesco/system@1.0.0/system.css">
<style>
html,body{{margin:0;width:1200px;height:630px;background:#000;color:#fff;overflow:hidden}}
.card{{position:absolute;inset:0;padding:64px 72px;display:flex;flex-direction:column;justify-content:space-between}}
.tag{{align-self:flex-start;background:#ffe500;color:#000;font-family:var(--font-label);font-weight:700;font-size:24px;letter-spacing:.03em;text-transform:uppercase;padding:9px 14px 6px}}
h1{{margin:0;font-family:var(--font-display);font-weight:700;text-transform:uppercase;letter-spacing:-.01em;line-height:.92;font-size:{share_size(t["title"])}px}}
.foot{{display:flex;justify-content:space-between;align-items:flex-end;font-family:var(--font-label);font-weight:700;font-size:26px;letter-spacing:.03em}}
.foot b{{color:#ffe500;font-weight:700}}
</style></head><body><div class="card">
<div class="tag">Take #{t["number"]}</div>
<h1>{html.escape(curl(t["title"]))}</h1>
<div class="foot"><span>WES JONES</span><b>jonesco.com/takes/{t["slug"]}</b></div>
</div></body></html>'''


def share_size(title):
    n = len(title)
    return 120 if n <= 30 else 104 if n <= 40 else 92 if n <= 52 else 80


def render_share(t, out):
    if not os.path.exists(CHROME):
        print('  (Chrome not found; skipped share image)')
        return
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(share_card(t))
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--virtual-time-budget=8000',
                    '--window-size=1200,630', f'--screenshot={out}', 'file://' + f.name],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.unlink(f.name)


def update_sitemap(takes):
    path = os.path.join(ROOT, 'sitemap.xml')
    s = open(path, encoding='utf-8').read()
    s = re.sub(r'\n  <!-- takes -->.*?<!-- /takes -->', '', s, flags=re.S)
    urls = [(f'{SITE}/takes/', 'weekly', '0.7')] + [(f'{SITE}/takes/{t["slug"]}', 'yearly', '0.6') for t in takes]
    block = '\n  <!-- takes -->' + ''.join(
        f'\n  <url>\n    <loc>{u}</loc>\n    <changefreq>{c}</changefreq>\n    <priority>{p}</priority>\n  </url>' for u, c, p in urls
    ) + '\n  <!-- /takes -->'
    s = s.replace('\n</urlset>', block + '\n</urlset>')
    open(path, 'w', encoding='utf-8').write(s)


def main():
    if '--number' in sys.argv:
        used = {parse(os.path.join(ROOT, '_takes', f))['number'] for f in os.listdir(os.path.join(ROOT, '_takes')) if f.endswith('.md') and f != 'README.md'}
        n = str(random.SystemRandom().randint(100000, 999999))
        while n in used:
            n = str(random.SystemRandom().randint(100000, 999999))
        print(n)
        return
    src = os.path.join(ROOT, '_takes')
    takes = [parse(os.path.join(src, f)) for f in sorted(os.listdir(src)) if f.endswith('.md') and f != 'README.md']
    nums = [t['number'] for t in takes]
    if len(set(nums)) != len(nums):
        sys.exit('two takes share a number')
    takes.sort(key=lambda t: (t['date'], os.path.basename(t['path'])), reverse=True)   # newest first
    os.makedirs(os.path.join(ROOT, 'takes'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'images', 'takes'), exist_ok=True)
    for i, t in enumerate(takes):
        nxt = takes[i + 1] if i + 1 < len(takes) else (takes[0] if len(takes) > 1 else None)   # older; wraps to newest
        open(os.path.join(ROOT, 'takes', f'{t["slug"]}.html'), 'w', encoding='utf-8').write(take_page(t, nxt))
        render_share(t, os.path.join(ROOT, 'images', 'takes', f'{t["slug"]}.png'))
        print(f'  takes/{t["slug"]}.html  Take #{t["number"]}')
    open(os.path.join(ROOT, 'takes', 'index.html'), 'w', encoding='utf-8').write(index_page(takes))
    open(os.path.join(ROOT, 'feed.xml'), 'w', encoding='utf-8').write(feed(takes))
    update_sitemap(takes)
    print(f'built {len(takes)} takes: takes/index.html, feed.xml, sitemap.xml')


if __name__ == '__main__':
    main()
