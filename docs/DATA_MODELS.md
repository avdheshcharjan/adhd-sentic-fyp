# Data Models & Schemas

> Covers PostgreSQL database schema, Pydantic request/response models, trained model artifacts, and static knowledge base formats.
> **Version**: 1.0.0 | **Last Updated**: 2026-03-30

---

## PostgreSQL Database Schema

### `activities` — Screen Activity Log

```sql
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_name VARCHAR NOT NULL,
    window_title VARCHAR NOT NULL,
    url VARCHAR,
    category VARCHAR NOT NULL,
    is_idle BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metrics JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_activities_app ON activities(app_name);
CREATE INDEX idx_activities_category ON activities(category);
CREATE INDEX idx_activities_timestamp ON activities(timestamp);
```

### `senticnet_analyses` — Emotion Analysis Results

```sql
CREATE TABLE senticnet_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    source VARCHAR NOT NULL,            -- 'chat_message', 'screen_title', 'vent'
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    emotion_profile JSONB NOT NULL,     -- {primary_emotion, setfit_confidence, primary_adhd_state, hourglass...}
    safety_flags JSONB NOT NULL,
    adhd_signals JSONB NOT NULL
);
```

### `interventions` — Intervention History

```sql
CREATE TABLE interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    intervention_type VARCHAR NOT NULL,  -- 'distraction_spiral', 'sustained_disengagement', etc.
    trigger_reason VARCHAR NOT NULL,
    user_response VARCHAR,               -- 'accepted', 'dismissed', 'ignored'
    effectiveness_score FLOAT,           -- -1.0 to 1.0
    context_data JSONB DEFAULT '{}'
);
CREATE INDEX idx_interventions_timestamp ON interventions(timestamp);
```

### `whoop_data` — Daily Whoop Snapshots

```sql
CREATE TABLE whoop_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date VARCHAR NOT NULL UNIQUE,        -- 'YYYY-MM-DD'
    recovery_score FLOAT NOT NULL,
    sleep_score FLOAT NOT NULL,
    strain_score FLOAT NOT NULL,
    metrics JSONB NOT NULL               -- {hrv_rmssd, resting_hr, sws_pct, rem_pct, disturbance_count}
);
CREATE UNIQUE INDEX idx_whoop_date ON whoop_data(date);
```

### `focus_tasks` — Focus Session Tasks

```sql
CREATE TABLE focus_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    duration_seconds INTEGER NOT NULL,
    progress FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

### `behavioral_patterns` — Detected Behavioral Patterns

```sql
CREATE TABLE behavioral_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR NOT NULL,       -- 'procrastination_trigger', 'peak_focus_time', etc.
    description TEXT NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    confidence FLOAT DEFAULT 1.0,
    embedding VECTOR(1536),              -- text-embedding-3-small dimension
    source_evidence JSONB DEFAULT '[]'
);
CREATE INDEX idx_patterns_type ON behavioral_patterns(pattern_type);
```

### `daily_snapshots` — End-of-Day Metric Summaries

```sql
CREATE TABLE daily_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date VARCHAR NOT NULL UNIQUE,        -- 'YYYY-MM-DD'

    -- Core metrics
    total_active_minutes FLOAT NOT NULL DEFAULT 0.0,
    total_focus_minutes FLOAT NOT NULL DEFAULT 0.0,
    total_distraction_minutes FLOAT NOT NULL DEFAULT 0.0,
    focus_percentage FLOAT NOT NULL DEFAULT 0.0,
    distraction_percentage FLOAT NOT NULL DEFAULT 0.0,
    context_switches INTEGER NOT NULL DEFAULT 0,

    -- Interventions
    interventions_triggered INTEGER NOT NULL DEFAULT 0,
    interventions_accepted INTEGER NOT NULL DEFAULT 0,

    -- Rich data (JSON blobs)
    top_apps JSONB NOT NULL DEFAULT '[]',           -- [{app_name, category, minutes, percentage}]
    behavioral_states JSONB NOT NULL DEFAULT '{}',  -- {state: minutes}
    focus_timeline JSONB NOT NULL DEFAULT '[]',     -- [{category, duration}]
    emotion_scores JSONB,                            -- {pleasantness, attention, sensitivity, aptitude}

    -- Whoop (nullable)
    whoop_recovery JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_snapshots_date ON daily_snapshots(date);
```

### pgvector Extension

```sql
CREATE EXTENSION IF NOT EXISTS vector;
-- Used by Mem0 for semantic similarity search
-- Used by BehavioralPattern for embedding storage
```

---

## Pydantic Models

### Screen Activity

```python
# models/screen_activity.py
class ScreenActivityInput(BaseModel):
    app_name: str
    window_title: str
    url: str | None = None
    is_idle: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    off_task_alerts_enabled: bool = False
    off_task_alerts_always: bool = False

class ScreenActivityResponse(BaseModel):
    category: str
    metrics: dict
    intervention: Intervention | None
    off_task: bool = False
```

### Chat Messages

```python
# models/chat_message.py
class ChatInput(BaseModel):
    text: str
    conversation_id: str | None = None

class EmotionDetail(BaseModel):
    polarity: float
    mood_tags: list[str]
    hourglass_pleasantness: float
    hourglass_attention: float
    hourglass_sensitivity: float
    hourglass_aptitude: float
    sentic_concepts: list[str]

class ChatResponse(BaseModel):
    response: str
    emotion_profile: dict | None
    safety_flags: dict | None
    suggested_actions: list[InterventionAction] | None
    used_llm: bool
    thinking_mode: str | None = None      # "think" or "no_think"
    emotion_context: EmotionDetail | None = None
    ablation_mode: bool = False
    latency_ms: float = 0.0
    token_count: int = 0
```

### SenticNet Results

```python
# models/senticnet_result.py
class SafetyResult(BaseModel):
    level: str                    # "critical" | "high" | "moderate" | "normal"
    depression_score: float
    toxicity_score: float
    intensity_score: float
    is_critical: bool

class EmotionResult(BaseModel):
    primary_emotion: str
    hourglass: dict              # {introspection, temper, attitude, sensitivity}
    polarity_score: float
    is_subjective: bool
    sarcasm_score: float
    sarcasm_detected: bool

class ADHDSignals(BaseModel):
    engagement_score: float
    wellbeing_score: float
    intensity_score: float
    is_disengaged: bool
    is_overwhelmed: bool
    is_frustrated: bool
    emotional_dysregulation: bool

class SenticNetResult(BaseModel):
    safety: SafetyResult
    emotion: EmotionResult
    adhd_signals: ADHDSignals
    primary_adhd_state: str       # SetFit-derived ADHD state
    setfit_confidence: float      # SetFit prediction confidence
    concepts: list[str]
    aspects: dict
    personality: dict | None = None
```

### Intervention

```python
# models/intervention.py
class InterventionAction(BaseModel):
    id: str
    emoji: str
    label: str

class Intervention(BaseModel):
    id: str
    type: str
    ef_domain: str
    acknowledgment: str
    suggestion: str
    actions: list[InterventionAction]
    notification_tier: int = 3
    explanation: dict | None = None
```

### ADHD State

```python
# models/adhd_state.py
class ADHDMetrics(BaseModel):
    context_switch_rate_5min: float = 0.0
    focus_score: float = 0.0
    distraction_ratio: float = 0.0
    current_streak_minutes: float = 0.0
    hyperfocus_detected: bool = False
    behavioral_state: str = "unknown"
    current_app: str | None = None
    current_category: str | None = None
```

### Vent Models

```python
# models/vent_models.py
class VentChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    history: list[dict] = []         # [{role, content}]

class VentChatResponse(BaseModel):
    response: str
    is_crisis: bool = False
```

### Brain Dump Models

```python
# models/brain_dump_models.py
class BrainDumpRequest(BaseModel):
    content: str
    session_id: str | None = None    # Links to focus session

class BrainDumpResponse(BaseModel):
    id: str
    status: str                      # "captured"
    emotional_state: str | None
    timestamp: datetime

class BrainDumpReviewItem(BaseModel):
    id: str
    content: str
    emotional_state: str | None
    timestamp: datetime
    session_id: str | None

class BrainDumpReviewResponse(BaseModel):
    items: list[BrainDumpReviewItem]
    count: int
```

### Insights Models

```python
# models/insights.py
class DailyInsights(BaseModel):
    total_active_minutes: float
    total_focus_minutes: float
    total_distraction_minutes: float
    focus_percentage: float
    distraction_percentage: float
    context_switches: int
    interventions_triggered: int
    interventions_accepted: int
    top_apps: list[dict]
    behavioral_states: dict

class WeeklyInsights(BaseModel):
    avg_focus_percentage: float
    avg_distraction_percentage: float
    total_interventions: int
    intervention_acceptance_rate: float
    daily_focus_scores: list[dict]   # [{date, focus_pct, distraction_pct}]
    best_focus_day: str | None
    worst_focus_day: str | None
    trend: str                       # "improving" | "stable" | "declining"
```

### XAI Explanation

```python
# models/explanation.py
class Explanation(BaseModel):
    tier_1: dict                     # {color: "green"|"amber"|"red"}
    tier_2: str                      # One-sentence plain English explanation
    tier_3: dict                     # Full concept breakdown + counterfactual
```

---

## Trained Model Artifacts

Stored in `backend/models/`:

### `adhd-emotion-setfit/` — Production Emotion Classifier (Approach B)

```
adhd-emotion-setfit/
├── sentence_transformer/          # Fine-tuned all-mpnet-base-v2
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer.json
│   └── ...
├── classifier.pkl                 # LogisticRegression head
└── label_encoder.pkl              # LabelEncoder (6 classes)
```

- **Architecture**: Contrastive fine-tuned all-mpnet-base-v2 + LogisticRegression
- **Training**: 210 curated sentences, CoSENT loss, all-unique-pair mining, hard negatives, 1 epoch
- **Accuracy**: 86% on 50-sentence test set
- **Labels**: joyful, focused, frustrated, anxious, disengaged, overwhelmed

### `adhd-emotion-finetune/` — DistilBERT Classifier (Approach C)

```
adhd-emotion-finetune/
├── model.safetensors              # 267MB DistilBERT
├── config.json
├── tokenizer.json
└── checkpoints/
```

- **Architecture**: Full DistilBERT fine-tune
- **Accuracy**: 72% on augmented data (1.2K samples)

### `adhd-emotion-hybrid/` — Hybrid Classifier (Approach A)

```
adhd-emotion-hybrid/
├── classifier.pkl                 # sklearn classifier
├── label_encoder.pkl
└── scaler.pkl                     # Feature scaler
```

- **Architecture**: Sentence embeddings + SenticNet features → sklearn
- **Accuracy**: 74% (embedding only), 70% with SenticNet features

---

## Static Knowledge Bases

### `knowledge/app_categories.json`
Maps ~40 app names to categories:
- IDE/terminals → `development`
- Notion/Todoist → `productivity`
- Slack/Zoom → `communication`
- Spotify/Netflix → `entertainment`
- Safari/Chrome → `browser`

### `knowledge/url_categories.json`
Maps ~30 domains to categories:
- github.com → `development`
- reddit.com → `social_media`
- youtube.com → `entertainment`
- arxiv.org → `research`

### `knowledge/adhd_interventions.json`
Evidence-based intervention library mapped to Barkley's 5 EF domains.

### `knowledge/barkley_ef_model.json`
Definitions of the 5 Executive Function deficit domains with associated symptoms and intervention mappings.
