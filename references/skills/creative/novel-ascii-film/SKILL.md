---
name: novel-ascii-film
description: "Convert novel chapters to atmospheric ASCII films with TTS narration — pipeline for markdown parsing, neural TTS, numpy-based ASCII backgrounds, and ffmpeg assembly."
platforms: [linux]
---

# Novel-to-ASCII-Film Pipeline

## When to use
Converting novels/stories into narrated ASCII art films: chapter-by-chapter markdown → TTS audio → atmospheric ASCII backgrounds → text overlay → MP4.

## Architecture

```
Chapter .md → parse_chapter_text() → TTS segments (edge-tts/NeuTTS)
                                    → render_frame() → ASCII backgrounds (numpy)
                                    → render_subtitles() → text overlay
                                    → ffmpeg pipe → MP4 + AAC audio
```

## Key Files (at /workspace/the-firman-of-monsoons/film/pipeline/)

- `tts_engine.py` — Chapter parsing, voice assignment (protagonist/antagonist/narrator), edge-tts generation, period-accurate pronunciation fixes, timeline construction
- `render_engine.py` — 7 atmospheric numpy backgrounds (monsoon rain, stone temple, mist, fire, water, parchment, dawn), composite blending, PIL subtitle overlay with typewriter effect, title/end cards
- `render_chapter.py` — Full orchestrator: parse → TTS → timeline → render frames → ffmpeg mux → final MP4

## TTS Voice Selection
- User prefers **NeuTTS** for natural/emotional voices (not edge-tts which sounded robotic)
- edge-tts is available as fallback (free, no API key): en-IN-NeerjaNeural, en-IN-PrabhatNeural, en-US-AriaNeural
- Voice assignment by role: protagonist POV, male dialogue, third-person narrator, archive/authority voice

## Performance (720p/20fps, 15GB Docker)
- Numpy backgrounds: 30-80ms each
- Composite frame (2 BGs + text): ~100ms
- Full chapter render (~14K frames): ~23 minutes
- Subagent timeout is 600s — CANNOT render full chapter in subagent; must run directly or chunk

## Pitfalls
1. **Background process broken in Docker** — every `terminal(background=True)` exits -1 silently. Use foreground only or cronjob scripts.
2. **Subagent 600s timeout** — renders exceeding 10 minutes cannot run via delegate_task
3. **Noise overflow** — `_fbm()` must be normalized to [-1,1] and colors clamped with `_make_color()`
4. **Per-char PIL draw.text() causes OOM at 720p** — use numpy vectorized backgrounds + bulk text rendering per row
5. **Edge darkness** — empty pixels must be filled with dark grey (10,15,25) not pure black (0,0,0) or output is invisible

## Chapter Config Pattern
```python
CHAPTER_CONFIGS = {
    "01": {"title": "Chapter Title", "bg": ["monsoon_rain", "stone_temple"], 
           "bg_i": [1.0, 0.3], "text_c": (255, 220, 160)},
}
```

## Commands
```bash
export HOME=/root PYTHONPATH=/workspace/pylibs:/film/pipeline
python3 -u render_chapter.py --chapter 01 --fps 20
python3 -u render_chapter.py --chapter 01 --fps 20 --quick  # 4 segments only
```
