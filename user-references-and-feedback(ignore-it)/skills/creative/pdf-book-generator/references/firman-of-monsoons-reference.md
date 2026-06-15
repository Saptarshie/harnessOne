# Firman of Monsoons — Production Build Reference

This is the production script used to generate "The Firman of Monsoons" — an 8-chapter, 61-page A5 PDF book from markdown files with ASCII art illustrations at each chapter head.

## Key Decisions

- **fpdf2** over reportlab/weasyprint: lightest dep, no system libs needed
- **A5 format** (148×210mm): book-like, good for prose
- **DejaVu fonts**: universally available on Linux, no extra install
- **pyfiglet** for title banners: 571 fonts, `small` font works best for chapter numbers
- **Custom Unicode box-drawing art**: avoids image deps, renders natively in mono font
- **No markdown parser**: simple line-by-line parsing sufficient for clean markdown
- **Scene dividers**: replace `***` with `─────── ◆ ───────` for visual breaks

## Font Sizes (Proven)

| Element | Font | Size | Color |
|---------|------|------|-------|
| Cover title banner | Mono Bold | 5pt | (60, 40, 20) dark brown |
| Cover illustration | Mono | 4pt | (80, 60, 40) |
| Chapter number banner | Mono Bold | 6pt | (60, 40, 20) |
| Chapter title | Serif Bold | 11pt | (60, 40, 20) |
| Chapter subtitle | Serif | 7pt | (120, 100, 80) muted |
| Chapter ASCII art | Mono | 4pt | (100, 80, 50) warm brown |
| Body prose | Serif | 7.5pt | (40, 30, 20) near-black |
| Blockquote | Serif | 7pt | (100, 80, 60) |
| Scene divider | Mono | 6pt | (150, 130, 100) |
| Running header | Serif | 7pt | (130, 130, 130) gray |
| Page number (footer) | Serif | 6pt | (160, 160, 160) |
| TOC entry | Serif | 8pt | (60, 40, 20) |
| Act label (TOC) | Serif Bold | 8pt | (100, 70, 40) |

## ASCII Art Sizing

All custom art must fit within BODY_W (116mm at 16mm margins on A5). At 4pt mono, this gives ~45-50 characters per line. Keep art width to ~46 chars max for reliable centering.

## File Output

Typical output for an 8-chapter novel: ~60 pages, ~195 KB.
