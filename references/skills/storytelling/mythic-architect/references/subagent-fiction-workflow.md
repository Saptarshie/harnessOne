# Subagent-Driven Fiction Workflow

> *Writer → Critic → Revision pipeline. Prevents context bloat. Enforces writer/critic separation.*

## Why Subagents for Fiction

Long-form fiction burns context. A single novel chapter can consume 15K+ tokens of prose alone, plus the architecture context needed to write it. By Chapter 03, the agent's context window is saturated with prior chapters, and quality degrades — prose gets looser, constraints get forgotten, continuity drifts.

**Solution:** Each chapter is drafted by a FRESH writer subagent with a targeted context brief. The orchestrator (you) never reads the full chapter during drafting — only the critic's evaluation. The orchestrator's context stays clean for architecture decisions, pacing oversight, and continuity management.

## The Pipeline

```
[Orchestrator]                          [Writer Subagent]              [Critic Subagent]
      │                                        │                              │
      │ ──── Dispatch with brief ────────────→ │                              │
      │                                        │ generates chapter            │
      │ ←──── Return summary ───────────────── │                              │
      │                                                                       │
      │ ──── Dispatch with chapter + protocol ──────────────────────────────→ │
      │                                                                       │ evaluates
      │ ←──── Return critique + priority actions ─────────────────────────── │
      │
      │ ──── Apply surgical cuts (patch tool) ──→ final chapter
      │
      │ ──── Update ledger, RSO log
```

## Writer Brief Construction (CRITICAL)

The writer subagent knows NOTHING about your world, characters, or prior chapters. Every piece of context it needs must be in the brief. A good brief contains:

### 1. Chapter Frontmatter
The exact markdown block the chapter should start with (title, epigraph, act designation).

### 2. Structure (POVs + Sequence)
Which POVs appear, in what order, approximate word count per section. Specify which POVs are absent (e.g., "NO Calibrator — dead").

### 3. Irreversible Action per POV
Each POV must take ONE concrete, irreversible action. State it explicitly. This is the chapter's spine — the writer should not have to invent it.

### 4. Recalibrated Prose Constraints
Copy the CURRENT version of the prose rules from the Story Bible. Do NOT rely on the writer loading skills — include the rules directly in the brief. Rules evolve; the brief is the source of truth for this chapter.

### 5. Somatic Marker Assignments
List each POV's somatic tell(s) and when they should deploy:
```
- Kaelen: finger-tapping when stressed/lying
- Theron: touching own face at individuation moments
- Saskia: blank face when genuinely moved; hand shaking when alone
- Idris: hands freezing mid-equation when morally troubled
- Nera: touching right forearm scar at decision points
```

### 6. Sensory Anchor Targets
Which anchors to fire in this chapter, in which POV's section:
```
- Ozone: fire in Kaelen (Nexus air) and Nera (on the wind)
- Scar: Nera touches it at a decision point
- Pressure change: if Storm precursor, use in Saskia or Nera
```

### 7. Zeigarnik Targets
Which existing loops to escalate, which new loops to open. Be specific:
```
ESCALATE: L2 (anomalous frequency), L3 (Chorus secret), L7 (Kaelen's deleted escalation)
NEW: L9 (falsified logs), L10 (Storm precursors), L11 (Theron's hidden crystal)
```

### 8. Neuro-Narrative Wave
The cortisol-oxytocin rhythm for this chapter's POV sequence:
```
- POV 1: CORTISOL (tension)
- POV 2: CORTISOL (peak)
- POV 3: OXYTOCIN (procedural calm, breath)
- POV 4: CORTISOL (return)
- POV 5: OXYTOCIN (grounding, closing image)
```

### 9. World Quick-Reference
A 5-10 line summary of the world, factions, and current crisis state. Just enough to ground the writer without overloading.

## Continuity Checklist (per chapter)

Before dispatching the writer, verify these against prior chapters:

- [ ] **Somatic markers:** Are all POV somatic tells consistent with prior deployment? (e.g., Nera's scar is on her RIGHT FOREARM, not her collarbone — check Ch.01 before writing Ch.02)
- [ ] **Physical descriptions:** Scars, hair color, age, build — did the prior chapter establish these? If so, include them in the brief to prevent drift.
- [ ] **Timeline:** How much time has passed since the last chapter? What time of day is it for each POV?
- [ ] **Location:** Where is each POV at chapter start? Did they move since last appearance?
- [ ] **Anchor status:** Which anchors were fired in the prior chapter? Which need to fire now? (Every 1-2 chapters for the Master Anchor.)
- [ ] **Loop status:** Which loops are escalating? Which are decaying? Check the Zeigarnik Ledger.
- [ ] **Character knowledge:** What does each POV know at this point? What do they NOT know? (Information asymmetry is the engine — don't accidentally give a character knowledge they shouldn't have.)

## Pitfall: Continuity Drift Across Subagents

**Symptom:** Nera's scar was on her right forearm in Chapter 01 but appears on her left collarbone in Chapter 02.

**Root cause:** The writer subagent for Chapter 02 didn't have Nera's physical description in its brief. It invented a scar location that contradicted Chapter 01.

**Prevention:** Every writer brief MUST include each POV's established physical traits and somatic tells. Never assume the subagent will check prior chapters — it won't. The brief is the single source of truth the subagent will reference.

**Detection:** The orchestrator (you) should spot-check continuity after receiving the final chapter. Compare the first paragraph of each POV's section against their last appearance. Physical descriptions, locations, and time-of-day should align.

## Critic Brief Construction

The critic subagent loads ONLY the evaluation protocol. Its brief should contain:

1. **The chapter file path** (so it can read the prose)
2. **The full 8-step evaluation protocol** (from storytelling-critic)
3. **The current prose constraint rules** (so it can check compliance)
4. **Somatic marker assignments** (so it can verify deployment)
5. **Sensory anchor targets** (so it can verify firing)
6. **Output format specification** (so results are structured and actionable)

The critic should NEVER receive the Story Bible, character models, or outline — only what it needs to evaluate the prose as a cold reader.

## Surgical Revision Protocol

After receiving the critic's priority actions:

1. **Maximum 3 actions.** The critic ranks them by impact.
2. **Prefer subtraction.** Most fixes are cuts, not additions. Removing scar tissue, not adding new organs.
3. **Execute via patch tool.** One action per patch. Verify each before moving to the next.
4. **Never "improve while you're there."** If the critic said "cut line 113," cut line 113. Don't also "enhance the atmosphere."
5. **Read the full chapter after all cuts** to verify nothing broke.
6. **If a cut exposes a gap** (e.g., removing exposition leaves a motivation unclear), note it for the NEXT chapter's writer brief — don't fix it in this one.

## When NOT to Use Subagents

- **First chapter of a novel:** The orchestrator should write Chapter 01 directly (or via a single subagent) to establish the prose voice. Subsequent chapters can be subagent-driven because the voice is now established in the brief.
- **Short pieces (<1,500 words):** The overhead of constructing a brief exceeds the chapter's context cost. Just write it directly.
- **Continuity-critical transitions:** If a chapter contains a major reveal that recontextualizes prior events, the orchestrator should write it directly — subagents lack the full narrative memory to handle complex continuity.
