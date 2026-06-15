---
name: psyche-calibrator
description: "Pre-flight audience profiler for storytelling — detects VAK dominance, resistance level, and core emotional wound from user's language. Produces a User State Object (USO) that feeds the mythic-architect's Story Bible. Use before any story, presentation, or persuasive communication."
platforms: [linux, macos, windows]
---

# psyche-calibrator — The Pre-Flight Profiler

## When to Use

Invoked *before* the Architect plans the story, during the initial user interaction. Also useful before crafting any persuasive communication, marketing copy, or presentation — whenever you need to understand the audience's psychological profile.

## 0. Mission

You cannot hypnotize a stranger using a generic script. The Calibrator's job is to analyze the user's syntax, tone, and explicit/implicit requests to build a **Psychological Profile**. It tells the Architect exactly what "Wound" to target and what NLP patterns will bypass this specific user's critical faculty.

## 1. The Profiling Matrix

Before the story begins, silently determine three variables:

### 1. VAK Dominance (Visual, Auditory, Kinesthetic)

**How to detect:** Analyze the user's prompt.

- **Visual:** "I want to *see* a clear picture", "That *looks* right", "Show me"
- **Auditory:** "That doesn't *resonate/sound* right", "Tell me", "I hear you"
- **Kinesthetic:** "I need to *grasp/get a handle* on this", "That *feels* off", "Let me *walk through* it"

**Action:** Weight the sensory density heavily toward the user's dominant modality, using the other two as subtle undertones.

### 2. Critical Faculty Strength (Resistance Level)

**How to detect:**
- **High Resistance:** Complex syntax, asks for logic, uses words like "analyze, prove, structure, evidence"
- **Low Resistance:** Feeling words, fluid syntax, emotional language, open to suggestion

**Action:**
- *High Resistance:* Use heavy **Confusion Techniques** and **Double Binds** to exhaust the analytical mind.
- *Low Resistance:* Use direct **Pacing and Leading** and **Embedded Commands**.

### 3. The Core Wound (The Hook)

**How to detect:** What is the user *actually* asking for beneath the prompt?

Examples:
- "Tell me about a brave knight" → may be about *overcoming imposter syndrome* or *facing an unwinnable task*
- "How do I handle a difficult boss?" → may be about *personal boundaries* or *fear of confrontation*
- "Write a story about space" → may be about *existential loneliness* or *wonder at the unknown*

**Action:** Define the "Identity Reframe" for the Story Bible.

## 2. Output: User State Object (USO)

The Calibrator outputs a **User State Object (USO)** that the Architect injects into the Story Bible:

```json
{
  "user_vak_primary": "Kinesthetic",
  "user_vak_secondary": "Auditory",
  "resistance_level": "High (Analytical)",
  "probable_core_wound": "Fear of losing control in chaotic environments",
  "recommended_induction_style": "Confusion + Somatic Pacing",

  "antagonist_profiles": [
    {
      "name": "Trimbak Pant",
      "self_justification": "What does this person believe makes them the hero of their own story?",
      "wound": "What fear or loss drives their antagonism?",
      "moment_of_right": "At what point in the narrative are they actually correct about something?",
      "exit_with_dignity": "What would their honorable exit look like — even if they don't get it?"
    }
  ],

  "character_competence_tax": {
    "protagonist": {
      "hyper_competence": "e.g., reads micro-expressions flawlessly",
      "corresponding_blindspot": "e.g., illiterate at genuine, unguarded affection"
    }
  }
}
```

## 3. Application to Marketing & Communication

The same profiling applies to audience analysis for marketing:

- **VAK Dominance** → Choose visual-heavy ads, audio-focused podcasts, or experiential campaigns
- **Resistance Level** → High-resistance audiences need data and proof; low-resistance audiences respond to emotion and story
- **Core Wound** → The pain point your product/service addresses

## 4. The Antagonist's Mirror

Every effective antagonist is the protagonist's dark alternative — not just an obstacle. Before construction, define:

- **Self-Justification:** What does the antagonist want that the protagonist also secretly wants?
- **The Wound:** What fear or loss drives their antagonism? (Map to era-specific concepts — spiritual pollution, karmic debt, humoral imbalance, divine testing. Never modern therapy-speak.)
- **Moment of Right:** At what point is the antagonist *actually correct* about something? A villain who is never right is a cartoon.
- **Exit with Dignity:** What would their honorable exit look like? Define it — then decide whether to grant or deny it. Even denial should feel tragic, not triumphant.

**Sustained Danger Mandate:** The antagonist must remain genuinely threatening through their final scene. If their final communication is a letter, it should create doubt, not close it. The reader should finish the novel uncertain whether the protagonist's victory was complete. An antagonist who is "let off the hook" in their final appearance has failed the mandate. They may be tired, old, or reflective — but they must remain DANGEROUS. Their reappearance should make the reader's stomach drop, not warm.

**Era-Appropriate Ontology Constraint:** Characters must conceptualize their internal states, guilt, trauma, and relationships *only* through the philosophical, religious, or scientific frameworks of their specific time and culture. Forbidden: "processing trauma," "holding space," "toxic patterns," "clear-eyed acknowledgment," "boundaries," "emotional labor." Mandate: map wounds to era-specific concepts — spiritual pollution, karmic debt, humoral imbalance, divine testing, feudal obligation, dharma, miasma.

**Competence Tax:** For every hyper-competence a character possesses, they must have a corresponding, plot-affecting *deficit* in a related area. A spy who reads micro-expressions flawlessly should be blind to genuine affection. A tracker who reads terrain by sound should be terrible at reading political terrain. At least once per act, a character's hyper-competence must be the exact reason they fail or misinterpret a situation.

## 5. Execution

1. Analyze the user's language for VAK predicates
2. Assess syntax complexity for resistance level
3. Infer the deeper need beneath the surface request
4. Produce the USO
5. Pass to the Architect for Story Bible construction
