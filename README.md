# wesjones.info

Wes Jones's portfolio. Plain HTML and CSS — no build step, no dependencies.

## Structure

- `index.html` — home page (bio, what I bring, case study tiles, contact)
- `<case-study>.html` — one file per case study; the URL drops the `.html` (`/fund-manager` serves `fund-manager.html`)
- `flatbed-privacy.html`, `flatbed-support.html` — standalone pages for the Flatbed Mac app
- `css/wesjones.css` — all site styling; `trade/` and `fonts/` hold the webfonts
- `images/` — page images; `images/work/` holds case study art
- `llms.txt`, `sitemap.xml`, `robots.txt` — search and AI crawler files

Every page carries its own copy of the header (`<nav class="site-nav">`) and, on case studies, the
"Next case study" link at the bottom. When adding a page, copy an existing case study and edit it,
then add a tile to `index.html` and an entry to `sitemap.xml` and `llms.txt`.

## Preview locally

Any static server works. To get the extensionless URLs (`/fund-manager`) like the live site, use one
that falls back to `.html`, for example:

```
npx serve .
```

## History

Until October 2026 this was a Create React App site; the React source is in git history before the
`html` conversion commit. The HTML was generated from those React pages, so content and markup match.
