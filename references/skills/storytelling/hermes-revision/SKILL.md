---
name: hermes-revision
description: >-
  Use when performing post-completion prose polish on a fully-written novel.
  Actor subagent that revises prose chapter-by-chapter for engagement, sensory
  density, rhythm, and neuro-narrative architecture — WITHOUT altering story-line,
  plot, character actions, or dialogue meaning. Works in /revisions/ dir. Always
  paired with hermes-revision-critic in a separate agent for drift validation.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [storytelling, revision, prose-polish, novel, post-completion]
    related_skills:
      - hermes-revision-primer
      - hermes-revision-critic
      - neuro-narrative-architecture
      - novel-weaver
      - novel-writing-pipeline
---

# Hermes Revision — Post-Completion Prose Polish (Actor)

## Core Philosophy

This skill exists to make an ALREADY-COMPLETE novel more attractive at the prose
level — without touching story architecture. It is a finish-quality pass, not a
rewrite. The novel's plot, characters, themes, and emotional arcs are SACRED.
The revision touches ONLY the surface: language, rhythm, sensory texture, and
neuro-narrative engagement.

**The prime directive: REVISED CHAPTER N MUST BE PLOT-COMPATIBLE WITH ORIGINAL
CHAPTER N+1. The revision is invisible to the story engine. A reader who read
original Ch.1-10 and revised Ch.11-31 should experience zero continuity breaks.**

---

## When to Use

- Novel is COMPLETE (all chapters drafted, all architecture files final)
- User wants to enhance prose quality without changing the story
- User wants improved sensory density, rhythm, subtext, and reader engagement
- User invokes the revision pipeline explicitly

**Do NOT use:**

- Mid-draft (during initial writing — use the main writing pipeline instead)
- When story-level changes are needed (this is prose-only)
- When architecture files are not finalized

---

## What the Revisor CAN Do

### Permitted Operations

| Category                    | What                                                    | Example                                                                                                                        |
| --------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Sentence rhythm**         | Vary length, break run-ons, combine fragments           | Split a 40-word sentence into 12+15+13. Combine three 5-word fragments into one flowing line.                                  |
| **Word choice**             | Sharpen verbs, cut filler, replace weak adjectives      | "walked slowly" → "trudged." "very cold" → "bitter."                                                                           |
| **Sensory density**         | Add/refine VAK details (≥1 per 3 sentences target)      | After "She entered the room" add "The stone was wet under her palm, and somewhere water dripped with the patience of geology." |
| **Somatic markers**         | Displace emotion onto physical objects                  | "She was afraid" → "Her right hand found the scar on her forearm and pressed until the dead tissue ached."                     |
| **Register degradation**    | Ensure prose fragments under physical stress            | Replace lyrical exhaustion description with "Wet. Still moving. That was all."                                                 |
| **Cortisol-oxytocin waves** | Ensure action scenes are followed by vulnerability      | After combat: cut tactical debrief, add intimate moment where a character's hands shake and someone notices.                   |
| **Information gaps**        | Insert micro-mysteries at scene breaks                  | End a section mid-thought so the next section's opening carries an unresolved cognitive itch.                                  |
| **Subtext protection**      | Cut thesis statements that name what was shown          | Delete "She realized the war had changed her." The scene already showed the change.                                            |
| **Paragraph breaking**      | Restructure paragraph flow for reader momentum          | Break a 200-word wall into 3-4 paragraphs with white space at emotional peaks.                                                 |
| **Redundancy removal**      | Cut repeated words, phrases, or ideas within same scene | Same adjective used 3x in 5 sentences → keep strongest, replace others.                                                        |
| **Dialogue rhythm**         | Tighten tags, remove unnecessary beats                  | "he said" / "she said" minimalism. Cut "she paused, considering her words" — the dialogue IS the consideration.                |
| **Transition sharpening**   | Make *** scene breaks land harder                       | Ensure the line before *** earns the break — unresolved tension or an irreversible action.                                     |

### The Finishing Polish Mindset

This is NOT editing. This is polishing. Think of it as: the sculpture is complete.
Now you're removing tool marks, buffing surfaces, and ensuring light catches the
right angles — NOT adding new limbs or changing the pose.

---

## What the Revisor CANNOT Do (Hard Prohibitions)

| Category                       | Prohibition                                                                       | Detection                                           |
| ------------------------------ | --------------------------------------------------------------------------------- | --------------------------------------------------- |
| **Plot events**                | Cannot add, remove, or reorder story events                                       | Compare event sequence between original and revised |
| **Character actions**          | Cannot change what any character DOES                                             | Compare character action verbs                      |
| **Dialogue content**           | Cannot change what anyone SAYS (only HOW it's tagged) | Compare quoted dialogue verbatim                    |
| **Dialogue meaning**           | Cannot alter subtext, implication, or emotional weight of dialogue                | Critic review                                       |
| **Character motivations**      | Cannot add/change stated or implied reasons for action                            | Compare internal monologue content                  |
| **Backstory**                  | Cannot add/change character history or Canon Lockbox facts                        | Compare against architecture files                  |
| **BFS**                        | Cannot change the Blunt Force Summary or its placement                            | Chapter BFS must match original                     |
| **Epigraph**                   | Cannot change the epigraph text or attribution                                    | Verbatim match required                             |
| **Scene count**                | Cannot add or remove scenes or section breaks                                     | *** count must match                                |
| **POV characters**             | Cannot change which POVs appear or their scene allocation                         | POV count per chapter must match                    |
| **Emotional arc**              | Cannot change the emotional trajectory of a scene or chapter                      | Critic review                                       |
| **Thematic content**           | Cannot add/remove/alter themes                                                    | Critic review                                       |
| **Character deaths/survivals** | Cannot change who lives or dies (even off-page references)                        | Compare casualty references                         |
| **Timeline**                   | Cannot change temporal references (hours, sequence)                               | Compare time markers                                |
| **Location**                   | Cannot change where scenes take place                                             | Compare setting descriptions                        |
| **Canon Lockbox**              | Cannot contradict any Lockbox fact                                                | Compare against Lockbox                             |
| **Story structure**            | Cannot merge, split, or reorder chapters                                          | Chapter count and sequence invariant                |

---

## Revision Workflow (Chapter-by-Chapter)

### Pre-Flight (Before Revising Any Chapter)

1. **Verify novel is complete:** All chapters exist, all architecture files final.
2. **Load architecture files:** Read 01-character-models.md, 02-zeigarnik-ledger.md, 03-rso-log.md, README.md.
3. **Initialize revision-log.md** in /revisions/ (if first run).
4. **Copy the Canon Lockbox** from novel-writing-pipeline or README — this is your constraint boundary.
5. **Identify which chapter to revise** (typically sequential: 1→N).

### Per-Chapter Revision Protocol

```
For each chapter N:

1. READ original chapter (chapters/NN-title.md) — full read, no skimming.

2. EXTRACT structural skeleton:
   - Scene count (*** dividers)
   - POV sequence
   - Key events per scene (1-line each)
   - BFS location and exact text
   - Epigraph exact text
   - Dialogue content (who speaks, what they say)
   - Emotional arc per scene (tension start → peak → resolve)
   - Setting descriptions

3. REVISE prose — apply permitted operations ONLY:
   a. Sensory density pass: ≥1 VAK per 3 sentences. Add where sparse.
   b. Rhythm pass: vary sentence lengths. No 3 identical-length sentences in sequence.
   c. Somatic marker pass: replace emotion-TELLING with body-SHOWING.
   d. Register pass: ensure prose degrades under physical stress.
   e. Cortisol-oxytocin pass: ensure action→vulnerability rhythm.
   f. Subtext pass: cut ALL thesis statements that name what was shown.
   g. Redundancy pass: cut repeated distinctive words/phrases.
   h. Transition pass: ensure *** breaks land on unresolved tension.
   i. Dialogue tag pass: minimize to said/asked. Cut explanatory beats.

4. VERIFY skeleton integrity:
   - Scene count matches original
   - POV sequence matches original
   - BFS exact text matches original
   - Epigraph exact text matches original
   - Dialogue content matches original (verbatim quote comparison)
   - Key events match original (1-line summaries)
   - Character actions match original

5. SAVE to revisions/NN-title-revised.md

6. LOG in revision-log.md:
   - Chapter N revised
   - Word count delta (original → revised)
   - Operations applied (checklist)
   - Any edge cases or notes
```

### Word Count Budget

Net word count change per chapter should be modest. The goal is polish, not
expansion. Typical ranges:

| Chapter Length    | Expected Delta |
| ----------------- | -------------- |
| 1,500-2,500 words | ±100-200 words |
| 2,500-4,000 words | ±150-300 words |
| 4,000+ words      | ±200-400 words |

If a revision exceeds +500 words net, it is probably adding content, not
polishing. The critic should flag this.

---

## Subagent Integration

The revisor runs as a **delegate_task subagent** with:

**Skills loaded:**

- `hermes-revision-primer` (LOAD FIRST — full system context and architecture overview)
- `hermes-revision` (this skill — the protocol)
- `neuro-narrative-architecture` (engagement patterns)
- `novel-weaver` (novel-scale constraints reference)

**Toolsets:** ["file", "terminal"]

**Context packet MUST include:**

1. The full original chapter text (or path to read it)
2. The Canon Lockbox (from architecture)
3. Character models summary (from architecture)
4. The chapter's BFS and epigraph (exact text)
5. The revision-log.md current state
6. ALL abbreviation definitions (VAK, BFS, etc. — subagents have no memory)

**The revisor MUST NOT:**

- Self-criticize or evaluate its own output quality
- Run constraint audits (that's the critic's job)
- Modify architecture files
- Access chapters other than the one being revised (except for context reference)

---

## Revision Log Format

The revision-log.md lives at `/revisions/revision-log.md` and tracks:

```markdown
# Revision Log — The Chrysalis Protocol

> Post-completion prose polish. Actor: hermes-revision. Critic: hermes-revision-critic.

## Status

| Ch | Original | Revised | Critic Pass | Notes |
|----|----------|---------|-------------|-------|
| 01 | ✅ | ⬜ | ⬜ | |
| 02 | ✅ | ⬜ | ⬜ | |
| ... | | | | |
| 31 | ✅ | ⬜ | ⬜ | |

## Chapter Summaries

### Chapter N — Title
- **Revised:** [timestamp]
- **Word count:** [original] → [revised] (Δ: +X/-Y)
- **Operations:** [checklist of applied ops]
- **Critic verdict:** [PASS / ISSUES / BLOCKED]
- **Critic issues:** [if any]
- **Compatibility note:** [any edge cases for Ch.N+1]
```

---

## Integration with Novel-Writing Pipeline

The revision pipeline is a SEPARATE phase that runs AFTER the main writing
pipeline has produced all chapters. The sequence is:

```
1. Main writing pipeline (Ch.1 → Ch.N) → novel complete
2. Architecture files finalized → state frozen
3. REVISION PIPELINE (this skill):
   a. For each chapter N (sequential):
      - Dispatch REVISOR subagent (hermes-revision + neuro-narrative-architecture)
      - Dispatch CRITIC subagent (hermes-revision-critic ONLY — separate agent)
      - If critic passes: proceed to Ch.N+1
      - If critic flags issues: fix, re-submit to critic
   b. After all chapters revised: final integration check
4. Rebuild PDF from /revisions/ if desired
```

---

## Common Pitfalls

1. **Over-polishing:** Adding sensory details that change the scene's meaning
   or emotional valence. The revisor must preserve the EXACT emotional arc.
   Fix: After revision, read the original and revised side-by-side. If the
   revised scene FEELS different (not just reads better), you over-polished.

2. **Drift by accumulation:** Small changes that are individually harmless
   compound into story-level drift by Ch.31. Fix: The critic checks
   compatibility with the NEXT chapter, not just the current one.

3. **Thesis insertion:** The revisor, trained on showing-not-telling, may be
   tempted to add a clarifying sentence "for the reader." This is worse than
   the original. Fix: The subtext protection rule — if the original showed it,
   the revision must not name it.

4. **Voice homogenization:** Polishing all chapters to the same "good prose"
   standard erases character voice differences. Kaelen's technical register,
   Theron's choral syntax, Nera's terse pragmatism — these must survive polish.
   Fix: Before revising, note the POV's distinctive voice markers. Preserve them.

5. **Conflict with Canon Lockbox:** Adding a sensory detail that contradicts
   established facts (e.g., mentioning ozone AFTER Ch.30 when it's extinguished).
   Fix: The Canon Lockbox in the context packet prevents this.

6. **BFS dilution:** The revisor might be tempted to "improve" the BFS language.
   The BFS is SACRED — its exact wording was user-designated. Fix: BFS text
   must match original verbatim.

8. **Scene button preservation (CRITICAL — caught post-Ch.12 audit):**
   Original chapters often have punchier scene endings than revisions. The revisor
   must NOT replace a strong closing line with a softer or more "literary" version.
   Field examples of nearly-lost closers: "Confirming. He still had a face. Still
   had secrets. Still had a self that the Chorus did not own... Not yet." (Ch.2),
   "Twenty-three minds had agreed on a lie, and the twenty-fourth could not make
   himself heard." (Ch.3), "She had spent her whole life running away from other
   people. For the first time, she was riding toward one." (Ch.9).
   **Fix: When the original closes on a distinctive rhythmic pattern (staccato,
   Rule of Three, aphoristic punch, ironic reversal), keep it intact. These are
   the chapter's buttons — they're what the reader exits on. Polish AROUND them.**

9. **Active agency over passive paralysis (CRITICAL — caught Ch.9 audit):**
   When a character makes an active, defining choice at chapter end (Nera mounting
   her horse and riding toward someone for the first time), do NOT replace it with
   passive reflection (sitting in the dark, paralyzed by fear). The thriller needs
   momentum. The character's choice IS the prose. **Fix: Character action at
   chapter close is sacred — same protection tier as BFS and epigraph.**

10. **Negative space for psychology (CRITICAL — caught Ch.10 audit):**
    A single word or phrase can carry immense psychological weight. "A sin of
    cowardice" transforms Idris's self-assessment from factual to self-lacerating.
    "The universe did not reward elegance with truth" is philosophically harder
    than "The universe preferred mess." **Fix: When the original uses morally
    weighted language (sin, cowardice, reward, truth, lie), do not neutralize
    it into morally neutral alternatives (mess, different, omission). The moral
    weight IS the character's psychology.**

12. **Clinical detachment after violence (Ch.23):**
    After extreme physical violence (battalion incinerated, Null-dome discharge),
    let the prose go cold and impersonal. Short declarative sentences. The
    physics doesn't care. The universe just completed a circuit. "Nobody spoke.
    The ozone was very clean." "The physics had no further comment." This
    registers as sociopathic detachment from the universe itself — far more
    chilling than emotional description.

13. **Ontological shock naming (Ch.24):**
    After a paradigm-shattering revelation (the world IS a machine), name
    explicitly what was lost. Not just "they were silent" — enumerate the
    casualties of worldview: the reflex of touch, the belief that stone was
    geology, the lid of a containment vessel. Make the reader feel the
    psychological death beneath the physical survival.

14. **Body-horror precision (Ch.26):**
    When violence happens to a body, slow time. Each thread, each nerve, each
    flash gets its own sentence. "A small star dying" for a severed neural link.
    "A wave of cold" for nerve release. "The way you know when a room you have
    been in for hours is suddenly empty" for the finest, almost imperceptible
    break. This is sci-fi body-horror — the violence is intimate and sequential.

15. **Degraded syntax under compulsion (Ch.27):**
    When a character is being controlled/overridden by an external force
    (machine, artifact, compulsion), their sentences MUST fragment. No clauses.
    No conjunctions. Subject-verb-object stripped to bare meaning. "Harvest
    profile inverts damping nodes. Containment architecture reverses. Machine
    consumes." She isn't arguing — she's translating the machine's death
    rattle through vocal cords that are no longer hers.

16. **Punchy cynicism over elegant metaphor (Ch.28):**
    At moments of cosmic absurdity (empires fighting 300 years over a broken
    machine), the metaphor should land like a punchline. "Ripped the dashboard
    out" beats "became visible." The factions' wars weren't tragic — they
    were stupid. The cynicism IS the thematic point. Elegance undercuts it.

---

## Verification Checklist

Before submitting a revised chapter to the critic:

- [ ] Scene count (*** dividers) matches original
- [ ] POV sequence matches original
- [ ] BFS exact text matches original
- [ ] Epigraph exact text matches original
- [ ] All dialogue content matches original (spot-check 5+ quotes)
- [ ] All character actions match original
- [ ] No Canon Lockbox violations
- [ ] Word count delta within budget (±400 words)
- [ ] No thesis sentences added that weren't in original
- [ ] POV character voice markers preserved
- [ ] Sensory density improved (≥1 VAK per 3 sentences)
- [ ] File saved to revisions/NN-title-revised.md
- [ ] Revision-log.md updated
