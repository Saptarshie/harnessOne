---
name: storytelling-critic
description: >
  A rigorous self-reflection and criticism framework for evaluating creative writing.
  Use when you have generated a story, novel chapter, or narrative fiction and need
  to critically evaluate it — BEFORE declaring it done, BEFORE revising, or when
  asked whether it is good enough. Also trigger when comparing two versions of a
  story or evaluating whether a revision improved or worsened the work. Always use
  a SEPARATE agent from the writing agent to avoid self-grading bias.
---

# Storytelling Self-Reflection & Critic Skill

## Core Philosophy

The purpose of this skill is to evaluate narrative fiction the way a rigorous, honest
editor would — not the way a cheerleader would, and not the way a critic invested in
their own previous notes would.

**The three failure modes this skill exists to prevent:**

1. **Confirmation bias in revision** — evaluating a revised draft by how well it
   addressed prior feedback rather than whether it is actually better. "Addressed my
   notes" is not the same as "better book."

2. **Cinematic vs. true** — confusing improvements that make a story more gripping
   with improvements that make it more honest and lasting.

3. **Explaining vs. trusting** — the tendency to state what a scene has already shown.
   If the prose names an emotion after showing it, the naming destroys the showing.

---

## The Evaluation Protocol

Run this protocol in order. Do not skip sections. Do not soften findings.

### STEP 0 — The Blind Test Integrity Check

Before evaluating any blind test results (whether from an external evaluator or a
prior agent run), verify that the evaluator actually read the version they claim to
have read. Blind test corruption is common: evaluators conflate features from
different versions, credit "Version B" with an opening that Version A actually has,
or score a phantom version that combines the best of both drafts.

**The check:**
1. Identify the evaluator's strongest praise. Quote it.
2. Locate that praised element in the draft under evaluation. Does it exist?
3. If it does not exist — the blind test is corrupted. Discard the contaminated
   scores. Re-run the evaluation on the actual draft.
4. If the contamination is partial (some praise maps to the draft, some doesn't),
   note which scores are unreliable and downgrade confidence accordingly.

This step prevented V4 from being evaluated against a phantom — the V3 blind test
had credited V3 with V2's sensory opening, inflating scores by ~0.5 points.

### STEP 1 — The Blind Read Test

Ask: *If I encountered this story cold, with no knowledge of its construction or
revision history — would I keep reading?*

Identify the first moment where the contract between writer and reader weakens.
This is almost always one of:
- The opening fails to install a specific, irreversible question
- A character makes a decision the plot requires but the character does not
- The prose explains something the scene already showed
- The stakes are told rather than felt

**Output:** Name the first potential stopping point. Name what broke the contract.

### STEP 2 — The Wound Test

- **What is the wound?** State in one sentence that could not describe any other story.
- **Is the wound specific or generic?** Generic wounds produce forgettable fiction.
- **Is the wound pressed hard enough?** The reader should reach a point where they
  cannot look away.
- **Does the resolution honor the wound?** A wound neatly healed by the ending was
  never real. The best endings change the character's relationship to carrying it.

**Output:** State the wound. Rate its specificity. Identify where pressed hardest.
Identify whether the ending honors or domesticates it.

### STEP 3 — The Stake Inventory

- **Global stakes** — What is threatened at the macro level?
- **Personal stakes** — What does the protagonist stand to lose that cannot be replaced?
- **Moral stakes** — What does the protagonist have to become? This is the most
  important tier.

**Embodiment check:** Are global stakes embodied in at least one specific, named,
humanized instance? A child's wooden toy in the mud after cavalry comes is stakes-embodiment.

**Output:** Map all three tiers. Flag any abstract tier. Identify the single most
specific stake and assess whether it carries enough weight.

### STEP 4 — The Antagonist Audit

- **Is the antagonist right about something?** The most dangerous antagonists hold a
  position the reader almost agrees with.
- **Is the antagonist defanged at the end?** If the final scene provides warmth or
  closure — the novel has betrayed its own threat.
- **Does the antagonist's logic survive the ending?** The best antagonists win
  something even in defeat.

**Output:** State the antagonist's core argument in one sentence. Assess whether it
survives the ending. Flag if the antagonist is defanged.

### STEP 5 — The Subtext Audit

Flag every instance where the prose:
- States an emotional conclusion a scene has already dramatized
- Names a character's psychological state rather than embodying it
- Uses an observation sentence at the end of a scene to ensure understanding
- Has a character articulate their own internal conflict in dialogue

**Severity:** Minor (redundant — cut), Moderate (replaces showing — rewrite),
Critical (reveals distrust of reader — structural issue)

**Output:** List the top 3 subtext violations by severity. Quote the offending line.
State what the scene had already shown.

### STEP 6 — The Pacing Architecture Review

Map the novel at scene level. For each scene: function (establish/escalate/complicate/
breathe/pivot/resolve), emotional register, whether it advances plot AND character.

**Red flags:**
- Three or more consecutive scenes without permanent cost to any character
- A breath beat with no new information or character movement
- Midpoint lacks a genuine reversal
- Ending resolves at a lower pitch than preceding scene

**Output:** Name the dead zone (if any). Name the scene of highest velocity.

### STEP 7 — The Revision Trap Check (revised drafts only)

- **Prescription trap:** Did revision add elements that address prior feedback without
  integrating organically? Additions that feel like "fixes."
- **Opening regression:** Revision almost always weakens the opening. Does the revised
  opening start LATER in action, or with reflection/context that the original didn't have?
- **Redundant revelation:** Information delivered twice (once through action, once through
  statement). Cut the second instance.
- **Over-layering:** Did the revision make the story leaner or heavier? Complexity serves
  depth only when tightly integrated.

**Output:** For each trap triggered, name the specific passage. Recommend: cut,
integrate, or restore original.

### STEP 8 — The Memorability Threshold

- **What question does this story leave unresolved — permanently?** A human question
  the reader will carry into their own life.
- **Is there a scene the reader cannot forget?** Not the most dramatic — the most
  quietly unbearable.
- **Does the ending give something to carry or something to put down?** Satisfying
  endings are put down. Haunting endings are carried.

**The unforgettability test:** Could this story's central moral question be asked about
the reader's own life? If yes, and the story refuses to answer cleanly — the story has
a chance at being unforgettable.

**Output:** State the unresolved human question. Identify the single most unforgettable
scene or image. Render a verdict: *Satisfying*, *Memorable*, or *Potentially Unforgettable*.

---

## Output Format

```
## STORYTELLING CRITIQUE

### The Contract (Step 1)
[First stopping point and what broke it]

### The Wound (Step 2)
[Wound | Specificity | Where pressed | Ending verdict]

### Stakes (Step 3)
[Global / Personal / Moral | Embodiment check]

### Antagonist (Step 4)
[Core argument | Survival assessment | Defanging flag]

### Subtext Violations (Step 5)
[Top 3 violations, quoted, with severity]

### Pacing (Step 6)
[Dead zone | Highest velocity scene | Ending pitch]

### Revision Traps (Step 7 — only if revised draft)
[Each trap triggered, passage named, recommendation]

### Memorability Verdict (Step 8)
[Unresolved question | Most unforgettable element | Final rating]

### PRIORITY ACTIONS
[Maximum 3. Ordered by impact. Specific, surgical.]
```

---

## Critical Reminders

**Do not soften the critique.** The work does not have feelings. The writer does —
but dishonest critique is more damaging than honest critique.

**Do not mistake length for depth.** A shorter story that presses one wound hard is
more memorable than a longer story that handles many things well.

**Do not confuse investment in prior feedback with evidence of improvement.** If you
suggested an addition and it made things worse — say so. Update your prescription.

**The blind test overrides everything.** Craft invisible to a cold reader does not exist.

## Reference

See `references/v3-to-v4-case-study.md` for a worked example of all three revision
traps firing (opening regression, redundant revelation, prescription trap) and the
surgical revision that resolved them in ~300 words.
