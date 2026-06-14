# Font Glyph Coverage for PDF Book Generation

## The Core Problem

When embedding ASCII art in PDFs via fpdf2, you MUST use only characters that your chosen monospace font can actually render. If a glyph is missing, fpdf2 prints a warning like:

```
Font MPDFAA+DejaVuSansMonoBook is missing the following glyphs: '🐐' (U+1F410)
```

The PDF will still be generated, but those characters will appear as blank boxes or `.notdef` rectangles. The user won't see your art — they'll see holes.

## DejaVu Sans Mono Coverage

DejaVu Sans Mono (the standard Linux monospace font) covers:

### ✅ Safe — Fully Supported
- **ASCII printable (32–126)**: letters, digits, punctuation
- **Latin-1 Supplement (160–255)**: accented letters, common symbols
- **Box Drawing (2500–257F)**: `╔╗╚╝║═╠╣╦╩╬┌┐└┘│─├┤┬┴┼`
- **Block Elements (2580–259F)**: `░▒▓█▄▀▌▐`
- **Geometric Shapes (25A0–25FF)**: `●○■□▲△▼▽◆◇◉★☆`
- **Arrows (2190–21FF)**: `←→↑↓↔`
- **General Punctuation (2000–206F)**: em-dash, en-dash, bullet `•`

### ❌ Not Supported — Will Render as Blank
- **Emoji (1F300–1F9FF)**: 🐐🐎🧑☀️🐱🐕 etc.
- **Miscellaneous Symbols (2600–26FF)**: ☀️☁️☂️ (the emoji presentation forms)
- **Devanagari (0900–097F)**: ॐ and other Indic scripts
- **Some special Unicode (various)**: ⊚ (U+229A), ♜ (U+265C), ⚖️ (U+2696 + U+FE0F)
- **Variation selectors (FE0F)**: the invisible character that forces emoji presentation

### ⚠️ Borderline — May Work
- `★` (U+2605, BLACK STAR) — in DejaVu Sans Mono's text presentation. The emoji variant `★️` (with U+FE0F) will NOT work.
- `♜` (U+265C) — chess symbols are in DejaVu Sans Mono but rendering may vary by PDF viewer.

## The Rule

**When in doubt, use ASCII only.** Every character from space (32) to tilde (126) is guaranteed. Box-drawing and block elements are second-tier safe. Everything else: test first or avoid.

## Quick Replacement Table

| Emoji / Unicode | ASCII replacement |
|----------------|-------------------|
| 🐐 goat | `/||\`  or  `\\O/` |
| 🐎 horse | `(())`  or  `/\\/\\` |
| 🧑 person | `o`  or  `|o|` |
| ☀️ sun | `*`  or  `sunburst` |
| ⚖️ scales | `[*]`  or  `^` |
| ★ star | `*` |
| ॐ om | `Om` |
| ⊚ | `@`  or  `(o)` |
| ♜ rook | `R` |

## Font Discovery

To check what glyphs a font supports:

```bash
# List all glyphs in a font (needs fonttools)
pip install fonttools
python3 -c "
from fontTools.ttLib import TTFont
font = TTFont('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')
cmap = font.getBestCmap()
# Check specific codepoint
for cp in [0x1F410, 0x2600, 0xFE0F]:
    print(f'U+{cp:04X}: {\"PRESENT\" if cp in cmap else \"MISSING\"} ({cmap.get(cp, \"?\")})')
"

# Simpler: just try rendering and check warnings
python3 -c "
from fpdf import FPDF
pdf = FPDF()
pdf.add_font('Mono', '', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')
pdf.add_page()
pdf.set_font('Mono', '', 10)
pdf.cell(0, 10, 'Test: 🐐 ★ ॐ')
pdf.output('/tmp/font_test.pdf')
print('Check /tmp/font_test.pdf for blank boxes')
"
```
