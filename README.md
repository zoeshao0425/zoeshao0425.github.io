# zoeshao0425.github.io

Personal academic homepage, built with [Jekyll](https://jekyllrb.com/) on the
[luost26/academic-homepage](https://github.com/luost26/academic-homepage) theme.
Deployed by GitHub Pages' default build from `master`.

## Where the content lives

| To change… | Edit |
| --- | --- |
| Name, bio, email, CV link, education, experience, awards | `_data/profile.yml` |
| Navbar items | `_data/navigation.yml` (a `name` must match the page's `navbar_title`) |
| How many news items show on the homepage, footer text | `_data/display.yml` |
| Co-author names → homepage links | `_data/authors.yml` |
| Publications | one file per paper in `_publications/<year>/` |
| News feed on the homepage | one file per item in `_news/` |
| Teaching & talks | `teaching.html` (plain HTML, no collection) |
| The Chichi page | `_showcase/chichi/` |
| PDFs (papers, slides, CV) | `files/` |

`selected: true` on a publication puts it in the homepage's **Selected Publications**
card. Everything in `_publications/` appears on `/publications/` regardless.

Author names in a publication's `authors:` list are looked up in `_data/authors.yml`.
A trailing `*` marks equal contribution, `#` marks corresponding author — the theme
adds the footnote automatically.

## Publication cover images

Each paper's cover is a thumbnail of the top of its first page, generated from the PDF:

```bash
tools/make_covers.sh files/YourPaper.pdf assets/images/covers/venue-shortname.png
```

Then point the entry's `cover:` at it. Requires Ghostscript (`brew install ghostscript`).
A paper with no `cover:` falls back to an auto-generated colored bubble pattern.

## Running locally

```bash
bundle install          # first time only
bundle exec jekyll serve
```

If you don't want to use Bundler, the site also builds with a plain global Jekyll:

```bash
JEKYLL_NO_BUNDLER_REQUIRE=true jekyll build --safe
```

`--safe` matches how GitHub Pages builds: it skips `jekyll-email-protect`, which is not on
the GitHub Pages plugin allowlist. That plugin only obfuscates the `mailto:` address against
scrapers — without it the address renders normally, so the site is identical either way.

## Notes

- `.legacy_academicpages/` holds the previous academicpages theme and its content, kept
  only as a reference during the migration. It is excluded from the build and safe to delete.
- Institution badges in `assets/images/badges/` are plain generic monogram SVGs, not official
  logos, deliberately — it avoids trademark issues and they stay crisp at 18px.
