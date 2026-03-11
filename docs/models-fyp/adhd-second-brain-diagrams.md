---
title: ADHD Second Brain — Complete UML Diagrams (FINAL)
---
%% This file contains 5 diagrams. Render each ```mermaid block separately.
%% Replaces architecture-diagram.mermaid (which is now outdated).
%%
%% DIAGRAM INDEX:
%% 1. Master Component Diagram — every subsystem and connection
%% 2. Screen Monitor → Intervention Sequence — the core real-time loop
%% 3. Venting Chat Sequence — emotion detection → coaching response
%% 4. Notification Tier State Machine — how interventions escalate
%% 5. Onboarding & Calibration Flow — first-time user experience


%% ═══════════════════════════════════════════════════════════════
%% DIAGRAM 1: MASTER COMPONENT DIAGRAM
%% Shows every subsystem from all 4 documents with correct models
%% ═══════════════════════════════════════════════════════════════

graph TB
    subgraph UserLayer["🖥️ USER INTERFACE LAYER"]
        direction LR
        SwiftApp["🍎 Swift Menu Bar App<br/><i>~25MB RAM, Accessibility API only</i><br/>─────────────<br/>• ScreenMonitor (AXUIElement)<br/>• BrowserMonitor (AppleScript)<br/>• IdleMonitor (IOHIDSystem)<br/>• TransitionDetector<br/>• PhenotypeCollector<br/>─────────────<br/>• AmbientMenuBar (Tier 1-2)<br/>• CalmOverlayPanel (Tier 3)<br/>• EMAPromptView<br/>• OnboardingFlow<br/>• PrivacyDashboard"]
        OpenClaw["🦞 OpenClaw Gateway<br/><i>Optional Interface</i><br/>─────────────<br/>• Telegram / WhatsApp<br/>• adhd-vent skill<br/>• morning-briefing skill<br/>• weekly-review skill"]
        Dashboard["📊 React Dashboard<br/><i>Optional Web UI</i><br/>─────────────<br/>• FocusTimeline<br/>• EmotionRadar (Hourglass)<br/>• WhoopCard<br/>• InterventionLog<br/>• ProgressView (XP)"]
    end

    subgraph BackendLayer["⚙️ PYTHON FASTAPI BACKEND (localhost:8420)"]
        direction TB

        subgraph APIRoutes["REST API Routes"]
            ScreenAPI["POST /screen/activity<br/><i>&lt;100ms</i>"]
            ChatAPI["POST /chat/message<br/><i>&lt;3s</i>"]
            WhoopAPI["GET /whoop/morning-briefing"]
            InsightsAPI["GET /insights/*"]
            OnboardingAPI["POST /onboarding/asrs<br/>POST /onboarding/profile"]
            EMAAPI["GET /ema/prompt<br/>POST /ema/response"]
            GamificationAPI["GET /gamification/daily"]
            CorrectAPI["POST /screen/correct-category"]
            PrivacyAPI["GET /privacy/export<br/>DELETE /privacy/all-data"]
        end

        subgraph MonitoringPipeline["📡 MONITORING PIPELINE (always-on, <100ms)"]
            ActivityClassifier["🏷️ Activity Classifier<br/>─────────────<br/>L1: App name rules (0.01ms)<br/>L2: URL domain lookup (0.01ms)<br/>L3: Title keywords (0.1ms)<br/>L4: all-MiniLM-L6-v2 (25ms)<br/>L0: User corrections (instant)"]

            MetricsEngine["📈 ADHD Metrics Engine<br/>─────────────<br/>• Context switch rate/5min<br/>• Focus score (0-100)<br/>• Distraction ratio (0-1)<br/>• Current streak minutes<br/>• Behavioral state"]

            TransitionDetector["🚦 Transition Detector<br/>─────────────<br/>• App switch events<br/>• Tab burst detection<br/>• Idle resume detection<br/>• Breakpoint freshness (10s)<br/>• Focus suppression gate"]

            HyperfocusClassifier["🔬 Hyperfocus Classifier<br/>─────────────<br/>• Productive (PROTECT)<br/>• Unproductive (gentle redirect)<br/>• Ambiguous (check-in at 60min)<br/>• 4hr wellbeing check"]
        end

        subgraph DecisionPipeline["🎯 DECISION PIPELINE"]
            JITAIEngine["🎯 JITAI Engine<br/>─────────────<br/>Gate 0: Transition required<br/>Gate 1: Hyperfocus protection<br/>Gate 2: Per-block cap (3/90min)<br/>Gate 3: Adaptive bandit<br/>─────────────<br/>Rules: distraction spiral,<br/>sustained disengagement,<br/>hyperfocus check,<br/>emotional escalation"]

            AdaptiveBandit["🎰 Thompson Sampling<br/>─────────────<br/>Context: hour, recovery,<br/>  recency, app category<br/>Learns WHEN to intervene<br/>~50-100 decisions to personalize"]

            NotificationTier["📢 Tier Selector<br/>─────────────<br/>T1: Ambient color shift<br/>T2: Gentle pulse<br/>T3: Non-activating overlay<br/>T4: Toast notification<br/>T5: Full (safety only)"]

            XAIExplainer["🔍 XAI Explainer<br/>─────────────<br/>• Concept Bottleneck<br/>• Progressive disclosure<br/>  (traffic light → sentence<br/>   → full detail)<br/>• User concept corrections"]
        end

        subgraph SenticPipeline["🧠 SenticNet Pipeline (emotion engine)"]
            SenticClient["SenticNet Client<br/><i>sentic.net/api/ + pip senticnet</i>"]

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

            HourglassMapper["🔄 Hourglass → ADHD State<br/>─────────────<br/>• boredom_disengagement<br/>• frustration_spiral<br/>• shame_rsd<br/>• productive_flow<br/>• emotional_dysregulation<br/>• anxiety_comorbid"]
        end

        subgraph CoachingPipeline["💬 COACHING PIPELINE (on-demand)"]
            ChatProcessor["💬 Chat Processor<br/>─────────────<br/>1. SenticNet analysis<br/>2. Safety check<br/>3. Build context<br/>4. /think or /no_think<br/>5. Generate response<br/>6. Store in memory"]

            MLXInference["🤖 MLX Inference<br/>─────────────<br/>Qwen3-4B 4-bit (~2.3GB)<br/>Load on demand (~2s)<br/>Unload after 2min idle<br/>30-40 tok/s on M4<br/>+ LoRA adapter (optional)"]
        end

        subgraph SupportSystems["🔧 SUPPORT SYSTEMS"]
            OnboardingService["📋 Onboarding<br/>─────────────<br/>• ASRS-v1.1 screener<br/>• ADHD profile creation<br/>• Subtype calibration<br/>• BRIEF-A upload (optional)<br/>• Medication tracking"]

            EMAService["📊 EMA Service<br/>─────────────<br/>• 2x daily check-ins<br/>• 3-5 slider items<br/>• Calibrates passive models<br/>• Ground truth for CBM"]

            GamificationService["🏆 Gamification<br/>─────────────<br/>• XP for focus/breaks<br/>• Variable rewards (PINCH)<br/>• Forgiveness streaks<br/>• NEVER punishment<br/>• 2-week reward rotation"]

            PhenotypeCollector["📱 Digital Phenotyping<br/>─────────────<br/>• 15-min behavior summaries<br/>• Switch variability (CV)<br/>• Typing speed/errors<br/>• Session bimodality<br/>• Medicated vs unmedicated"]

            WhoopService["💚 Whoop Service<br/>─────────────<br/>• OAuth 2.0 flow<br/>• Recovery / HRV / Sleep<br/>• Morning briefing gen<br/>• Separate med baselines"]

            MemoryService["🧩 Memory (Mem0)<br/>─────────────<br/>• Conversation history<br/>• Pattern storage<br/>• Intervention effectiveness<br/>• Context retrieval"]

            PrivacyService["🔒 Privacy (PDPA)<br/>─────────────<br/>• Zero-cloud default<br/>• 30-day auto-delete<br/>• Granular consent<br/>• Export / full delete"]
        end
    end

    subgraph DataLayer["💾 DATA LAYER"]
        direction LR
        PostgreSQL[("PostgreSQL + pgvector<br/>─────────────<br/>• activities<br/>• senticnet_analyses<br/>• interventions<br/>• whoop_data<br/>• messages<br/>• adhd_profiles<br/>• ema_responses<br/>• phenotype_summaries<br/>• gamification_events<br/>• concept_corrections<br/>• bandit_state<br/>• vector embeddings")]
        SQLite[("SQLite Cache<br/>─────────────<br/>• Offline activity buffer<br/>• User corrections<br/>• App category cache<br/>• Recent metrics")]
    end

    subgraph ExternalAPIs["☁️ EXTERNAL APIs"]
        SenticNetCloud["SenticNet Cloud<br/>sentic.net/api/"]
        WhoopCloud["Whoop API v2"]
        ClaudeAPI["Claude API<br/><i>Cloud fallback only</i>"]
    end

    subgraph OnDeviceModels["🧠 ON-DEVICE MODELS (Apple MLX)"]
        SentenceTransformer["all-MiniLM-L6-v2<br/>22M params, ~80MB<br/><i>Always resident</i>"]
        Qwen3["Qwen3-4B 4-bit<br/>4B params, ~2.3GB<br/><i>Load on demand</i>"]
        SenticNetLocal["SenticNet Python<br/>400K concepts, ~50MB<br/><i>Always resident</i>"]
    end

    %% === USER → BACKEND connections ===
    SwiftApp -->|"POST /screen/activity<br/>event-driven"| ScreenAPI
    SwiftApp -->|"POST /screen/correct-category"| CorrectAPI
    OpenClaw -->|"POST /chat/message"| ChatAPI
    OpenClaw -->|"GET /whoop/morning-briefing"| WhoopAPI
    Dashboard -->|"GET /insights/*"| InsightsAPI

    %% === MONITORING FLOW ===
    ScreenAPI --> ActivityClassifier
    ActivityClassifier --> MetricsEngine
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

    %% === MODEL connections ===
    ActivityClassifier -->|"Layer 4 fallback"| SentenceTransformer
    MLXInference --> Qwen3
    SenticClient --> SenticNetLocal
    SenticClient -->|"REST API (12 endpoints)"| SenticNetCloud

    %% === SUPPORT SYSTEM connections ===
    OnboardingAPI --> OnboardingService
    EMAAPI --> EMAService
    GamificationAPI --> GamificationService
    WhoopAPI --> WhoopService
    PrivacyAPI --> PrivacyService

    JITAIEngine -->|"Profile thresholds"| OnboardingService
    EMAService -->|"Calibration signals"| MetricsEngine
    GamificationService -->|"XP on focus/breaks"| MetricsEngine

    %% === DATA connections ===
    MetricsEngine --> PostgreSQL
    JITAIEngine --> PostgreSQL
    WhoopService --> PostgreSQL
    MemoryService --> PostgreSQL
    EMAService --> PostgreSQL
    GamificationService --> PostgreSQL
    PhenotypeCollector --> PostgreSQL
    OnboardingService --> PostgreSQL
    ActivityClassifier --> SQLite

    %% === EXTERNAL API connections ===
    WhoopService -->|"REST + OAuth"| WhoopCloud
    MLXInference -.->|"Fallback only"| ClaudeAPI

    %% === STYLING ===
    classDef swift fill:#007AFF,stroke:#005EC4,color:white,stroke-width:2px
    classDef openclaw fill:#E85D3A,stroke:#C44A2E,color:white,stroke-width:2px
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
    class OpenClaw openclaw
    class Dashboard dashboard
    class ScreenAPI,ChatAPI,WhoopAPI,InsightsAPI,OnboardingAPI,EMAAPI,GamificationAPI,CorrectAPI,PrivacyAPI api
    class ActivityClassifier,MetricsEngine,TransitionDetector,HyperfocusClassifier monitor
    class JITAIEngine,AdaptiveBandit,NotificationTier,XAIExplainer decision
    class SenticClient,Emotion,Polarity,Subjectivity,Sarcasm,Engagement,Wellbeing,ConceptParsing,Aspects,HourglassMapper sentic
    class Depression,Toxicity,Intensity safety
    class ChatProcessor,MLXInference coaching
    class OnboardingService,EMAService,GamificationService,PhenotypeCollector,WhoopService,MemoryService,PrivacyService support
    class PostgreSQL,SQLite db
    class SenticNetCloud,WhoopCloud,ClaudeAPI external
    class SentenceTransformer,Qwen3,SenticNetLocal model


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

    Note over API,Classify: Layer 1-4 classification (<25ms total)

    API->>Classify: classify("Safari", "Twitter / X", "x.com")
    Classify-->>Classify: L0: Check user corrections → miss
    Classify-->>Classify: L1: App name "safari" → "browser" (need URL)
    Classify-->>Classify: L2: URL "x.com" → "social_media" ✓
    Classify-->>API: ("social_media", 0.95)

    API->>Metrics: update(app="Safari", category="social_media")
    Metrics-->>Metrics: Record app switch event
    Metrics-->>Metrics: Increment context_switch_rate_5min
    Metrics-->>Metrics: Update distraction_ratio
    Metrics-->>Metrics: Compute behavioral_state = "distracted"
    Metrics-->>API: ADHDMetrics snapshot

    API->>Transition: detect_breakpoint_type()
    Transition-->>API: APP_SWITCH (fresh breakpoint available)

    API->>Hyperfocus: classify(session_minutes=2, ...)
    Hyperfocus-->>API: None (not in hyperfocus, session too short)

    API->>JITAI: evaluate(metrics, emotion_context=None)

    Note over JITAI: Gate 0: Transition available? ✅ (app switch)
    Note over JITAI: Gate 1: Hyperfocus protection? ✅ (not hyperfocusing)
    Note over JITAI: Gate 2: Per-block cap? ✅ (0/3 used this block)

    JITAI->>Bandit: should_deliver(context={hour: 14, recovery: "green", recency: "not_recent"})
    Bandit-->>JITAI: True (sampled reward > 0.5)

    Note over JITAI: Gate 3: Bandit approves ✅
    Note over JITAI: Rule match: context_switch_rate=8, distraction_ratio=0.3<br/>Below threshold — NO intervention yet

    JITAI-->>API: None (thresholds not met)
    API-->>Swift: {category: "social_media", metrics: {...}, intervention: null}

    Note over User,TierMgr: === 5 MINUTES LATER: USER STILL ON SOCIAL MEDIA ===

    Swift->>API: POST /screen/activity (periodic title change detected)
    API->>Classify: classify(...)
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

    API-->>Swift: {category: "social_media", metrics: {...}, intervention: {...}}

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
%% (via OpenClaw on Telegram/WhatsApp or direct Swift UI)

sequenceDiagram
    autonumber
    participant User as 👤 User (Telegram)
    participant OC as 🦞 OpenClaw
    participant API as ⚙️ POST /chat/message
    participant Sentic as 🧠 SenticNet Pipeline
    participant Safety as 🚨 Safety Check
    participant Hourglass as 🔄 Hourglass Mapper
    participant Memory as 🧩 Mem0 Memory
    participant MLX as 🤖 Qwen3-4B (MLX)
    participant DB as 💾 PostgreSQL

    User->>OC: "I can't focus on anything today<br/>and I feel like a complete failure"
    OC->>API: POST /chat/message<br/>{text: "...", source: "openclaw", conversation_id: "..."}

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
    Note over MLX: Model loads if not already resident (~2s first time)

    Note over MLX: System prompt: ADHD coaching persona<br/>+ SenticNet context injected:<br/>"Emotion: frustration_spiral<br/>Intensity: -72/100<br/>Engagement: -45/100<br/>Concepts: failure, focus, inability<br/>ADHD state: frustration_spiral<br/>Safety: yellow"<br/>+ Memory context:<br/>"Breathing exercises helped 3/4 times"<br/>+ User message: "I can't focus on anything..."<br/>+ Mode: /think

    MLX->>MLX: Qwen3-4B generates response<br/>(~4-6 seconds with /think on M4)

    MLX-->>API: "That sounds really tough — not being able to<br/>focus when you want to is one of the most<br/>frustrating parts of ADHD. You're not a failure<br/>for having a hard focus day. A 2-minute breathing<br/>reset has helped you before — want to try that,<br/>or would talking it through help more?"

    Note over API,DB: Step 4: Store everything for pattern tracking

    API->>Memory: add_conversation_memory([user_msg, assistant_msg])
    API->>DB: INSERT INTO senticnet_analyses (emotion_profile, safety_flags, ...)
    API->>DB: INSERT INTO messages (role, content, senticnet_analysis, ...)

    API-->>OC: {response: "That sounds really tough...",<br/>senticnet: {emotion: "frustration_spiral", ...},<br/>thinking_mode: "think"}
    OC-->>User: "That sounds really tough — not being able<br/>to focus when you want to is one of the most<br/>frustrating parts of ADHD. ..."

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
%% Shows the first-time user experience: ASRS screener → profile setup →
%% permissions → calibration period. Each screen is designed for ADHD
%% attention spans (under 60 seconds per screen).

flowchart TD
    Start([🚀 User installs app]) --> Welcome

    subgraph Screen1["Screen 1: Welcome + ASRS Screener (~2 min)"]
        Welcome["Welcome! Let's set up your<br/>ADHD Second Brain 🧠"]
        Welcome --> ASRS["ASRS-v1.1 Screener<br/>6 questions, 5-point scale<br/><i>Freely available WHO instrument</i>"]
        ASRS --> Score["Compute scores:<br/>• Total (0-24)<br/>• Dark-zone count (0-6)<br/>• Inattention sub (0-12)<br/>• Hyperactivity sub (0-12)"]
        Score --> Severity{Severity band?}
        Severity -->|0-9| LowNeg["Low negative<br/>sensitivity: 0.5<br/>fewer interventions"]
        Severity -->|10-13| HighNeg["High negative<br/>sensitivity: 0.75"]
        Severity -->|14-17| LowPos["Low positive<br/>sensitivity: 1.0<br/>standard"]
        Severity -->|18-24| HighPos["High positive<br/>sensitivity: 1.5<br/>more check-ins"]
    end

    LowNeg --> Screen2
    HighNeg --> Screen2
    LowPos --> Screen2
    HighPos --> Screen2

    subgraph Screen2["Screen 2: ADHD Profile (~1 min)"]
        direction TB
        ProfileQ1["What's your ADHD subtype?<br/>[Inattentive] [Hyperactive] [Combined] [Not sure]"]
        ProfileQ2["Are you currently on medication?<br/>[No] [Methylphenidate] [Amphetamine] [Other]"]
        ProfileQ3["What time do you take it? ___:___<br/><i>Used for separate HRV baselines</i>"]
        ProfileQ4["Optional: Upload BRIEF-A T-scores?<br/>[Skip] [Enter scores]<br/><i>BRI, MI, GEC scores from clinician</i>"]
        ProfileQ1 --> ProfileQ2 --> ProfileQ3 --> ProfileQ4
    end

    ProfileQ4 --> ComputeProfile["Compute derived parameters:<br/>• intervention_sensitivity<br/>• max_interventions_per_90min<br/>• focus_block_default_minutes<br/>• Subtype-specific intervention profile"]

    ComputeProfile --> Screen3

    subgraph Screen3["Screen 3: macOS Permissions (~30 sec)"]
        direction TB
        Perm1["1️⃣ Accessibility Permission<br/><i>Needed for window titles (AXUIElement)</i><br/><i>One-time grant, NO monthly re-auth</i>"]
        Perm2["2️⃣ Automation Permission<br/><i>Needed for browser URLs (AppleScript)</i><br/><i>Granted per-app on first use</i>"]
        PermNote["ℹ️ No Screen Recording needed!<br/>Unlike Rize and other trackers,<br/>we use the Accessibility API only."]
        Perm1 --> Perm2 --> PermNote
    end

    PermNote --> Screen4

    subgraph Screen4["Screen 4: Optional Integrations (~30 sec)"]
        direction TB
        Whoop["Connect Whoop? (optional)<br/>[Connect via OAuth] [Skip]<br/><i>Enables morning briefings,<br/>recovery-aware interventions</i>"]
        OpenClawSetup["Connect Telegram/WhatsApp? (optional)<br/>[Setup OpenClaw] [Skip]<br/><i>Enables venting chat +<br/>morning briefings via messaging</i>"]
        Whoop --> OpenClawSetup
    end

    OpenClawSetup --> CalibrationStart

    subgraph CalibrationPeriod["14-Day Silent Calibration Period"]
        direction TB
        CalibrationStart["✅ Setup complete!<br/>'I'll learn your patterns over the next 2 weeks.<br/>You'll see me in your menu bar — that's it for now.'"]
        CalibrationStart --> Day1["Days 1-3: Collect baseline data<br/>• App usage patterns<br/>• Context switch frequency<br/>• Session duration distribution<br/>• Time-of-day patterns"]
        Day1 --> Day4["Days 4-7: Compute personal baselines<br/>• EWMA for each metric<br/>• Separate medicated/unmedicated<br/>• Separate weekday/weekend"]
        Day4 --> Day8["Days 8-14: Test intervention thresholds<br/>• Set thresholds at 1.5 SD from personal mean<br/>• First EMA prompts begin (2x daily)<br/>• Ambient indicators start (Tier 1-2 only)"]
        Day8 --> CalibrationComplete["Calibration complete ✅<br/>Full system activated:<br/>• All notification tiers enabled<br/>• Adaptive bandit starts learning<br/>• Gamification XP begins"]
    end

    subgraph SubtypeProfiles["ADHD Subtype → System Behavior"]
        direction TB
        PI["ADHD-PI (Inattentive)<br/>─────────────<br/>• 20-min focus blocks<br/>• Max 3 interventions/90min<br/>• Task initiation scaffolding<br/>• Time management prompts<br/>• Written list suggestions<br/>• Gentler notification cadence"]
        HI["ADHD-HI (Hyperactive)<br/>─────────────<br/>• 15-min focus blocks<br/>• Max 4 interventions/90min<br/>• Movement break prompts<br/>• Impulse-control nudges<br/>• Fidget suggestions<br/>• More frequent check-ins"]
        Combined["ADHD-C (Combined)<br/>─────────────<br/>• 15-min focus blocks<br/>• Max 4 interventions/90min<br/>• Both initiation + impulse support<br/>• Emotional regulation priority<br/>• Shortest text in interventions"]
    end

    ComputeProfile -.->|"Subtype determines"| SubtypeProfiles

    %% Styling
    style Screen1 fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px
    style Screen2 fill:#E3F2FD,stroke:#2196F3,stroke-width:2px
    style Screen3 fill:#FFF3E0,stroke:#FF9800,stroke-width:2px
    style Screen4 fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px
    style CalibrationPeriod fill:#ECEFF1,stroke:#607D8B,stroke-width:2px
    style SubtypeProfiles fill:#FFF8E1,stroke:#FFC107,stroke-width:2px

