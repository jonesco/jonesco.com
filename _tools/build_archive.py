#!/usr/bin/env python3
"""Build /archive: the projects from the original jonesco.com, kept quiet.

Content is word for word from the old site, snapshotted in _tools/archive-source.json (projects)
Every page is noindex, nofollow; nothing on the main site links here; /archive is
left out of sitemap.xml and llms.txt and disallowed in robots.txt.

Writes archive/index.html, archive/<slug>.html, and a redirect stub at each old jonesco.com URL
(/vitaminwater.html → /archive/vitaminwater) so old links keep working. The old /about goes home.
  python3 _tools/build_archive.py
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://jonesco.com'
CSS_V = 63

# grid order from the old home page (Wayblazer skipped: it is a case study on this site; PartsTree dropped)
ORDER = ['firefly', 'ironsight', 'prime', 'rta', 'dort', 'travelocity',
         'joule', 'vitaminwater', 'rembrandt']
THUMB = {'firefly': 'firefly_thumb.jpg', 'ironsight': 'ironsight_thumb.jpg',
         'prime': 'prime_thumb.jpg', 'rta': 'rta-shirts_thumb.jpg', 'dort': 'glbc_card.jpg',
         'travelocity': 'travelocity_thumb.jpg', 'joule': 'joule_card.png', 'vitaminwater': 'vw_thumb.jpg',
         'rembrandt': 'rembrandt_thumb.jpg'}
# archive numbers, shown like the case study numbers
NUM = {'firefly': 4565, 'wellsmith': 7828, 'ironsight': 1647, 'prime': 4832, 'rta': 5973, 'youga': 9650, 'dort': 4864, 'travelocity': 3966, 'joule': 3773, 'vitaminwater': 6016, 'rembrandt': 9118}
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
}
TITLE_PARTS = {'Firefly', 'Wellsmith', 'Ironsight Brewers', 'Prime Institutional Group', 'RTA +', 'Cleveland Sports', 'Youga',
               'Have a drink', 'with a good friend.', 'Travelocity + CLE', 'Joule Energy', 'Unlock your', 'inner awesome.',
               'What makes a', 'Rembrandt a Rembrandt?'}

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


# white logos on transparent PNGs; the old pages set the brand color behind them
IMG_BG = {'images/archive/work/prime-logo.png': '#00457c'}


def media(items):
    """Images in the case study style: one full width, several in a grid."""
    def one(kind, src):
        if kind == 'img' and src in IMG_BG:
            return (f'<div style="background-color: {IMG_BG[src]}; text-align: center;"><img src="/{src}" alt="" '
                    'class="shadowed-div" loading="lazy" style="max-width: 80%; margin: 0 auto;" /></div>')
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
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png" />
    <link rel="manifest" href="/manifest.json" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <meta name="theme-color" content="#000000" />
    <meta name="robots" content="noindex, nofollow" />
    <title>{e(title)}</title>
    <meta name="description" content="{html.escape(desc)}" />
    <meta name="author" content="Wes Jones" />
    <link rel="canonical" href="{url}" />
    <link rel="apple-touch-icon" sizes="180x180" href="/jonesco-bug180.png" />
    <link rel="apple-touch-icon" sizes="152x152" href="/jonesco-bug152.png" />
    <link rel="stylesheet" href="https://design.jonesco.com/v/2.0.0/system.css" />
    <link rel="stylesheet" href="/css/jonesco.css?v={CSS_V}" />
  </head>
  <body>
    <header class="site-header">
      <div class="bar">
        <a class="brand" href="/" aria-label="Jonesco, home">
          <picture><source media="(max-width: 329px)" srcset="/images/jonesco-logo-j.svg" /><source media="(max-width: 399px)" srcset="/images/jonesco-logo-jns.svg" /><img src="/images/jonesco-logo.svg" alt="Jonesco" /></picture>
        </a>
        <nav>
          <a href="/#work">Work</a>
          <a href="/#contact">Contact</a>
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
        <small>© <span class="yr">2026</span> Wes Jones</small>
      </div>
    </footer>
    <script>document.querySelectorAll('.yr').forEach(e => e.textContent = new Date().getFullYear());</script>
  </body>
</html>
'''


def project_page(p, nxt):
    """nxt is (href, name) of the next item in the archive grid."""
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
        next_band(nxt[0], 'Next in the archive', nxt[1]) + FOOTER


# newer work parked here for now, ahead of the old projects: (href, thumb, number, name, description, tag)
EXTRA = [('/network-intelligence', '/images/work/ini-thumb.jpg', 5260, 'IBM Network Intelligence',
          'Designing how people oversee an AI agent that investigates network problems on its own.', 'AI agents')]


def tile(href, src, num, name, desc, tag):
    """Same card as the home page's Selected work: image on top, words on newsprint, a tag and View case at the foot."""
    return f'''          <a class="work-card" href="{href}">
            <span class="tile-image"><img src="{src}" alt="" /></span>
            <span class="work-num">#{num}</span>
            <h3>{e(name)}</h3>
            <p>{e(desc)}</p>
            <span class="work-foot"><span class="work-tag">{e(tag)}</span><span class="work-view">View case →</span></span>
          </a>'''


# short card tags where the category line is too long for a pill
TAG = {'dort': 'SMS campaign', 'travelocity': ':30 TV spot'}


def tag(slug):
    c = TAG.get(slug) or META[slug][1]
    return c[:1].upper() + c[1:]


def index_page():
    tiles = '\n'.join([tile(*x) for x in EXTRA] + [tile(f'/archive/{s}', f'/images/archive/thumb/{THUMB[s]}', NUM[s], META[s][2], DESC[s], tag(s)) for s in ORDER])
    body = f'''
    <div id="root">
      <div class="page archive-index">
        <div>
          <h1><strong>/Archive</strong></h1>
        </div>
        <div class="work-grid">
{tiles}
        </div>
      </div>
    </div>'''
    return head('Archive | Jonesco', 'Additional work.', '/archive/') + body + FOOTER


# projects removed from the archive; their data stays in archive-source.json
RETIRED = ['wellsmith', 'youga']


def stub(target):
    """An old jonesco.com URL: send visitors on to its new page (GitHub Pages can't 301)."""
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
    # the grid's reading order, wrapping around: the EXTRA pages first, then the old projects
    chain = [(x[0], x[3]) for x in EXTRA] + [(f'/archive/{s}', META[s][2]) for s in ORDER]
    for i, slug in enumerate(ORDER):
        nxt = chain[(len(EXTRA) + i + 1) % len(chain)]
        p = project(slug, src[slug])
        w(f'archive/{slug}.html', project_page(p, nxt))
        w(f'{slug}.html', stub(f'/archive/{slug}'))
        print(f'archive/{slug:12} hero {len(p["hero"])}  ' + ', '.join(f'{s["label"]} ({len(s["media"])})' for s in p['sections']))
    w('archive/index.html', index_page())
    w('about.html', stub('/'))
    for gone in RETIRED:   # taken out of the archive 2026-11-10: old links land on the archive grid
        w(f'{gone}.html', stub('/archive/'))   # the archive's About page was retired 2026-11-10
    print('archive/index.html and redirect stubs at the old URLs')


if __name__ == '__main__':
    main()
