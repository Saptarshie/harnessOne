---
name: hermes-revision-primer
description: >-
  Primes the LLM with the complete revision architecture — actor-critic loop,
  pipeline execution, constraints, directory structure, and integration. Load
  BEFORE hermes-revision to ground the subagent in the full system context.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [storytelling, revision, primer, novel, post-completion]
    related_skills:
      - hermes-revision
      - hermes-revision-critic
      - neuro-narrative-architecture
      - novel-weaver
      - novel-writing-pipeline
---

# HERMES REVISION SKILL — Post-Completion Prose Polish System

> *Actor-Critic architecture for chapter-by-chapter prose polish of a completed novel. Does NOT alter story-line, plot, character actions, or dialogue meaning. Fully subagent-driven.*

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                 REVISION PIPELINE                        │
│                                                         │
│  For each chapter N (1 → 31):                           │
│                                                         │
│  ┌──────────────┐     ┌──────────────────────┐          │
│  │ REVISOR      │────▶│ REVISION CRITIC      │          │
│  │ (Actor)      │     │ (Separate Agent)      │          │
│  │              │     │                      │          │
│  │ Skills:      │     │ Skills:              │          │
│  │ • hermes-    │     │ • hermes-revision-   │          │
│  │   revision   │     │   critic ONLY        │          │
│  │ • neuro-     │     │                      │          │
│  │   narrative- │     │ Checks:              │          │
│  │   arch.      │     │ 1. Structural match  │          │
│  │ • novel-     │     │ 2. Story integrity   │          │
│  │   weaver     │     │ 3. Prose improvement │          │
│  │ • hermes-    │     │ 4. Artifact scan     │          │
│  │   revision-  │     │ 5. Ch.N+1 compat.    │          │
│  │   primer     │     │                      │          │
│  │              │     │ Produces:            │          │
│  │ Produces:    │     │ Critique report      │          │
│  │ revisions/   │     │                      │          │
│  │ NN-title-    │     └──────────────────────┘          │
│  │ revised.md   │              │                         │
│  └──────────────┘              │                         │
│         │                      │                         │
│         └────────┬─────────────┘                         │
│                  ▼                                       │
│         ┌────────────────┐                               │
│         │ ORCHESTRATOR   │                               │
│         │ (Hermes Agent) │                               │
│         │                │                               │
│         │ • Dispatches   │                               │
│         │   both agents  │                               │
│         │ • Applies fixes│                               │
│         │ • Updates log  │                               │
│         └────────────────┘                               │
└─────────────────────────────────────────────────────────┘
```

---

## Skills Required

| Skill | Type | Location |
|-------|------|----------|
| `hermes-revision` | Actor — prose polisher | `~/.hermes/skills/storytelling/hermes-revision/SKILL.md` |
| `hermes-revision-critic` | Critic — drift validator | `~/.hermes/skills/storytelling/hermes-revision-critic/SKILL.md` |
| `hermes-revision-primer` | Primer — full system context (THIS SKILL) | `~/.hermes/skills/storytelling/hermes-revision-primer/SKILL.md` |
| `neuro-narrative-architecture` | Engagement patterns (loaded by actor) | `~/.hermes/skills/storytelling/neuro-narrative-architecture/SKILL.md` |
| `novel-weaver` | Novel-scale constraints (loaded by actor) | `~/.hermes/skills/storytelling/novel-weaver/SKILL.md` |

---

## When to Run

- **AFTER** the novel is fully written (all chapters drafted)
- **AFTER** all architecture files are finalized
- **BEFORE** the final PDF build (if you want revised prose in the book)
- The revision is OPTIONAL — the original chapters remain untouched

---

## What the Revision Does

### Permitted (Prose-Only Polish)
- Sharpen word choice, vary sentence rhythm, fix run-ons
- Add/refine sensory details (visual, auditory, kinesthetic)
- Displace emotion onto physical objects (somatic markers)
- Ensure prose degrades under physical stress
- Cut redundant language, repeated words, thesis statements
- Improve paragraph structure and white-space rhythm
- Tighten dialogue tags, cut explanatory beats
- Apply cortisol-oxytocin wave pacing
- Ensure subtext remains subtext

### FORBIDDEN (Story Alteration)
- Change plot events, character actions, or dialogue content
- Add/remove scenes, characters, or story beats
- Alter BFS text, epigraph text, or chapter structure
- Change emotional arcs, themes, or character motivations
- Contradict Canon Lockbox facts
- Change POV sequence or scene count
- Alter timeline references

---

## Directory Structure

```
the-chrysalis-protocol/
├── chapters/           ← ORIGINAL chapters (NEVER modified)
│   ├── 01-the-anomaly.md
│   ├── 02-the-silence-after.md
│   └── ...
├── revisions/          ← REVISED chapters (created by pipeline)
│   ├── revision-log.md
│   ├── 01-the-anomaly-revised.md
│   ├── 02-the-silence-after-revised.md
│   └── ...
├── architecture/       ← Reference (read-only for revision)
│   ├── 00-story-bible.md
│   ├── 01-character-models.md
│   ├── 02-zeigarnik-ledger.md
│   └── 03-rso-log.md
```

---

## Pipeline Execution (Orchestrator's Script)

For each chapter N (sequential, 1→31):

### 1. Dispatch Revisor Subagent

```
delegate_task(
    goal="Revise Chapter N prose for engagement, sensory density, rhythm. DO NOT change story elements.",
    context="""
    ORIGINAL CHAPTER: /workspace/the-chrysalis-protocol/chapters/NN-title.md
    OUTPUT PATH: /workspace/the-chrysalis-protocol/revisions/NN-title-revised.md
    REVISION LOG: /workspace/the-chrysalis-protocol/revisions/revision-log.md
    
    CANON LOCKBOX:
    [Copy full Lockbox from README.md or novel-writing-pipeline skill]
    
    CHARACTER MODELS SUMMARY:
    [Copy relevant character states from architecture/01-character-models.md]
    
    BFS (EXACT TEXT — DO NOT CHANGE):
    "[Chapter N's BFS from README catalog]"
    
    EPIGRAPH (EXACT TEXT — DO NOT CHANGE):
    "[Chapter N's epigraph]"
    
    DEFINITIONS:
    - BFS = Blunt Force Summary: ONE devastating simple sentence per chapter
    - VAK = Visual, Auditory, Kinesthetic sensory details
    - Canon Lockbox = Immutable facts that must never be contradicted
    
    RULES:
    - Read the original chapter fully before starting
    - Extract structural skeleton (scenes, POVs, events, dialogue)
    - Polish prose ONLY — no story changes
    - Save to the output path
    - Update the revision log
    """,
    toolsets=["file", "terminal"]
)
```

### 2. Dispatch Critic Subagent (SEPARATE agent)

```
delegate_task(
    goal="Validate Chapter N revision: check story integrity, prose improvement, Ch.N+1 compatibility.",
    context="""
    ORIGINAL: /workspace/the-chrysalis-protocol/chapters/NN-title.md
    REVISED: /workspace/the-chrysalis-protocol/revisions/NN-title-revised.md
    NEXT CHAPTER: /workspace/the-chrysalis-protocol/chapters/NN+1-title.md
    
    CANON LOCKBOX:
    [Copy full Lockbox]
    
    CHARACTER MODELS:
    [Copy relevant character states]
    
    BFS EXACT TEXT: "[Chapter N's BFS]"
    
    Follow the hermes-revision-critic protocol:
    1. Structural skeleton match (scene count, POVs, BFS, epigraph)
    2. Story integrity deep scan (dialogue, actions, events, emotional arc, Lockbox)
    3. Prose improvement assessment (8 dimensions, 1-5 each)
    4. Revision artifact scan (7 patterns)
    5. Ch.N+1 compatibility handoff test
    
    Output the full critique format.
    If Phase 1 or 2 fails → BLOCKED. Report specific mismatches.
    """,
    toolsets=["file", "terminal"]
)
```

### 3. Evaluate Critic Verdict

- **PASS** → Mark chapter complete in revision-log. Proceed to Ch.N+1.
- **CONDITIONAL PASS** (minor issues) → Apply fixes, re-submit to critic.
- **BLOCKED** → Revision failed. Review specific mismatches. May need re-revision.

### 4. After All Chapters

- Run a final integration check: read revised Ch.N ending + original Ch.N+1 opening for all chapters.
- Optionally rebuild PDF from /revisions/.
- Update README to note revision status.

---

## Revision Log Format

Save at `/revisions/revision-log.md`. Initialize before first run:

```markdown
# Revision Log

> Post-completion prose polish. Actor: hermes-revision. Critic: hermes-revision-critic.
> Started: [date]
> Novel: The Chrysalis Protocol — 31 chapters, ~97,000 words

## Progress

| Ch | Title | Original | Revised | Critic | Notes |
|----|-------|----------|---------|--------|-------|
| 01 | The Anomaly | ✅ | ⬜ | ⬜ | |
| 02 | The Silence After | ✅ | ⬜ | ⬜ | |
| ... | | | | | |
| 31 | The Archive Coda | ✅ | ⬜ | ⬜ | |

## Chapter Details

### Chapter N — Title
- **Revised:** [timestamp]
- **Word count:** X → Y (Δ: ±Z)
- **Critic verdict:** PASS / CONDITIONAL / BLOCKED
- **Critic issues:** [if any]
- **Compatibility (→Ch.N+1):** Clean / [specific note]
```

---

## Important Constraints

1. **Original chapters are NEVER modified.** The revisor writes to `/revisions/` only.
2. **Revised-chapter-N must be compatible with original-chapter-N+1.** This is the hardest constraint. The critic verifies it.
3. **Each chapter revision is independent.** The revisor can only read the current chapter + architecture files. It does not see other revised chapters.
4. **Net word count change per chapter should be modest** (±100-400 words typical).
5. **The BFS and epigraph are SACRED.** They must match the original verbatim.

---

## Integration with Novel-Writing Pipeline

The revision pipeline is Phase 5 of the overall workflow:

```
Phase 1: Story Bible + Character Models
Phase 2: Chapter Writing (Ch.1 → Ch.N) via writer→critic→reviewer pipeline
Phase 3: Architecture Finalization
Phase 4: PDF Build (from /chapters/)
Phase 5: REVISION PIPELINE (this system) — prose polish pass
Phase 6: Final PDF Build (from /revisions/ or /chapters/, user choice)
```

The `novel-writing-pipeline` skill should reference this system as the post-completion phase.

---

## Quick Start

```bash
# 1. Create revisions directory
mkdir -p /workspace/the-chrysalis-protocol/revisions

# 2. Initialize revision log
# (Use the template above)

# 3. Load skills
skill_view(name='hermes-revision')
skill_view(name='hermes-revision-primer')
skill_view(name='hermes-revision-critic')

# 4. Start with Chapter 1
# Dispatch revisor subagent → critic subagent → evaluate → repeat
```
