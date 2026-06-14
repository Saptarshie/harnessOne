---
name: novel-writing-pipeline
description: >
  Battle-tested workflow for multi-chapter novel drafting with subagent-driven\n  quality control. Hard-won learnings from 21-chapter Act I+II of The Chrysalis\n  Protocol (midpoint reached). Use BEFORE writing or planning any novel chapter.
category: storytelling
---

# Novel Writing Pipeline — Lessons Learned (27-Chapter Act I+II, 64% Complete, Turning Point Reached)

## MANDATORY PRE-FLIGHT (before ANY chapter)

### STARTUP INTEGRITY CHECK — RUN FIRST (before any novel work)

**When:** Session start, reconnection after disconnect, or any time you begin working on the novel.

**Check:** Compare actual chapter count vs. RSO's `chapters_written`. If they don't match, someone wrote a chapter without updating logs. STOP and fix before doing anything else.

```bash
# Verify: actual chapter count must equal RSO's chapters_written
ls chapters/*.md | wc -l          # actual count
grep "chapters_written" architecture/03-rso-log.md   # RSO claim
```

If mismatch:
1. Read the unwritten chapter(s) and the current RSO log
2. Update ALL architecture files (RSO, Zeigarnik ledger, README, character models)
3. Verify each file references the correct chapter count
4. Only THEN proceed with new work

**This is the #1 process failure. Chapters drafted without log updates create a ghost state — the files say one thing, the logs say another. Every subsequent chapter compounds the drift. Fix it before anything else touches the novel.**

### Load Skills

**Load these skills BEFORE dispatching the writer subagent:**
1. `neuro-narrative-architecture` — THE KEY TO AUDIENCE RETENTION. Zeigarnik lattice, somatic markers, cortisol-oxytocin wave pacing, reward prediction error. Without this, chapters become flat description. Load EVERY TIME.
2. `novel-weaver` — Novel-scale patterns, anchor distribution, breath beat requirements, dialogue misalignment protocol, thesis guillotine rules.
3. `mythic-weaver` — Base patterns (loaded by novel-weaver as dependency).

**Update architecture files BEFORE writing:**
- RSO log: add pre-chapter state + NLP directive for this chapter
- Zeigarnik ledger: verify loop statuses are current
- README: verify POV states are current

**Update architecture files AFTER writing (BEFORE presenting to user):**
- RSO log: post-chapter state, new NLP directive
- Zeigarnik ledger: chapter summary, loop updates, anchor tracker
- README: progress %, POV states, new anchors
- Character models: update Current Status table if POV states changed significantly

**FORGETTING THESE UPDATES IS THE #1 PROCESS FAILURE.** The user has had to prompt for log updates multiple times. Do it proactively after every chapter.

**POST-UPDATE VERIFICATION (Ch.15+ lesson):** After updating all four architecture files, run a quick integrity check:
```
grep -l "Chapter N" architecture/*.md   # all files should reference the new chapter
grep -l "END OF CHAPTER N" architecture/01-character-models.md  # character models match
grep "chapters_written.*N" architecture/03-rso-log.md  # RSO count matches actual
```
The Zeigarnik ledger header, the character models status table heading, and the RSO's `chapters_written` field are the three most-likely-to-drift elements. Verify all three match the actual chapter count before moving on.

**README TABLE PATCH SAFETY (Ch.17 lesson):** When patching table rows in README.md, the `old_string` MUST include at least 2 surrounding rows above and below the target to ensure uniquess. The README has duplicate chapter numbers (Ch.13 appears in both Act I and Act II quick-reference tables). A patch targeting `| 13 |` without enough surrounding context will match the wrong table and corrupt the file. Minimum context: 4+ lines of surrounding table rows.

---

## SUBAGENT-DRIVEN WORKFLOW (MANDATORY FOR LONG CONTEXT)

**Why:** Multi-chapter fiction destroys context windows. A single agent that writes 12 chapters accumulates context bloat → quality degradation. The writer/critic separation prevents self-grading false positives. The reviewer (story-reviewer) catches what the critic misses and enforces process hygiene.

**The pipeline (6 stages):**

```
1. UPDATE ARCHITECTURE FILES (pre-chapter)
   ├── RSO: add current state + NLP directive
   └── Zeigarnik: verify loop statuses

2. DISPATCH WRITER SUBAGENT (delegate_task)
   ├── Context: scene briefs + Canon Lockbox + constraint cheat sheet + chapter epigraph
   ├── Toolsets: ["file", "terminal"]
   └── Goal: "Write Chapter N. Full prose. Save to chapters/XX-title.md."

3. PRE-CRITIC CONSTRAINT + CONTINUITY SWEEP (orchestrator — BEFORE critic)
   ├── CONTINUITY:
   │   ├── Scar location (right forearm, always — Nera only. DEAD since Ch.08.)
   │   ├── Timeline (hours, not days/weeks)
   │   ├── Data provenance (what each character knows and when)
   │   ├── Casualty count (only Calibrator + caravan + 1 child dead)
   │   └── Location/nomenclature consistency
   ├── CONSTRAINT AUDIT (same priority as continuity — fix before critic):
   │   ├── Blunt Force Summary COUNT — exactly 1 per chapter. Writer subagents over-produce BFS (3-4 per chapter is common). Scan for ALL short devastating declarative sentences. Keep only the NLP-mandated one. Cut or demote the rest.
   │   ├── Anti-thetical scan — grep for "not " / "wasn't " / "was not " / "were not " / "did not ". Classify each: sensory/emotional → REWRITE; functional/technical → keep; thematic/rhetorical → is it the ONLY one? If no, pick strongest and rewrite rest.
   │   ├── Trigger-word scan — grep for "trigger" in narrative prose (exclude epigraph). If found → replace with "conduit," "bridge," "circuit," or other electrical metaphor. The WORD is tainted after Ch.12.
   │   ├── Rhythmic negation scan — sequences like "She was not X. She was not Y. She was Z." must be rewritten to direct affirmatives.
   │   ├── Sensory repetition scan — any word repeated 3+ times as predicate across consecutive sentences ("X grounded him. Y grounded him. Z grounded him.") → cut to strongest follow-through.
   │   ├── POV gaze recap scan — "She looked at [Name] — [biography]" patterns → cut to "She looked at each of them in turn."
   │   ├── Closing BFS cluster scan — in final 100 words, any short standalone devastating sentence competing with designated BFS → integrate or cut.
   │   ├── Thesis framing in dialogue scan — "The difference between us:" / "The distinction is:" → remove frame, keep content.
   │   ├── Thesis guillotine scan — search for "realized that" / "understood that" / numbered realizations / end-of-section summaries / somatic explanations / self-rationalizations. Cut ALL.
   │   └── Therapy-speak scan — "self-soothing" (permitted if established in character model), "processing trauma" (BANNED), modern psychological terms
   └── Fix ALL constraint violations BEFORE critic sees draft. Critics evaluate prose, not compliance.

4. DISPATCH CRITIC SUBAGENT (delegate_task — SEPARATE from writer)
   ├── Context: chapter file path + craft element checklist
   ├── Toolsets: ["file", "terminal"]
   ├── Skill: "storytelling-critic" ONLY (no writer skills)
   └── Goal: "Evaluate Chapter N. 8-step protocol. Max 3 priority actions."

5. SURGICAL REVISION (orchestrator)
   ├── Apply ONLY the 3 priority actions from critic
   ├── Prefer subtraction over addition (net change <300 words)
   ├── Do NOT "improve while you're there" — stick to the critic's list
   └── VERIFY: After applying fixes, read the patched area + 5 lines before/after. Check for:
       ├── Duplicate lines (old text wasn't fully removed — Ch.25: lines 132-134 duplicated after critic fix)
       ├── Broken paragraph transitions (patched text doesn't connect to surrounding prose)
       └── Lingering patterns the critic explicitly flagged for removal

6. DISPATCH REVIEWER SUBAGENT (delegate_task — FINAL GATE)
   ├── Context: chapter file + architecture files + last ~10 chapters
   ├── Toolsets: ["file", "terminal"]
   ├── Skill: "story-reviewer" (loads storytelling-critic as reference only)
   ├── Goal: "Review Chapter N after critic + fixes. Audit constraints, continuity,
   │          anchors, process hygiene. Flag issues. Generate Ch.N+1 prompt."
   └── FALLBACK: If reviewer times out (600s, common with 9-29 API calls on large context),
       do NOT re-dispatch. The reviewer typically completes file writes before the timeout
       signal propagates. Verify with: grep "chapters_written.*N\|N/42\|END OF CHAPTER N"
       across RSO, README, and character models. If headers are updated, reviewer succeeded.
       If not, handle architecture updates directly — update all four files manually.
```

**HARD RULES:**
- Writer subagent loads mythic-weaver + novel-weaver + neuro-narrative-architecture
- Critic subagent loads ONLY storytelling-critic
- Reviewer subagent loads story-reviewer (+ storytelling-critic as reference)
- Never mix writer and critic in the same agent
- Reviewer runs AFTER critic + fixes — it does NOT replace the critic
- **Writer subagent: DO NOT SELF-PATCH.** Write the prose, verify format, return the draft. Do NOT run constraint audits, anti-thetical scans, or prose rewrites. That is the orchestrator's job (pre-critic sweep + critic). Writer self-patching adds 15-39 tool calls of latency, frequently introduces patch-duplication bugs (Ch.25: duplicated lines 132-134), and produces constraints the orchestrator must then un-patch. The writer's sole job: write. Return. Stop.

**Post-chapter updates (orchestrator, AFTER reviewer passes):**
- RSO log: post-chapter state + NLP directive from reviewer
- Zeigarnik ledger: chapter summary, loop updates, anchor tracker
- README: progress %, POV states
- Character models: update if POV states changed significantly

---

## SUBAGENT CONTEXT PROTOCOL — DEFINE ALL TERMS

**THE PROBLEM:** Subagents receive context packets dense with abbreviated constraints (BFS, VAK, DMN, NLP, RSO). If a term is undefined in the subagent's context, the subagent cannot evaluate it. The Ch.14 critic returned "Cannot evaluate BFS — term undefined in protocol" — wasting a critic cycle on a definition gap.

**THE RULE:** Every constraint abbreviation used in a subagent context packet MUST be defined on first use in that packet. The writer context, critic context, and reviewer context are SEPARATE packets — define terms in each one independently. Do not assume carryover.

**Minimum definitions for every subagent context:**
- **BFS (Blunt Force Summary):** A single devastatingly simple sentence (under 15 words) that states a horrific reality without metaphor, earned by rising tension. ONE per chapter. The chapter's designated BFS moment is specified in the scene briefs. **CRITICAL EXCEPTION (Ch.24, 27, 29):** The user occasionally designates BFS that themselves contain the \"not X, but Y\" structure for thematic/factual revelations — e.g., \"The sky was not a weather system. It was a broken machine\" (Ch.24), \"The sky was not a heaven. It was a ceiling\" (Ch.27), \"They were not gods deciding the fate of the world. They were janitors\" (Ch.29). These are USER-DESIGNATED and explicitly permitted. The negation serves a factual/thematic revelation, not emotional/sensory description. Do NOT flag or rewrite these — they are intentional craft choices at major turning points. The anti-thetical constraint applies to EMOTIONAL/SENSORY descriptions, not to these thematic gut-punches.
- **Anti-thetical contrast (sensory negation):** Any "Not X. Y." or "was not X, but Y." construction describing atmosphere, emotion, or physical sensation. ZERO TOLERANCE. Rewrite to direct positive description.
- **VAK:** Visual, Auditory, Kinesthetic — sensory modalities. ≥1 VAK detail per 3 sentences.
- Any other abbreviation specific to this novel's constraint system.

**Ch.14 field example:** The critic's protocol said "One BFS only, placed correctly" without defining BFS. The critic correctly flagged it as undefined and could not score it. Fixed by defining the term in the critic's context packet.

## CANON LOCKBOX (anti-drift weapon)

Writer subagents have no memory of prior chapters. They WILL invent: wrong scar locations, wrong timelines ("days" instead of "hours"), wrong data provenance, invented casualties. EVERY writer context MUST include:

```
CANON LOCKBOX (do not contradict):
- Nera's scar: right forearm, 6cm. DEAD since Ch.08 — cold, numb, sensationless.
- Nera's artifact hand: RIGHT hand Ch.04–Ch.14 (locks in vault, rides, endures shockwave, picks up from med-bay table). During Null-dome creation (Ch.14 climax), the artifact PHYSICALLY MIGRATES from right palm to LEFT palm — argent threads retract from blistered right hand, fuse into the open wound of the left claw-hand. ALL chapters Ch.15–31: artifact fused to Nera's LEFT palm. When Idris severs it (Ch.26), Kaelen receives it into HER left hand (her right hand is dead from the live wire). The left-hand association is permanent post-Ch.14.
- Calibrator died: ~X hours ago. ALL chapters set within hours, not days/weeks.
- Only deaths: Calibrator (Ch.01), civilian caravan (Ch.06), 1 child in incubator (Ch.08). Thousands dying off-page from Severance.
- Theron's data: origin data from deep archives. NOT Directorate telemetry.
- Kaelen's loupe: SHATTERED (Ch.08). Core circuitry intact but lens gone.
- **Trigger-word prohibition:** After Ch.12 silenced the Post-Hypnotic Trigger, the WORD "trigger" must never appear in narrative prose to describe any character, action, or object. The word carries thematic weight the reader associates with the silenced hum. Use "conduit," "bridge," "catalyst," "spark," or "circuit" instead. Epigraphs (in-universe documents written before Ch.12 events) are exempt.
- [Any other immutable facts from prior chapters]
```

**Most common drift patterns (caught in Act I+II):**
| Drift | Example | Chapters Affected |
|-------|---------|-------------------|
| Scar migration | Nera's scar moved from right forearm to other locations | Ch.03, Ch.04 |
| Artifact hand drift | Nera's artifact described in wrong hand (right pre-Ch.14, left post-Ch.15) | Ch.06, Ch.14–15 gap, late chapters (caught in post-completion audit) |
| Timeline compression | "Three days prior" / "weeks earlier" / "three days unchanged" when only hours passed | Ch.04, Ch.10, Ch.16 |
| Data provenance | Theron's crystal described as "Directorate telemetry" | Ch.03 |
| Casualty inflation | "743 deaths" invented by subagent | Ch.04, Ch.06 |
| Location invention | "Engine chamber" not in prior canon | Ch.08 |
| Markdown headings | `## N. SCENE TITLE` inserted between scenes | Ch.17 |
| **Trigger word in narrative** | Using "trigger" to describe any character/object/event (e.g., "she became the trigger") — the WORD is tainted after Ch.12 silenced the Post-Hypnotic Trigger. Replace with "conduit," "bridge," "circuit," or other electrical metaphor | Ch.23 |

**Timeline-word detection (pre-critic):** Before critic dispatch, grep the draft for "days" / "weeks" / "months". If found, verify against the Canon Lockbox timeline (hours, not days). The word "days" in a subagent draft is almost always a drift error. Ch.16 had "three days unchanged" for bandages that were hours old.

---

## CHAPTER FORMAT — HARD RULE (Ch.16-19 lesson)

**Chapter heading format:** Every chapter file MUST begin with `# CHAPTER X: TITLE` as the absolute first line, followed by a blank line, then the epigraph. Do NOT use markdown `## N. SCENE TITLE` headings between scenes.

```
# CHAPTER 16: THE ARCHITECTURE OF STAGNATION

*"Epigraph text..."*
— Attribution

***
[prose]
***
[prose]
***
[prose]
```

**Detection (pre-critic):** Verify line 1 of every chapter file matches `# CHAPTER \d+:`. If missing, prepend it BEFORE critic sees the draft. Ch.16-18 were submitted without headings — caught by user audit.

---

## CONSTRAINT ENFORCEMENT (HARD-WON)

### Anti-Thetical Contrast — HARDENED (Ch.13-15)

**Emotional/sensory negations: ZERO TOLERANCE.** Any sentence describing atmosphere, emotion, or physical sensation using "not/never/no" followed by a restatement must be rewritten. This includes the classic "Not X. Y." pattern AND subtler variants.

**Functional/technical negations: PERMITTED.** "This signal was not a ghost. This was a physical tap." "She did not move. She could not move."

**Thematic negations: ONE per chapter, deliberate.** Must be earned by rising tension. If any other negation appears, this one must be cut too.

**NEW — Rhythmic Negation (parallel-negation cadence):** The writer uses parallel negations as a rhythmic device: "She was not healed. She was not ready. She was a woman..." or "The grammar resolved — not words, but a frequency..." These read as prose tics. Detection: any sequence of 2+ sentences beginning with negation, followed by an affirmation. Rewrite to direct positive: "She was ruined. She was unready. She was a woman consumed..." / "The grammar resolved into a frequency..."

**Field examples (Ch.13-15):**
```
BEFORE (rhythmic negation — BANNED):
  "She was not healed. She was not ready. She was a woman who had been consumed..."

AFTER (direct positive):
  "She was ruined. She was unready. She was a woman consumed by a parasite..."

BEFORE (dash-negation — BANNED):
  "The grammar resolved — not words, but a frequency that made her molars ache..."

AFTER (direct positive):
  "The grammar resolved into a frequency that made her molars ache..."

BEFORE (triple negation on sensory — BANNED):
  "a wet exhale that was not language and not silence and not anything human"

AFTER (positive description):
  "a wet exhale that was neither word nor breath — something animal scraping past locked vocal cords"

BEFORE ("no longer X. Y." — BANNED for emotional/sensory):
  "He was no longer a mind reaching for the Chorus. He was a man pumping a bellow."

AFTER (invert, drop the negation frame):
  "A man pumping a bellow. His hands. His choice."
```

**Detection (pre-critic sweep):** After receiving draft, run three scans:
1. `grep -n "not \|wasn't \|was not \|were not \|did not \|no longer" chapter.md` — classify each hit
2. Manual scan for parallel negation: 2+ consecutive sentences starting with negation → rewrite
3. Manual scan for dash-negation: "— not X, but Y" or "— no X, only Y" → rewrite

### Truth-Statement Negation Overuse — MAX 2 PER CHAPTER (Ch.17)

**THE PROBLEM:** The "X was not Y. X was Z." structural pattern is devastating when used sparingly for factual revelations. The writer deploys it 5+ times per chapter: "The Calibrator was not a god. It was a scientist." / "The left hand was no longer soothing. It was executing." / "Resonance was not divine. It was artificial." By the fifth instance, the reader is pattern-matching, not feeling.

**THE RULE:** Keep the 1-2 strongest instances where the negation-then-revelation serves a genuine thematic gut-punch. Rephrase all others to direct statements without the negation frame.

### Philosophical/Abstraction Negation — NEW PATTERN (Ch.17)

**THE PROBLEM:** A subtler variant escapes existing anti-thetical scans because it's not sensory — it's philosophical/abstract: "The question was not whether the truth would destroy him. The question was what a man did with the truth..." This is a rhetorical structure (negate one question, posit another), not a sensory description, but it reads as the same authorial tic. The existing grep-based anti-thetical scan catches sensory negations but MISSES this pattern because it doesn't contain "not" adjacent to a sensory word.

**THE RULE:** Any sentence structured as "The X was not Y. The X was Z." where X is an abstraction (question, problem, issue, truth, reality) must be rephrased to direct affirmative: "The truth would destroy him. The only remaining question was what a man did with the truth..."

**Detection:** Scan for "The question was not" / "The problem was not" / "The issue was not" / "The truth was not" — all variants of the same pattern. Rewrite to direct positive.

### Internal Indecision Negation — NEW PATTERN (Ch.20)

A character's internal indecision rendered as a series of negations: "She did not know if she would go to the Rift. She did not know if she could leave the bunker..." This is a rhythmic "did not know if / did not know if" cadence. Replace with direct present-tense affirmatives that externalize the tension into physical objects: "The Rift waited. The bunker held her. The choice remained unresolved."

Detection: scan for "did not know if" appearing 2+ times within 3 lines.

### Metaphor Duplication Across Characters — CUT THE ECHO (Ch.19)

**THE PROBLEM:** The writer applies the same distinctive metaphor to two different characters in the same chapter: "He had spent eighteen years as a peripheral device for the Calculus Engine" (Idris) + "He had spent forty years as a peripheral device for that lie" (Theron). The identical metaphor across POVs reads as authorial tic, not character voice. Each character's experience is distinct; the metaphor should be too.

**THE RULE:** Any distinctive 3+ word metaphorical construction applied to more than one character in the same chapter must be cut from one of them. Rewrite the weaker instance using character-specific language. Idris was literally a peripheral for the Engine (keep); Theron was a "node" in the Chorus (rephrase).

**Detection:** After writer draft, grep for distinctive metaphorical phrases. If the same phrase describes two different characters, keep the stronger match, rephrase the other.

### Over-Explanation After Strong Lines — CUT THE ESCORT

**THE PROBLEM:** The writer delivers a devastating line ("She was optimizing the Directorate's funeral"), then immediately follows it with 2-3 sentences that restate the same idea in diluted form. The strong line stands perfectly alone; the escort weakens it.

**THE RULE:** After any sentence that qualifies as a potential gut-punch (short, specific, devastating), the NEXT paragraph must introduce NEW information — not restate, explain, or soften what was just delivered. If the next paragraph echoes the gut-punch, cut it. Trust the reader.

**Ch.17 field example:** "She was optimizing the Directorate's funeral" was followed by "That was the difference between a technician and an architect. The technician obeyed the specification. The architect understood what the specification was for." — a restatement of the epigraph. Cut. The funeral line stands alone now and hits twice as hard.

### Sensory Repetition + Itemized List — NEW PATTERN (Ch.22)

**THE PROBLEM:** The writer repeats a word three times with different subjects, then follows with an itemized list restating the same sensory details: "The mud grounded him. The cold grounded him. The pressure of the Storm on the horizon — ears popping, teeth aching — grounded him. Only the physical world: mud, cold, pressure, the sharp smell of ozone..." The repetition reads as authorial insistence and the itemized list re-tells what was already shown. This is a close cousin of the BFS over-explanation — the narrator insisting on the point.

**THE RULE:** After establishing the grounding effect (which the preceding paragraph already does through the steady-hands somatic marker), cut straight to the stark image. Keep only the strongest declarative sentence.

**Ch.22 field example:**
```
BEFORE:
  The mud grounded him. The cold grounded him. The pressure of the Storm on the horizon — ears popping, teeth aching — grounded him. A man in rain with steady hands. Equations silent. Only the physical world: mud, cold, pressure, the sharp smell of ozone bleeding off the Storm's leading edge, the wet wool of his coat against his throat, the burn in his atrophied legs.

AFTER:
  A man in rain with steady hands. Equations silent.
```

**Detection:** Scan for any word repeated 3+ times as a predicate across consecutive sentences ("X grounded him. Y grounded him. Z grounded him."). If found, cut to the strongest follow-through image.

### Character Recap Through POV Gaze — NEW PATTERN (Ch.22)

**THE PROBLEM:** The writer uses a POV character's gaze as an excuse to recite backstories the reader already knows. "She looked at Kaelen — the Platinum Index calibration engineer who had destroyed the Directorate vanguard... She looked at Idris — the Crown Analyst who had designed the Vel Coronat war mathematics... She looked at Theron — the Prelate who had discovered..." Each "she looked at" triggers a paragraph of known biography. This delays the action (in Ch.22, it delays the Failed Articulation and BFS) and insults the reader's memory.

**THE RULE:** Cut the backstory recitation. Replace with "She looked at each of them in turn." The reader already carries the biographies. The somatic action (the looking) is preserved. The weight transfers to what follows.

**Ch.22 field example:** 125 words of character recap before the BFS. Cut to 7 words. The BFS ("The war had no architects left") lands immediately and hits three times harder.

**Detection:** Scan for "She looked at [Name] — [multi-line biographical clause]" / "He looked at [Name] — [backstory]". If character biographies are recited through POV gaze, cut to "looked at each of them in turn."

### Closing BFS Cluster — NEW PATTERN (Ch.23)

**THE PROBLEM:** After the designated BFS has been delivered, the chapter's closing paragraphs produce additional short devastating sentences that compete for BFS status: "The Directorate battalion was ash." / "The weapon had worked." These are individually good lines, but they cluster at chapter-end and dilute the designated BFS. The reader should exit on the BFS's resonance, not on a pile-up of micro-punches.

**THE RULE:** The designated BFS is the ONLY standalone devastating sentence. Any short declarative sentence in the chapter's final 100 words that could read as a summary punch must be (a) cut, or (b) integrated into a compound sentence with surrounding sensory prose so it no longer stands alone.

**Ch.23 field example:**
```
BEFORE (3 BFS-like punches at close):
  "The Storm had found its ground, and the ground was made of meat." [DESIGNATED BFS]
  ...
  "The Directorate battalion was ash. The weapon had worked."

AFTER (1 BFS only):
  "The Storm had found its ground, and the ground was made of meat." [DESIGNATED BFS]
  ...
  "The Directorate battalion was ash, and the ozone hung thick as blood..."
```

**Detection:** In pre-critic sweep, after identifying the designated BFS, scan the chapter's final 100 words for any short (under 15 words) standalone sentence that reads as a devastating summary. If found, integrate or cut.

### Thesis Framing in Dialogue — NEW PATTERN (Ch.23)

**THE PROBLEM:** A character delivers a subtext-rich confession, but the writer prefaces it with a thesis-frame that tells the reader what to conclude: "The difference between us: you believed the war was necessary and I knew it was not." The parallel structure between "you believed" and "I knew" already does the work. The framing ("The difference between us:") is the author elbowing the reader.

**THE RULE:** Remove the thesis-frame. Let the parallel structure carry the weight. If the contrast is real, the reader assembles it — and the assembly is more powerful than the delivery.

**Ch.23 field example:**
```
BEFORE:
  "The difference between us: you believed the war was necessary and I knew it was not."

AFTER:
  "You believed the war was necessary. I knew it was not."
```

**Detection:** Scan dialogue for "The difference between us:" / "The distinction is:" / "What separates us:" / any explicit framing that names the subtext before delivering it. Remove the frame, keep the content.

### Blunt Force Summary — ONE PER CHAPTER (HARD CAP)

**THE PROBLEM:** Writer subagents over-produce BFS. A chapter with 3 scenes will reliably produce 3-4 standalone devastating-simple-sentence punches. This is the #1 constraint violation that survives the writer → critic → reviewer pipeline because (a) the writer doesn't count them, (b) the critic praises individual BFS quality without noticing the count, and (c) they're individually good lines so the orchestrator hesitates to cut them.

**THE RULE:** ONE BFS per chapter. Period. The user's scene briefs designate which moment gets it. All other devastating-simple-sentence punches must be either (a) cut entirely, or (b) demoted by integrating them into preceding sensory/action prose so they no longer stand as standalone summary.

**Detection (pre-critic sweep):** Use `references/constraint-audit-checklist.md` as the step-by-step scan. Run it before every critic dispatch. The BFS has a distinctive cadence: "The X was Y, and the Z was W." or "X had been Y; now it was Z." Count them. If count > 1, keep only the NLP-mandated one. Cut the rest.

**Ch.14 field example:** The draft had 3 BFS:
- "The math was blood, and she had helped aim the guns." (Kaelen — CUT, the tapping breakdown already dramatized this)
- "The lie that had been her life for twelve years was dead on the screen..." (Kaelen — CUT, redundant)
- "The empire was blind, and the man who had blinded it was finally running." (Idris — KEPT, NLP-mandated)

### Phrase Repetition Dilution — MAX 2x PER CHAPTER

**THE PROBLEM:** Writer subagents craft resonant phrases ("a mercy and a countdown") and deploy them 4-5 times across a chapter. Each repetition dilutes impact. By the fourth appearance, the reader has internalized the phrase and the repetition reads as authorial insecurity — the writer doesn't trust the reader to remember.

**THE RULE:** Any distinctive resonant phrase (3+ words, metaphorical or thematic) may appear at most TWICE in a chapter: once in the epigraph and once in the body. If the phrase appears more than 2x, cut the weakest instances. The epigraph + body cap provides one structural echo — enough for resonance, not enough for dilution.

**Ch.15 field example:** "mercy and a countdown" appeared in epigraph (L3), paragraph 2 (L16), Scene 1 ending (L54), and Scene 3 ending (L154). Fixed by cutting all internal instances, leaving only the epigraph. The chapter gained power from the subtraction.

**Detection:** After writer draft, grep for distinctive phrases. Count occurrences. If > 2, keep epigraph + strongest body instance. Cut the rest.

### Thesis Sentence Guillotine
- **95% rule:** Never summarize what was shown through action.
- **ONE Blunt Force Summary per chapter** — devastating simple sentence after rising tension. Must be earned.
- **Banned sub-patterns:** "She realized that...", "He understood then that...", numbered realizations, end-of-section summaries, somatic explanations, self-rationalizations.

### Other Always-Active Rules
- No therapy-speak. No character-as-author dialogue.
- Register degrades under physical stress.
- Sensory density: ≥1 VAK per 3 sentences.
- No bold on thematic lines.
- Section breaks: `***` between scenes. No markdown headings in prose.
- **NO `## N. SCENE TITLE` or any markdown heading between scenes.** Writer subagents frequently insert these — caught in Ch.17. Pre-critic sweep must scan for and remove ALL `## ` prefixed lines.

---

## BREATH BEAT REQUIREMENTS (every 3rd chapter)

- At least one Failed Articulation (character starts thought, cannot finish)
- At least one Failed Comfort (comfort needed and not given — NOT comfort given quietly)
- At least one ugly/uncomfortable physical detail
- Dialogue shorter than feels satisfying
- Prose heavy, slow, claustrophobic
- NO character wisdom demonstrations
- This is where the reader catches breath — NOT where the character demonstrates insight

**Breath Beat + Major Plot Beat (Ch.27, Ch.30):** When a Breath Beat coincides with a major plot event (Turning Point, Grand Climax), the Breath Beat requirements still apply. Ch.27 was both Breath Beat AND Turning Point — the Failed Articulation (Nera's "Aa—") and Failed Comfort (Theron's three-second touch) were woven into the apocalyptic action. Ch.30 was both Breath Beat AND Grand Climax — the Failed Articulation (Saskia unable to speak after the silence fell) and Failed Comfort (the silence swallowing everything) were integral to the aftermath. The Breath Beat provides the oxytocin landing AFTER the cortisol spike of the major event, not instead of it.

---

## ANTI-THETICAL CONTRAST BUDGETING (Ch.28 lesson)

The user tracks the ONE permitted thematic negation per chapter as a finite resource that can be intentionally saved for future chapters. In Ch.28, the user explicitly directed: "Save the ONE permitted anti-thetical contrast for a future chapter, as we used it in Ch 27." This means:

- The one-per-chapter thematic negation quota is NOT automatically refilled — the user may choose to leave it unused
- When the user says "save it for later," the chapter must contain ZERO thematic/factual negations in narrative prose, even ones that would normally qualify as the permitted one
- The BFS should be written without negation when the quota is being saved
- This is a resource-management constraint, not a prose-quality constraint — the user is budgeting dramatic devices across the arc

---

## COMPRESSION PREPARATION

When context window grows too large and user plans to `/compress`:
1. Update ALL architecture files with complete post-chapter state
2. README must serve as standalone recovery hub
3. RSO log must have NLP directive for next chapter
4. Zeigarnik ledger must have complete loop table
5. Character models must have current status table

---

## POST-COMPLETION CONTINUITY AUDIT (Phase 4.5 — BEFORE PDF build)

> *After all chapters are written. Systematic grep-based sweep for physical/spatial continuity errors. Subagents have no memory — hand locations, scar sides, and body-part assignments WILL drift across chapters. This audit catches what the per-chapter pre-critic sweep misses: cross-chapter inconsistencies that only become visible when the full manuscript exists.*

### When to Run

- All chapters drafted, all architecture files final
- BEFORE PDF build (Phase 4)
- After any user-identified continuity error (to catch sibling issues)
- On user request: "check for continuity errors"

### Methodology (4-pass sweep)

**Pass 1 — Identify the anchor terms.** Map every physical/spatial detail that recurs across chapters:
- Body parts: which hand holds what, scar locations, wound sides
- Objects: artifact, loupe, weapons, tools — who carries them, which side
- Locations: which character is where, what floor/room/position
- Timeline markers: hours elapsed, sequence of events relative to each other

**Pass 2 — grep every chapter for the anchor terms.** One grep command across all chapter files:
```bash
grep -n "right hand\|left hand\|right palm\|left palm\|right forearm\|left forearm" chapters/*.md
```
Sort results by chapter, then by line number. Read each hit in context (3 lines before/after) to determine which character and what action.

**Pass 3 — Build a timeline.** For each anchor, trace chapter-by-chapter:
- Chapter N: [character] — [body part] — [state/action]
- Note the transition chapter if the anchor changes (e.g., artifact moves from right hand to left)

**Pass 4 — Flag and fix inconsistencies.** Any chapter that contradicts the timeline is a bug. Fix by:
- If the outlier is a single chapter: patch that chapter to match the consensus
- If the transition is missing: add an explicit migration paragraph at the most dramatic/narratively-earned moment (NOT a random chapter — tie it to a major event like a shockwave, dome creation, or severance)
- If the consensus is unclear: determine which option serves the story better (e.g., Kaelen receiving artifact into her left hand because her right is dead), then patch ALL outliers to that option

### Chrysalis Protocol Specific Checkpoints

Run these exact greps when auditing this novel:

```bash
# Check 1: Nera's scar — must be RIGHT forearm in every chapter
grep -n "left wrist\|left forearm" chapters/*.md | grep -i "nera\|scar"

# Check 2: Nera's artifact hand — RIGHT Ch.04–14, LEFT Ch.15–31
grep -n "right hand\|right palm\|left hand\|left palm" chapters/*.md | grep -i "artifact\|lattice\|fused"

# Check 3: Kaelen's right hand — DEAD since Ch.11 live wire. All movement must be machine-forced
grep -n "right hand" chapters/*.md | grep -i "kaelen"

# Check 4: Kaelen's artifact hand (post-Ch.26) — must be LEFT (her right hand is dead)
grep -n "left hand\|left palm" chapters/2[6-9]-*.md chapters/3[0-1]-*.md | grep -i "kaelen\|fused\|lattice"

# Check 5: Idris's palsy — right hand trembles pre-Ch.19, steadies after
grep -n "right hand.*trembl\|right hand.*twitch\|right hand.*claw\|right hand.*still\|right hand.*steady" chapters/*.md | grep -i "idris"
```

### Ch.14 Migration Canon (the critical transition)

The artifact migrates from Nera's RIGHT hand to her LEFT hand during the Null-dome creation climax (Ch.14). The in-text description added during the post-completion audit:

> *"And beneath the silver, beneath the grammar and the cold and the ozone scoring her lungs, the artifact physically relocated. The crystalline lattice in her right palm pulsed once — a final, surgical surge — and then the argent threads retracted from the blistered flesh... the threads found the open wound of her left palm — the claw-hand, the bleeding flesh where her nails had driven into the meat — and fused."*

This paragraph is now CANON. Do not remove, rewrite, or relocate it. Future chapters must respect: Nera's left hand is the artifact host from Ch.15 onward. Her right hand carries only blisters from the pre-migration grip.

### Kaelen Dead-Hand Canon

Kaelen's right hand is DEAD — nerves burned to carbon by the live wire (Ch.11). ALL subsequent movement of that hand (trembling Ch.26, rigidity Ch.27–28, twitch Ch.30) is explicitly MACHINE-FORCED via argent threads reanimating dead motor neurons. It is NEVER described as healing, recovering, or improving. The language must always attribute movement to argent threads / machine puppeteering / paranormal animation, not to natural nerve regeneration.

---

## FINALE / EPILOGUE CRAFT (Ch.31 field-tested)

**THE PROBLEM:** A finale that ends with characters sitting in the dark — powerful as a single image, but static. The reader needs to see the survivors move, act, and re-enter the world they helped change. Pure stasis undercuts the earned weight of survival.

**THE RULE:** Aftermath chapters must include PHYSICAL PROGRESSION. The survivors must transition from where the climax left them to where they will begin the new world. A climb. A walk. An emergence. The movement IS the bridge between cataclysm and aftermath. Without it, the jump to epilogue/archival material feels abrupt.

**Ch.31 field example:** The user rewrote the finale to add a three-hour climb sequence where each character ascends with their signature somatic vocabulary (Saskia's raw palms, Idris's steady hands, Theron's bare feet reading rust, Nera's human hand slipping, Kaelen last). They emerge into ordinary grey rain — scattered skiffs, wandering soldiers, no Relays, no Assembly. Then they begin the walk back to the bunkers. This physical progression earns the right to then shift into archival/epilogue material. The bridge line was simple: "But the junction was a tomb, and the surface was waiting."

**Minimum requirements for finale aftermath:**
- Show the survivors leaving the climax location
- Each character's exit should use their signature somatic marker
- The world they emerge into should be recognizably post-cataclysm, not identical to before
- A single bridge sentence before the tonal shift (e.g., to archival, to epilogue, to time skip)

---

## IN-WORLD DOCUMENT CRAFT (Ch.31 field-tested)

**THE PROBLEM:** Subagent-generated in-world documents (poems, decrees, dispatches, recovered fragments) default to prose — free verse for poems, clinical lists for decrees. The "crude" / "honest" / "found" aesthetic can become an excuse for abandoning formal craft.

**THE RULE:** In-world documents benefit from STRUCTURE. Even a "crude" anonymous poem should have meter, rhyme, or deliberate formal choices. The honesty comes THROUGH the craft, not despite it. A Sovereign's decree should have rhetorical architecture. A dispatch should have the cold cadence of military bureaucracy. A poem found in a relay station should have the rough but intentional music of someone who learned to write late but felt deeply.

**Ch.31 field example:** The user rewrote the relay station poem from free verse ("I did not know blood made a sound / I did not know I had been listening to something else / for forty-three years") into rhymed couplets with consistent meter:
```
Just the sound of my blood, a quiet fire.
I did not know that blood could make a sound,
or that a borrowed song had held me down
for forty-three years.
```
The formal choices — the rhyme of "fire" with "wire," "sound" with "down," the final couplet "The ear that hears no frequency / at last hears its own, and is free" — make the poem feel REAL. A real person, writing in the aftermath, reaching for form to contain the uncontainable. The craft IS the characterization.

**Document type guidelines:**
- **Poems:** Meter and rhyme even if described as "crude." The attempt at form is characterization. End on a couplet that resonates with the chapter's theme.
- **Decrees:** Rhetorical structure — opening salvo, body of justification, closing self-indictment or deflection. The Sovereign's decree follows: acknowledgment → arithmetic → self-justification → acceptance of judgment.
- **Dispatches:** Cold cadence. Numbered operational points. Clinical vocabulary. The horror lives in what is NOT said emotionally.
- **Archival notes:** Bureaucratic distance. Provenance details. A single devastating detail (e.g., "the truth cost seventeen copper weights").

---

## AUTONOMOUS MODE — INVOKING THE REVIEWER

When the user asks for completely autonomous story generation, the pipeline runs end-to-end without user intervention. The story-reviewer replaces the user's manual review:

1. Writer subagent → draft
2. Orchestrator → pre-critic sweep
3. Critic subagent → evaluation + 3 priority actions
4. Orchestrator → surgical revision
5. Reviewer subagent → final gate (audit + next-chapter prompt)
6. Orchestrator → present clean chapter + next prompt to user

The reviewer generates the next chapter prompt from architecture state, enabling chapter chaining without user input. Invoke only when user explicitly requests autonomous mode.

---

## POST-COMPLETION REVISION PIPELINE (Phase 5)

> *After all chapters are written and architecture is finalized. Prose polish only — no story changes.*

The revision pipeline is a SEPARATE phase that runs after the main writing pipeline. It polishes prose for engagement, sensory density, rhythm, and neuro-narrative impact WITHOUT altering story-line, plot, character actions, or dialogue meaning.

### When to Run

- Novel is COMPLETE (all chapters drafted, all architecture files final)
- User wants to enhance prose quality before final PDF build
- User explicitly invokes the revision pipeline

### Skills

| Skill | Role | Location |
|-------|------|----------|
| `hermes-revision-primer` | **Primer** — full system context (LOAD FIRST) | Load WITH hermes-revision (actor only) |
| `hermes-revision` | **Actor** — prose polisher | Load for revisor subagent |
| `hermes-revision-critic` | **Critic** — drift validator | Load for critic subagent ONLY |
| `neuro-narrative-architecture` | Engagement patterns | Load WITH hermes-revision (actor only) |
| `novel-weaver` | Novel-scale constraints reference | Load WITH hermes-revision (actor only) |

**Reference file:** `/workspace/the-chrysalis-protocol/story-telling-skills/revision-skills/HERMES_REVISION_SKILL.md`

### Actor-Critic Loop Architecture

```
For each chapter N (1 → 31, sequential):

1. DISPATCH REVISOR SUBAGENT (delegate_task)
   ├── Skills: hermes-revision-primer + hermes-revision + neuro-narrative-architecture + novel-weaver
   ├── Context: original chapter path + Canon Lockbox + character models + BFS text + epigraph
   ├── Toolsets: ["file", "terminal"]
   └── Goal: "Polish Chapter N prose. Save to revisions/NN-title-revised.md."

2. DISPATCH CRITIC SUBAGENT (delegate_task — SEPARATE agent)
   ├── Skills: hermes-revision-critic ONLY
   ├── Context: original path + revised path + next chapter path + Lockbox + BFS
   ├── Toolsets: ["file", "terminal"]
   └── Goal: "Validate Chapter N revision per 5-phase protocol. Output critique."

3. EVALUATE CRITIC VERDICT
   ├── PASS → Mark complete in revision-log. Proceed to Ch.N+1.
   ├── CONDITIONAL PASS → Apply fixes, re-submit to critic.
   └── BLOCKED → Phase 1 or 2 failed. Review mismatches. Re-revise.

4. AFTER ALL CHAPTERS
   ├── Final integration check (revised Ch.N ending → original Ch.N+1 opening)
   └── Optionally rebuild PDF from /revisions/
```

### What the Revisor CAN Do

- Sharpen word choice, vary sentence rhythm
- Add/refine sensory details (VAK: ≥1 per 3 sentences)
- Displace emotion onto physical objects (somatic markers)
- Ensure prose degrades under physical stress
- Cut redundant language, repeated words, thesis statements
- Improve paragraph structure and white-space rhythm
- Tighten dialogue tags, cut explanatory beats
- Apply cortisol-oxytocin wave pacing

### What the Revisor CANNOT Do (Hard Prohibitions)

- Change plot events, character actions, or dialogue CONTENT
- Add/remove scenes, characters, or story beats
- Alter BFS text, epigraph text, or chapter structure
- Change emotional arcs, themes, or character motivations
- Contradict Canon Lockbox facts
- Change POV sequence, scene count, or timeline references
- Modify original /chapters/ files (works in /revisions/ only)

### Directory Structure

```
the-chrysalis-protocol/
├── chapters/           ← ORIGINAL (NEVER modified)
├── revisions/          ← REVISED (created by pipeline)
│   ├── revision-log.md
│   └── NN-title-revised.md
├── architecture/       ← Reference (read-only)
└── story-telling-skills/revision-skills/
    └── HERMES_REVISION_SKILL.md  ← Full reference
```

### HARD RULES

1. **Original chapters are NEVER modified.** The revisor writes to `/revisions/` only.
2. **Revised-chapter-N must be compatible with original-chapter-N+1.** Critic verifies.
3. **Revisor and critic are SEPARATE subagents.** Never the same agent.
4. **BFS and epigraph are SACRED.** Verbatim match required.
5. **Net word count delta per chapter: ±100-400 words typical.**
6. **If Phase 1 (structural) fails, STOP.** Redo the revision.
7. **Phase 2 (story integrity) issues are BLOCKING.** Even one dialogue word changed → fail.
8. **The revision-log.md tracks all progress.** Update after each chapter.

### Overall Workflow (Complete Novel Lifecycle)

```
Phase 1: Story Bible + Character Models
Phase 2: Chapter Writing (Ch.1 → Ch.N) via writer→critic→reviewer pipeline
Phase 3: Architecture Finalization (all four files)
Phase 4: POST-COMPLETION CONTINUITY AUDIT (see section above) — grep-based sweep for hand/scar/location/timeline drift
Phase 5: PDF Build (from /chapters/)
Phase 6: REVISION PIPELINE (prose polish pass)
Phase 7: Final PDF Build (from /revisions/ or /chapters/, user choice)
```

---

---

## PROSE SHIFT TECHNIQUE — DEATH OF MAGIC (Ch.30 lesson)

When the novel reaches a moment where the supernatural/magical/technological system that has defined the world is PERMANENTLY EXTINGUISHED, the prose itself must transition from the dense, sensory-overloaded register of that system into stark, grounded, mundane reality. This is a reader-level extinction event — the vocabulary and rhythm the reader has associated with the world for the entire novel must die on the page.

**Execution (Ch.30 — Collapse of Resonance):**
1. **Sensory anchor extinguishment:** The OZONE anchor — fired in every chapter since Ch.01 — was explicitly extinguished mid-chapter. The prose registered the change: "The sharp, metallic tang... thinned." The anchor was replaced by mundane sensory language: "wet stone. Copper. Basalt dust. The smell of a cave."
2. **Frequency anchor extinction:** The 60Hz hum — the carrier wave vibrating through every chapter — spiked once, then cut to absolute zero. The silence was described as a physical presence, not an absence.
3. **Vocabulary shift:** Technical language (hexagonal grid, damping nodes, argent threads, crystalline lattice) was systematically removed from the prose as the machine died. By the final paragraphs, the vocabulary was human-scale: heartbeat, breath, silence, dark.
4. **Sentence-length contraction:** Early scenes used long, clause-dense sentences characteristic of sci-fi horror. After the collapse, sentences shortened. Fragments appeared. The rhythm matched the new reality — simpler, quieter, smaller.
5. **No going back:** Once extinguished, the anchor must NEVER fire again in subsequent chapters. The ozone is gone. The hum is dead. The prose has permanently changed register. Act III must operate in the new register.

**When to use:** Any chapter where a defining sensory/technological/magical system is permanently ended. The prose transition signals to the reader that this is not a temporary setback — the world has fundamentally changed.

---

## PER-ACT REQUIREMENTS (reset each act)

- ≥1 Failed Articulation per act
- ≥1 Failed Comfort per act
- ≥1 Dialogue Misalignment per act
- Breath Beat every 3rd chapter
- Master anchor (ozone) fired ≥3 times per act
- Post-Hypnotic Trigger: plant early, recur mid-act, detonate late-act

---

## NEURO-NARRATIVE ARCHITECTURE — NEVER SKIP

This skill IS the glue that holds reader attention. Before planning any chapter:
- Zeigarnik lattice: never close a loop without opening two smaller ones
- Somatic markers: displace emotion onto physical objects (scar, loupe, claw-hand, burned palm)
- Cortisol-oxytocin wave: high cortisol (action) MUST be followed by oxytocin (vulnerability)
- Reward prediction error: set up expectation, pivot to devastating psychological reality
- DMN haunting: the central question must force the reader to interrogate their own moral complicity
