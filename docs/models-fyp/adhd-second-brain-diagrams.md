---
title: ADHD Second Brain — Complete UML Diagrams (FINAL)
---
%% This file contains 5 diagrams. Render each ```mermaid block separately.
%%
%% DIAGRAM INDEX:
%% 1. Master Component Diagram — every subsystem and connection
%% 2. Screen Monitor → Intervention Sequence — the core real-time loop
%% 3. Venting Chat Sequence — emotion detection → coaching response
%% 4. Notification Tier State Machine — how interventions escalate
%% 5. Onboarding & Calibration Flow — first-time user experience


%% ═══════════════════════════════════════════════════════════════
%% DIAGRAM 1: MASTER COMPONENT DIAGRAM
%% Shows every subsystem from all documents with correct models
%% ═══════════════════════════════════════════════════════════════

graph TB
    subgraph UserLayer["🖥️ USER INTERFACE LAYER"]
        direction LR
        SwiftApp["🍎 Swift macOS App<br/><i>macOS 14+, ~25MB RAM</i><br/>─────────────<br/>• NotchIsland (5-state widget)<br/>• BrainDump Modal (Cmd+Shift+B)<br/>• Vent Modal (Cmd+Shift+V)<br/>• TaskCreation Modal (Cmd+Shift+T)<br/>─────────────<br/>• ScreenMonitor (AXUIElement)<br/>• BrowserMonitor (AppleScript)<br/>• IdleMonitor (IOHIDSystem)<br/>• TransitionDetector<br/>─────────────<br/>• TierManager (5-tier notif)<br/>• DashboardView / HistoryView<br/>• SettingsView / OnboardingView<br/>• KeyboardShortcutManager"]
        TelegramBot["📱 Telegram Bot<br/><i>python-telegram-bot v21</i><br/>─────────────<br/>• /start command<br/>• Default text → vent<br/>• Morning Briefing (7:30 AM)<br/>• Focus Check (every 30min)<br/>• Weekly Review (Sun 8 PM)"]
        Dashboard["📊 React Dashboard<br/><i>Vite 5 + React 18 + Recharts</i><br/>─────────────<br/>• FocusTimeline<br/>• EmotionRadar (Hourglass)<br/>• WhoopCard<br/>• MetricsCard<br/>• InterventionLog<br/>• WeeklyReport"]
    end

    subgraph BackendLayer["⚙️ PYTHON FASTAPI BACKEND (localhost:8420)"]
        direction TB

        subgraph APIRoutes["REST API Routes (12 routers)"]
            ScreenAPI["POST /screen/activity<br/><i>Target: &lt;100ms</i>"]
            ChatAPI["POST /chat/message<br/><i>Target: &lt;3s</i>"]
            VentAPI["POST /api/v1/vent/chat/stream<br/>POST /api/v1/vent/chat"]
            BrainDumpAPI["POST /api/v1/brain-dump/<br/>POST /api/v1/brain-dump/stream"]
            FocusAPI["POST /api/v1/tasks/create<br/>GET /api/v1/focus/*"]
            NotchAPI["GET /api/v1/dashboard/*<br/>GET /api/v1/emotion/current<br/>GET /api/v1/calendar/upcoming"]
            InsightsAPI["GET /insights/*"]
            EvalAPI["POST /eval/ablation<br/>POST /eval/logging"]
            AuthAPI["GET /api/auth/whoop<br/>GET /api/auth/google"]
            CorrectAPI["POST /screen/correct-category"]
        end

        subgraph MonitoringPipeline["📡 MONITORING PIPELINE (always-on, <100ms)"]
            ActivityClassifier["🏷️ Activity Classifier<br/>─────────────<br/>L0: User corrections (instant)<br/>L1: App name rules (0.01ms)<br/>L2: URL domain lookup (0.01ms)<br/>L3: Title keywords (0.1ms)<br/>L4: all-MiniLM-L6-v2 (25ms)"]

            SetFitClassifier["🎯 SetFit Emotion Classifier<br/>─────────────<br/>all-mpnet-base-v2 (contrastive)<br/>6 ADHD states, 86% accuracy<br/>→ PASE radar profile"]

            MetricsEngine["📈 ADHD Metrics Engine<br/>─────────────<br/>• Context switch rate/5min<br/>• Focus score (0-100)<br/>• Distraction ratio (0-1)<br/>• Current streak minutes<br/>• Behavioral state"]

            TransitionDetector["🚦 Transition Detector<br/>─────────────<br/>• App switch events<br/>• Tab burst detection<br/>• Idle resume detection<br/>• Breakpoint freshness"]

            HyperfocusClassifier["🔬 Hyperfocus Classifier<br/>─────────────<br/>• Productive (PROTECT)<br/>• Unproductive (gentle redirect)<br/>• Ambiguous (check-in)"]
        end

        subgraph DecisionPipeline["🎯 DECISION PIPELINE"]
            JITAIEngine["🎯 JITAI Engine<br/>─────────────<br/>Gate 0: Transition required<br/>Gate 1: Hyperfocus protection<br/>Gate 2: Per-block cap (3/90min)<br/>Gate 3: Adaptive bandit"]

            AdaptiveBandit["🎰 Thompson Sampling<br/>─────────────<br/>Context: hour, recovery,<br/>  recency, app category<br/>Learns WHEN to intervene"]

            NotificationTier["📢 Tier Selector<br/>─────────────<br/>T1: Ambient color shift<br/>T2: Gentle pulse<br/>T3: Non-activating overlay<br/>T4: Toast notification<br/>T5: Full (safety only)"]

            XAIExplainer["🔍 XAI Explainer<br/>─────────────<br/>• Concept Bottleneck<br/>• Progressive disclosure<br/>  (traffic light → sentence<br/>   → full detail)<br/>• User concept corrections"]
        end

        subgraph SenticPipeline["🧠 SenticNet Pipeline (emotion engine)"]
            SenticClient["SenticNet Client<br/><i>13 REST APIs + pip senticnet</i>"]

            subgraph SafetyTier["Tier 1: Safety FIRST"]
                Depression["Depression"]
                Toxicity["Toxicity"]
                Intensity["Intensity"]
            end

            subgraph EmotionTier["Tier 2: Emotional"]
                Emotion["Emotion<br/>(Hourglass)"]
                Polarity["Polarity"]
                Subjectivity["Subjectivity"]
                Sarcasm["Sarcasm"]
            end

            subgraph ADHDTier["Tier 3: ADHD Signals"]
                Engagement["Engagement"]
                Wellbeing["Well-being"]
                ConceptParsing["Concepts"]
                Aspects["Aspects"]
            end

            HourglassMapper["🔄 Hourglass → ADHD State<br/>─────────────<br/>• boredom_disengagement<br/>• frustration_spiral<br/>• productive_flow<br/>• emotional_dysregulation<br/>• anxiety_comorbid"]
        end

        subgraph CoachingPipeline["💬 COACHING PIPELINE (on-demand)"]
            ChatProcessor["💬 Chat Processor<br/>─────────────<br/>1. SenticNet analysis<br/>2. Safety check<br/>3. Build context<br/>4. /think or /no_think<br/>5. Generate response<br/>6. Store in memory"]

            MLXInference["🤖 MLX Inference<br/>─────────────<br/>Qwen3-4B 4-bit (~2.3GB)<br/>Load on demand (~2-5s)<br/>Unload after 2min idle<br/>~37 tok/s on M4"]

            VentService["🗣️ Vent Service<br/>─────────────<br/>Layer 1: Crisis keywords<br/>Layer 2: SenticNet semantic<br/>Layer 3: Output safety<br/>Layer 4: Session escalation"]

            BrainDumpService["🧠 Brain Dump Service<br/>─────────────<br/>• Capture + Mem0 store<br/>• AI summary via MLX<br/>• Emotion tagging"]
        end

        subgraph SupportSystems["🔧 SUPPORT SYSTEMS"]
            FocusService["🎯 Focus Service<br/>─────────────<br/>• Task creation<br/>• Focus timer<br/>• Off-task detection<br/>  (embedding similarity)"]

            SnapshotService["📸 Snapshot Service<br/>─────────────<br/>• Daily save at 23:55<br/>• Backfill on startup<br/>• History browsing"]

            InsightsService["📊 Insights Service<br/>─────────────<br/>• Daily/weekly aggregation<br/>• Dashboard stats<br/>• PASE score computation"]

            GoogleCalendar["📅 Google Calendar<br/>─────────────<br/>• OAuth 2.0 tokens<br/>• Upcoming events<br/>• Calendar strip data"]

            WhoopService["💚 Whoop Service<br/>─────────────<br/>• whoopskill CLI wrapper<br/>• Recovery / HRV / Sleep<br/>• Morning briefing gen"]

            MemoryService["🧩 Memory (Mem0)<br/>─────────────<br/>• Conversation history<br/>• Brain dump storage<br/>• Pattern storage<br/>• Semantic retrieval"]
        end

        subgraph TelegramServices["📱 TELEGRAM BOT"]
            TGScheduler["Scheduler<br/>─────────────<br/>• Morning briefing 7:30<br/>• Focus check 30min<br/>• Weekly review Sun 8PM"]
            TGHandlers["Handlers<br/>─────────────<br/>• /start<br/>• vent (default text)<br/>• morning_briefing<br/>• focus_check<br/>• weekly_review"]
        end
    end

    subgraph DataLayer["💾 DATA LAYER"]
        direction LR
        PostgreSQL[("PostgreSQL 16 + pgvector<br/>─────────────<br/>• activities<br/>• senticnet_analyses<br/>• interventions<br/>• whoop_data<br/>• focus_tasks<br/>• behavioral_patterns<br/>• daily_snapshots<br/>• Mem0 vector embeddings")]
    end

    subgraph OnDeviceModels["🧠 ON-DEVICE MODELS (Apple MLX)"]
        SentenceTransformer["all-MiniLM-L6-v2<br/>22M params, ~80MB<br/><i>Always resident</i>"]
        SetFitModel["all-mpnet-base-v2 (SetFit)<br/>109M params, ~420MB<br/><i>Singleton at startup</i>"]
        Qwen3["Qwen3-4B 4-bit<br/>4B params, ~2.3GB<br/><i>Load on demand</i>"]
        SenticNetLocal["SenticNet Python<br/>400K concepts, ~50MB<br/><i>Always resident</i>"]
    end

    subgraph ExternalAPIs["☁️ EXTERNAL SERVICES"]
        SenticNetCloud["SenticNet Cloud<br/>sentic.net/api/ (13 endpoints)"]
        WhoopCLI["Whoop (whoopskill CLI)"]
        GoogleAPI["Google Calendar API"]
        TelegramAPI["Telegram Bot API"]
    end

    %% === USER → BACKEND connections ===
    SwiftApp -->|"POST /screen/activity<br/>every 2-3s"| ScreenAPI
    SwiftApp -->|"POST /screen/correct-category"| CorrectAPI
    SwiftApp -->|"POST /api/v1/brain-dump/"| BrainDumpAPI
    SwiftApp -->|"POST /api/v1/vent/chat/stream"| VentAPI
    SwiftApp -->|"POST /api/v1/tasks/create"| FocusAPI
    SwiftApp -->|"GET /api/v1/dashboard/*"| NotchAPI
    TelegramBot -->|"POST /chat/message"| ChatAPI
    TelegramBot -->|"POST /api/v1/vent/chat"| VentAPI
    Dashboard -->|"GET /insights/*"| InsightsAPI

    %% === MONITORING FLOW ===
    ScreenAPI --> ActivityClassifier
    ActivityClassifier --> SetFitClassifier
    SetFitClassifier --> MetricsEngine
    MetricsEngine --> TransitionDetector
    MetricsEngine --> HyperfocusClassifier
    TransitionDetector --> JITAIEngine
    HyperfocusClassifier --> JITAIEngine

    %% === DECISION FLOW ===
    JITAIEngine --> AdaptiveBandit
    AdaptiveBandit --> NotificationTier
    NotificationTier --> XAIExplainer
    XAIExplainer -->|"Queued intervention"| SwiftApp

    %% === COACHING FLOW ===
    ChatAPI --> ChatProcessor
    ChatProcessor --> SenticClient
    SenticClient --> SafetyTier
    SenticClient --> EmotionTier
    SenticClient --> ADHDTier
    EmotionTier --> HourglassMapper
    ChatProcessor --> MLXInference
    ChatProcessor --> MemoryService

    VentAPI --> VentService
    VentService --> MLXInference
    VentService --> SenticClient

    BrainDumpAPI --> BrainDumpService
    BrainDumpService --> MLXInference
    BrainDumpService --> MemoryService

    FocusAPI --> FocusService

    %% === MODEL connections ===
    ActivityClassifier -->|"Layer 4 fallback"| SentenceTransformer
    SetFitClassifier --> SetFitModel
    FocusService -->|"Off-task similarity"| SentenceTransformer
    MLXInference --> Qwen3
    SenticClient --> SenticNetLocal
    SenticClient -->|"REST API (13 endpoints)"| SenticNetCloud

    %% === SUPPORT connections ===
    NotchAPI --> InsightsService
    NotchAPI --> SnapshotService
    NotchAPI --> GoogleCalendar
    AuthAPI --> WhoopService
    AuthAPI --> GoogleCalendar
    TGScheduler --> TGHandlers

    %% === DATA connections ===
    MetricsEngine --> PostgreSQL
    JITAIEngine --> PostgreSQL
    WhoopService --> PostgreSQL
    MemoryService --> PostgreSQL
    FocusService --> PostgreSQL
    SnapshotService --> PostgreSQL
    InsightsService --> PostgreSQL

    %% === EXTERNAL connections ===
    WhoopService --> WhoopCLI
    GoogleCalendar --> GoogleAPI
    TGHandlers --> TelegramAPI

    %% === STYLING ===
    classDef swift fill:#007AFF,stroke:#005EC4,color:white,stroke-width:2px
    classDef telegram fill:#0088CC,stroke:#006699,color:white,stroke-width:2px
    classDef dashboard fill:#34C759,stroke:#28A745,color:white,stroke-width:2px
    classDef api fill:#5856D6,stroke:#4240B0,color:white,stroke-width:1px
    classDef monitor fill:#FF9500,stroke:#CC7600,color:white,stroke-width:1px
    classDef decision fill:#FF2D55,stroke:#CC2444,color:white,stroke-width:1px
    classDef sentic fill:#AF52DE,stroke:#8B42B2,color:white,stroke-width:1px
    classDef safety fill:#FF3B30,stroke:#CC2F26,color:white,stroke-width:2px
    classDef coaching fill:#5AC8FA,stroke:#48A0C8,color:white,stroke-width:1px
    classDef support fill:#FFCC00,stroke:#CC9900,color:black,stroke-width:1px
    classDef db fill:#636366,stroke:#48484A,color:white,stroke-width:2px
    classDef external fill:#8E8E93,stroke:#636366,color:white,stroke-width:1px
    classDef model fill:#30D158,stroke:#28A745,color:white,stroke-width:2px

    class SwiftApp swift
    class TelegramBot telegram
    class Dashboard dashboard
    class ScreenAPI,ChatAPI,VentAPI,BrainDumpAPI,FocusAPI,NotchAPI,InsightsAPI,EvalAPI,AuthAPI,CorrectAPI api
    class ActivityClassifier,SetFitClassifier,MetricsEngine,TransitionDetector,HyperfocusClassifier monitor
    class JITAIEngine,AdaptiveBandit,NotificationTier,XAIExplainer decision
    class SenticClient,Emotion,Polarity,Subjectivity,Sarcasm,Engagement,Wellbeing,ConceptParsing,Aspects,HourglassMapper sentic
    class Depression,Toxicity,Intensity safety
    class ChatProcessor,MLXInference,VentService,BrainDumpService coaching
    class FocusService,SnapshotService,InsightsService,GoogleCalendar,WhoopService,MemoryService,TGScheduler,TGHandlers support
    class PostgreSQL db
    class SenticNetCloud,WhoopCLI,GoogleAPI,TelegramAPI external
    class SentenceTransformer,SetFitModel,Qwen3,SenticNetLocal model


---

---
title: "ADHD Second Brain — Screen Monitor → Intervention Sequence"
---
%% This shows the CORE REAL-TIME LOOP: what happens every time the user switches apps
%% or a window title changes. This is the most performance-critical path in the system.

sequenceDiagram
    autonumber
    participant User as 👤 User's Screen
    participant Swift as 🍎 Swift Menu Bar App
    participant API as ⚙️ FastAPI Backend
    participant Classify as 🏷️ Activity Classifier
    participant SetFit as 🎯 SetFit Classifier
    participant Metrics as 📈 Metrics Engine
    participant Transition as 🚦 Transition Detector
    participant Hyperfocus as 🔬 Hyperfocus Classifier
    participant JITAI as 🎯 JITAI Engine
    participant Bandit as 🎰 Adaptive Bandit
    participant Tier as 📢 Tier Selector
    participant XAI as 🔍 XAI Explainer
    participant TierMgr as 🔔 Tier Manager (Swift)

    Note over User,TierMgr: === USER SWITCHES FROM VS CODE TO TWITTER ===

    User->>Swift: NSWorkspace.didActivateApplicationNotification
    Note right of Swift: Event-driven (not polling)<br/>Zero CPU cost when idle

    Swift->>Swift: AXUIElement → get window title
    Swift->>Swift: AppleScript → get browser URL (if browser)
    Swift->>Swift: TransitionDetector.recordAppSwitch()

    Swift->>API: POST /screen/activity<br/>{app: "Safari", title: "Twitter / X", url: "x.com"}

    Note over API,Classify: Layer 0-4 classification (<25ms total)

    API->>Classify: classify("Safari", "Twitter / X", "x.com")
    Classify-->>Classify: L0: Check user corrections → miss
    Classify-->>Classify: L1: App name "safari" → "browser" (need URL)
    Classify-->>Classify: L2: URL "x.com" → "social_media" ✓
    Classify-->>API: ("social_media", 0.95)

    Note over API,SetFit: SetFit emotion classification (<50ms)

    API->>SetFit: predict("Twitter / X - social_media")
    SetFit-->>API: (label: "disengaged", confidence: 0.72, PASE: {P:0.35, A:0.15, S:0.25, Ap:0.20})

    API->>Metrics: update(app="Safari", category="social_media", emotion="disengaged")
    Metrics-->>Metrics: Record app switch event
    Metrics-->>Metrics: Increment context_switch_rate_5min
    Metrics-->>Metrics: Update distraction_ratio
    Metrics-->>Metrics: Compute behavioral_state = "distracted"
    Metrics-->>API: ADHDMetrics snapshot

    API->>Transition: detect_breakpoint_type()
    Transition-->>API: APP_SWITCH (fresh breakpoint available)

    API->>Hyperfocus: classify(session_minutes=2, ...)
    Hyperfocus-->>API: None (not in hyperfocus, session too short)

    API->>JITAI: evaluate(metrics, emotion_context={label: "disengaged"})

    Note over JITAI: Gate 0: Transition available? ✅ (app switch)
    Note over JITAI: Gate 1: Hyperfocus protection? ✅ (not hyperfocusing)
    Note over JITAI: Gate 2: Per-block cap? ✅ (0/3 used this block)

    JITAI->>Bandit: should_deliver(context={hour: 14, recovery: "green", recency: "not_recent"})
    Bandit-->>JITAI: True (sampled reward > 0.5)

    Note over JITAI: Gate 3: Bandit approves ✅
    Note over JITAI: Rule match: context_switch_rate=8, distraction_ratio=0.3<br/>Below threshold — NO intervention yet

    JITAI-->>API: None (thresholds not met)
    API-->>Swift: {category: "social_media", metrics: {...}, emotion: {...}, intervention: null}

    Note over User,TierMgr: === 5 MINUTES LATER: USER STILL ON SOCIAL MEDIA ===

    Swift->>API: POST /screen/activity (periodic title change detected)
    API->>Classify: classify(...)
    API->>SetFit: predict(...)
    API->>Metrics: update(...)
    Metrics-->>Metrics: distraction_ratio = 0.65, switch_rate = 14
    Metrics-->>Metrics: behavioral_state = "distracted"

    API->>JITAI: evaluate(metrics)
    Note over JITAI: All gates pass ✅
    Note over JITAI: Rule: switch_rate > 12 AND distraction_ratio > 0.5<br/>→ "distraction_spiral" intervention triggered

    JITAI->>Tier: select_tier(type="distraction_spiral", state="distracted", ...)
    Tier-->>JITAI: Tier 3 (Non-activating overlay)

    JITAI->>XAI: generate_explanation(type="distraction_spiral", metrics)
    XAI-->>JITAI: {tier_1: {color: "amber"}, tier_2: "Your attention has been jumping around...", ...}

    JITAI-->>API: Intervention object with tier=3 + explanation

    API-->>Swift: {category: "social_media", metrics: {...}, emotion: {...}, intervention: {...}}

    Swift->>TierMgr: deliver(intervention)
    Note over TierMgr: Transition detector confirms breakpoint is fresh

    TierMgr->>User: CalmOverlayPanel slides in (top-right)<br/>Does NOT steal keyboard focus<br/>"Looks like things are scattered — that's okay.<br/>A 2-minute reset could help. What feels right?"<br/>[🫁 Breathe] [🎯 Pick one task] [☕ Break]

    alt User clicks "Pick one task"
        User->>Swift: action = "task_pick"
        Swift->>API: POST /interventions/respond {action: "task_pick", dismissed: false}
        API->>Bandit: update(context, success=true)
        API->>JITAI: record_response → reset cooldown
    else User clicks "Not now"
        User->>Swift: dismissed = true
        Swift->>API: POST /interventions/respond {dismissed: true}
        API->>Bandit: update(context, success=false)
        API->>JITAI: record_response → increase cooldown
    else Panel auto-dismisses (15 seconds)
        TierMgr->>TierMgr: Auto-dismiss, no response recorded
    end


---

---
title: "ADHD Second Brain — Venting Chat → Coaching Response Sequence"
---
%% Shows the full pipeline when a user sends a message through the venting chat
%% (via Telegram Bot or Swift Vent Modal)

sequenceDiagram
    autonumber
    participant User as 👤 User (Telegram)
    participant TG as 📱 Telegram Bot
    participant API as ⚙️ POST /chat/message
    participant Sentic as 🧠 SenticNet Pipeline
    participant Safety as 🚨 Safety Check
    participant Hourglass as 🔄 Hourglass Mapper
    participant Memory as 🧩 Mem0 Memory
    participant MLX as 🤖 Qwen3-4B (MLX)
    participant DB as 💾 PostgreSQL

    User->>TG: "I can't focus on anything today<br/>and I feel like a complete failure"
    TG->>API: POST /chat/message<br/>{text: "...", source: "telegram", conversation_id: "..."}

    Note over API,Sentic: Step 1: SenticNet does the HARD part (emotion detection)

    API->>Sentic: full_analysis(text)

    par Safety tier (runs FIRST, non-negotiable)
        Sentic->>Safety: depression API → score: 45
        Sentic->>Safety: toxicity API → score: 55 (self-directed: "failure")
        Sentic->>Safety: intensity API → score: -72
        Safety-->>Sentic: level: "yellow" (concerning but not critical)
    and Emotion tier
        Sentic->>Sentic: emotion API → introspection: -0.6, temper: -0.3
        Sentic->>Sentic: polarity API → NEGATIVE (-0.78)
        Sentic->>Sentic: subjectivity → SUBJECTIVE
        Sentic->>Sentic: sarcasm → 12 (not sarcastic)
    and ADHD signals tier
        Sentic->>Sentic: engagement → -45
        Sentic->>Sentic: wellbeing → -38
        Sentic->>Sentic: concepts → ["failure", "focus", "inability"]
    end

    Sentic->>Hourglass: map_hourglass_to_adhd_state()
    Note over Hourglass: introspection: -0.6 (sadness)<br/>temper: -0.3 (mild anger)<br/>→ frustration_spiral detected<br/>→ EF domain: self_regulation_emotion
    Hourglass-->>Sentic: primary_adhd_state: "frustration_spiral"

    Sentic-->>API: SenticNetFullResult

    Note over API: Step 2: Safety check — is this a crisis?

    alt Safety level = CRITICAL (depression > 70 AND toxicity > 60)
        API-->>User: "I hear you. If things feel really heavy,<br/>these people can help: [crisis resources]"
        Note over API: STOP. No LLM. No coaching. Only compassion + resources.
    else Safety level = YELLOW or GREEN (this case)
        Note over API: Continue to Step 3
    end

    Note over API,MLX: Step 3: LLM does the EASY part (generate natural language)

    API->>Memory: search_relevant_context("frustration focus failure")
    Memory-->>API: Previous patterns: "User experiences focus crashes<br/>most often in afternoons. Breathing exercises<br/>helped 3 out of 4 times."

    API->>API: Determine thinking mode
    Note over API: intensity = 72 (> 60 threshold)<br/>→ use /think mode for deeper reasoning

    API->>MLX: generate_coaching_response()
    Note over MLX: Model loads if not already resident (~2-5s first time)

    Note over MLX: System prompt: ADHD coaching persona<br/>+ SenticNet context injected:<br/>"Emotion: frustration_spiral<br/>Intensity: -72/100<br/>Engagement: -45/100<br/>Concepts: failure, focus, inability<br/>ADHD state: frustration_spiral<br/>Safety: yellow"<br/>+ Memory context:<br/>"Breathing exercises helped 3/4 times"<br/>+ User message: "I can't focus on anything..."<br/>+ Mode: /think

    MLX->>MLX: Qwen3-4B generates response<br/>(~4-6 seconds with /think on M4)

    MLX-->>API: "That sounds really tough — not being able to<br/>focus when you want to is one of the most<br/>frustrating parts of ADHD. You're not a failure<br/>for having a hard focus day. A 2-minute breathing<br/>reset has helped you before — want to try that,<br/>or would talking it through help more?"

    Note over API,DB: Step 4: Store everything for pattern tracking

    API->>Memory: add_conversation_memory([user_msg, assistant_msg])
    API->>DB: INSERT INTO senticnet_analyses (emotion_profile, safety_flags, ...)
    API->>DB: INSERT INTO messages (role, content, senticnet_analysis, ...)

    API-->>TG: {response: "That sounds really tough...",<br/>senticnet: {emotion: "frustration_spiral", ...},<br/>thinking_mode: "think",<br/>used_llm: "Qwen/Qwen3-4B-4bit",<br/>latency_ms: 4200}
    TG-->>User: "That sounds really tough — not being able<br/>to focus when you want to is one of the most<br/>frustrating parts of ADHD. ..."

    Note over MLX: After 2 minutes idle → auto-unload to free 2.3 GB RAM


---

---
title: "ADHD Second Brain — Notification Tier State Machine"
---
%% Shows how an intervention escalates (or doesn't) through the 5-tier
%% calm notification architecture. The key insight: interventions are
%% QUEUED at trigger time and DELIVERED at next breakpoint.

stateDiagram-v2
    [*] --> Monitoring: App starts

    state Monitoring {
        [*] --> Scanning
        Scanning --> FocusDetected: behavioral_state = "focused"
        Scanning --> DriftDetected: distraction signals rising
        FocusDetected --> Scanning: focus ends (app switch)
        DriftDetected --> InterventionTriggered: JITAI rules + bandit approve

        state FocusDetected {
            [*] --> ProtectedFocus
            ProtectedFocus --> ProtectedFocus: ALL interventions suppressed
            ProtectedFocus --> WellbeingCheck: 4+ hours continuous
            note right of ProtectedFocus
                NEVER interrupt productive focus.
                This is the #1 design rule.
            end note
        }
    }

    InterventionTriggered --> CheckBreakpoint: Intervention queued

    state CheckBreakpoint {
        [*] --> WaitingForBreakpoint
        WaitingForBreakpoint --> BreakpointFound: App switch / tab burst / idle resume
        WaitingForBreakpoint --> Timeout: 5 minutes, no breakpoint
        BreakpointFound --> DeliverAtTier
        Timeout --> DowngradeToAmbient: Moment passed, go gentle
    }

    state DeliverAtTier {
        [*] --> SelectTier

        SelectTier --> Tier1_Ambient: Low urgency OR low recovery day
        SelectTier --> Tier2_Pulse: Moderate, first intervention of session
        SelectTier --> Tier3_Overlay: User actively distracted
        SelectTier --> Tier4_Toast: Sustained disengagement (5+ min)
        SelectTier --> Tier5_Full: SAFETY CRITICAL ONLY

        state Tier1_Ambient {
            [*] --> ColorShift
            note right of ColorShift
                Menu bar icon shifts
                green → amber.
                User may not notice.
                That's okay.
            end note
        }

        state Tier2_Pulse {
            [*] --> PulseAnimation
            note right of PulseAnimation
                Menu bar icon gently
                pulses. Peripheral
                awareness only.
            end note
        }

        state Tier3_Overlay {
            [*] --> ShowPanel
            ShowPanel --> WaitForResponse: NSPanel appears (non-activating)
            WaitForResponse --> ActionTaken: User clicks action button
            WaitForResponse --> Dismissed: User clicks "Not now"
            WaitForResponse --> AutoDismiss: 15 seconds timeout
            note right of ShowPanel
                CalmOverlayPanel:
                - Does NOT steal keyboard focus
                - Slides in from top-right
                - Max 2-3 sentences
                - Max 3 action choices
                - Auto-dismisses in 15s
            end note
        }

        state Tier4_Toast {
            [*] --> SystemNotification
            note right of SystemNotification
                macOS toast notification.
                Brief sound (optional).
                Used rarely.
            end note
        }

        state Tier5_Full {
            [*] --> CrisisPanel
            note right of CrisisPanel
                ONLY for safety-critical:
                depression > 70 AND toxicity > 60.
                Shows crisis resources.
                Pauses all other interventions.
            end note
        }
    }

    ActionTaken --> RecordSuccess: Bandit learns "good timing"
    Dismissed --> RecordDismissal: Bandit learns "bad timing"
    AutoDismiss --> Cooldown: No signal recorded

    RecordSuccess --> Cooldown
    RecordDismissal --> IncreaseCooldown: 3+ dismissals → longer cooldown

    Cooldown --> Monitoring: Default 5 min cooldown
    IncreaseCooldown --> Monitoring: Adaptive cooldown (up to 30 min)
    DowngradeToAmbient --> Monitoring: Show ambient indicator only


---

---
title: "ADHD Second Brain — Onboarding & Calibration Flow"
---
%% Shows the first-time user experience: permissions → optional integrations →
%% calibration period. Each screen is designed for ADHD attention spans
%% (under 60 seconds per screen).

flowchart TD
    Start([🚀 User installs app]) --> Welcome

    subgraph Screen1["Screen 1: Welcome + Permissions (~1 min)"]
        Welcome["Welcome! Let's set up your<br/>ADHD Second Brain 🧠"]
        Welcome --> Perm1["1️⃣ Accessibility Permission<br/><i>Needed for window titles (AXUIElement)</i><br/><i>One-time grant, NO monthly re-auth</i>"]
        Perm1 --> Perm2["2️⃣ Automation Permission<br/><i>Needed for browser URLs (AppleScript)</i><br/><i>Granted per-app on first use</i>"]
        Perm2 --> PermNote["ℹ️ No Screen Recording needed!<br/>Unlike Rize and other trackers,<br/>we use the Accessibility API only."]
    end

    PermNote --> Screen2

    subgraph Screen2["Screen 2: Optional Integrations (~30 sec)"]
        direction TB
        Whoop["Connect Whoop? (optional)<br/>[Connect via whoopskill CLI] [Skip]<br/><i>Enables morning briefings,<br/>recovery-aware interventions</i>"]
        TelegramSetup["Connect Telegram? (optional)<br/>[Setup Telegram Bot] [Skip]<br/><i>Enables venting chat +<br/>morning briefings via messaging</i>"]
        GoogleCal["Connect Google Calendar? (optional)<br/>[Connect via OAuth] [Skip]<br/><i>Enables calendar strip<br/>in Notch expanded panel</i>"]
        Whoop --> TelegramSetup --> GoogleCal
    end

    GoogleCal --> CalibrationStart

    subgraph CalibrationPeriod["14-Day Silent Calibration Period"]
        direction TB
        CalibrationStart["✅ Setup complete!<br/>'I'll learn your patterns over the next 2 weeks.<br/>You'll see me in your menu bar — that's it for now.'"]
        CalibrationStart --> Day1["Days 1-3: Collect baseline data<br/>• App usage patterns<br/>• Context switch frequency<br/>• Session duration distribution<br/>• Time-of-day patterns"]
        Day1 --> Day4["Days 4-7: Compute personal baselines<br/>• EWMA for each metric<br/>• Separate weekday/weekend"]
        Day4 --> Day8["Days 8-14: Test intervention thresholds<br/>• Set thresholds at 1.5 SD from personal mean<br/>• Ambient indicators start (Tier 1-2 only)"]
        Day8 --> CalibrationComplete["Calibration complete ✅<br/>Full system activated:<br/>• All notification tiers enabled<br/>• Adaptive bandit starts learning<br/>• Daily snapshots begin"]
    end

    %% Styling
    style Screen1 fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px
    style Screen2 fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px
    style CalibrationPeriod fill:#ECEFF1,stroke:#607D8B,stroke-width:2px
