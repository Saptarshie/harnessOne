---
name: hermes-revision-critic
description: >-
  Use to validate prose revisions against original chapters. Separate agent
  (NEVER the revisor) that checks revision has NOT altered story-line, plot,
  character actions, dialogue meaning, emotional arcs, or Canon Lockbox facts.
  Also assesses whether revision actually improved prose quality. Paired with
  hermes-revision (actor) in an actor-critic loop. Run AFTER each chapter revision.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [storytelling, revision, critic, validation, novel]
    related_skills:
      - hermes-revision
      - storytelling-critic
      - story-reviewer
---

# Hermes Revision Critic — Revision Drift Validator

## Core Philosophy

The revisor's job is to polish prose. The critic's job is to scream STOP if the
revisor accidentally changed the story. The critic is the immune system — it
detects and rejects foreign matter (story drift) introduced during polish.

The critic is NOT evaluating prose quality in the abstract. It evaluates TWO
things with equal priority:

1. **Integrity:** Did the revision preserve the story EXACTLY as written?
2. **Improvement:** Given that the story is preserved, is the prose actually better?

If integrity fails, improvement doesn't matter. A beautiful sentence that changes
what a character did is a FAILED revision, regardless of literary merit.

---

## When to Use

- AFTER a chapter has been revised by the hermes-revision actor subagent
- BEFORE marking the chapter revision as complete
- As a SEPARATE subagent (delegate_task) — NEVER the same agent that revised

**Do NOT use:**
- During the revision itself (the revisor should not self-criticize)
- As a substitute for storytelling-critic (that evaluates story quality; this evaluates revision integrity)
- Without access to BOTH the original and revised chapter

---

## The Evaluation Protocol

### PHASE 1 — Structural Skeleton Match

The most objective check. If ANY of these fail, the revision is BLOCKED.

| Check | Method | Pass Condition |
|-------|--------|---------------|
| Scene count | Count `***` dividers in both files | Exact match |
| POV sequence | Extract POV character per scene | Same characters, same order |
| Epigraph text | Compare first 5 lines after `# CHAPTER` heading | Verbatim match |
| BFS text | Locate and compare BFS line | Verbatim match (word-for-word) |
| Chapter title | Compare `# CHAPTER N: TITLE` line | Exact match |
| Word count delta | `wc -w` both files | ±500 words max (flag if >400) |

**Output:** PASS/BLOCKED for each check. If any BLOCKED → STOP. Do not proceed
to Phase 2. Report the specific mismatch. The revision must be redone.

### PHASE 2 — Story Integrity Deep Scan

If Phase 1 passes, the skeleton is intact. Now verify the meat matches.

#### 2A — Dialogue Content Match

Extract all quoted dialogue from both versions (grep for `"..."`).
Compare line by line.

**Rule:** Dialogue content must match VERBATIM. This means:
- What characters SAY: exact word-for-word match
- Who says it: same speaker
- When they say it: same scene/sequence

**Permitted changes to dialogue passages:**
- Dialogue tags (`"she said"` → `"she whispered"` is PERMITTED if it preserves tone)
- Beats between dialogue lines (action descriptions CAN change)
- Paragraph breaks within dialogue sequences

**BLOCKED changes:**
- Any change to words inside quotation marks
- Any reordering of who speaks when
- Any change to what a character reveals or conceals

#### 2B — Character Action Match

Extract all character actions (verbs where a POV character is the subject
performing a physical or decisive act).

For each action in the original, verify it appears in the revised version
at the same relative position in the narrative.

**Rule:** Actions must MATCH in WHAT was done, WHO did it, and WHEN.

**Permitted changes:**
- How an action is described (`"She walked to the door"` → `"She crossed to the door, her boots scuffing stone"`)
- Sensory detail added around the action
- Internal reaction prose (as long as it doesn't add new realizations)

**BLOCKED changes:**
- Adding a new action the character didn't take
- Removing an action the character took
- Changing the sequence of actions

#### 2C — Key Event Match

Using the 1-line event summaries (extracted by revisor before revision),
verify each key event exists in the revised chapter at the same relative
position.

**Rule:** Every key event from the original must be present. No new key
events may be added.

#### 2D — Emotional Arc Preservation

For each scene, compare:
- Starting emotional register (tone/mood of opening paragraphs)
- Peak emotional moment (what it is, where it lands)
- Ending emotional register

**Rule:** The emotional trajectory must be preserved. The revision can make
the existing emotions more VIVID, but cannot change WHAT is felt or WHEN.

**BLOCKED changes:**
- Scene ends on hope when original ended on despair (or vice versa)
- Emotional peak shifts to a different moment
- A character's emotional response to an event changes in kind (not just degree)

#### 2E — Canon Lockbox Compliance

Check revised chapter against the Canon Lockbox (supplied in context packet).

**Flag if:**
- Nera's scar described on wrong body part or as active when it should be dead
- Timeline references use "days/weeks" when canon says "hours"
- Trigger word used in narrative prose (post-Ch.12)
- Extinguished anchors fired (e.g., ozone after Ch.30, hum after Ch.30)
- Any Lockbox fact contradicted

#### 2F — Cross-Chapter Compatibility

The revised chapter N must be compatible with ORIGINAL chapter N+1.

**Check:** Read original Ch.N+1's opening scene. Does anything in the revised
Ch.N make Ch.N+1's opening impossible or contradictory?

Specific checks:
- Character locations at chapter end: same place?
- Physical states: same injuries/conditions?
- Carried items: same objects in possession?
- Knowledge state: does revised Ch.N reveal something that Ch.N+1 treats as unknown?
- Emotional state: does Ch.N+1's opening emotional register follow naturally from revised Ch.N's ending?

**This is the most important compatibility check.** If revised Ch.N ends with
a character in a different emotional or physical state than the original,
Ch.N+1's opening will feel disconnected. The critic MUST verify the handoff.

---

### PHASE 3 — Prose Improvement Assessment

Only after Phases 1-2 pass. Now evaluate: is the revised prose actually BETTER?

Score each dimension 1-5 (1=worse, 3=same, 5=significantly better):

| Dimension | What to Check |
|-----------|---------------|
| **Sensory density** | VAK details per 3 sentences improved? New details organic, not forced? |
| **Sentence rhythm** | Variety improved? Run-ons fixed? Fragments used intentionally? |
| **Somatic grounding** | Emotion shown through body, not told through abstraction? |
| **Subtext integrity** | Thesis statements removed? Subtext preserved or enhanced? |
| **Register authenticity** | Prose degrades under physical stress? Character voice preserved? |
| **Pacing** | Paragraph breaks create momentum? White space at emotional peaks? |
| **Redundancy** | Repeated words/phrases cut? Distinctive metaphors not overused? |
| **Dialogue rhythm** | Tags minimal? Beats earned? No explanatory dialogue additions? |

**Overall improvement verdict:**
- **DEGRADED** (score < 18): Revision made prose worse. Recommend rollback.
- **NEUTRAL** (score 18-24): Changes are lateral. Acceptable but low impact.
- **IMPROVED** (score 25-32): Clear prose improvement. Revision successful.
- **SIGNIFICANTLY IMPROVED** (score 33+): Exceptional polish. Revision is a clear win.

---

### PHASE 4 — Revision Artifact Scan

Check for common revision artifacts — patterns that indicate the revisor
overstepped:

| Artifact | Detection | Severity |
|----------|-----------|----------|
| **Explanatory addition** | New sentence that explains what original showed | CRITICAL — cut immediately |
| **Thesis injection** | "She realized that..." / "He understood then..." added | CRITICAL — cut immediately |
| **Voice bleed** | One POV's distinctive vocabulary appears in another POV's section | MODERATE — flag for fix |
| **Padding** | Sensory details that don't serve the scene (describe for its own sake) | MINOR — note only |
| **Over-writing** | Simple effective line replaced with more "literary" but less impactful version | MODERATE — flag for fix |
| **Tone shift** | Revised passage feels like a different genre than original | CRITICAL — needs rewrite |
| **Rhythm monotony** | Revision created same-length sentences where original had variety | MINOR — note only |

---

### PHASE 5 — Compatibility With Next Chapter

The definitive integration test:

1. Read original Ch.N+1's opening 200 words
2. Read revised Ch.N's closing 200 words
3. Do they form a seamless read?

**The handoff test:** If you read revised Ch.N's ending, then immediately
read original Ch.N+1's opening, does anything feel wrong? A location
mismatch? An emotional disconnect? A knowledge gap? An object that
appeared/disappeared?

**Output:** "Compatible" or "Incompatible: [specific issue]."

---

## Output Format

```
## REVISION CRITIQUE — Chapter N: TITLE

### PHASE 1 — Structural Skeleton
| Check | Original | Revised | Match |
|-------|----------|---------|-------|
| Scenes | N | N | PASS/FAIL |
| POV sequence | [list] | [list] | PASS/FAIL |
| Epigraph | "[text]" | "[text]" | PASS/FAIL |
| BFS | "[text]" | "[text]" | PASS/FAIL |
| Title | "[title]" | "[title]" | PASS/FAIL |
| Word count | N | M (Δ: ±X) | PASS/FLAG |

**Phase 1 verdict:** PASS / BLOCKED

(If BLOCKED, STOP here. List specific mismatches.)

### PHASE 2 — Story Integrity
- **Dialogue:** N quotes checked — [all match / N mismatches found]
- **Character actions:** N actions checked — [all match / N mismatches found]
- **Key events:** N events checked — [all present / N missing / N added]
- **Emotional arc:** [preserved / altered — specify which scene]
- **Canon Lockbox:** [clean / N violations]
- **Cross-chapter compatibility (Ch.N→N+1):** [compatible / issue found]

**Phase 2 verdict:** PASS / ISSUES FOUND

### PHASE 3 — Prose Improvement
| Dimension | Score (1-5) |
|-----------|-------------|
| Sensory density | X |
| Sentence rhythm | X |
| Somatic grounding | X |
| Subtext integrity | X |
| Register authenticity | X |
| Pacing | X |
| Redundancy | X |
| Dialogue rhythm | X |
| **TOTAL** | **XX/40** |

**Improvement verdict:** DEGRADED / NEUTRAL / IMPROVED / SIGNIFICANTLY IMPROVED

### PHASE 4 — Artifact Scan
[Any detected artifacts with severity]

### PHASE 5 — Ch.N+1 Compatibility
**Handoff test:** [compatible / issue description]

### FINAL VERDICT
**Revision status:** PASS / CONDITIONAL PASS (N issues to fix) / BLOCKED

### PRIORITY ACTIONS (if any)
[Maximum 3. Specific, surgical. Reference exact line numbers.]
```

---

## Relationship to Other Skills

| Skill | Role | Relationship |
|-------|------|-------------|
| `hermes-revision` | Actor — revises prose | This skill CRITIQUES its output |
| `storytelling-critic` | Story quality evaluation | Different scope — evaluates story, not revision integrity |
| `story-reviewer` | Process/constraint audit | Different phase — runs during writing, not post-completion revision |
| `neuro-narrative-architecture` | Engagement patterns | Used by revisor (actor), NOT by this critic |

**Critic loads ONLY this skill.** It does not need neuro-narrative-architecture,
novel-weaver, or any writer skills. Its sole lens: "Did the revision preserve
the story, and is the prose better?"

---

## HARD RULES

1. **Critic and revisor are SEPARATE subagents.** Never the same agent.
2. **Critic evaluates revision, NOT the original.** The original is the
   gold standard. The revision must match it in story terms.
3. **If Phase 1 fails, STOP.** Do not proceed to later phases. Structural
   mismatch means the revision was done wrong — redo it.
4. **Phase 2 issues are BLOCKING.** Even one dialogue word changed inside
   quotes → revision fails. This is not negotiable.
5. **Compatibility with Ch.N+1 is a hard gate.** If revised Ch.N doesn't
   hand off cleanly to original Ch.N+1, the revision pipeline stalls.
6. **Prose improvement is secondary to integrity.** A revision that
   preserves the story but doesn't improve prose much is acceptable.
   A revision that improves prose but changes the story is BLOCKED.

---

## Subagent Context Requirements

When dispatching the critic as a delegate_task subagent, the context packet
MUST include:

1. **Original chapter path:** `chapters/NN-title.md`
2. **Revised chapter path:** `revisions/NN-title-revised.md`
3. **Next chapter path:** `chapters/NN+1-title.md` (for compatibility check)
4. **Canon Lockbox** (full text from architecture)
5. **Character models summary** (key physical/mental states per POV)
6. **BFS exact text** (from original chapter)
7. **Epigraph exact text** (from original chapter)

**Toolsets:** ["file", "terminal"]

**The critic reads both files, compares them, and produces the output format above.**
It does not modify files. It reports findings. The orchestrator applies fixes.

---

## Verification Checklist

Before accepting the critic's verdict:

- [ ] All 6 Phase 1 checks executed with explicit results
- [ ] Phase 2 dialogue check sampled at least 5 quotes per scene
- [ ] Phase 2 character action check verified all major actions
- [ ] Phase 2 emotional arc check assessed every scene
- [ ] Phase 2 Canon Lockbox check ran against full Lockbox
- [ ] Phase 2 cross-chapter check read original Ch.N+1
- [ ] Phase 3 scored all 8 dimensions with evidence
- [ ] Phase 4 scanned for all 7 artifact types
- [ ] Phase 5 performed the handoff test
- [ ] Output format matches specification exactly
