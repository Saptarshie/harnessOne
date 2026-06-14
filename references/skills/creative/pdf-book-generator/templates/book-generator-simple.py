#!/usr/bin/env python3
"""
PDF Book Generator — Simple Scaffold
=====================================
Simpler alternative to the full build_pdf.py template.
Good for quick book builds from markdown chapters with ASCII art.

Customize CHAPTERS_DIR, OUTPUT_PDF, chapter list, and ASCII art.
See references/book-generation-reference.md for the full production example.
See references/firman-of-monsoons-reference.md for a specific build reference.

Dependencies: pip install fpdf2 pyfiglet --target=/path/to/libs --no-deps
"""

import os, sys, re
sys.path.insert(0, '/workspace/pylibs')  # adjust to your pip target

from fpdf import FPDF
import pyfiglet

# ── Paths ──────────────────────────────────────────────
CHAPTERS_DIR = "./chapters"
OUTPUT_PDF  = "./output.pdf"
FONT_DIR    = "/usr/share/fonts/truetype/dejavu"
FONT_MONO   = os.path.join(FONT_DIR, "DejaVuSansMono.ttf")
FONT_SERIF  = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD   = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

# ── Book dimensions (A5) ────────────────────────────────
PAGE_W, PAGE_H = 148, 210
MARGIN = 16
BODY_W = PAGE_W - 2 * MARGIN

# ── ASCII Art (replace with your own) ───────────────────
COVER_ART = r"""Your cover art here"""

CHAPTER_ART = {
    1: r"""Chapter 1 art""",
    2: r"""Chapter 2 art""",
    # ...
}

SCENE_DIVIDER = "       ─────── ◆ ───────"


class BookPDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', (PAGE_W, PAGE_H))
        self.set_auto_page_break(True, MARGIN)
        self.add_font('Serif', '', FONT_SERIF)
        self.add_font('Serif', 'B', FONT_BOLD)
        self.add_font('Mono', '', FONT_MONO)
        self.page_has_header = True

    def header(self):
        if not self.page_has_header: return
        self.set_font('Serif', '', 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 4, 'Book Title', align='L')
        self.cell(0, 4, str(self.page_no()), align='R', new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(180, 180, 180)
        self.line(self.l_margin, self.get_y()+1, PAGE_W-self.r_margin, self.get_y()+1)
        self.ln(5)

    def footer(self):
        self.set_y(-MARGIN + 8)
        self.set_font('Serif', '', 6)
        self.set_text_color(160, 160, 160)
        self.cell(0, 4, str(self.page_no()), align='C')

    def title_page(self, title, subtitle=""):
        self.add_page()
        self.page_has_header = False
        self.set_font('Mono', 'B', 5)
        self.set_text_color(60, 40, 20)
        banner = pyfiglet.figlet_format(title, font="small")
        for line in banner.split('\n'):
            if line.strip():
                self.cell(0, 3.2, line, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(6)
        if COVER_ART:
            self.set_font('Mono', '', 4)
            self.set_text_color(80, 60, 40)
            for line in COVER_ART.split('\n'):
                self.cell(0, 2.5, line, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(6)
        self.set_font('Serif', '', 10)
        self.cell(0, 6, subtitle, align='C', new_x="LMARGIN", new_y="NEXT")

    def start_chapter(self, num, title, art=""):
        self.add_page()
        self.page_has_header = False
        # Chapter number banner
        self.set_font('Mono', 'B', 6)
        self.set_text_color(60, 40, 20)
        num_text = pyfiglet.figlet_format(f"Chapter {num}", font="small")
        for line in num_text.split('\n'):
            if line.strip():
                self.cell(0, 3.8, line, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        # Title
        self.set_font('Serif', 'B', 11)
        self.cell(0, 6, title, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        # Rules + art
        self.set_draw_color(160, 130, 90)
        self.line(self.l_margin+15, self.get_y(), PAGE_W-self.r_margin-15, self.get_y())
        self.ln(4)
        if art:
            self.set_font('Mono', '', 4)
            self.set_text_color(100, 80, 50)
            for line in art.split('\n'):
                if line.strip():
                    self.cell(0, 2.5, line, align='C', new_x="LMARGIN", new_y="NEXT")
            self.ln(4)
            self.line(self.l_margin+15, self.get_y(), PAGE_W-self.r_margin-15, self.get_y())
            self.ln(5)
        self.page_has_header = True

    def render_prose(self, text):
        self.set_text_color(40, 30, 20)
        self.set_font('Serif', '', 7.5)
        for line in text.split('\n'):
            if not line.strip():
                self.ln(2)
                continue
            if line.strip().startswith('>'):
                self.set_font('Serif', '', 7)
                self.set_text_color(100, 80, 60)
                self.set_x(self.l_margin + 6)
                self.multi_cell(BODY_W - 12, 4.2, line.strip().lstrip('>').strip())
                self.set_font('Serif', '', 7.5)
                self.set_text_color(40, 30, 20)
                self.ln(2)
                continue
            if line.strip() in ('***', '* * *', '---'):
                self.ln(3)
                self.set_font('Mono', '', 6)
                self.set_text_color(150, 130, 100)
                self.cell(0, 4, SCENE_DIVIDER, align='C', new_x="LMARGIN", new_y="NEXT")
                self.set_font('Serif', '', 7.5)
                self.set_text_color(40, 30, 20)
                self.ln(3)
                continue
            self.multi_cell(BODY_W, 4.2, line, align='J')


def parse_chapter(filepath):
    """Extract title and body from markdown chapter."""
    with open(filepath) as f:
        content = f.read()
    lines = content.split('\n')
    title = ""
    body_lines = []
    in_header = True
    for line in lines:
        if in_header and line.startswith('# '):
            title = re.sub(r'^Chapter\s+\w+[\s:—–-]+', '', line.lstrip('# ').strip(), flags=re.IGNORECASE)
            continue
        if in_header and line.startswith('>'):
            continue
        if in_header and line.startswith('---'):
            in_header = False
            continue
        if not in_header:
            body_lines.append(line)
    return title, '\n'.join(body_lines)


def main():
    pdf = BookPDF()
    pdf.title_page("YOUR TITLE", "Your Subtitle")

    chapter_files = sorted(f for f in os.listdir(CHAPTERS_DIR) if f.endswith('.md'))
    for i, fname in enumerate(chapter_files, 1):
        title, body = parse_chapter(os.path.join(CHAPTERS_DIR, fname))
        pdf.start_chapter(i, title, CHAPTER_ART.get(i, ""))
        pdf.render_prose(body)

    pdf.output(OUTPUT_PDF)
    print(f"Done: {OUTPUT_PDF} ({pdf.page_no()} pages)")


if __name__ == '__main__':
    main()
