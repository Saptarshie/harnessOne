# Pre-Critic Constraint Audit Checklist

Run this BEFORE dispatching the critic subagent. Fix everything flagged. Critics evaluate prose quality — they don't catch BFS count, anti-thetical drift, or subtext violations. That's the orchestrator's job.

---

## 1. BFS COUNT (HARD CAP: 1)

**Scan:** Look for short standalone sentences that state devastating truths without metaphor. Target pattern: "The X was Y, and the Z was W." or "X had been Y; now it was Z."

**Action:** If count > 1, keep only the NLP-mandated BFS. Cut the rest or demote by integrating into surrounding action prose.

**Ch.14 example:** 3 BFS found. Kept: "The empire was blind, and the man who had blinded it was finally running." Cut: "The math was blood, and she had helped aim the guns." (tapping breakdown already showed this). Cut: "The lie that had been her life..." (redundant ending).

---

## 2. ANTI-THETICAL SCAN (ZERO TOLERANCE FOR SENSORY)

**Primary grep:** `grep -n "not \|wasn't \|was not \|were not \|did not \|no longer " chapter.md`

**Classify each hit:**
- **Sensory/emotional** → REWRITE to direct positive. No exceptions.
- **Functional/technical** → KEEP. "She could not calibrate." "He did not know the way."
- **Thematic/rhetorical** → Is it the ONLY one in the chapter? If yes, keep. If no, pick strongest and rewrite the rest.

**Rhythmic negation (special case — Ch.13, Ch.15 field-tested):**
Sequences of repeated negations are a prose tic. Detection patterns:
- Parallel negation: "She was not X. She was not Y. She was Z." → "She was ruined. She was unready. She was Z."
- Dash-negation: "resolved — not words, but a frequency..." → "resolved into a frequency..."
- Triple sensory negation: "was not X and not Y and not Z" → positive description
- "No longer X. Y." frame for emotional/sensory → invert, drop the negation frame

**Ch.13 example:**
```
BEFORE: "She was not healed. She was not ready. She was a woman who had been consumed..."
AFTER:  "She was ruined. She was unready. She was a woman consumed by a parasite..."
```

**Ch.15 example:**
```
BEFORE: "a wet exhale that was not language and not silence and not anything human"
AFTER:  "a wet exhale that was neither word nor breath — something animal scraping past locked vocal cords"

BEFORE: "He was no longer a mind reaching for the Chorus. He was a man pumping a bellow."
AFTER:  "A man pumping a bellow. His hands. His choice."
```

**"No longer X. Y." frame — HARDENED (Ch.21-22, user audit):**
The user flagged two classic violations that slipped through pre-critic. Both follow the pattern: negate what something ISN'T, then state what it IS. The negation frame always softens the affirmation.

```
Ch.22 BEFORE (user-flagged):
  "The gesture was not trust. It was the recognition..."

Ch.22 AFTER (user-specified fix):
  "The gesture was recognition. A man carrying information..."

Ch.21 BEFORE (user-flagged):
  "The cold was not unbearable. The cold was real."

Ch.21 AFTER (user-specified fix):
  "The cold was real. And reality, he had learned..."
```

**Hardened detection:** After grep, manually scan each hit for "[Subject] was not [negated quality]. [Subject] was [positive quality]." If negated quality is sensory/emotional/abstract → cut the negation frame, keep the affirmation. If the line works BETTER without the negation → cut it.

**Philosophical/abstraction negation (NEW — Ch.17 field-tested):**
This pattern escapes the standard anti-thetical grep because it's not sensory — it's a rhetorical structure that negates one abstract question/statement and posits another. Reads as the same authorial tic.

**Detection:** `grep -n "question was not\|problem was not\|issue was not\|truth was not" chapter.md`

**Rule:** Any sentence structured as "The X was not Y. The X was Z." where X is an abstraction must be rephrased to direct affirmative.

```
BEFORE: "The question was not whether the truth would destroy him. The question was what a man did with the truth..."
AFTER:  "The truth would destroy him. The only remaining question was what a man did with the truth..."
```

**Internal indecision negation (NEW — Ch.20 field-tested):**
A character's internal state rendered as rhythmic negations: "She did not know if she would go... She did not know if she could leave... She did not know if..."

**Detection:** `grep -n "did not know if" chapter.md` — if 2+ hits within 3 lines, rewrite to externalized present-tense affirmatives.

```

---

## 3. THESIS GUILLOTINE SCAN (95% RULE)

**Search for:**
- "She realized that..." / "He understood then that..."
- Numbered realizations ("He understood three things. First: ... Second: ...")
- End-of-section summaries ("Without the equations, he was just a man.")
- Somatic explanations ("Some things the body knew before the mind caught up.")
- Self-rationalizations ("She told herself it was protocol...")

**The single-sentence test:** Delete the sentence. If the scene loses nothing the reader hadn't already absorbed through action/sensory/subtext → CUT IT.

---

## 4. PHRASE REPETITION SCAN (MAX 2x PER CHAPTER)

**Rule:** Any distinctive resonant phrase (3+ words, metaphorical or thematic) may appear at most TWICE: once in the epigraph, once in the body. If count > 2, cut the weakest instances.

**Ch.15 example:** "mercy and a countdown" appeared 4x (epigraph + 3 body). Fixed by cutting all internal instances, leaving only the epigraph. Chapter gained power from the subtraction.

**Grep for distinctive phrases.** Count. If > 2, keep epigraph + strongest body hit. Cut the rest.

---

## 5. METAPHOR DUPLICATION SCAN (NEW — Ch.19)

**Rule:** Any distinctive 3+ word metaphorical construction applied to more than one character in the same chapter must be cut from one of them. Each character's experience is distinct; the metaphor should be too.

**Detection:** Scan for distinctive metaphorical phrases. If the same phrase describes two different characters, keep the stronger match, rephrase the other.

**Ch.19 example:** "peripheral device" used for both Idris and Theron. Idris kept (literally was a peripheral for the Engine). Theron rephrased to "node" (closer to his experience in the Chorus).

---

## 6. OVER-EXPLANATION SCAN (NEW — Ch.17, Ch.18)

**Rule:** After any sentence that qualifies as a potential gut-punch (short, specific, devastating), the next paragraph must introduce NEW information. If it restates or softens the gut-punch, CUT IT.

**Detection:** Identify gut-punch candidates (short declarative sentences carrying thematic weight). Read the next paragraph. If it says the same thing in different words, cut the next paragraph.

**Ch.17 example:** "She was optimizing the Directorate's funeral" was followed by 3 lines restating the epigraph's architect/technician distinction. Cut the restatement.

### 6a. Sensory Repetition + Itemized List (Ch.22)

**Pattern:** Word repeated 3+ times as predicate across consecutive sentences, then itemized list. "The mud grounded him. The cold grounded him. The pressure... grounded him. Only the physical world: mud, cold, pressure..."

**Action:** Cut to strongest follow-through image. The grounding is already shown.

### 6b. POV Gaze Recap (Ch.22)

**Pattern:** "She looked at [Name] — [multi-line biography]." "He looked at [Name] — [backstory known to reader]."

**Action:** Replace with "She looked at each of them in turn." Biographies known. Somatic action preserved.

### 6c. Thesis Framing in Dialogue (Ch.23)

**Pattern:** "The difference between us: [thesis]" — dialogue that names its own subtext.

**Action:** Remove frame. Let parallel structure carry weight.

### 6d. Closing BFS Cluster (Ch.23)

**Pattern:** After designated BFS, chapter's final 100 words contain additional short standalone devastating sentences competing for BFS status.

**Action:** Integrate into compound sentences with sensory prose. Only the designated BFS stands alone.

### 6e. Redundant Atmospheric Description (Ch.25)

**Pattern:** Same sensory detail described near-verbatim in two different scenes. "Basalt dust coated every surface — fine as ground bone, cold as the deep earth..." (Scene 1) then "Basalt dust coated every surface and tongue" (Scene 2).

**Action:** Keep the stronger/earlier instance. Cut the repetition. Scene-setting is earned once.

### 6f. Weak Generic Closing Line (Ch.25)

**Pattern:** Chapter ends on passive, non-sensory sentence: "The dark pressed in." / "The silence held." / "The weight was unbearable."

**Action:** Close on a somatic anchor — a specific character's physical state, a sensory detail from the environment. Trust the reader to feel the dark without being told the dark is pressing.

---

## 7. THERAPY-SPEAK SCAN

**Banned:** "processing trauma," "holding space," "boundaries," "emotional labor," "toxic," "safe space," any modern psychological jargon.

**Permitted (if established in character model):** "self-soothing" (Kaelen's somatic tell), "calibrating" (Kaelen's framework), era-appropriate terms.

---

## 8. CHAPTER FORMAT CHECK (NEW — Ch.16-19)

**Verify:** Line 1 must be `# CHAPTER X: TITLE`. No markdown headings (`## `) between scenes — only `***` dividers. Epigraph format: italicized quote + em-dash attribution.

**Ch.16-18 example:** Three chapters submitted without `# CHAPTER X: TITLE` heading. Caught by user audit. Fixed by prepending heading to each file.

---

## 9. CONTINUITY (QUICK PASS)

- Scar: right forearm, DEAD since Ch.08 — cold, numb. Never active.
- Claw-hand: left hand. Currently: hybrid marionette → fully human post-Ch.30.
- Timeline: hours, not days/weeks. Same day as Calibrator's death.
- Data provenance: what each character knows and when they learned it.
- Deaths: only Calibrator, caravan, 1 child (named). Thousands off-page from Severance. Post-Ch.23: ~12 Directorate battalion. Post-Ch.28: Directorate surface army (off-page mass death).
- Kaelen's loupe: shattered (Ch.08). Right hand: burned (Ch.11), dead/rigid (Ch.26-29), ordinary dead scar tissue (Ch.30).
- Idris's palsy: ceased (Ch.12). Both hands steady.
- Calculus Engine: dead (Ch.12). 60 Hz hum gone. Post-Ch.30: hum permanently killed, entire Resonance field collapsed.
- Post-Hypnotic Trigger: silenced (Ch.12). Word "trigger" banned from narrative body. Post-Ch.30: concept dead.
- **Ozone anchor: EXTINGUISHED post-Ch.30.** Never fire in Act III. Replaced by mundane sensory language.
- **Argent threads/crystalline lattice: DESTROYED post-Ch.30.** Never reference as active. Kaelen carries dead scar tissue only.
- **Resonance field: COLLAPSED post-Ch.30.** No Resonance technology functions. World is mundane.
- **Trigger WORD:** grep for "trigger" in narrative prose (exclude epigraph). If found → replace with "conduit," "bridge," "circuit." The word is tainted after Ch.12.

---

## 10. ANCHOR CHECK

- Designated anchors fired? (Ozone in Scene X, Pressure in Scene Y, etc.)
- Scar NOT referenced? (DEAD)
- Post-Hypnotic Trigger NOT active? Word "trigger" absent from narrative body?
- Necrosis correctly positioned? (collarbone → carotid → threatening heart → breached heart → silver scar over heart)
- Artifact state correct? (dormant/waking/answering/piloting → transferred to Kaelen → interface complete → CRUMBLED TO DUST post-Ch.30)
- **Post-Ch.30 Act III verification:** Ozone anchor EXTINGUISHED forever. 60Hz hum KILLED permanently. Argent threads DISSOLVED to dead scar tissue. Prose register shifted to mundane reality. Resonance field COLLAPSED — no Resonance technology functions.
