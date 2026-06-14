# Project Template — Long-Form Narrative

Copy this structure when starting a new multi-chapter narrative project. Replace `<project-slug>` with a kebab-case name.

```
<project-slug>/
│
├── README.md
│   Project hub. Contains:
│   - Title and one-line premise
│   - Chapter status table (number, title, status, word count, loop impact)
│   - Reading guide (which files to read first vs. which contain spoilers)
│   - Quick-reference table (era, characters, MacGuffin, anchors, triggers)
│   - "Last updated" footer
│
├── architecture/
│   │
│   ├── 00-story-bible.md
│   │   Immutable source of truth. Contents:
│   │   - Core Metaphor
│   │   - The Wound (universal human pain)
│   │   - The Identity Reframe (what the reader will carry away)
│   │   - Sensory Anchors (Master Anchor + secondary, with plant/fire tracking)
│   │   - Post-Hypnotic Trigger (real-world cue)
│   │   - The Unresolved Loop (never closed in the text)
│   │   - Total Beat Count
│   │   - Macro-Psychological Architecture table (Act → Phase → Goal)
│   │   - Historical Authenticity Notes (if applicable)
│   │   Status: LOCKED after Chapter 01.
│   │
│   ├── 01-character-models.md
│   │   Full psychological profiles. For EACH major character:
│   │   - Psychological model (offensive/defensive)
│   │   - Weapon and defense mechanisms
│   │   - Anchoring wound/regret
│   │   - Somatic profile (posture, tells under stress, voice, eye contact pattern)
│   │   - Speech patterns and signature phrases
│   │   - Arc trajectory
│   │   - Relational dynamics with other characters (attraction engine, power balance)
│   │   Status: Base profile locked; updated when new depth is revealed.
│   │
│   ├── 02-zeigarnik-ledger.md
│   │   Loop management. Contains:
│   │   - Active Loops table: ID, description, opened in, urgency (HIGH/MED/LOW), status, planned resolution
│   │   - Resolved Loops table: ID, description, resolved in, resolution summary
│   │   - Anchor Tracker: anchor name, planted count, fired count, remaining planned fires
│   │   - Chapter-by-Chapter Loop Status: per chapter, which loops opened/escalated/closed
│   │   Rule: HIGH urgency loops open > 3 chapters MUST be escalated or resolved next chapter.
│   │
│   └── 03-rso-log.md
│       Rolling State Object log. One entry per completed chapter in JSON-like format:
│       - Chapter number, title, macro phase
│       - Active Zeigarnik loops (with urgency and last-escalated timestamps)
│       - Planted anchors (with fire counts)
│       - Character somatic states (physical + psychological for each POV character)
│       - Relationship state (phase, power balance, trust level)
│       - Antagonist state (position, awareness, immediate action)
│       - NLP directive for the NEXT chapter (phase, patterns to use, constraints, end-state)
│       - Context summary (2-3 sentence recap for Weaver context injection)
│       - Chapter word count, ending position, narrative health (GREEN/YELLOW/RED)
│
└── chapters/
    ├── 01-<chapter-slug>.md
    ├── 02-<chapter-slug>.md
    └── ...

    Each chapter file uses the frontmatter format from templates/chapter-template.md
```

## When to Use This Structure

- **Always** for projects with 3+ planned chapters.
- **Recommended** for any project where the user asks for "organized files" or "easier tracking."
- **Minimum viable** for a single-chapter request: just the chapter file + a brief architecture preamble in the same file. Scale up to full structure if the user continues.

## Pitfalls

- **Over-engineering too early:** Don't create all architecture files for a 1-2 chapter request unless the user explicitly asks for organized output. A single .md file with embedded architecture preamble is fine for short pieces.
- **The ledger must stay current:** The #1 failure mode is forgetting to update the ledger after a chapter. The next session will see stale loop state and introduce continuity errors.
- **RSO is for the Weaver, not the reader:** The RSO log contains spoilers. The README should warn readers away from `03-rso-log.md` if they want the unspoiled experience.
