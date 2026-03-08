# Data Models & Schemas

> Covers PostgreSQL database schema, Pydantic request/response models, and static knowledge base formats.

---

## PostgreSQL Database Schema

### `activities` — Screen Activity Log

```sql
CREATE TABLE activities (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    app_name VARCHAR(255),
    window_title TEXT,
    url TEXT,
    category VARCHAR(50),
    is_idle BOOLEAN DEFAULT FALSE,
    metrics JSONB              -- snapshot of ADHDMetrics at this point
);
CREATE INDEX idx_activities_timestamp ON activities(timestamp DESC);
```

### `senticnet_analyses` — Emotion Analysis Results

```sql
CREATE TABLE senticnet_analyses (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(20),        -- 'chat', 'screen', 'journal'
    input_text TEXT,
    emotion_profile JSONB,
    safety_flags JSONB,
    adhd_signals JSONB,
    concepts JSONB,
    raw_results JSONB
);
```

### `interventions` — Intervention History

```sql
CREATE TABLE interventions (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    type VARCHAR(50),
    ef_domain VARCHAR(50),
    suggestion TEXT,
    actions JSONB,
    explanation JSONB,
    user_action VARCHAR(50),   -- which button clicked, or 'dismissed'
    dismissed BOOLEAN DEFAULT FALSE,
    effectiveness_rating INTEGER  -- 1-5, optional self-report
);
CREATE INDEX idx_interventions_type ON interventions(type, timestamp DESC);
```

### `whoop_data` — Daily Whoop Snapshots

```sql
CREATE TABLE whoop_data (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    recovery_score FLOAT,
    recovery_tier VARCHAR(10),
    hrv_rmssd FLOAT,
    resting_hr FLOAT,
    sleep_performance FLOAT,
    sws_percentage FLOAT,
    rem_percentage FLOAT,
    disturbance_count INTEGER,
    strain FLOAT,
    raw_data JSONB
);
```

### `conversations` + `messages` — Chat History

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    role VARCHAR(20),          -- 'user' or 'assistant'
    content TEXT,
    senticnet_analysis JSONB,
    source VARCHAR(20)         -- 'openclaw', 'dashboard', 'swift_app'
);
```

### pgvector Extension

```sql
CREATE EXTENSION IF NOT EXISTS vector;
-- Used by Mem0 for semantic similarity search
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
    timestamp: datetime = Field(default_factory=datetime.now)

class ScreenActivityResponse(BaseModel):
    category: str
    metrics: dict
    intervention: Intervention | None
```

### SenticNet Results

```python
# models/senticnet_result.py
class EmotionProfile(BaseModel):
    primary_emotion: str
    hourglass_dimensions: dict    # {pleasantness, attention, sensitivity, aptitude}
    polarity: str
    polarity_score: float
    is_subjective: bool
    sarcasm_score: float
    sarcasm_detected: bool

class SafetyFlags(BaseModel):
    level: str                    # "critical" | "high" | "moderate" | "normal"
    depression_score: float
    toxicity_score: float
    intensity_score: float
    is_critical: bool

class ADHDRelevantSignals(BaseModel):
    engagement_score: float
    wellbeing_score: float
    intensity_score: float
    is_disengaged: bool
    is_overwhelmed: bool
    is_frustrated: bool
    emotional_dysregulation: bool

class SenticNetFullResult(BaseModel):
    emotion_profile: EmotionProfile
    safety_flags: SafetyFlags
    adhd_signals: ADHDRelevantSignals
    concepts: dict
    aspects: dict
    personality: dict
    ensemble: dict
    raw_results: dict
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
```

### Intervention

```python
# models/intervention.py
class InterventionAction(BaseModel):
    id: str
    emoji: str
    label: str

class Intervention(BaseModel):
    type: str
    ef_domain: str
    acknowledgment: str
    suggestion: str
    actions: list[InterventionAction]
    requires_senticnet: bool = False
```

### Chat

```python
# models/chat_message.py
class ChatInput(BaseModel):
    text: str
    conversation_id: str | None = None
    context: dict | None = None

class ChatResponse(BaseModel):
    response: str
    emotion_profile: EmotionProfile | None
    safety_flags: SafetyFlags | None
    suggested_actions: list[InterventionAction] | None
```

---

## Static Knowledge Bases

### `app_categories.json`
Maps ~40 app names to categories. Key entries:
- IDE/terminals → `development`
- Notion/Todoist → `productivity`
- Slack/Zoom → `communication`
- Spotify/Netflix → `entertainment`
- Safari/Chrome → `browser`

### `url_categories.json`
Maps ~30 domains to categories. Key entries:
- github.com → `development`
- reddit.com → `social_media`
- youtube.com → `entertainment`
- arxiv.org → `research`

### `adhd_interventions.json`
Evidence-based intervention library mapped to Barkley's EF domains.

### `barkley_ef_model.json`
Definitions of the 5 Executive Function deficit domains with associated symptoms and interventions.
