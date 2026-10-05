# Takes

Short takes on design, AI and product. Each take is one Markdown file in this folder.
This folder starts with `_`, so it is never published; the build writes the public pages.

## Write a take
1. Add `_takes/YYYY-MM-DD-slug.md`:

   ```
   ---
   title: The take, as a sentence.
   date: 2026-10-04
   slug: the-slug            # the URL: wesjones.info/takes/the-slug
   number: 123456            # random six digits, shown as Take #123456; never reuse one
   tags: [ai, design]
   linkedin:                 # paste post URLs here after cross-posting (see below)
   x:
   bluesky:
   ---
   Plain paragraphs. **bold**, *italic* and [links](https://example.com) work.
   ```
   No em dashes. Straight quotes are fine; the build curls them.
2. Build: `python3 _tools/build_takes.py`
   (`python3 _tools/build_takes.py --number` prints a fresh random number.)
3. Preview locally, then commit and push.

The build writes `takes/index.html`, `takes/<slug>.html`, `feed.xml`, the share images in
`images/takes/` and the takes entries in `sitemap.xml`. Don't edit those by hand.

## Cross-posting (stub)
wesjones.info is the source of truth; other channels point back to it.
- **LinkedIn** (primary): post the text, end with the take's URL. Attach `images/takes/<slug>.png`.
- **X / Bluesky**: the title plus the URL; the share image shows automatically from the page.
- After posting, paste each post's URL into the take's `linkedin:`, `x:` or `bluesky:` field and rebuild.
  The take page then shows "Also on LinkedIn · X · Bluesky".
- Later, this step can be automated from `feed.xml` (every take is in the feed with its full text).
