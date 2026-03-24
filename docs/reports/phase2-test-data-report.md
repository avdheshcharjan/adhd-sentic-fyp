---
title: Phase 2 — Test Data Preparation Report
date: 03/24/2026
original-plan: docs/testing-benchmarking/02-phase2-test-data.md
---

# Overview

Phase 2 of the ADHD Second Brain evaluation pipeline created all test datasets needed for the benchmark (Phase 3) and accuracy (Phase 4) evaluations. Five JSON data files were generated covering window title classification, coaching prompt scenarios, emotion analysis, memory retrieval profiles, and ADHD personas. All files are located in `backend/evaluation/data/` and conform to the Phase 2 specification. The evaluation package structure (`evaluation/benchmarks/`, `evaluation/accuracy/`, `evaluation/results/`) was also prepared for subsequent phases.

---

## Files Created

| File | Location | Items | Purpose |
|------|----------|-------|---------|
| `window_titles_200.json` | `evaluation/data/` | 200 | Classification benchmark + accuracy evaluation |
| `coaching_test_prompts.json` | `evaluation/data/` | 30 | LLM coaching quality evaluation |
| `emotion_test_sentences.json` | `evaluation/data/` | 50 | SenticNet accuracy evaluation |
| `memory_test_profiles.json` | `evaluation/data/` | 20 | Mem0 memory retrieval quality evaluation |
| `adhd_personas.json` | `evaluation/data/` | 5 | LLM persona simulation for persona runner |
| `__init__.py` | `evaluation/benchmarks/` | — | Package initialization for benchmarks module |
| `__init__.py` | `evaluation/accuracy/` | — | Package initialization for accuracy module |
| `.gitkeep` | `evaluation/data/` | — | Directory placeholder for git |
| `.gitkeep` | `evaluation/results/` | — | Directory placeholder for results output |

---

## Dataset 1: Window Title Classification Dataset

**File:** `evaluation/data/window_titles_200.json`
**Items:** 200 realistic macOS window titles with ground truth labels

### Design Rationale

The window title dataset serves dual purpose in the evaluation pipeline: (1) benchmark throughput testing of the 5-layer activity classifier and (2) accuracy evaluation of classification correctness. Window titles were crafted to reflect realistic macOS usage patterns including IDE titles, browser tabs with URLs, terminal sessions, and application names.

### Label Schema

A critical design decision was made regarding the labelling system. The Phase 2 specification used simplified `productive/neutral/distracting` labels, but the actual `ActivityClassifier` in `backend/services/activity_classifier.py` operates with a richer category taxonomy: `development`, `writing`, `research`, `communication`, `social_media`, `entertainment`, `news`, `shopping`, `design`, `productivity`, `finance`, `system`, `browser`, and `other`.

To bridge this gap, each entry carries **two label fields**:
- `label`: The classifier's actual category (e.g., `development`, `entertainment`)
- `productivity_label`: The simplified productivity assessment (`productive`, `neutral`, `distracting`)

This dual-labelling approach enables both fine-grained category accuracy testing and coarse productivity-level evaluation.

### Distribution

| Productivity Label | Count | Percentage |
|-------------------|-------|------------|
| Productive | 79 | 39.5% |
| Neutral | 62 | 31.0% |
| Distracting | 59 | 29.5% |

| Classifier Category | Count |
|---------------------|-------|
| development | 42 |
| entertainment | 34 |
| social_media | 20 |
| communication | 18 |
| productivity | 17 |
| research | 14 |
| system | 11 |
| writing | 9 |
| design | 8 |
| shopping | 7 |
| finance | 7 |
| news | 5 |
| other | 3 |

### Category Coverage

The dataset covers the following subcategories as specified:

**Productive (~79 items):**
- IDEs: VS Code, PyCharm, Xcode, IntelliJ, Cursor, Vim, Neovim, Sublime Text, Zed, Android Studio
- Documents: Google Docs, Microsoft Word, Notion, Overleaf, Pages, Preview, Obsidian, Grammarly
- Browsers with work URLs: github.com, stackoverflow.com, docs.python.org, arxiv.org, developer.apple.com, huggingface.co, kaggle.com, pypi.org, npmjs.com, devdocs.io, supabase.com, firebase.google.com
- Terminal/CLI: Terminal, iTerm2, Warp (various commands: pytest, docker, git, ssh, npm, python)
- Research: Google Scholar, PubMed, Semantic Scholar, ResearchGate, Nature, IEEE, ACM, ScienceDirect, JSTOR
- Design: Figma, Sketch, Adobe Photoshop, Canva
- Project management: Linear, Jira, Trello, Asana, ClickUp, Todoist, Things, TickTick

**Neutral (~62 items):**
- System utilities: Finder, Calculator, System Settings, Activity Monitor, Keychain Access, Disk Utility, App Store
- Email: Mail app, Gmail, Outlook, Yahoo Mail, ProtonMail
- Calendar: Calendar app, Google Calendar, Reminders
- Messaging: Slack, Microsoft Teams, Zoom, Messages, Telegram, FaceTime, WhatsApp Web, Google Meet
- File management: Google Drive, Dropbox, OneDrive
- Browsers with ambiguous URLs: medium.com, wikipedia.org, britannica.com, substack.com
- Music (background): Spotify (focus playlists, brown noise), Apple Music (lo-fi study beats), Music app
- Finance (utilities): Wise, PayPal, Revolut
- Media: VLC (lecture recordings), QuickTime Player

**Distracting (~59 items):**
- Social media: Reddit (r/gaming, r/memes, r/AskReddit, r/cats), Twitter/X, Instagram (feed + reels), TikTok, Facebook, Threads, Pinterest, Bluesky, Xiaohongshu, Lemon8
- Entertainment video: YouTube (MrBeast, PewDiePie, Shorts, compilations), Netflix, Twitch, Disney+, HBO Max, Dailymotion, 9anime, Crunchyroll, Bilibili, Vimeo
- Gaming: Steam (Counter-Strike 2), Valorant, Minecraft, League of Legends, Epic Games, Roblox
- Shopping: Amazon, Shopee, Lazada, Shein, Temu, Etsy, AliExpress
- News/browsing: CNN, BBC (Sports), Reuters (Markets), BuzzFeed, Mashable, IGN, GameSpot
- Finance (speculative): CoinMarketCap, Binance, Robinhood, TradingView

### Edge Cases

10 intentionally ambiguous titles were included to test classifier boundary handling:

| ID | Title | Classifier Label | True Productivity |
|----|-------|-----------------|-------------------|
| edge_001 | YouTube - MIT OpenCourseWare Lecture 5 | entertainment | productive |
| edge_002 | ChatGPT — Help me debug Python error | other | productive |
| edge_003 | Discord - FYP Project Server #code-review | communication | productive |
| edge_004 | Reddit - r/MachineLearning: ADHD paper | social_media | productive |
| edge_005 | Spotify - Focus Playlist Brain.fm | entertainment | neutral |
| edge_006 | twitter.com/ylecun — LLM reasoning post | social_media | neutral |
| edge_007 | WhatsApp Web — FYP Group Chat | communication | neutral |
| edge_008 | Netflix - Documentaries About the Brain | entertainment | distracting |
| edge_009 | Preview - vacation-photos-2025.pdf | design | distracting |
| edge_010 | Terminal - neofetch | development | neutral |

These edge cases are particularly important for evaluating the classifier's ability to handle context-dependent classifications where the app/domain category differs from the actual productivity intent.

---

## Dataset 2: Coaching Test Prompts

**File:** `evaluation/data/coaching_test_prompts.json`
**Items:** 30 ADHD user messages across 6 scenarios (5 per scenario)

### Design Rationale

These prompts simulate real messages that ADHD users would send to the coaching assistant. They were designed to test the full chat pipeline: SenticNet emotional analysis, LLM response generation, and the appropriateness of coaching suggestions. Each prompt includes expected emotion labels and Hourglass of Emotions dimension directions to enable automated evaluation.

### Scenario Distribution

| Scenario | Count | Description |
|----------|-------|-------------|
| overwhelm | 5 | Paralysis, too many tasks, shutdown mode |
| distracted | 5 | Task-switching, rabbit holes, phone checking |
| emotional_dysregulation | 5 | Anger, rejection sensitivity, shame |
| time_blindness | 5 | Lost track of time, late, panic |
| task_decomposition | 5 | Big project, don't know where to start |
| positive | 5 | Good day, momentum building, small wins |

### Variation Strategy

Within each scenario, prompts vary across multiple dimensions:
- **Emotional intensity:** From mild concern to acute distress
- **Self-awareness:** Some users recognize their patterns, others are confused
- **Explicitness:** Some ask for help directly, others just vent
- **Length:** From single-sentence fragments to multi-sentence paragraphs
- **Specificity:** Some describe concrete situations, others express general feelings

### Expected Emotion Distribution

| Emotion | Count |
|---------|-------|
| overwhelmed | 11 |
| frustrated | 7 |
| anxious | 6 |
| joyful | 4 |
| focused | 1 |
| disengaged | 1 |

The heavy skew toward negative emotions (25 out of 30) reflects the reality that ADHD coaching interactions disproportionately occur during difficulty, not during productive periods.

### Hourglass of Emotions Mapping

Each prompt includes expected Hourglass dimension directions following SenticNet's 4-dimensional model:
- **Pleasantness:** Joy (+) ↔ Sadness (-)
- **Attention:** Anticipation (+) ↔ Surprise (-)
- **Sensitivity:** Anger (+)/Fear (+) ↔ Calmness (-)
- **Aptitude:** Trust (+) ↔ Disgust (-)

The positive scenario prompts consistently show `high` across all dimensions, while negative scenarios show `low` pleasantness/aptitude with variable attention/sensitivity depending on whether the user is in active panic (high attention) or shutdown (low attention).

---

## Dataset 3: Emotion Test Sentences

**File:** `evaluation/data/emotion_test_sentences.json`
**Items:** 50 ADHD-relevant sentences with expected emotion labels

### Design Rationale

This dataset evaluates SenticNet's emotion detection accuracy on ADHD-specific language. Sentences were crafted to reflect how ADHD individuals actually describe their experiences — not clinical descriptions, but authentic first-person expressions including informal language, run-on thoughts, and emotional intensity markers.

### Emotion Category Distribution

| Emotion | Count | Example Themes |
|---------|-------|---------------|
| joyful | 8 | Task completion, unexpected productivity, medication working, remembering appointments |
| focused | 8 | Flow state, deep work, hyperfocus, sustained concentration, ideas connecting |
| frustrated | 9 | Repeated failures, broken tools, interrupted focus, medication not working, comparison to others |
| anxious | 9 | Deadline pressure, presentation fear, grade anxiety, imposter syndrome, procrastination avoidance |
| disengaged | 8 | Boredom, apathy, going through motions, brain offline, no motivation |
| overwhelmed | 8 | Too many tasks, sensory overload, emotional flooding, paralysis |

### ADHD-Specific Language Patterns

The sentences deliberately incorporate ADHD-specific language patterns that may challenge standard sentiment analysis:

1. **Negation with positive outcome:** "I can't believe I actually finished it" (joyful, not disbelief)
2. **Metaphorical shutdown:** "My brain is offline" (disengaged, not literal)
3. **Self-deprecation masking emotion:** "Is something wrong with me?" (frustrated/anxious)
4. **Paradoxical statements:** "ADHD almost feels like a superpower" (focused, positive)
5. **Physical symptom descriptions:** "My stomach drops every time" (anxious)
6. **Time-related distortions:** "Three hours had passed but productive hours" (focused)

---

## Dataset 4: Memory Test Profiles

**File:** `evaluation/data/memory_test_profiles.json`
**Items:** 20 user profiles, each with 10 stored memories and 5 test queries

### Design Rationale

This dataset evaluates Mem0's semantic memory retrieval quality. Each profile represents a distinct ADHD user with specific patterns, preferences, and coping strategies. Test queries require semantic understanding to match — they don't use the same keywords as the stored memories, testing whether Mem0's embedding-based search can bridge semantic gaps.

### Profile Diversity

| Profile | Description | ADHD Type | Severity | Key Challenge |
|---------|-------------|-----------|----------|---------------|
| user_001 | CS graduate student | Combined | Moderate | Long reading tasks |
| user_002 | Marketing professional | Inattentive | Mild | Email management |
| user_003 | Freelance designer | Hyperactive-impulsive | Severe | Emotional reactivity |
| user_004 | First-year university student | Inattentive | Moderate | Suspected undiagnosed |
| user_005 | Software engineer | Combined | Moderate | Stress-induced crashes |
| user_006 | PhD researcher | Inattentive | Moderate | Writing perfectionism |
| user_007 | High school teacher | Combined | Moderate | Afternoon energy crashes |
| user_008 | Graphic design student | Hyperactive | Moderate | Exercise-dependent focus |
| user_009 | Working mother | Inattentive | Moderate | Childcare + remote work |
| user_010 | Entrepreneur | Combined | Moderate | Operations vs. vision |
| user_011 | Data analyst | Inattentive | Moderate | Detail-oriented reports |
| user_012 | Nursing student | Combined | Moderate | Clinical rotation schedules |
| user_013 | Accountant | Inattentive | Mild | Late diagnosis, coping systems |
| user_014 | Music producer | Combined | Moderate | Creative hyperfocus |
| user_015 | Law student | Inattentive | Moderate | Reading volume |
| user_016 | Retired military | Combined | Moderate | Structure transition |
| user_017 | College athlete | Hyperactive | Moderate | Sport/academic balance |
| user_018 | Journalist | Combined | Moderate | Deadline-driven crashes |
| user_019 | Returning parent | Inattentive | Moderate | Career re-entry |
| user_020 | Game developer | Combined | Moderate | Health neglect during hyperfocus |

### Memory Topic Coverage

Each profile's 10 memories span diverse topics:
- **Strategies & coping:** Work techniques, study methods, regulation strategies
- **Preferences:** Tools, environments, learning styles, communication
- **Patterns:** Energy cycles, peak hours, weekly rhythms, procrastination triggers
- **Medication:** Type, dosage, timing, effectiveness factors
- **Emotional patterns:** Triggers, reactions, RSD, shame cycles
- **Support systems:** Partners, accountability partners, groups, accommodations
- **Self-awareness:** Known strengths, weaknesses, diagnosis history

### Query Design

Test queries are phrased as natural language questions a user might ask the coaching system. They require semantic matching rather than keyword matching:
- Query: "How should I approach this long paper?" → Memory: "User prefers breaking reading into 15-minute chunks"
- Query: "Why are Mondays always so hard?" → Memory: "User's focus drops significantly on Mondays; attributes it to weekend sleep schedule disruption"
- Query: "What do I do before starting deep work?" → Memory: "User meditates for 5 minutes before starting deep work"

Total queries across all profiles: **100** (20 profiles × 5 queries each)

---

## Dataset 5: ADHD Personas

**File:** `evaluation/data/adhd_personas.json`
**Items:** 5 ADHD personas for LLM simulation

### Design Rationale

These personas enable automated evaluation using the persona runner (`evaluation/persona_runner.py`). An LLM role-plays as each persona, sends messages to the coaching system, and the responses are evaluated for appropriateness, empathy, and actionability. The 5 personas were chosen to cover the primary ADHD subtypes, severity levels, life stages, and gender identities.

### Persona Summary

| Persona | Age | Gender | Subtype | Severity | Occupation | Key Trait |
|---------|-----|--------|---------|----------|------------|-----------|
| Alex | 22 | Male | Combined | Moderate | CS student | Recently diagnosed, medication adjustment |
| Priya | 28 | Female | Inattentive | Mild | Marketing pro | Strong masking, impostor syndrome |
| Jordan | 35 | Non-binary | Hyperactive-impulsive | Severe | Freelance designer | Unmedicated, high emotional reactivity |
| Maya | 19 | Female | Inattentive | Moderate | University student | Undiagnosed, family stigma |
| Sam | 41 | Male | Combined | Moderate | Software engineer | Medicated, crashes during stress |

### Coverage Analysis

- **ADHD Subtypes:** Combined (3), Inattentive (2), Hyperactive-Impulsive (1) — reflects clinical prevalence
- **Severity:** Mild (1), Moderate (3), Severe (1)
- **Medication:** Medicated (2), Unmedicated by choice (1), Undiagnosed (1), Adjusting (1)
- **Age range:** 19–41 years
- **Gender:** Male (2), Female (2), Non-binary (1)
- **Occupations:** Student (2), Tech professional (1), Creative (1), Marketing (1)
- **Conversation starters:** 5 per persona (25 total), covering diverse emotional states

### Format Differences from Existing Configuration

An existing `evaluation/personas_config.json` contains 5 personas in a different format (Alex, Priya, Jordan, Mei Ling, Daniel with `num_messages` field). The new `evaluation/data/adhd_personas.json` follows the Phase 2 specification with different persona compositions (Alex, Priya, Jordan, Maya, Sam) and includes `conversation_starters` instead of `num_messages`, as required by the updated evaluation pipeline.

---

## Validation Results

The Phase 2 completion criteria validation script ran successfully:

```
window_titles_200.json: 200 items ✓
coaching_test_prompts.json: 30 items ✓
emotion_test_sentences.json: 50 items ✓
memory_test_profiles.json: 20 items ✓
adhd_personas.json: 5 items ✓
```

Additional validation checks performed:
- All JSON files parse without errors
- All IDs are unique within each file
- All `expected_memory_id` values in test queries reference valid memory IDs within the same profile
- Scenario distribution in coaching prompts: exactly 5 per scenario
- Emotion distribution in test sentences matches specification: joyful(8), focused(8), frustrated(9), anxious(9), disengaged(8), overwhelmed(8)
- All memory profiles have exactly 10 memories and 5 test queries

---

## Directory Structure After Phase 2

```
evaluation/
├── __init__.py
├── accuracy/
│   └── __init__.py
├── analyze_results.py           (pre-existing)
├── benchmarks/
│   └── __init__.py
├── data/
│   ├── .gitkeep
│   ├── adhd_personas.json       ← NEW (5 items)
│   ├── coaching_test_prompts.json ← NEW (30 items)
│   ├── emotion_test_sentences.json ← NEW (50 items)
│   ├── memory_test_profiles.json   ← NEW (20 items)
│   └── window_titles_200.json     ← NEW (200 items)
├── persona_runner.py            (pre-existing)
├── personas_config.json         (pre-existing)
├── questionnaires.py            (pre-existing)
└── results/
    └── .gitkeep
```

---

## Design Decisions & Rationale

### 1. Dual-Label System for Window Titles

The actual `ActivityClassifier` classifies into fine-grained categories (`development`, `entertainment`, `social_media`, etc.) rather than the simplified `productive/neutral/distracting` scheme. We added both labels to each entry, enabling:
- Fine-grained category accuracy testing (does the classifier detect the correct category?)
- Productivity-level accuracy testing (does the mapping to productive/neutral/distracting work?)
- Analysis of which category confusions occur most frequently

### 2. Authentic ADHD Language

All text content (coaching prompts, emotion sentences, persona conversation starters) uses authentic first-person ADHD language rather than clinical descriptions. This is critical because:
- The SenticNet emotion analysis must work on informal, emotional text
- The LLM must respond appropriately to messy, real-world expressions
- Clinical language would not test the system under realistic conditions

### 3. Memory Query Semantic Gap

Test queries in the memory profiles deliberately avoid keyword overlap with stored memories. This forces the evaluation to test actual semantic understanding rather than simple keyword matching, which is the primary value proposition of using Mem0's embedding-based retrieval.

### 4. Edge Case Inclusion

The 10 edge cases in the window title dataset test the most challenging classification scenarios: educational YouTube content, productive Discord/Reddit usage, focus music on entertainment apps, and deceptive file names. These cases are expected to be misclassified by rule-based tiers and test the embedding-based fallback tier.

---

## Considerations for Subsequent Phases

### Phase 3 (Benchmarks)
- `window_titles_200.json` is the primary throughput dataset — benchmark each classifier tier's speed across all 200 titles
- The edge cases may have longer classification times if they fall through to Layer 4 (embedding similarity)

### Phase 4 (Accuracy)
- `emotion_test_sentences.json` should be tested against SenticNet API for emotion detection accuracy
- `coaching_test_prompts.json` should be evaluated for appropriate coaching response quality
- `memory_test_profiles.json` requires Mem0 to be running with OpenAI embeddings

### Phase 5 (Logger & Aggregator)
- All evaluation results should be logged using the evaluation logger service
- Results should be aggregated into the `evaluation/results/` directory

---

## Limitations

1. **Ground truth subjectivity:** Emotion labels and Hourglass dimension directions are researcher-assigned, not validated by multiple annotators or ADHD individuals. Inter-annotator agreement has not been measured.

2. **Window title realism:** While titles are realistic, they represent a curated selection rather than actual screen recordings. Real usage would include many more system-level titles and rapid title changes.

3. **Memory retrieval evaluation:** The expected memory IDs assume a single "best" match, but in practice multiple memories may be relevant to a given query. The evaluation should consider top-k retrieval, not just exact match.

4. **Persona coverage:** Five personas cannot fully represent the diversity of ADHD experiences across cultures, socioeconomic backgrounds, or comorbid conditions. The personas are weighted toward English-speaking, educated individuals.

5. **No fabricated metrics:** All counts, distributions, and validation results reported here are from actual measurement of the created files. No performance metrics or accuracy numbers are included as those are Phase 3 and Phase 4 deliverables.
