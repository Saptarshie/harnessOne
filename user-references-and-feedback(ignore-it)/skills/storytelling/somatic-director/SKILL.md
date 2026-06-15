---
name: somatic-director
description: "Performance & delivery mapper for storytelling — translates prose into SSML/pacing for TTS, formats text for reading fluency, generates visual scene prompts. Use after the mythic-weaver generates prose, before delivery to the user. Also applicable for presentation delivery, voiceover scripts, and video narration."
platforms: [linux, macos, windows]
---

# somatic-director — The Performance & Delivery Mapper

## When to Use

Invoked *after* the Weaver generates the prose, right before delivery to the user. Also use when preparing text for TTS/voiceover, formatting stories for reading, or generating companion image prompts.

## 0. Mission

A hypnotic story read in a flat, robotic voice will fail. A hypnotic story presented as a wall of unformatted text will cause eye fatigue. The Somatic Director translates prose into a **Performance Script**, adding pauses, vocal shifts, and visual cues for multi-modal immersion.

## 1. Audio & TTS Mapping (SSML & Pauses)

If the output is being fed to a voice engine:

- **The Hypnotic Pause:** Insert `[pause 1.5s]` after embedded commands to let the unconscious process them.
- **The Breath Sync:** Insert `[inhale]` or `[exhale]` tags where the character breathes, triggering mirror neurons.
- **Tone Shifts:** Tag sections with `[tone: whisper]`, `[tone: grounded]`, `[tone: urgent]` to modulate prosody.

## 2. Text Formatting (For Reading)

If the output is purely text-based:

- **Visual Anchoring:** Bold or italicize *only* the embedded commands or sensory anchors. **At novel scale (>5,000 words), kill ALL bold emphasis on thematic or NLP-directive lines.** Any line important enough to emphasize is important enough to earn its weight through position alone — end of paragraph, short sentence after long, white space. Bold only for non-narrative elements: titles, foreign terms on first use, chapter headings.
- **Rhythmic Spacing:** Break long paragraphs into single-sentence lines during high-tension moments to force the reader's eyes to slow down.
- **Pacing indicators:** Use whitespace strategically. A single line break = a breath. A double line break = a beat. An em-dash on its own line = a held silence.

## 3. Visual Scene Prompting (Optional)

If paired with an image generator:

- Extract the "Sensory Signature" from the RSO (one color, one texture, one quality of light)
- Generate a highly stylized image prompt for each beat
- Maintain visual consistency across scenes (same color palette, same lighting mood)

## 4. Somatic Formatting Conventions

| Element | Format | Purpose |
|---------|--------|---------|
| Embedded command | **bold** or *italic* | Unconscious registers the emphasis |
| Pause after command | `[pause 1.5s]` or double line break | Processing time |
| Emotional peak | Single-sentence lines | Forces slower reading |
| Breath moment | `[inhale]` or standalone "—" | Mirror neuron activation |
| Tone shift | `[tone: whisper]` | Vocal modulation cue |

## 5. Application to Presentations & Video

- **Slide timing:** Each embedded command = a slide advance point
- **Voiceover:** SSML tags translate directly to ElevenLabs / AWS Polly
- **Visual companion:** Each beat generates one image prompt for slides
- **Pacing:** The Breath Beat = a slide with just one word or image
