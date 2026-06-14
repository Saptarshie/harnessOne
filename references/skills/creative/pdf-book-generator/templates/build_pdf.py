#!/usr/bin/env python3
"""
PDF Book Generator — Template Script
=====================================
Converts multi-chapter markdown files into a professionally formatted
A5 PDF book with ASCII art illustrations.

Adaptation checklist:
  1. Set CHAPTERS_DIR to your markdown chapters directory
  2. Set OUTPUT_PDF to your desired output path
  3. Verify FONT_* paths for your platform
  4. Replace ASCII art constants (COVER_ART, CH*_ART) with your own art
  5. Adjust chapter count in main() loop
  6. Set PAGE_W/PAGE_H for different page sizes if needed
  7. Install: pip install fpdf2 pyfiglet --target=/path/to/libs --no-deps
  8. Run: PYTHONPATH=/path/to/libs python3 build_pdf.py

Dependencies: fpdf2, pyfiglet (both zero hard deps at runtime)
Fonts: DejaVu family (standard on Linux, brew install font-dejavu on macOS)
"""

import os, sys, re
sys.path.insert(0, '/workspace/pylibs')  # <-- adjust to your pip --target path

from fpdf import FPDF
import pyfiglet

# ═══════════════════════════════════════════════════════════
# CONFIGURATION — adjust these
# ═══════════════════════════════════════════════════════════

CHAPTERS_DIR = "/path/to/your/chapters"   # directory with 01-*.md files
OUTPUT_PDF  = "/path/to/output/book.pdf"
FONT_DIR    = "/usr/share/fonts/truetype/dejavu"
FONT_MONO   = os.path.join(FONT_DIR, "DejaVuSansMono.ttf")
FONT_SERIF  = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD   = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
FONT_MONO_B = os.path.join(FONT_DIR, "DejaVuSansMono-Bold.ttf")

# Page dimensions (A5 — book-like)
PAGE_W, PAGE_H = 148, 210  # mm
MARGIN = 16
BODY_W = PAGE_W - 2 * MARGIN

# ═══════════════════════════════════════════════════════════
# ASCII ART ILLUSTRATIONS — replace with your own
# ═══════════════════════════════════════════════════════════

COVER_ART = r"""
                ╔══════════════════════════════╗
                ║        YOUR BOOK TITLE       ║
                ╚══════════════════════════════╝
                        , - ~ ~ ~ - ,
                    , '               ' ,
                  ,                     ,
                 ,                       ,
                ,                         ,
                '                         '
                 ,                       ,
                  '                     '
                   '                   '
"""

CHAPTER_ART = {
    1: r"""
         ╔════════════════════════╗
         ║      CHAPTER ONE       ║
         ╚════════════════════════╝
              [your art here]
    """,
    # Add entries for chapters 2..N
}

COLOPHON_ART = r"""
         ╔══════════════════════════════════╗
         ║      End of Book                 ║
         ╚══════════════════════════════════╝
"""

SCENE_DIVIDER = "       ─────── ◆ ───────"


# ═══════════════════════════════════════════════════════════
# PDF CLASS
# ═══════════════════════════════════════════════════════════

class BookPDF(FPDF):
    """Custom PDF with headers, chapter starts, and body rendering."""

    def __init__(self):
        super().__init__(orientation='P', unit='mm', format=(PAGE_W, PAGE_H))
        self.set_auto_page_break(True, MARGIN)
        self.add_font('Serif', '', FONT_SERIF)
        self.add_font('Serif', 'B', FONT_BOLD)
        self.add_font('Mono', '', FONT_MONO)
        self.add_font('Mono', 'B', FONT_MONO_B)
        self.chapter_num = 0
        self.page_has_header = True

    def header(self):
        if not self.page_has_header:
            return
        self.set_font('Serif', '', 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 4, 'Book Title Here', align='L')
        self.cell(0, 4, str(self.page_no()), align='R', new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(180, 180, 180)
        self.line(self.l_margin, self.get_y() + 1, PAGE_W - self.r_margin, self.get_y() + 1)
        self.ln(5)

    def footer(self):
        self.set_y(-MARGIN + 8)
        self.set_font('Serif', '', 6)
        self.set_text_color(160, 160, 160)
        self.cell(0, 4, str(self.page_no()), align='C')

    def title_page(self):
        self.add_page()
        self.page_has_header = False
        self.set_font('Mono', 'B', 5)
        self.set_text_color(60, 40, 20)
        banner = pyfiglet.figlet_format("YOUR TITLE", font="small")
        for line in banner.split('\n'):
            if line.strip():
                self.cell(0, 3.2, line, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(6)
        self.set_font('Mono', '', 4)
        self.set_text_color(80, 60, 40)
        for line in COVER_ART.split('\n'):
            self.cell(0, 2.5, line, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(8)
        self.set_font('Serif', '', 10)
        self.set_text_color(60, 40, 20)
        self.cell(0, 6, 'A Novel', align='C', new_x="LMARGIN", new_y="NEXT")

    def table_of_contents(self, toc_entries):
        """toc_entries: list of (number_str, title_str, optional_subtitle_str)"""
        self.add_page()
        self.page_has_header = False
        self.set_font('Serif', 'B', 14)
        self.set_text_color(60, 40, 20)
        self.cell(0, 8, 'Contents', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(8)
        for num, title in toc_entries:
            self.set_font('Serif', '', 8)
            self.set_text_color(60, 40, 20)
            self.cell(16, 5, num, align='R')
            self.set_font('Serif', 'B', 8)
            self.cell(0, 5, f'  {title}', align='L', new_x="LMARGIN", new_y="NEXT")
            self.ln(2)

    def start_chapter(self, num, title, art, subtitle=""):
        self.chapter_num = num
        self.add_page()
        self.page_has_header = False
        self.set_font('Mono', 'B', 6)
        self.set_text_color(60, 40, 20)
        num_text = pyfiglet.figlet_format(f"Chapter {num}", font="small")
        for line in num_text.split('\n'):
            if line.strip():
                self.cell(0, 3.8, line, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_font('Serif', 'B', 11)
        self.set_text_color(60, 40, 20)
        self.cell(0, 6, title, align='C', new_x="LMARGIN", new_y="NEXT")
        if subtitle:
            self.set_font('Serif', '', 7)
            self.set_text_color(120, 100, 80)
            self.cell(0, 4, subtitle, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_draw_color(160, 130, 90)
        self.set_line_width(0.3)
        rule_y = self.get_y()
        self.line(self.l_margin + 15, rule_y, PAGE_W - self.r_margin - 15, rule_y)
        self.ln(4)
        if art:
            self.set_font('Mono', '', 4)
            self.set_text_color(100, 80, 50)
            for line in art.split('\n'):
                if line.strip():
                    self.cell(0, 2.5, line, align='C', new_x="LMARGIN", new_y="NEXT")
            self.ln(4)
            self.set_draw_color(160, 130, 90)
            rule_y2 = self.get_y()
            self.line(self.l_margin + 15, rule_y2, PAGE_W - self.r_margin - 15, rule_y2)
            self.ln(5)
        self.page_has_header = True

    def render_prose(self, text):
        """Render chapter body with formatting — blockquotes, scene dividers, bold spans."""
        self.set_text_color(40, 30, 20)
        body_font_size = 7.5
        self.set_font('Serif', '', body_font_size)
        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                self.ln(2)
                i += 1
                continue
            if line.strip().startswith('>'):
                self.set_font('Serif', '', 7)
                self.set_text_color(100, 80, 60)
                content = line.strip().lstrip('>').strip()
                self.set_x(self.l_margin + 6)
                self.multi_cell(BODY_W - 12, 4.2, content, align='L')
                self.set_font('Serif', '', body_font_size)
                self.set_text_color(40, 30, 20)
                self.ln(2)
                i += 1
                continue
            if line.strip() in ('***', '* * *'):
                self.ln(3)
                self.set_font('Mono', '', 6)
                self.set_text_color(150, 130, 100)
                self.cell(0, 4, SCENE_DIVIDER, align='C', new_x="LMARGIN", new_y="NEXT")
                self.set_font('Serif', '', body_font_size)
                self.set_text_color(40, 30, 20)
                self.ln(3)
                i += 1
                continue
            self.set_x(self.l_margin)
            self.multi_cell(BODY_W, 4.2, line, align='J')
            i += 1


# ═══════════════════════════════════════════════════════════
# UTILITY — extract title/subtitle/body from markdown chapter
# ═══════════════════════════════════════════════════════════

def parse_chapter_text(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    lines = content.split('\n')
    title = ""
    subtitle = ""
    body_lines = []
    in_header = True
    for line in lines:
        if in_header and line.startswith('# '):
            title = line.lstrip('# ').strip()
            title = re.sub(r'^Chapter\s+\w+[\s:—–-]+', '', title, flags=re.IGNORECASE)
            continue
        if in_header and line.startswith('>'):
            subtitle = line.strip().lstrip('>').strip().strip('*').strip()
            continue
        if in_header and line.startswith('---'):
            in_header = False
            continue
        if not in_header:
            body_lines.append(line)
    return title, subtitle, '\n'.join(body_lines)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    pdf = BookPDF()
    pdf.title_page()

    # Build TOC from chapter files
    toc_entries = []
    chapter_files = sorted([f for f in os.listdir(CHAPTERS_DIR) if f.endswith('.md')])
    for fname in chapter_files:
        fpath = os.path.join(CHAPTERS_DIR, fname)
        title, _, _ = parse_chapter_text(fpath)
        num = fname[:2]  # assumes "01-*.md" naming
        toc_entries.append((num, title))
    pdf.table_of_contents(toc_entries)

    # Render chapters
    for i, fname in enumerate(chapter_files, 1):
        fpath = os.path.join(CHAPTERS_DIR, fname)
        title, subtitle, body = parse_chapter_text(fpath)
        art = CHAPTER_ART.get(i, "")
        print(f"  Chapter {i}: {title}")
        pdf.start_chapter(i, title, art, subtitle)
        pdf.render_prose(body)

    # Colophon
    pdf.add_page()
    pdf.page_has_header = False
    pdf.set_font('Mono', '', 4)
    pdf.set_text_color(80, 60, 40)
    for line in COLOPHON_ART.split('\n'):
        pdf.cell(0, 2.5, line, align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.output(OUTPUT_PDF)
    size_kb = os.path.getsize(OUTPUT_PDF) / 1024
    print(f"\nPDF generated: {OUTPUT_PDF}  ({size_kb:.0f} KB, {pdf.page_no()} pages)")


if __name__ == '__main__':
    main()
