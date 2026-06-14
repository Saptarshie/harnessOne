---
name: pdf-book-generator
description: "Convert multi-chapter markdown books into professionally formatted PDFs with ASCII art illustrations — title page, TOC, chapter art, book typography."
version: 1.0.0
category: creative
tags: [pdf, book, novel, fpdf2, pyfiglet, ascii-art, typography, markdown]
---

# PDF Book Generator

Convert a multi-chapter markdown novel, report, or documentation set into a clean, professionally formatted PDF book with ASCII art chapter illustrations, title page, table of contents, and book typography.

**When to use this skill:**
- User has multiple markdown chapters and wants a single PDF "book"
- User asks to "convert novel to PDF", "make a PDF book", "format as a book", "generate a PDF with illustrations"
- Any multi-file markdown project that deserves polished print-ready output

## Quick Start

1. Read the template script at `templates/build_pdf.py` — it's the complete generator.
2. Adapt the chapter directory path, output path, and ASCII art illustrations.
3. Install deps and run.

## Dependencies

```bash
pip install fpdf2 --target=/path/to/libs --no-deps
pip install pyfiglet --target=/path/to/libs --no-deps
```

The `--no-deps` flag avoids slow dependency resolution. fpdf2 and pyfiglet each have zero hard dependencies at runtime.

## Font Requirements

You need a monospace font for ASCII art and a readable body font. DejaVu is universally available on Linux:

```
/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf      ← ASCII art
/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf           ← body text
/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf      ← headings/bold
/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf  ← bold mono
```

On macOS, use system fonts or install DejaVu via `brew install font-dejavu`.

### Italic Font — The DejaVuSerif Technique

**DejaVuSans has NO italic/oblique variant.** Using `add_font('Serif', 'I', DejaVuSans.ttf)` silently registers the regular font under the italic style — text marked as italic renders upright, indistinguishable from regular. This IS NOT a cosmetic issue — the reader literally cannot see italic content.

**The fix:** Register DejaVuSerif as the italic variant. The serif vs sans-serif contrast creates an immediate visual distinction that the eye processes as emphasis. This is a legitimate typographic technique used in publishing when true italics aren't available in the chosen typeface:

```python
self.add_font('Serif', '',  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
self.add_font('Serif', 'B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
self.add_font('Serif', 'I',  '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')      # italic via serif contrast
self.add_font('Serif', 'BI', '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf')  # bold-italic
```

**Why not Times?** Core PDF fonts (Times, Helvetica) cannot render Unicode — em-dashes (—), smart quotes, and other non-Latin-1 characters break with `UnicodeEncodeError: 'latin-1' codec can't encode character`. DejaVu fonts have full Unicode coverage. Since DejaVu lacks true italic, DejaVuSerif fills the role.

**Verification:** After building, extract text from a page with known italic content. The extracted text should contain NO raw `*` or `_` markers. Search the entire PDF with:
```python
for pg in range(len(reader.pages)):
    text = reader.pages[pg].extract_text()
    for line in text.split('\n'):
        if line.strip().startswith('*') and line.strip().endswith('*') and '**' not in line:
            print(f'RAW ITALIC on page {pg+1}')  # should never fire
```

## Book Layout (Recommended)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Page size | A5 (148×210 mm) | Book-like proportions, fits on screens |
| Margins | 16 mm all around | Generous but not wasteful |
| Body font | DejaVu Sans, 8–8.5 pt | Readable; 7.5pt too small on modern screens |
| Mono font | DejaVu Sans Mono, 4–6 pt | Fits ASCII art on narrow columns |
| Title font | pyfiglet "small" at 5–6 pt | Compact banners that fit A5 width |
| Text alignment | Justified (long lines), Left (short lines) | Smart: poems/attributions left-aligned, prose justified |

## Structure

The PDF should contain, in order:

1. **Cover page** — full-bleed PNG image (optional)
2. **Title page** — pyfiglet ASCII banner, cover illustration, subtitle, stats
3. **Table of contents** — front matter listing + chapter list grouped by act/part, decorative rules
4. **Front matter** — prologue, preface, or foreword (chapter 0, un-numbered)
5. **Chapters** — each on a new page with:
   - Chapter number as pyfiglet banner
   - Chapter title in serif bold
   - Subtle decorative rule
   - ASCII art illustration (custom, scene-relevant)
   - Prose body text (justified/long, left-aligned/short, 8.5 pt)
   - Scene-break dividers (`─────── ◆ ───────`)
6. **Colophon** — closing page with production notes

## ASCII Art for PDF — Critical Pitfall

**Never use emoji or non-Latin-1 Unicode in ASCII art destined for a PDF.** Fonts like DejaVu Sans Mono lack glyphs for emoji (🐐🐎🧑☀️⚖️♜★ॐ⊚). The PDF build will succeed but those characters will render as blank boxes or `.notdef` glyphs.

**Replace before embedding:**

| Problem glyph | Safe replacement |
|---------------|-----------------|
| 🐐 (goat) | `/||\` |
| 🐎 (horse) | `(())` |
| ☀️ (sun) | `sunburst` or `*` |
| 🧑 (person) | `o` face in box |
| ⚖️ (scales) | `[*]` |
| ★ (star) | `*` |
| ॐ (om) | `Om` |
| ⊚ (circled dot) | `@` |
| ♜ (rook) | `R` |

Stick to: ASCII printable (32–126), box-drawing (╔╗╚╝║═╠╣╦╩╬), block elements (░▒▓█), and geometric shapes (▲▼◆◇●○). These are in DejaVu Sans Mono.

**Full glyph coverage reference:** See `references/font-glyphs.md` for the complete safe/unsafe Unicode range table, programmatic font inspection commands, and a test script.

## fpdf2 API Notes

- `add_font(name, style, path)` — do NOT pass `uni=True`; it's deprecated since v2.5.1
- `multi_cell(w, h, text, align='J')` — justified text for body prose; auto-wraps
- `set_auto_page_break(True, margin)` — enable automatic page breaks
- `cell(0, h, text, ...)` — **DOES NOT WRAP.** `w=0` extends to right margin but clips overflow. Use `multi_cell()` for any text that may exceed line width
- Header/footer: override `header()` and `footer()` methods
- Use `self.page_has_header = False` on title/chapter-start pages to suppress headers

### Critical fpdf2 Gotchas

**1. Margins must be set explicitly.** `set_auto_page_break(True, 16)` sets the *bottom* margin only. Left and right margins default to 10mm regardless. Always call:
```python
self.set_left_margin(MARGIN)
self.set_right_margin(MARGIN)
```

**2. `cell()` clips, `multi_cell()` wraps.** This is the #1 cause of text running off the right edge. Epigraphs, blockquotes, and any text that might be longer than the body width MUST use `multi_cell()`. The template script's epigraph rendering uses `cell()` — replace it.

**3. Links must have destinations before use.** `add_link()` creates a link target; `set_link(link, page=N)` MUST be called before `cell(link=link)`. But pages can be FUTURE — fpdf2 accepts page numbers that don't exist yet. See TOC section below for the two-pass pattern.

**4. `l_margin` vs `MARGIN`.** The PDF class has `self.l_margin` (current left margin) and `self.r_margin`. After calling `set_left_margin(16)`, both `self.l_margin` and the constant `MARGIN` equal 16mm. Use `self.l_margin` for position calculations — it reflects the actual current state.

## TOC with Page Numbers + Clickable Internal Links — Two-Pass Approach

**The problem:** The TOC renders before chapters, so chapter start pages aren't known yet. And fpdf2 requires `set_link()` to be called BEFORE `cell(link=...)` — you cannot create a link, use it in the TOC, then set its destination later when the chapter page is created. The error is: `ValueError: Cannot insert link N with no page number assigned`.

**The solution:** Two-pass build + pre-set future-page destinations.

**Pass 1** — render the full book (title, real TOC, all chapters, colophon) and record each chapter's start page:
```python
chapter_start_pages = {}
for num, title, epigraph, body in chapters:
    pdf.start_chapter(num, title, epigraph, add_toc_link=False)
    chapter_start_pages[num] = pdf.page  # current page number after add_page()
    pdf.render_prose(body)
```

**Pass 2** — pre-create all links, set their destinations using pass 1 page numbers BEFORE rendering the TOC, then build:
```python
# Pre-create links and set destinations to FUTURE pages (fpdf2 accepts this!)
for num, _, _, _ in chapters:
    link = pdf.add_link()
    dest_page = chapter_start_pages.get(num, 0)
    if dest_page > 0:
        pdf.set_link(link, page=dest_page)  # page doesn't exist yet — OK
    pdf.chapter_links[num] = link

# Now build the TOC — links have valid destinations
pdf.table_of_contents(toc_entries)  # passes link=pdf.chapter_links[num] to cell()

# Then render chapters normally (no need to create links again)
for num, title, epigraph, body in chapters:
    pdf.start_chapter(num, title, epigraph, add_toc_link=False)
    pdf.render_prose(body)
```

**Critical detail:** Pass 1's TOC MUST have the same page count as Pass 2's TOC, otherwise chapter start pages will be offset. Render the real TOC in pass 1 (without links) so its page count matches.

**Verification:** After building, search the raw PDF for `/Subtype /Link` — you should find exactly N links (one per chapter). Check with:
```python
with open('book.pdf', 'rb') as f:
    content = f.read().decode('latin-1', errors='replace')
print(f"Links: {content.count('/Subtype /Link')}")  # should == number of chapters
```

A production example (31 chapters, 249 pages, 31 clickable TOC links) lives at `references/production-build-31ch.md`.

## Inline Formatting Pragmatics

**Bold spans (`**text**`):** Two approaches, depending on bold usage density:

**Approach A — Strip and render regular (recommended for novels):**
```python
clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
self.multi_cell(BODY_W, line_h, clean, align='J')
```
Most novels have sparse bold (a few document titles per chapter). Readers don't miss inline bold — the prose carries its own weight. This approach is simple, reliable, and preserves `multi_cell()` auto-wrapping.

**Approach B — Inline cell() segments (for document-heavy chapters):**
When chapters contain archival documents with frequent bold labels, strip `**` markers and render bold segments with separate `cell()` calls:
```python
parts = re.split(r'(\*\*[^*]+\*\*)', line)
if len(parts) == 1:
    self.multi_cell(BODY_W, line_h, line, align='J')  # no bold, use multi_cell
else:
    x = self.l_margin; y = self.get_y()
    for idx, part in enumerate(parts):
        if not part: continue
        is_bold = (idx % 2 == 1)
        self.set_font('Serif', 'B' if is_bold else '', font_size)
        text = part[2:-2] if is_bold else part
        w = self.get_string_width(text)
        if x + w > max_x and x > self.l_margin:
            y += line_h; x = self.l_margin  # word-wrap
            self.set_xy(x, y)
        self.cell(w, line_h, text)
        x += w
    self.set_xy(self.l_margin, y + line_h)
```
**Limitation:** Bold segments use `cell()` (no auto-wrap within a segment), so long bold spans can overflow. This is acceptable for document titles and short labels — the dominant use case in novels. Lines without bold fall back to `multi_cell()` for full wrapping.

**Italic spans (`*text*` and `_text*`):** Both asterisk and underscore forms are common in markdown. Handle both FOR WHOLE LINES and INLINE within paragraphs. See the `_render_segments` helper below for the combined bold+italic inline renderer.

**Combined inline bold + italic:** When a single line may contain `**bold**`, `*italic*`, and `_underline_` markers simultaneously, use a two-stage split: split by `**bold**` first, then within each non-bold segment split by `*italic*` (and also `_italic_`). Each segment renders with the correct font style via `cell()`:

```python
def _render_rich_line(self, line, font_size, line_h):
    # Stage 1: split by **bold**
    bold_parts = re.split(r'(\*\*[^*]+\*\*)', line)
    if len(bold_parts) == 1:
        # No bold — check for *italic*, then _italic_
        italic_parts = re.split(r'(\*[^*]+\*)', line)
        if len(italic_parts) > 1:
            self._render_segments(italic_parts, font_size, line_h, italic_mode='*')
            return
        # Check _italic_ too...
        self.multi_cell(BODY_W, line_h, line, align=align)
        return
    # Stage 2: render bold segments, recursively check non-bold for italic
    for idx, part in enumerate(bold_parts):
        if idx % 2 == 1:  # bold segment
            self.set_font('Serif', 'B', font_size)
            text = part[2:-2]
        else:  # non-bold — check for *italic* within
            italic_parts = re.split(r'(\*[^*]+\*)', part)
            if len(italic_parts) > 1:
                for ii, ipart in enumerate(italic_parts):
                    is_italic = (ii % 2 == 1)
                    self.set_font('Serif', 'I' if is_italic else '', font_size)
                    text = ipart[1:-1] if is_italic else ipart
                    # render with cell()
            else:
                text = re.sub(r'_([^_]+)_', r'\1', part)
                self.set_font('Serif', '', font_size)
                # render with cell()
    self.set_xy(self.l_margin, y + line_h)

def _render_segments(self, parts, font_size, line_h, italic_mode='*'):
    """Render segments alternating italic/regular via cell()."""
    for idx, part in enumerate(parts):
        is_italic = (idx % 2 == 1)
        self.set_font('Serif', 'I' if is_italic else '', font_size)
        text = part[1:-1] if is_italic else part
        # Strip _italic_ from non-italic segments
        if not is_italic:
            text = re.sub(r'_([^_]+)_', r'\1', text)
        # Render with cell(), manual word-wrap
        ...
```

**Limitation:** `cell()` is used for all formatted segments — no `multi_cell()` auto-wrap. Long formatted lines can overflow. This is acceptable for the dominant use case (short bold/italic spans like document titles or emphasis words). Lines with NO formatting markers fall back to `multi_cell()` for full wrapping.

## Markdown Parsing Robustness

Chapter markdown formats vary in the wild. Handle these patterns:

| Variation | Example |
|-----------|---------|
| Title case | `# Chapter 1: Title` or `# CHAPTER 1: TITLE` |
| Epigraph style | `> *italic epigraph*` (blockquote) or `*italic epigraph*` (standalone) |
| Separator | `---` or `***` |
| Leading blank lines | Some chapters have 1-3 blank lines before `# ` |
| Attribution lines | `— Author Name, Source` (em-dash attribution) |
| Underscore italic | `_Found inscribed on a fragment..._` — same as `*italic*` |
| Headings in body | `### Section Title` and `#### Document Title` — need explicit rendering |
| Bold formatting | `**bold text**` — entire-line or inline |
| Trailing spaces | `  \n` (markdown line breaks in poems) — strip with `rstrip()` |
| No epigraph or separator | Prologues / front matter: body text starts right after title + blank line — no `>` blockquote and no `---`/`***` |

**Parser state-machine pitfall — missing `else` in `find_epigraph`:** The state machine's `find_epigraph` state checks for `>`, `*`, `"`, and `---`/`***` — but a regular prose line matches NONE of these. Without an `else` clause, the parser silently skips every body line, staying stuck in `find_epigraph` until EOF. The body ends up containing the raw title heading plus all text. **Fix:** add an `else: body_start = i; break` after the separator check:

```python
elif stripped in ('---', '***'):
    body_start = i + 1
    break
else:
    # Non-epigraph, non-separator — body has started (e.g., prologue)
    body_start = i
    break
```

This fires when a line after the title is neither blank, epigraph-like, nor a separator — correctly treating it as the start of body prose.

**Regex pitfall:** `r'^(?i)Chapter...'` fails with `global flags not at the start of the expression`. Inline `(?i)` must be at regex position 0, but `^` occupies it. Use `flags=re.IGNORECASE` instead:
```python
# WRONG: re.sub(r'^(?i)Chapter\s+\d+\s*[:—–-]?\s*', '', title)
# RIGHT:
re.sub(r'^Chapter\s+\d+\s*[:—–-]?\s*', '', title, flags=re.IGNORECASE)
```

**Robust parser pattern:** State-machine approach that handles all variations:
1. Skip blank lines → `find_title` state (look for `# `)
2. Collect epigraph lines (anything after title, before separator)
3. Detect separator (`---` or `***`) → everything after is body
4. If no separator found, body starts after epigraph
5. If no epigraph AND no separator (prologues, front matter): body starts at the first non-epigraph, non-separator line — requires `else: body_start = i; break` in `find_epigraph` state (see pitfall above)

### Prose Body Rendering — Markdown in Chapter Text

**Detection order is load-bearing.** Each pattern check in `render_prose()` returns early on match. Placing checks in the wrong order causes cascading misrenders. The correct sequence:

```
1. Blank line          → paragraph break
2. #### heading        → before ### (4-char check before 3-char)
3. ### heading
4. ## heading
5. > blockquote        → before bold/italic (blockquotes may contain ** and *)
6. *** / ---           → scene divider
7. **entire bold line** → BEFORE *italic* check! (`**text**` starts with `*`)
8. *italic line*        → check `not stripped.startswith('**')` as guard
9. _italic line_        → check `not stripped.startswith('__')` as guard
10. Regular text        → _render_rich_line (handles inline **bold** and *italic*)
```

**Why #7 must precede #8:** `**bold text**` matches BOTH the bold-line check (`startswith('**') and endswith('**')`) AND the italic-line check (`startswith('*') and endswith('*')`). If italic comes first, bold text renders as muted italic with asterisks stripped — all visual emphasis lost.

**Why #7 uses a 4-char minimum:** `**` alone (empty bold) is not a formatting instruction. Require `len(stripped) > 4` so single `**word**` is caught but bare `**` is not.

When chapter bodies contain markdown formatting (common in archival/epistolary chapters), the renderer must handle:

| Pattern | Detection | Rendering |
|---------|-----------|-----------|
| `### heading` | `stripped.startswith('### ')` | Bold Serif, 9.5pt, left-aligned, spacing above/below |
| `#### subheading` | `stripped.startswith('#### ')` | Bold Serif, 8.5pt, left-aligned |
| `**entire bold line**` | `stripped.startswith('**') and stripped.endswith('**')` | Bold Serif, body font size |
| `*italic line*` | `stripped.startswith('*') and not stripped.startswith('**')` | Muted italic, 8pt |
| `_italic line_` | `stripped.startswith('_') and not stripped.startswith('__')` | Same as `*italic*` |
| `> **bold** and *italic* blockquote` | Blockquote handler | Strip ALL `**`, `*`, `_` markers; render as muted regular |

### Smart Alignment for Mixed Content

Justified alignment (`align='J'`) stretches short lines across the full body width, creating ugly gaps. Detect short lines and left-align them:
```python
est_width = self.get_string_width(line)  # strip markers first
if est_width < BODY_W * 0.6:
    align = 'L'  # poems, attributions, standalone sentences
else:
    align = 'J'  # prose paragraphs
```
This prevents poem lines like "The ear that hears no frequency" from being stretched with massive word gaps.

## Parsing Chapter Markdown

The template script expects markdown chapters in this format:

```markdown
# Chapter One: Title Here

> *Epigraph or subtitle — optional*

---

Prose text starts here...
```

The parser extracts:
- Title from the `# ` heading (strips "Chapter X:" prefix)
- Subtitle from the `>` blockquote after the heading
- Body from everything after the first `---` horizontal rule

## Adding Front Matter (Prologue, Preface, Foreword)

When a book has un-numbered front matter before Chapter 1, treat it as chapter 0.

### Loading
Load the prologue/preface file with `parse_chapter()` and prepend as `(0, title, epigraph, body)` to the chapters list. The parser's `else: body_start = i; break` clause (see Markdown Parsing Robustness above) handles prose-first formats where body text follows the title with no epigraph or separator.

### Rendering in start_chapter()
Check `if num == 0:` to render "PROLOGUE" / "PREFACE" / "FOREWORD" as the pyfiglet banner instead of "Chapter 0". Strip the prefix from the title for a clean subtitle:
```python
if num == 0:
    banner_text = "PROLOGUE"
    display_title = re.sub(r'^PROLOGUE:\s*', '', title, flags=re.IGNORECASE).strip()
```

### TOC entry
In `table_of_contents()`, add an `if num == 0:` block BEFORE the act-heading check. Show "Prologue" as the label instead of "Chapter 0". The prologue entry appears above act headers:
```python
if num == 0:
    self.set_font('Serif', 'B', 8.5)
    self.cell(25, 5, 'Prologue', align='R')
    prologue_title = re.sub(r'^PROLOGUE:\s*', '', title, flags=re.IGNORECASE).strip()
    if self.pass_num == 2 and 0 in self.chapter_links:
        self.cell(0, 5, f'  {prologue_title}', align='L', link=self.chapter_links[0], new_x="LMARGIN", new_y="NEXT")
    else:
        self.cell(0, 5, f'  {prologue_title}', align='L', new_x="LMARGIN", new_y="NEXT")
    # page number ...
    self.ln(6)
    continue
```

### Link verification
With front matter, TOC links should be `N + 1` (chapters + prologue). Verify:
```python
count = len(re.findall(r'/Subtype\s*/Link', raw_pdf_content))
# should equal number of chapters + 1 (for prologue)
```

### Title Page / Colophon
Update stats text to reflect the addition (e.g., `"Prologue + 31 Chapters  ·  ~100,000 Words"` instead of `"31 Chapters  ·  ~97,000 Words"`). The total page count will increase by the prologue's page count (typically +2 pages for a short prologue).

## Template Script

See `templates/build_pdf.py` — a complete working generator that produced a 61-page A5 book from 8 markdown chapters. Copy it, update the paths and ASCII art illustrations, and run.

For a simpler, lighter-weight scaffold (good for quick book builds with fewer formatting features), see `templates/book-generator-simple.py`.

For a production-grade builder with internal TOC links, markdown-in-body rendering, cover image support, and smart alignment, see `references/build_novel_pdf.py` — the location reference for the script that produced a 300-page, 31-chapter novel PDF. The production reference at `references/production-build-31ch.md` documents the full build stats, page distribution, format variations handled, and every bug encountered and fixed.

For a production font-size and color-palette reference from a different build (8-chapter "Firman of Monsoons"), see `references/firman-of-monsoons-reference.md`.

Key sections to customize:
- `CHAPTERS_DIR` — path to your markdown chapters
- `OUTPUT_PDF` — output path
- `FONT_*` constants — font paths
- `CHAPTER_ART` dict — ASCII art per chapter (add/remove entries as needed)
- `COVER_ART` — title page illustration
- `COLOPHON_ART` — closing page

## Cover Image (Title Page Alternative)

To add a full-page cover image (PNG) before the title page:

```python
def cover_page(self):
    """Full-page cover image with no margins."""
    if not os.path.exists(COVER_IMAGE):
        print(f"  WARNING: Cover image not found at {COVER_IMAGE}")
        return
    self.add_page()
    self.page_has_header = False
    self.image(COVER_IMAGE, x=0, y=0, w=PAGE_W, h=PAGE_H)
```

Call `cover_page()` before `title_page()` in the build sequence. The image fills the full A5 page. For A5 (148×210mm), a portrait image of ~1024×1536 works well — the 2:3 aspect ratio closely matches A5 proportions. Larger images are embedded at full resolution; a 2.3MB PNG adds ~2.7MB to the PDF.

**Important:** Adding a cover shifts all subsequent page numbers by +1. If using the two-pass TOC approach, pass 1 must also include the cover page so chapter start pages are calculated correctly.

## Italic Font Limitation — CRITICAL

**DejaVu Sans has NO italic/oblique variant.** The DejaVu font family provides DejaVuSansMono-Oblique.ttf (monospace italic) but no DejaVuSans-Oblique.ttf for the proportional body font. The DejaVuSerif.ttf files are regular/bold only — no italic.

**Do NOT attempt to substitute DejaVuSerif for italic text.** Serif and Sans have different character widths. In segment-by-segment inline renderers, `get_string_width()` measurements use the current font, but rendered segments alternate between Sans (regular) and Serif (italic). This produces mismatched widths → text overflow past the right margin → extra line wraps → phantom page count increases (observed: +6 pages, 300→306).

**The safe approach:** Strip `*italic*` and `_italic_` markers from prose. Render whole-line italics (attributions, epigraphs) in the body font at slightly smaller size with muted color for visual distinction.

**Times core font alternative:** Times is a PDF core font with true italic, but it supports only Latin-1 (Windows-1252) characters. Em-dashes (—, U+2014) and other Unicode cause `UnicodeEncodeError`. Do not switch to core fonts for Unicode text.

**Rigor checklist after ANY rendering change:**
1. Rebuild PDF — verify page count unchanged
2. `grep -c "'I'" build_pdf.py` — should be 0
3. Extract text with pypdf — scan for raw `*` and `_` markers
4. Spot-check known `*italic*` content
5. Verify TOC page numbers still match chapter starts
6. Check longest epigraph (Ch.30) for overflow

## Verification

After generating, validate the PDF:

```bash
file output.pdf                    # Should say "PDF document, version 1.3, N page(s)"
python3 -c "
with open('output.pdf', 'rb') as f:
    h = f.read(10)
    print('Valid PDF' if h.startswith(b'%PDF') else 'CORRUPT')
"
```
