# Production Build Reference — The Chrysalis Protocol (Prologue + 31 Chapters)

## Build Stats
- **Source:** 1 prologue + 31 markdown chapter files, ~100,000 words
- **Output:** A5 PDF (148×210mm), 329 pages, ~3.6 MB
- **Fonts:** DejaVuSans (body), DejaVuSans-Bold (bold), DejaVuSansMono (banners)
- **Build time:** ~90s (two-pass: page-counting + final with clickable TOC links)
- **Dependencies:** fpdf2, pyfiglet (installed to /workspace/pylibs)

## Page Distribution
- Page 1: Cover image (PNG, full-bleed A5)
- Page 2: Title page (pyfiglet banners + ASCII art)
- Pages 3-5: Table of Contents (prologue + 31 entries, 3 acts, 32 clickable internal links)
- Pages 6-7: Prologue — The Frequency of Lies
- Pages 8-328: All 31 chapters
- Page 329: Colophon

## Chapter Format Variations Handled
- `# Chapter 1: Title` and `# CHAPTER 1: TITLE`
- `# PROLOGUE: Title` — front matter with no epigraph and no separator; body starts immediately after title
- Epigraphs: `> *italic*` (blockquote), `*italic*` (standalone), `"quoted"` (plain)
- Separators: `---` and `***`
- No separator / no epigraph: prologues and front matter where body follows title directly
- Leading blank lines before title (1-3)
- Attribution lines: `— Author, Source`
- Inline `*italic*` and `_italic_` within prose paragraphs
- `**bold**` (entire-line and inline)
- `### Section Title` and `#### Document Title` headings in body
- Blockquotes with mixed `**bold**`, `*italic*`, and `_italic_`
- Poem lines with trailing double-spaces (markdown line breaks)

## Bugs Encountered and Fixed

| # | Symptom | Root Cause | Fix |
|---|---------|-----------|-----|
| 1 | Epigraph lines clipped off right edge | `cell()` doesn't wrap; used for chapter epigraphs | Replace with `multi_cell()` |
| 2 | Uneven left/right margins | fpdf2 defaults l_margin/r_margin to 10mm | `set_left_margin(16)` + `set_right_margin(16)` |
| 3 | `#### DOCUMENT A:` rendered as raw markdown | No heading detection in prose renderer | Add `###`/`####`/`##` handlers |
| 4 | `**Collapse Collection...**` rendered as italic | Bold check came AFTER italic check in `render_prose` | Reorder: bold-line check BEFORE italic-line check |
| 5 | `> **Archival Note:** *text*` — asterisks visible in blockquotes | Blockquote handler didn't strip `*italic*` | Add `re.sub` for `*`, `_` markers after `**` |
| 6 | Poem lines stretched with huge word gaps | Justified alignment on short lines | Smart align: width < 60% BODY_W → left-align |
| 7 | `*was*` rendered as literal asterisks | `_render_rich_line` only stripped `**`, not `*` | Add `*italic*` stripping in both simple and bold paths |
| 8 | Italic rendered as regular (no visual distinction) | DejaVuSans has no italic variant; registered same font as 'I' | Register DejaVuSerif as 'I' style (serif contrast) |
| 9 | TOC links broken (0 annotations) | Links created after TOC rendered; `set_link` not called before `cell(link=)` | Pre-create links, set destinations to future pages from pass 1 data |
| 10 | Cover shifted page numbers but TOC was wrong | Pass 1 didn't include cover page | Add `cover_page()` to both passes |
| 11 | `_(?i)Chapter` regex crash | `(?i)` flag must be at position 0, but `^` occupies it | Use `flags=re.IGNORECASE` parameter instead |
| 12 | Prologue body text swallowed; title heading appears in body | Parser's `find_epigraph` state had no fallback for prose-first lines — every body line skipped as non-epigraph | Add `else: body_start = i; break` in `find_epigraph` after separator check |

## Validator Commands
```bash
# Quick integrity
file book.pdf
python3 -c "with open('book.pdf','rb') as f: h=f.read(10); print('OK' if h.startswith(b'%PDF') else 'CORRUPT')"

# Link audit
python3 -c "
import re
with open('book.pdf','rb') as f: c=f.read().decode('latin-1',errors='replace')
print(f'Links: {len(re.findall(r\"/Subtype\s*/Link\", c))}')
"

# Raw-marker scan
python3 -c "
from pypdf import PdfReader
r = PdfReader('book.pdf')
for pg in range(len(r.pages)):
    for line in r.pages[pg].extract_text().split('\n'):
        s = line.strip()
        if s.startswith('*') and s.endswith('*') and '**' not in s and len(s)>3:
            print(f'RAW MARKER pg{pg+1}: {s[:80]}')
print('Scan complete.')
"
```
