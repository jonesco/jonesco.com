#!/usr/bin/env python3
"""Build /archive: the projects from the original jonesco.com, kept quiet.

Content is word for word from the old site, snapshotted in _tools/archive-source.json (projects)
and ABOUT below. Every page is noindex, nofollow; nothing on the main site links here; /archive is
left out of sitemap.xml and llms.txt and disallowed in robots.txt.

Writes archive/index.html, archive/<slug>.html, archive/about.html, and a redirect stub at each old
jonesco.com URL (/vitaminwater.html → /archive/vitaminwater) so old links keep working.
  python3 _tools/build_archive.py
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://jonesco.com'
CSS_V = 39

# grid order from the old home page (Wayblazer skipped: it is a case study on this site), PartsTree last
ORDER = ['firefly', 'wellsmith', 'ironsight', 'prime', 'rta', 'youga', 'dort', 'travelocity',
         'joule', 'vitaminwater', 'rembrandt', 'partstree']
THUMB = {'firefly': 'firefly_thumb.jpg', 'wellsmith': 'wellsmith_thumb.jpg', 'ironsight': 'ironsight_thumb.jpg',
         'prime': 'prime_thumb.jpg', 'rta': 'rta-shirts_thumb.jpg', 'youga': 'youga_thumb.png', 'dort': 'glbc_thumb.jpg',
         'travelocity': 'travelocity_thumb.jpg', 'joule': 'joule_thumb.png', 'vitaminwater': 'vw_thumb.jpg',
         'rembrandt': 'rembrandt_thumb.jpg', 'partstree': 'partstree_thumb.jpg'}
# archive numbers, shown like the case study numbers
NUM = {'firefly': 4565, 'wellsmith': 7828, 'ironsight': 1647, 'prime': 4832, 'rta': 5973, 'youga': 9650, 'dort': 4864, 'travelocity': 3966, 'joule': 3773, 'vitaminwater': 6016, 'rembrandt': 9118, 'partstree': 6663}
# one sentence under each archive tile, drawn from the old project copy
DESC = {
    'firefly': 'An interactive trade show display that launched Input/Output’s Firefly before the system was ready to demo.',
    'wellsmith': 'A healthcare web portal and mobile app that track patient compliance across medication, activity, nutrition and vitals.',
    'ironsight': 'Logo design for Ironsight Brewers.',
    'prime': 'Logo design for Prime Institutional Group.',
    'rta': 'Sports promotional items that reminded Cleveland fans the RTA was the best way to get to the big game.',
    'youga': 'A yoga app stretched into personalized workouts, with guided sessions, video and a yoga mix tape.',
    'dort': 'A text message and voicemail campaign that let beer drinkers reconnect with an old friend, Dortmunder Gold.',
    'travelocity': 'A cross-promotion pairing Cleveland Hopkins International Airport with Travelocity, online and offline.',
    'joule': 'Logo design for Joule Energy.',
    'vitaminwater': 'A brand campaign to make vitaminwater the drink of the next creative generation.',
    'rembrandt': 'A campaign for the Cleveland Museum of Art’s rare Rembrandt exhibition, from a bus wrap to a Facebook app.',
    'partstree': 'A specialized e-commerce platform that finds the right part by model number, brand or serial number.',
}
# page title as on the old page, its category line, and the name used on the archive grid
META = {
    'firefly': ('Firefly', 'product launch', 'Firefly'),
    'wellsmith': ('Wellsmith', 'web portal and mobile app', 'Wellsmith'),
    'ironsight': ('Ironsight Brewers', 'logo', 'Ironsight Brewers'),
    'prime': ('Prime Institutional Group', 'logo', 'Prime Institutional Group'),
    'rta': ('RTA + Cleveland Sports', 'promotional items', 'RTA + Cleveland Sports'),
    'youga': ('Youga', 'mobile app', 'Youga'),
    'dort': ('Have a drink with a good friend.', 'text message & voicemail campaign', 'Great Lakes Brewing Co.'),
    'travelocity': ('Travelocity + CLE', ':30 sec tv', 'Travelocity + CLE'),
    'joule': ('Joule Energy', 'logo', 'Joule Energy'),
    'vitaminwater': ('Unlock your inner awesome.', 'brand campaign', 'vitaminwater'),
    'rembrandt': ('What makes a Rembrandt a Rembrandt?', 'campaign', 'Cleveland Museum of Art'),
    'partstree': ('PartsTree', 'specialized e-commerce', 'PartsTree'),
}
TITLE_PARTS = {'Firefly', 'Wellsmith', 'Ironsight Brewers', 'Prime Institutional Group', 'RTA +', 'Cleveland Sports', 'Youga',
               'Have a drink', 'with a good friend.', 'Travelocity + CLE', 'Joule Energy', 'Unlock your', 'inner awesome.',
               'What makes a', 'Rembrandt a Rembrandt?', 'PartsTree'}

ABOUT = {
    'bio': ['I’ve always been a creative problem solver. And for more than two decades, it’s also been my career. I know how to create smart, engaging solutions that connect with the audience while supporting creative strategy.',
            'But if you were to ask my parents what I do for a living, they’d proudly tell you, “He makes brochures.”'],
    'clients': ['Microsoft', 'Samsung', 'IBM', 'S&P Global', 'ABB Robotics', 'Fidelity', 'PricewaterhouseCoopers', 'Hotels.com',
                'Neuberger Berman', 'Lubrizol', 'Loctite', 'Glidden', 'Ridgid Tools', 'vitaminwater', 'University Hospitals',
                'FirstMerit Bank', 'Great Lakes Brewing Co.', 'Fazoli’s', 'Cleveland Museum of Art', 'DARPA'],
    'published': ['LogoLounge: Master Library, Volume 2 (2010)', 'Graphis Design 2004 (2004)',
                  'Print Regional Annual (2002, 2003)', 'Communication Arts Design Annual (2003)'],
    'awards': ['Judge’s Choice Award from the American Advertising Federation Cleveland',
               'Judge’s Choice Award for Multimedia from the Houston Advertising Federation',
               'Regional Gold Addy Awards from the American Advertising Federation'],
    'gold_silver': ['American Advertising Federation Cleveland', 'AIGA Cleveland', 'The Art Directors Club of Houston',
                    'American Advertising Federation Houston', 'Houston American Marketing Association',
                    'Business Marketing Association, Houston Chapter', 'Dallas Society of Visual Communication'],
    'education': ['BFA in Communication Design from Texas State University', 'Graduated summa cum laude'],
}

e = lambda s: html.escape(s, quote=False)


def project(slug, toks):
    """The old page's ordered tokens → hero media, description and labeled sections (repeats dropped)."""
    title, cat, _ = META[slug]
    hero, desc, sections, seen, skip = [], None, [], set(), False
    for kind, val in toks:
        if kind == 't':
            if val in TITLE_PARTS or val == cat:
                continue
            if len(val) > 80:
                if desc is None:
                    desc = val
                elif val.replace('–', '-') == desc.replace('–', '-'):
                    continue                    # the old page repeated it for mobile
                elif sections and not skip:
                    sections[-1]['note'] = val
                continue
            skip = val in seen                  # the old page repeated some sections for mobile
            seen.add(val)
            if not skip:
                sections.append({'label': val, 'media': [], 'note': None})
            continue
        if skip:
            continue
        m = (kind, val.replace('http://', 'https://').replace('images/work/', 'images/archive/work/'))
        (sections[-1]['media'] if desc is not None and sections else hero).append(m)
    return {'slug': slug, 'title': title, 'cat': cat, 'desc': desc, 'hero': hero, 'sections': sections}


def media(items):
    """Images in the case study style: one full width, several in a grid."""
    def one(kind, src):
        if kind == 'img':
            return f'<div><img src="/{src}" alt="" class="shadowed-div" loading="lazy" /></div>'
        return (f'<div class="archive-video"><iframe src="{e(src)}" title="Video" '
                'allow="fullscreen; picture-in-picture" allowfullscreen></iframe></div>')
    if not items:
        return ''
    if len(items) == 1:
        return '\n        ' + one(*items[0])
    phones = len(items) >= 3 and all(re.search(r'mobile\d|youga\d|activity|meds|messaging|yourself', s) for _, s in items)
    cols = 'cols-4' if phones else 'cols-3' if len(items) in (3, 6) else 'cols-2'
    return f'\n        <div class="{cols} archive-media">' + ''.join(one(*m) for m in items) + '</div>'


def head(title, desc, path):
    url = SITE + path
    return f'''<!doctype html>
<html lang="en" dir="ltr" class="compact-header">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" type="image/png" href="/favicon-96x96.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#000000" />
    <meta name="robots" content="noindex, nofollow" />
    <title>{e(title)}</title>
    <meta name="description" content="{html.escape(desc)}" />
    <meta name="author" content="Wes Jones" />
    <link rel="canonical" href="{url}" />
    <link rel="apple-touch-icon" sizes="180x180" href="/jonesco-bug180.png" />
    <link rel="apple-touch-icon" sizes="152x152" href="/jonesco-bug152.png" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Libre+Franklin:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/jonesco/system@1.0.0/system.css" />
    <link rel="stylesheet" href="/css/jonesco.css?v={CSS_V}" />
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
    </header>'''


def next_band(href, label, title):
    return f'''
    <a class="next-band" href="{href}">
      <div class="bar">
        <span class="next-label">{label} &gt;</span>
        <span class="next-title">{e(title)}</span>
      </div>
    </a>'''


FOOTER = '''
    <footer class="site-footer">
      <div class="bar">
        <div class="links">
          <a href="mailto:wes@jonesco.com">wes@jonesco.com</a>
          <a href="https://www.linkedin.com/in/wes-jones-a0914312/" target="_blank" rel="noreferrer">LinkedIn</a>
          <a href="/images/Wes_Jones_Resume.pdf">Resumé</a>
        </div>
        <small>© <span class="yr">2026</span> Wes Jones</small>
      </div>
    </footer>
    <script>document.querySelectorAll('.yr').forEach(e => e.textContent = new Date().getFullYear());</script>
  </body>
</html>
'''


def project_page(p, nxt):
    blocks = ''
    for s in p['sections']:
        note = f'\n          <p>{e(s["note"])}</p>' if s['note'] else ''
        label = s['label'][:1].upper() + s['label'][1:]
        blocks += f'''
        <hr />
        <div>
          <h2><strong>{e(label)}</strong></h2>{note}
        </div>{media(s["media"])}'''
    desc = f'\n          <h4>{e(p["desc"])}</h4>' if p['desc'] else ''
    body = f'''
    <div id="root">
      <div class="page archive-page">
        <div>
          <h5 id="rcorners1">Project #{NUM[p["slug"]]}</h5>
          <h1><strong>{e(p["title"])}</strong></h1>{desc}
        </div>{media(p["hero"])}{blocks}
        <p class="archive-back"><a href="/archive/">All archive projects</a></p>
      </div>
    </div>'''
    title = f'{META[p["slug"]][2]} | Jonesco archive'
    return head(title, p['desc'] or f'{p["title"]}, {p["cat"]}.', f'/archive/{p["slug"]}') + body + \
        next_band(f'/archive/{nxt}', 'Next in the archive', META[nxt][2]) + FOOTER


def index_page():
    tiles = '\n'.join(f'''          <a href="/archive/{s}">
            <div class="tile-card">
              <div class="tile-image"><img src="/images/archive/thumb/{THUMB[s]}" alt="" /></div>
              <div class="tile-label">
                <div class="csid"><p>#{NUM[s]}</p></div>
                <h2><strong>{e(META[s][2])}</strong></h2>
                <p class="tile-description">{e(DESC[s])}</p>
              </div>
            </div>
          </a>''' for s in ORDER)
    body = f'''
    <div id="root">
      <div class="page archive-index">
        <div>
          <h1><strong>/Archive</strong></h1>
        </div>
        <div class="tile-grid">
{tiles}
        </div>
        <p class="archive-back"><a href="/archive/about">About, clients and awards from the original site</a></p>
      </div>
    </div>'''
    return head('Archive | Jonesco', 'Earlier work from the original jonesco.com.', '/archive/') + body + FOOTER


def about_page():
    A = ABOUT
    ul = lambda xs: '<ul class="a">' + ''.join(f'<li class="special-item">{e(x)}</li>' for x in xs) + '</ul>'
    body = f'''
    <div id="root">
      <div class="page archive-page">
        <div>
          <h5 id="rcorners1">About</h5>
          <h1><strong>Wes Jones</strong></h1>
          {''.join(f'<h4>{e(p)}</h4>' for p in A['bio'])}
        </div>
        <div class="cols-2">
          <div>
            <h5><strong>Clients:</strong></h5>
            {ul(A['clients'])}
          </div>
          <div>
            <h5><strong>Work published in:</strong></h5>
            {ul(A['published'])}
            <h5><strong>Awards:</strong></h5>
            {ul(A['awards'])}
            <h5><strong>Gold and Silver Awards from:</strong></h5>
            {ul(A['gold_silver'])}
            <h5><strong>Education:</strong></h5>
            {ul(A['education'])}
          </div>
        </div>
        <p class="archive-back"><a href="/archive/">All archive projects</a></p>
      </div>
    </div>'''
    return head('About | Jonesco archive', A['bio'][0], '/archive/about') + body + FOOTER


def stub(target):
    """An old jonesco.com URL: send visitors on to the archive page (GitHub Pages can't 301)."""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<meta name="robots" content="noindex, nofollow" />
<link rel="canonical" href="{SITE}{target}" />
<meta http-equiv="refresh" content="0; url={target}" />
<title>Moved</title></head>
<body><p><a href="{target}">This page moved to {SITE}{target}</a></p>
<script>location.replace({json.dumps(target)} + location.hash);</script></body></html>
'''


def main():
    src = json.load(open(os.path.join(ROOT, '_tools', 'archive-source.json'), encoding='utf-8'))
    os.makedirs(os.path.join(ROOT, 'archive'), exist_ok=True)
    w = lambda path, s: open(os.path.join(ROOT, path), 'w', encoding='utf-8').write(s)
    for i, slug in enumerate(ORDER):
        p = project(slug, src[slug])
        w(f'archive/{slug}.html', project_page(p, ORDER[(i + 1) % len(ORDER)]))
        w(f'{slug}.html', stub(f'/archive/{slug}'))
        print(f'archive/{slug:12} hero {len(p["hero"])}  ' + ', '.join(f'{s["label"]} ({len(s["media"])})' for s in p['sections']))
    w('archive/index.html', index_page())
    w('archive/about.html', about_page())
    w('about.html', stub('/archive/about'))
    print('archive/index.html, archive/about.html, and redirect stubs at the old URLs')


if __name__ == '__main__':
    main()
