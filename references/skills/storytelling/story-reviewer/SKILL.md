---
name: story-reviewer
description: >
  Final gate after critic + revisions. Audits constraint compliance, continuity,
  anchor firing, and process hygiene. Generates next-chapter prompt from
  architecture state. DOES NOT replace the critic — runs AFTER. Pattern-matched
  from the user's own reviewing behavior across a 12-chapter Act I.
---

# Story Reviewer — Final Gate After Critic

## When This Runs

AFTER the critic has evaluated the chapter AND surgical revisions have been applied. The reviewer is the LAST gate before presenting to the user. It performs the role the user has been performing manually across 12 chapters: catching what the critic missed, verifying process compliance, and generating the next chapter's plan.

This does NOT replace the storytelling-critic. The critic evaluates prose quality, subtext, pacing, wound, stakes, memorability. The reviewer evaluates: process hygiene, constraint enforcement, continuity, and forward planning.

## INVOCATION (as subagent via delegate_task)

The reviewer loads storytelling-critic as REFERENCE (to cross-check the critic's own output), not as its primary lens. Its primary lens is the checklist below. Invoke after critic + surgical revisions complete.

---

## PHASE 1: CONSTRAINT AUDIT

### Anti-Thetical Contrast Scan
Scan chapter for ALL constructions matching: `not [X]. [Y].`, `was not [X]. It was [Y].`, `wasn't [X]. [Y].`, `[X], not [Y]` where [Y] is emotional/sensory.

Classification:
- Emotional negation: "The cold was not just temperature, it was grief." → BANNED
- Sensory shortcut: "Not the dark of night. The dark of depth." → BANNED
- Functional/technical: "The signal was not a ghost. This was a physical tap." → PERMITTED
- Alien possession: "a heart that was not her own" → PERMITTED
- Deliberate thematic (max 1/ch): "Not the artifact's. Not the necrosis's. Hers." → PERMITTED if quota not exceeded

Output: Count of each type. If ANY banned patterns found, flag as CRITICAL with exact line numbers and suggested fixes.

### Thesis Sentence Guillotine Scan
Scan for: "She realized that...", "He understood then that...", "It was the silence of...", numbered realizations, end-of-section summaries that name what was shown, somatic explanations, self-rationalizations, character-as-author thematic statements.

BFS check: Exactly ONE? Placed after rising tension? Devastating and simple? Earns its weight?

### Other Constraints
- Therapy-speak? (modern psych language)
- Character-as-author dialogue?
- Register degrades under physical stress?
- Bold on thematic lines? (must be zero in prose body)

---

## PHASE 2: CONTINUITY VERIFICATION (rolling window: last ~10 chapters)

### Scar location (Nera only)
Right forearm, 6cm. DEAD since Ch.08. If referenced, must be cold/numb. Post-Ch.08: Nera's anchor is nail-into-palm pain, NOT scar.

### Timeline
Calibrator died ~X hours ago (X = chapter number). Internal references must match. "Days," "weeks" are ALWAYS WRONG for Act I. "Weeks ago" only valid for pre-novel events (Nera+Saskia contract).

### Data provenance
What does each POV know, and when did they learn it? Carried items accounted for?

### Casualty count
Confirmed: Calibrator (Ch.01), civilian caravan (Ch.06), 1 child (Ch.08). Thousands dying off-page from Severance (permissible). Any NEW named/specific deaths must be intentional.

### Anchor firing
Compare anchors fired against Zeigarnik ledger anchor tracker. Post-Hypnotic Trigger: SILENCED in Ch.12. Should NOT fire as hum in Act II.

---

## PHASE 3: ANCHOR INTEGRITY

| Anchor | Expected Status | Verify |
|--------|----------------|--------|
| Ozone | Fire in most chapters | Evolved: clean lightning → parasitic consumption |
| Pressure Drop | Every 2-3 chapters | Storm/combat/choral scenes |
| Scar | DEAD (Ch.08+) | Cold/numb if referenced. Nera's anchor = pain now |
| Post-Hypnotic Engine Hum | SILENCED (Ch.12+) | Must NOT fire as hum. Only as silence/absence |
| Silver-Vein Necrosis | Nera scenes | Spread: wrist→shoulder→collarbone→carotid |
| Dead Relay Hum | Baseline ambience | Silence/pressure in most scenes |
| Artifact Frequency | Nera scenes | Grammar. Dormant but waiting. Learned to answer |

---

## PHASE 4: PROCESS HYGIENE AUDIT

| File | Check |
|------|-------|
| `architecture/03-rso-log.md` | Post-chapter state? NLP directive for NEXT chapter? Does `chapters_written` match actual chapter count? |
| `architecture/02-zeigarnik-ledger.md` | Chapter summary? Loop statuses? Anchor tracker? |
| `README.md` | Progress %? POV states? New anchors? Chapter count correct? |
| `architecture/01-character-models.md` | Current Status table reflects chapter? |

**Architecture Integrity Check (phase mismatch detection):** Compare `chapters_written` in RSO log against actual chapter count on disk. If mismatch → chapters were drafted outside the pipeline. Flag as CRITICAL. Provide the full update text for ALL four architecture files to close the gap.

If any file was NOT updated, flag it and provide the update text.

---

## PHASE 5: NEXT CHAPTER PROMPT GENERATION

Generate prompt for Ch.N+1 from architecture state (RSO, Zeigarnik, character trajectories).

Prompt structure:
- Chapter N+1 title (abstract nouns, systemic metaphors — follow Act I pattern)
- Macro phase description
- Scene-by-scene: Setting, Action, Fatal Flaw/Escalation, Craft Constraint, Somatic Tell, Sensory Anchor, Ending beat
- Craft constraints checklist (anti-thetical quota, BFS designation, anchor firing, pacing, neuro-narrative)
- Epigraph

POV selection: Rotate. No POV unseen for >2-3 chapters. 3 POVs per chapter.

Breath Beat detection: Every 3rd chapter. Ch.15,18,21,24,27,30 in Act II. Include Failed Articulation, ugly physical detail, short dialogue, slow pacing.

Act structure: Early = consolidation. Mid = escalation. Late = crisis. Finale = new board.

---

## PHASE 6: FINAL VERDICT

```
REVIEW COMPLETE — Chapter N

CONSTRAINT AUDIT: [CLEAN / N ISSUES]
CONTINUITY: [CLEAN / N FLAGS]
ANCHORS: [ALL FIRED / N MISSING]
PROCESS HYGIENE: [COMPLETE / N FILES MISSING]

ISSUES REQUIRING FIX (if any):
1. [Line X] — [Issue] — [Suggested fix]

NEXT CHAPTER PROMPT: [Generated above]
```

If issues: present with specific fixes. Orchestrator applies them. Reviewer does NOT modify files.
If clean: "No issues. Chapter N passes review. Next chapter prompt ready."

---

## RELATIONSHIP TO OTHER SKILLS

| Skill | Role | When |
|-------|------|------|
| storytelling-critic | Prose quality, subtext, pacing, memorability | Before reviewer |
| story-reviewer (this skill) | Constraint audit, continuity, process, forward planning | After critic + fixes |
| neuro-narrative-architecture | Engagement architecture | During planning + writer dispatch |
| novel-weaver + mythic-weaver | Novel-scale patterns | During writer dispatch |

The reviewer does NOT evaluate prose quality. That's the critic's job. The reviewer checks whether the chapter followed the rules, maintained continuity, updated the logs, and is ready for the next chapter to be planned.

---

## USER PATTERNS LEARNED

| User Behavior | Encoded As |
|---------------|------------|
| Catches "Not X, but Y" sensory negations | Phase 1: Anti-Thetical Contrast Scan with classification |
| Suggests specific word-level fixes | Phase 6: Issues with fix suggestions |
| Verifies scar location and timeline | Phase 2: Continuity Verification |
| Checks log files were updated | Phase 4: Process Hygiene Audit |
| Provides next-chapter scene briefs | Phase 5: Next Chapter Prompt Generation |
| Checks anchor firing schedule | Phase 3: Anchor Integrity Check |
| Flags character-as-author moments | Phase 1: Thesis Guillotine Scan |
| Verifies against prior chapters | Phase 2: Rolling window last ~10 chapters |
| Breath Beat every 3rd chapter | Phase 5: Breath Beat detection |
