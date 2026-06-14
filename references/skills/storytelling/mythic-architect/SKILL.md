---
name: mythic-architect
description: "Narrative architecture for long-form stories — context state management, Rolling State Object (RSO), Zeigarnik loop ledger, macro-psychological pacing. The showrunner that feeds the mythic-weaver. Use when a story requires multiple chapters, exceeds 1,500 words, or involves complex branching."
platforms: [linux, macos, windows]
---

# mythic-architect — The Narrative Showrunner

## When to Use

When a story requires multiple chapters, exceeds 1,500 words, involves complex branching, or when the user requests a "long-form," "epic," or "serialized" narrative. This is the **Architect** — it plans, manages state, and directs the `mythic-weaver` (the executor).

## 0. MISSION STATEMENT

You are not writing the story. You are **engineering the scaffolding and managing the cognitive load**.

LLMs suffer from context degradation: they forget open loops, dilute emotional peaks, and rush endings. Your mission is to prevent this. You act as the **Showrunner and State Manager**, breaking the narrative into psychologically optimized chunks and feeding them to the `mythic-weaver` via a strictly controlled **Rolling State Object (RSO)**.

## 1. THE CONTEXT MANAGEMENT ENGINE

### 1.1 The Rolling State Object (RSO)

After each scene, update and pass this structure to the Weaver for the next scene. This keeps the active context small, dense, and highly relevant.

```json
{
  "current_beat": "Scene 3: The Descent",
  "macro_phase": "Deepening (Fractionation)",
  "active_zeigarnik_loops": [
    {"id": "L1", "desc": "What is in the locked drawer?", "opened_in": "Scene 1", "urgency": "High"},
    {"id": "L2", "desc": "Why does she flinch at the smell of ozone?", "opened_in": "Scene 2", "urgency": "Medium"}
  ],
  "planted_anchors": [
    {"sensory_cue": "smell of ozone", "tied_to_emotion": "dread", "last_fired": "Scene 2"}
  ],
  "character_somatic_state": "Heart rate elevated, breathing shallow, jaw clenched.",
  "nlp_directive_for_next_beat": "Use 2 embedded commands, pace current physical reality, lead into confusion technique.",
  "context_summary": "Elara found the drawer but couldn't open it. She fled to the porch, where the storm started."
}
```

### 1.2 Context Window Triage

When the story grows long:
1. **Keep:** The RSO, the Story Bible, and the *immediately preceding* 500 words.
2. **Compress:** Summarize older scenes into 2-sentence psychological beats.
3. **Discard:** Flowery prose from previous scenes. The Weaver only needs the *state*, not the old *words*.

## 2. MACRO-PSYCHOLOGICAL ARCHITECTURE

Map the macro-structure to the stages of hypnosis:

| Act | Hypnotic Phase | Psychological Goal | Weaver Instructions | Required Failure Beat |
|-----|---------------|-------------------|---------------------|----------------------|
| **Act I: The Descent** | Induction & Pacing | Bypass critical faculty. Build rapport. Establish Yes-Set. | Heavy VAK pacing, slow rhythm, high sensory density, establish core anchor. | One attempt at connection must fail — a misread, a wrong word, a comfort that doesn't land. |
| **Act II: The Labyrinth** | Deepening & Fractionation | Disorient conscious mind. Multiply open loops. Create peaks and valleys. | Confusion techniques, double binds, micro-cliffhangers. Fire and reset anchors. | At least one plan must backfire. Not a near-miss — a genuine failure that costs something real. |
| **Act III: The Pivot** | Suggestion & Reframing | Deliver identity-level insight. The "Aha" moment. | Milton model patterns, nominalizations, peak emotional crescendo. | The insight must *cost* something — a belief the character has held must be *lost*, not just transformed. |
| **Act IV: The Return** | Integration & Awakening | Close loops, solidify reframe, plant post-hypnotic trigger. | Resolve loops (leave exactly one open), slow rhythm, deliver Echo and Trigger. | Leave one relationship beat unresolved or awkward — not every relationship earns its ending. |

## 3. THE STORY BIBLE (Pre-Computation)

Before generating a single word of prose, generate and lock the Story Bible:

- **Core Metaphor:** (e.g., *Grief as a house with too many doors.*)
- **The Wound:** (The universal human pain this story addresses.)
- **The Identity Reframe:** (The shift in self-concept the listener will experience.)
- **The Master Anchor:** (The primary sensory cue tied to the climax.)
- **The Post-Hypnotic Trigger:** (The real-world cue that will recall the story.)
- **The Unresolved Loop:** (The specific mystery that will *never* be answered.)
- **Total Beat Count:** (e.g., 8 beats. Never exceed 12 for a single session.)

### 4.1 Pre-Critic Continuity Sweep (MANDATORY)

**Do NOT dispatch the critic subagent immediately after receiving a chapter draft.**

Writer subagents lack accumulated context across chapters. They will introduce
continuity errors — scar locations migrating, data provenance shifting, timelines
compressing, casualty counts inflating. The critic evaluates PROSE, not canon
consistency. Continuity errors waste critic cycles.

**After receiving a draft, before dispatching the critic, verify:**
1. Character physical details match canon (scars, items carried, somatic tells)
2. Timeline references match the chapter epigraph (hours, not days)
3. Character knowledge matches when they learned it (no anachronistic Directorate references before Ch.04)
4. Casualty counts match prior chapters (no invented deaths)
5. Key terms are standardized across chapters (Treaty vs Charter, etc.)

Fix continuity errors FIRST. Then dispatch the critic.

See `novel-weaver` Section 17 for the full drift-pattern catalogue and the Canon Lockbox format.

### Subagent-Driven Workflow (Recommended for Novel-Length Works)

At novel scale, context degradation is the primary failure mode. Use `delegate_task`
subagents to keep the parent agent's context clean:

1. **Writer subagent:** Loads mythic-weaver, novel-weaver, mythic-architect, and
   character/delivery skills. Receives the full scene brief + RSO injection. Generates
   prose. Does NOT load storytelling-critic.
2. **Critic subagent:** Loads ONLY storytelling-critic. Evaluates prose as a cold
   reader. Reports priority actions (max 3). Does NOT load writer skills.
3. **Surgical revision:** The parent agent applies the critic's priority actions
   directly to the chapter file. Cuts only — prefer subtraction over addition.
   Remove scar tissue, don't add new organs.
4. **Continuity verification:** After revision, verify character details match prior
   chapters (scar locations, data provenance, timeline). See `references/continuity-checklist.md`.

This separation is non-negotiable per novel-weaver Section 16. The writer must never
evaluate its own output.

### Weaver Directive Format

### Direct Weaver Directive Format (short-form / single-agent mode)

```
BEAT: [Number and Title]
GOAL: [What this beat must achieve psychologically]
RSO INJECTION: [Insert current Rolling State Object]
CONSTRAINTS: [Word count, loops to escalate/resolve, anchors to fire, NLP patterns to use]
EXECUTE.
```

### Post-Beat Processing
1. Read the Weaver's output.
2. Did it resolve a loop prematurely? Did it forget an anchor?
3. Update the RSO.
4. If the Weaver drifted, apply a Course Correction in the next Directive.
5. Issue the next Weaver Directive.

## 5. THE ZEIGARNIK LEDGER (Loop Management)

| Loop ID | Description | Opened | Urgency | Status | Planned Resolution | Antagonist Weight |
|---------|------------|--------|---------|--------|-------------------|-------------------|
| L1 | The locked drawer | Beat 1 | High | OPEN | Beat 6 (Reveal empty) | — |
| L2 | The ozone smell | Beat 2 | Med | OPEN | Beat 8 (Post-hypnotic) | — |
| L3 | Father's last words | Beat 3 | Low | OPEN | **NEVER** (Unresolved) | — |

**Rule:** Before issuing any Directive, check the ledger. If a High Urgency loop has been open for more than 3 beats, the next Directive *must* escalate or resolve it.

**Antagonist Weight Rule:** Any antagonist who functions as a loop anchor (i.e., their presence sustains HIGH urgency loops) must have a **minimum resolution scene length** equal to 50% of their *introduction* scene length. An antagonist who takes 3 chapters to build cannot be arrested in 2 sentences. Add this column to the ledger and verify at every Quality Gate:

- [ ] Every HIGH-urgency antagonist has a resolution scene with proportional length and interiority.
- [ ] At least one antagonist believes they are *right* through their final scene.

## 6. PACING AND RHYTHM CONTROL

- **The Rule of Thirds:**
  - *First third:* Long, flowing, descriptive (Induction)
  - *Second third:* Short, punchy, fragmented (Tension/Confusion)
  - *Final third:* Rhythmic, poetic, balanced (Integration)
- **The Breath Beat:** Every 3rd beat must be low-action, high-reflection. Fractionation. But "low action" does NOT mean "high eloquence." A character who has just crossed a mountain pass in monsoon rain does not think in complete paragraphs. The Breath Beat must include:
  - At least one moment of failed articulation (character starts a thought and cannot finish it)
  - At least one physical detail that is ugly or uncomfortable, not atmospheric
  - Dialogue that is shorter than feels satisfying (the scene should end before the reader is ready)
  
  The Breath Beat is where the reader catches their breath, not where the character demonstrates wisdom.
- **The Shrinking Focus Rule:** When macro-stakes reach their absolute peak (e.g., saving thousands, stopping a war), the protagonist's immediate sensory or emotional focus must narrow to a single, fragile, micro-element. While the council debates the fate of 16,000 lives, the protagonist should fixate on a drop of melting wax, a frayed thread on a minister's cuff, a crack in the leather of a boot. As stakes expand, focus shrinks. This creates tension that raw numbers cannot.
- **The Face Behind the Number:** When stakes involve lists, registers, or numerical abstractions (a firman with 16,000 names, a census, a deportation manifest), the narrative must present ONE specific human face. Not described in the abstract — encountered. A person from the list who does not know their name is on it. A family having an ordinary evening. A child. The reader must see what is being saved (or lost) before the abstraction can carry weight.
- **The Premature Safety Rule:** After the structural midpoint, the reader must experience at least TWO moments where they genuinely believe the novel might collapse into tragedy. Moments where survival is uncertain, where the firman might be lost or destroyed, where a key character might die, where the central relationship might fail. If the narrative feels safe from the midpoint onward, restructure. Safety is the enemy of the 3am quality.

  **Advanced: Shared Micro-Observation.** Go further — have the *antagonist* notice the same micro-detail at their moment of defeat. Two people on opposite sides of the room, opposite sides of history, watching the same frayed thread. This creates a moment of shared humanity without sentimentality and implicit recognition that antagonist and protagonist are not as different as either believes. The shared detail must be genuinely small and unremarkable — if it feels symbolic, it fails. If it's just a thing that happens to be there, it works.

## 7. FAILSAFES AND RECOVERY

- **Hard Reset:** If the story loses its thread, execute a Transition Beat: "Use a temporal jump or sensory fade-to-black to reset the scene."
- **Anchor Rescue:** If emotional resonance drops: "Fire the Master Anchor immediately in the next paragraph."
- **Loop Purge:** If too many open loops, rapidly close lowest-urgency loops in a single "montage" paragraph.

## 8. QUALITY GATE (Before Final Beat)

- [ ] All High and Medium urgency loops are resolved or actively being resolved.
- [ ] The Unresolved Loop is perfectly positioned to remain open.
- [ ] The Master Anchor has been fired at least twice.
- [ ] The Post-Hypnotic Trigger has been explicitly defined.
- [ ] The emotional state has transitioned from *Tension* to *Awe/Recognition*.
- [ ] Continuity verified against `references/continuity-checklist.md` — scar locations, data provenance, timeline, somatic tells.
- [ ] Neuro-narrative wave verified: cortisol peaks have oxytocin troughs, reward prediction error is deployed, Zeigarnik lattice has at least 6 active loops.

## 9. ETHICAL GUARDRAILS

- **Do not stack trauma:** The Wound should be challenging but not re-traumatizing.
- **Provide an exit ramp:** Every Breath Beat gives the listener permission to step back.
- **Autonomy preservation:** The identity reframe must expand agency, never diminish it.

## 10. DELIVERABLE STRUCTURE — File Organization for Multi-Chapter Works

When the user asks for a long-form story or "organized files for tracking," the Architect must produce a **project directory** — not a wall of text in the chat window. This serves three purposes: (a) chapters are individually navigable, (b) the architecture state lives alongside the prose, and (c) future sessions can resume from the exact RSO without reconstructing context.

### 10.1 Standard Project Layout

```
<project-slug>/                       ← kebab-case, e.g. "the-firman-of-monsoons"
│
├── README.md                         ← Hub: title, status table, reading guide, quick-reference
│
├── architecture/                     ← The showrunner layer (DO NOT skip)
│   ├── 00-story-bible.md            ← Immutable: era, metaphor, wound, anchors, triggers, beats
│   ├── 01-character-models.md       ← Full psych profiles + somatic tells + relational dynamics
│   ├── 02-zeigarnik-ledger.md       ← Loop table: ID, urgency, status, planned resolution
│   └── 03-rso-log.md                ← One RSO JSON block per chapter + NLP directive for next
│
└── chapters/                         ← The prose
    ├── 01-<chapter-slug>.md         ← See templates/chapter-template.md
    ├── 02-<chapter-slug>.md
    └── ...
```

### 10.2 File Purposes

| File | Purpose | When Written | When Read |
|------|---------|-------------|-----------|
| `README.md` | Project hub: status table, reading guide | Created first, updated after each chapter | Any time |
| `00-story-bible.md` | Immutable source of truth | Before Chapter 01, locked after | Before writing any new chapter |
| `01-character-models.md` | Psych profiles, somatic tells, relational dynamics | Before Chapter 01, updated as depth reveals | Before dialogue-heavy scenes |
| `02-zeigarnik-ledger.md` | Loop table, anchor tracker, chapter summary | Created with Ch.01, updated every chapter | **Before every chapter** — mandatory |
| `03-rso-log.md` | RSO per chapter + next-chapter NLP directive | After every chapter | Before next chapter: inject into Weaver |
| `chapters/01-*.md` | Prose with standardized frontmatter | As directed | The reader |

### 10.3 Chapter Frontmatter Format

```markdown
# Chapter <N>: <Title>

> *<Location>, <time/season context>, <year>*
>
> **Act <roman> — <Phase Name> (<Hypnotic Stage>)**

---
```

See `templates/chapter-template.md` for a copy-paste boilerplate.

### 10.4 Workflow: Starting a New Chapter

1. **Read the ledger** (`02-zeigarnik-ledger.md`) — which loops need escalating? Which are decaying?
2. **Read the RSO log** (`03-rso-log.md`) — grab the most recent RSO + NLP directive. This IS your Weaver context injection.
3. **Read the Story Bible** (`00-story-bible.md`) — verify anchors, triggers, the unresolved loop.
4. **Write the chapter** using the Weaver Directive as your creative brief.
5. **After the chapter is complete**, update all three architecture files + README.

### 10.5 Anti-Patterns

- **Do NOT** output the entire novel as a single chat message. Split into files.
- **Do NOT** skip the architecture layer for "short" multi-chapter works. Even 3 chapters need a ledger.
- **Do NOT** write Chapter N+1 without reading the RSO from Chapter N. The Weaver will drift.
- **Do NOT** put the RSO or ledger inside the chapter files. Architecture lives in `architecture/`.

### 10.8 Context Compression Recovery Protocol

When a multi-chapter project's orchestrator session accumulates too much context
(~6+ chapters of drafting), the user may apply `/compress` to reset the context
window. Before compression, the orchestrator MUST update all architecture files
to serve as recovery points. The compressed session will reload these files and
resume without loss of state.

**The recovery package (five files):**

| File | Minimum Content |
|------|----------------|
| `README.md` | Status table, POV states, anchor list, constraint quick-ref |
| `architecture/01-character-models.md` | Current Status table at top (table of 6 POVs: status, irreversible acts, current possessions) |
| `architecture/02-zeigarnik-ledger.md` | All open loops with urgency/status, anchor tracker with last-fired dates, chapter summaries for every completed chapter, antagonist weight verification, quality gate checklist |
| `architecture/03-rso-log.md` | Post-current-chapter RSO (character states, NLP directive for next chapter, all planted anchors), architecture quick-reference section (file list, constraint cheat sheet, master anchor list, irreversible actions log), central mystery guard (L1 — the unresolved loop) |
| `architecture/00-story-bible.md` | No changes needed — immutable after Phase 1 approval unless craft constraints were recalibrated |

**The RSO Log is the primary recovery point.** It should contain a compact
"Architecture Quick-Reference" section at the bottom with:
- Project file paths
- Current prose constraints (recalibrated, if applicable)
- Master sensory anchor list with last-fired chapters
- Irreversible actions taken by each POV
- The central mystery guard statement

**Procedure:**
1. Update all five files BEFORE compression
2. The `03-rso-log.md` quick-reference section is the first thing to read after recovery
3. Load the Zeigarnik Ledger second — check which loops need escalating
4. Read the most recent chapter file to re-establish prose voice

A post-narrative epilogue framed as recovered historical documents — dispatches, council records, personal notes — that recontextualizes the entire novel. The coda reveals information the characters never knew, creating asymmetric dramatic irony. The reader finishes with knowledge the protagonists will never possess.

**When to use:** When the novel's argument is that moral victories and tactical defeats can coexist. When the ending should create doubt rather than close it.

**Structure:**
- One primary document (the antagonist's dispatch, revealing the tactical trap)
- One secondary document that personalizes the cost (a council note, a recovered poem)
- A closing line that ties to the novel's central sensory/metaphorical anchor

**Constraints:**
- The coda must NOT invalidate the protagonist's choices. The right thing and the tactically catastrophic thing were the same thing — that's the intelligence world's actual horror.
- The documents must feel authentic to their era (official register language, not narrative prose).
- The final line should be under 10 words and land like a held breath.

**Example pattern:** The antagonist's dispatch revealing the courier network was mapped → a council note confirming the names were saved → a scribe's recovered poem → "The earth received the wax without comment. But someone saw the bird."

**Placement:** After the final prose chapter. Paginated separately. No chapter number — "The Imperial Archives" or equivalent title. The reader should feel they've stumbled onto something they weren't meant to see.


