# Subagent-Driven Fiction Workflow

> Refined across a 12-chapter Act I drafting session. Per-chapter pipeline,
> scene-brief template, Canon Lockbox format, constraint cheat sheet, and
> pre-critic continuity sweep checklist.

## The Per-Chapter Pipeline (Refined)

```
1. UPDATE RSO LOG FIRST
   └── Write RSO entry for AFTER the previous chapter BEFORE dispatching writer.
       Include: NLP directive for next chapter, character states, loop statuses,
       anchor tracker, craft constraint status, next-chapter options.
       The RSO is the writer's state injection. Without it, subagents drift.

2. DISPATCH WRITER SUBAGENT
   ├── Context: scene briefs + Canon Lockbox + constraint cheat sheet + RSO excerpt
   ├── Toolsets: ["file", "terminal"]
   └── Goal: "Write Chapter N... Full prose. Ready for critic."

3. RETRIEVE DRAFT
   ├── Read the chapter file
   ├── Normalize section breaks (*** not ## Headings)
   └── Verify word count in target range

4. PRE-CRITIC CONTINUITY SWEEP (MANDATORY — never skip)
   ├── Scar location (right forearm, always — verify in every Nera scene)
   ├── Timeline (hours, not days — check every internal reference to elapsed time)
   ├── Data provenance (what each character knows and when they learned it)
   ├── Casualty count (only Calibrator + caravan + one child through Ch.08)
   ├── Nomenclature (Karthesian Treaty vs. the Charter — same document)
   └── Fix ALL continuity errors BEFORE critic sees draft.
       Critics evaluate prose, not canon. Drift wastes critic cycles.

5. DISPATCH CRITIC SUBAGENT
   ├── Context: chapter file path + craft element verification checklist
   ├── Toolsets: ["file", "terminal"]
   └── Goal: "Evaluate Chapter N. 8-step protocol. Max 3 priority actions."

6. SURGICAL REVISION
   ├── Apply only the 3 priority actions from critic
   ├── Prefer subtraction over addition (cuts > adds)
   ├── Net change should be <300 words (best revisions remove scar tissue)
   └── Do NOT "improve while you're there"

7. UPDATE ARCHITECTURE FILES
   ├── RSO Log: add post-chapter state + NLP directive for next
   ├── Zeigarnik Ledger: update loop statuses, add chapter summary
   ├── Character Models: update Current Status table
   └── README: update progress stats + POV states

8. PRESENT FINAL
   └── Summary: word count, critic score, revisions applied, what was achieved
```

## Scene-Brief Template (for Writer Context)

```markdown
## SCENE N: CHARACTER NAME
- **Setting:** [Location, time of day, atmospheric details]
- **Action:** [What happens. The physical events. Be specific.]
- **The Fatal Flaw / Escalation:** [How the character's psychology drives the action]
- **CRAFT CONSTRAINT — [Type]:** [Failed Articulation / Failed Comfort /
   Dialogue Misalignment / Blunt Force Summary — describe exactly]
- **Somatic Tell:** [Specific physical action under stress]
- **Sensory Anchor:** [Which anchor fires — ozone, pressure, scar, Engine hum, necrosis, etc.]
- **Ending beat:** [The final image or micro-cliff]
```

## Canon Lockbox (MUST include in every writer context)

After multi-chapter sessions, writer subagents lose track of established facts.
Always copy the Canon Lockbox into the writer's context. Update after every chapter.

```markdown
CANON LOCKBOX (do not contradict):
- Nera's scar: right forearm, 6cm, from a woman who tried to kill her (adult wound, not childhood)
- Calibrator died: ~N hours ago. All chapters set within hours, not days. Verify epigraph timestamp.
- Theron's data: origin data from deep archives, copied in Ch.02. NOT Directorate telemetry.
- Kaelen's log: 14:02, 47.3 Hz. She deleted escalation in Ch.01. Voss recovered it in Ch.05.
- Only deaths: Calibrator (Ch.01), civilian caravan (Ch.06), one child in incubator (Ch.08) — through Act I
- [ADDITIONAL ENTRIES as novel progresses]
```

## Constraint Cheat Sheet (Recalibrated after Act I)

### Anti-Thetical Contrast — HARDENED (Zero Tolerance)
- **SENSORY negations: BANNED — rewrite all to direct positive.** No quota. No exceptions.
  - EX: "Not the darkness of night. The darkness of depth..." → "The darkness of depth..."
  - EX: "not absence but the presence of absence" → "was physical"
- **FUNCTIONAL/TECHNICAL negation: PERMITTED** (alien possession, technical clarity)
  - EX: "a heart that was not her own" — KEEP
- **THEMATIC negation: MAX ONE per chapter, deliberate, earned by tension**
  - EX: "She had become the thing she burned the Charter to prevent."
- **Detection threshold: ONE sensory negation triggers rewrite.** By three, the pattern is visible.
- **Pre-submission grep:** `grep -n "not \|wasn't \|was not " chapter.md | grep -v "could not\|did not know\|was not her own\|not a variable"`

### Thesis Sentence Guillotine
- 95% RULE: Never summarize what was shown through action
- BANNED: "She realized that...", "He understood then that...", "It was the silence of..."
- BANNED: Numbered realizations, end-of-section summaries, somatic explanations, self-rationalizations
- **BFS Grounding Rule:** The ONE BFS must pass the "say it aloud in character" test.
  Must contain at least one word/phrase from the POV character's sensory experience in that scene.
  NO abstract thematic language the character wouldn't use.

### Other Rules (always active)
- No therapy-speak (era-appropriate: spiritual pollution, humoral imbalance)
- No character-as-author dialogue
- Register degrades under physical stress
- Sensory density: ≥1 VAK per 3 sentences
- No bold on thematic lines
- Rhythm: never 3 identical-length sentences in sequence

### Per-Act Requirements
- At least 1 Failed Articulation per act
- At least 1 Failed Comfort per act
- At least 1 Dialogue Misalignment per act
- At least 1 Breath Beat every 3rd chapter

### Sensory Anchors Reference
| Anchor | Cue | Fire Rate | Notes |
|--------|-----|-----------|-------|
| Master — Ozone | Sharp, metallic, lightning-strike → smell of consumption | Every 1-2 chapters | Evolves from clean to parasitic over novel |
| Secondary — Pressure | Ears pop, teeth ache, skull-crush | Every 2-3 chapters | Tied to Storm + combat |
| Nera — Scar | RIGHT FOREARM, 6cm, touched unconsciously | Every Nera chapter | May go DEAD — if so, character loses anchor |
| Post-Hypnotic — Engine Hum | 60 Hz discordant, bone on bone | Plant once, recur, climax Act III | Can be silenced — silence becomes new trigger |
| Necrosis — Silver-vein | Luminescent argent lines under skin | When Resonance Sickness relevant | Advances with each artifact activation |
| Dead Relay Hum | 60 Hz absence — silence as wound | Baseline after network severance | Persist until restoration |
| Artifact Frequency | Sub-audible hum, grammar, heartbeat | When artifact is active | Evolves: grammar → questions → answers |

## Craft Constraint Deployment Tracker

Track which per-act requirements have been fulfilled. Reset after each act.

| Requirement | Target | Deployed |
|-------------|--------|----------|
| Failed Articulation | ≥1 per act | |
| Failed Comfort | ≥1 per act | |
| Dialogue Misalignment | ≥1 per act | |
| Breath Beat | Every 3rd chapter | |

## POV Convergence Protocol

When two POV characters share a scene for the first time:
1. Both characters must remain in their established voices
2. Neither character should explain themselves more than they would to themselves
3. The convergence should CREATE new tension, not resolve old tension
4. At least one character should misinterpret or partially misunderstand the other
5. The scene should end on an unresolved question between them
