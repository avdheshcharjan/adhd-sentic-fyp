# Phase 2: Test Data Preparation

## Context

Read `00-common.md` first. Phase 1 smoke tests must pass before starting this phase.

**Goal:** Create all test datasets needed by the benchmark (Phase 3) and accuracy (Phase 4) evaluations. All data files go in `evaluation/data/`.

---

## Task 2.1: Window Title Dataset (200 titles)

**File:** `evaluation/data/window_titles_200.json`

Create a JSON array of 200 realistic window titles with ground truth labels. This dataset serves dual purpose: benchmark throughput testing AND accuracy evaluation.

**Distribution:** ~80 productive, ~60 neutral, ~60 distracting

**Format:**
```json
[
  {
    "id": "prod_001",
    "title": "Visual Studio Code - main.py — adhd-sentic-fyp",
    "label": "productive",
    "category": "ide"
  },
  {
    "id": "dist_001",
    "title": "Reddit - r/gaming: What's the best RPG of 2026?",
    "label": "distracting",
    "category": "social_media"
  }
]
```

**Required coverage (include at least 5 titles per subcategory):**

Productive (~80):
- IDEs: VS Code, PyCharm, Xcode, IntelliJ, Cursor, Vim/Neovim
- Documents: Google Docs, Word, Preview PDF, Notion, Overleaf
- Browsers with work URLs: github.com, stackoverflow.com, docs.python.org, arxiv.org
- Terminal/CLI tools: Terminal, iTerm2, Warp
- Research: Zotero, Mendeley, Google Scholar
- Design: Figma, Sketch
- Project management: Linear, Jira, Trello

Neutral (~60):
- System utilities: Finder, Calculator, System Settings, Activity Monitor
- Email: Mail app, Gmail (could be work or personal)
- Calendar: Calendar app, Google Calendar
- Messaging (work-adjacent): Slack, Microsoft Teams, Zoom
- File management: Dropbox, Google Drive
- Browsers with ambiguous URLs: medium.com, wikipedia.org
- Music (background): Spotify, Apple Music (playing focus music vs browsing)

Distracting (~60):
- Social media: Reddit, Twitter/X, Instagram, TikTok, Facebook
- Entertainment video: YouTube (non-educational), Netflix, Twitch
- Gaming: Steam, specific game names
- Shopping: Amazon, Shopee, Lazada
- News/browsing: news sites, BuzzFeed
- Dating: Tinder, Bumble

**Edge cases (include at least 10 intentionally ambiguous titles):**
- "YouTube - MIT OpenCourseWare Lecture 5" (educational YouTube — productive)
- "Chrome - ChatGPT" (could be productive or distracting)
- "Discord - FYP Project Server" (productive Discord)
- "Reddit - r/MachineLearning: New paper on..." (productive Reddit)
- "Spotify - Focus Playlist" (neutral/productive)
- "Safari - twitter.com/elikiowa (AI researcher)" (ambiguous Twitter)
- "WhatsApp Web" (ambiguous)
- "Chrome - netflix.com/browse" (distracting even if just browsing)
- "Preview - memes.pdf" (distracting in Preview)
- "Terminal - ssh production-server" (productive terminal)

---

## Task 2.2: Coaching Test Prompts (30 prompts)

**File:** `evaluation/data/coaching_test_prompts.json`

30 ADHD user messages across 6 scenarios (5 per scenario). These must sound like real people, not clinical descriptions. Vary length, emotional intensity, and specificity.

**Format:**
```json
[
  {
    "id": "overwhelm_01",
    "scenario": "overwhelm",
    "message": "I have 6 things due this week and I haven't started any of them. I just keep opening and closing the same tabs.",
    "expected_emotion": "overwhelmed",
    "expected_hourglass": {
      "pleasantness": "low",
      "attention": "low",
      "sensitivity": "high",
      "aptitude": "low"
    }
  }
]
```

**Scenarios (5 prompts each):**

1. **Overwhelm / can't start** — paralysis, too many tasks, shutdown mode
   - Vary: some express frustration, some express numbness, some ask for help explicitly, some just vent
   - Example: "I literally cannot make myself open this document. I've been sitting here for an hour doing nothing."

2. **Distracted / can't focus** — task-switching, rabbit holes, phone checking
   - Vary: some are self-aware, some blame external factors, some are confused about why
   - Example: "I've opened YouTube 'just for a second' four times in the last 30 minutes and I don't know how to stop"

3. **Emotional dysregulation / frustrated** — anger, rejection sensitivity, meltdown
   - Vary: some are angry, some are sad, some feel shame about their reaction
   - Example: "My supervisor gave me feedback and I know it was fine but I feel like I'm going to cry and I can't calm down"

4. **Time blindness / missed deadline** — lost track of time, late, panic
   - Vary: some are panicking, some resigned, some looking for recovery strategies
   - Example: "It's 2am and the assignment is due at 9am and I'm only on the introduction. How did I let this happen again"

5. **Task decomposition needed** — big project, don't know where to start
   - Vary: some have vague ideas, some are completely blank, some have tried and failed to plan
   - Example: "I need to write a 3000 word essay. I've written the title. That's it. I don't know what comes next."

6. **Positive / momentum building** — good day, want to maintain it, celebrating small wins
   - Vary: some are cautiously optimistic, some excited, some worried they'll lose the momentum
   - Example: "I actually finished two whole tasks before lunch! I don't want to jinx it but what should I do next?"

---

## Task 2.3: Emotion Test Sentences (50 sentences)

**File:** `evaluation/data/emotion_test_sentences.json`

50 ADHD-relevant sentences with expected emotion labels and Hourglass dimension directions. Used to evaluate SenticNet accuracy.

**Format:**
```json
[
  {
    "id": "emo_001",
    "sentence": "I finally finished the hardest section of my report!",
    "expected_emotion": "joyful",
    "expected_hourglass": {
      "pleasantness": "high",
      "attention": "high",
      "sensitivity": "low",
      "aptitude": "high"
    }
  }
]
```

**Distribution across 6 emotion categories (~8 each):**

- **joyful** (8): task completion, unexpected productivity, positive feedback, small wins
- **focused** (8): deep work descriptions, flow state, sustained concentration
- **frustrated** (9): repeated failures, broken tools, interrupted focus, can't concentrate
- **anxious** (9): deadline pressure, uncertainty, social situations, fear of failure
- **disengaged** (8): boredom, apathy, going through motions, no motivation
- **overwhelmed** (8): too many tasks, sensory overload, emotional flooding, shutdown

Each sentence should be something a real ADHD person would say or type to a coaching assistant.

---

## Task 2.4: Memory Test Profiles (20 profiles)

**File:** `evaluation/data/memory_test_profiles.json`

20 synthetic user profiles for evaluating Mem0 retrieval quality.

**Format:**
```json
[
  {
    "profile_id": "user_001",
    "description": "Graduate student in CS, combined ADHD, struggles with long reading tasks",
    "memories": [
      {
        "memory_id": "mem_001",
        "content": "User prefers breaking reading into 15-minute chunks with 5-minute breaks",
        "metadata": {"topic": "reading_strategies", "emotion": "neutral"}
      },
      {
        "memory_id": "mem_002",
        "content": "User gets most focused work done between 10am and 1pm",
        "metadata": {"topic": "peak_hours", "emotion": "focused"}
      }
    ],
    "test_queries": [
      {
        "query": "How should I approach this long paper I need to read?",
        "expected_memory_id": "mem_001"
      },
      {
        "query": "When is the best time for me to work on hard problems?",
        "expected_memory_id": "mem_002"
      }
    ]
  }
]
```

Each profile should have:
- 10 stored memories covering different topics (strategies, preferences, emotional patterns, work habits, medication notes, social contexts)
- 5 test queries, each with an expected matching memory ID
- Realistic variety: some queries are straightforward, some require semantic understanding

---

## Task 2.5: ADHD Personas (5 personas)

**File:** `evaluation/data/adhd_personas.json`

The 5 ADHD personas for LLM simulation. These are used by the persona runner in `rui-mao-feedback-code-changes.md` (Change 3).

**Format:**
```json
[
  {
    "persona_id": "persona_01",
    "name": "Alex",
    "age": 22,
    "gender": "male",
    "occupation": "final-year computer science student",
    "adhd_subtype": "combined",
    "severity": "moderate",
    "context": "Struggling to complete FYP while managing coursework. Recently diagnosed, still adjusting to medication.",
    "emotional_tendency": "oscillates between hyperfocus excitement and frustration when interrupted",
    "conversation_starters": [
      "I've been staring at my code for an hour and nothing makes sense anymore",
      "My medication is making me feel weird today, kind of jittery but still can't focus"
    ]
  }
]
```

**5 personas covering:**

1. **Alex** — 22M, CS student, combined type, moderate severity, recently diagnosed
2. **Priya** — 28F, marketing professional, inattentive type, mild severity, long-diagnosed, uses established coping strategies that sometimes fail
3. **Jordan** — 35, freelance designer, hyperactive-impulsive type, severe, unmedicated by choice, high emotional reactivity
4. **Maya** — 19F, first-year university student, inattentive type, moderate, undiagnosed (suspects ADHD), anxious about academic performance
5. **Sam** — 41M, software engineer, combined type, moderate, medicated, manages well most days but crashes during high-stress periods

---

## Completion Criteria

All 5 files exist in `evaluation/data/` and are valid JSON:

```bash
python -c "
import json, os
files = ['window_titles_200.json', 'coaching_test_prompts.json', 
         'emotion_test_sentences.json', 'memory_test_profiles.json', 'adhd_personas.json']
for f in files:
    path = os.path.join('evaluation/data', f)
    data = json.load(open(path))
    print(f'{f}: {len(data)} items ✓')
"
```

Expected output:
```
window_titles_200.json: 200 items ✓
coaching_test_prompts.json: 30 items ✓
emotion_test_sentences.json: 50 items ✓
memory_test_profiles.json: 20 items ✓
adhd_personas.json: 5 items ✓
```

Also create `evaluation/__init__.py`, `evaluation/data/.gitkeep`, `evaluation/results/.gitkeep`, `evaluation/benchmarks/__init__.py`, `evaluation/accuracy/__init__.py` so the package structure is ready for Phases 3–5.
