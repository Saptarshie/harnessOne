# Production Builder Script Location

The production-grade PDF builder for The Chrysalis Protocol lives at:
  /workspace/the-chrysalis-protocol/build_pdf.py

To adapt for another project, copy it and change:
  - CHAPTERS_DIR — path to markdown chapters
  - OUTPUT_PDF — output path
  - COVER_IMAGE — path to cover PNG (or set to None to skip)
  - COVER_ART / COLOPHON_ART — ASCII art constants
  - FONT_* constants — font paths (keep DejaVu for Unicode support)
  - Chapter art dictionary

The script implements ALL patterns documented in the skill:
  - Two-pass TOC with clickable internal links
  - State-machine chapter parser (handles 8+ format variations)
  - Full markdown-in-body renderer (headings, bold, italic, blockquotes, dividers)
  - Smart alignment (justified prose, left-aligned poems)
  - Cover image embedding
  - DejaVuSerif italic technique (serif contrast for emphasis)
  - Explicit margin management
  - Pyfiglet chapter banners

Run: PYTHONPATH=/workspace/pylibs python3 build_pdf.py

Key classes and methods:
  - BookPDF(FPDF) — custom PDF class with header/footer overrides
  - parse_chapter(filepath) — state-machine markdown parser
  - render_prose(text) — body renderer with full markdown support
  - _render_rich_line(line, font_size, line_h) — inline bold+italic with smart align
  - _render_segments(parts, font_size, line_h, italic_mode) — segment-by-segment italic renderer
  - start_chapter(num, title, epigraph) — chapter opening page
  - table_of_contents(toc_entries) — TOC with act groupings and clickable links
  - cover_page() — full-bleed cover image
  - title_page() — pyfiglet banner + ASCII art
  - colophon() — closing page
