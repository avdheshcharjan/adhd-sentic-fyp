# ADHD Second Brain — Hybrid Architecture Technical Blueprint
## Code-Ready Implementation Plan for Claude Code

> **Project**: ADHD-focused "Second Brain" personal AI assistant using SenticNet + Explainable AI
> **Architecture**: Native Swift menu bar app + Python FastAPI backend + OpenClaw (optional chat interface)
> **Target**: macOS (Apple Silicon M1+), single-user, local-first

---

## TABLE OF CONTENTS

1. [Project Overview & Goals](#1-project-overview--goals)
2. [Repository Structure](#2-repository-structure)
3. [Phase 1: Python Backend (Core Engine)](#3-phase-1-python-backend)
4. [Phase 2: Native Swift Menu Bar App](#4-phase-2-native-swift-menu-bar-app)
5. [Phase 3: SenticNet Pipeline](#5-phase-3-senticnet-pipeline)
6. [Phase 4: Explainable AI & JITAI Engine](#6-phase-4-explainable-ai--jitai-engine)
7. [Phase 5: Whoop Integration](#7-phase-5-whoop-integration)
8. [Phase 6: Memory System](#8-phase-6-memory-system)
9. [Phase 7: On-Device LLM (Apple MLX)](#9-phase-7-on-device-llm-apple-mlx)
10. [Phase 8: OpenClaw Integration (Chat Interface)](#10-phase-8-openclaw-integration)
11. [Phase 9: Frontend Dashboard](#11-phase-9-frontend-dashboard)
12. [Data Models & Schemas](#12-data-models--schemas)
13. [API Contracts](#13-api-contracts)
14. [Configuration Files](#14-configuration-files)
15. [Environment & Dependencies](#15-environment--dependencies)
16. [Testing Strategy](#16-testing-strategy)
17. [Build Order & Critical Path](#17-build-order--critical-path)

---

## 1. PROJECT OVERVIEW & GOALS

### What This System Does
An always-on macOS menu bar application that:
- Monitors screen activity (active app, window title, browser URL, idle state) every 2-3 seconds
- Detects ADHD behavioral patterns: rapid context switching, distraction spirals, hyperfocus on wrong tasks, procrastination
- Processes behavioral + text data through SenticNet's 13 affective computing APIs
- Generates explainable, evidence-based ADHD interventions using a Concept Bottleneck XAI architecture
- Integrates Whoop physiological data (HRV, sleep, recovery) for morning briefings and context-aware recommendations
- Provides a venting/chat interface (via OpenClaw on Telegram/WhatsApp) for emotional regulation support
- Maintains long-term memory of patterns, preferences, and intervention effectiveness

### Architecture Summary
```
┌─────────────────────────────────────────────────────────────────┐
│                     USER'S MACBOOK                              │
│                                                                 │
│  ┌──────────────────────┐     ┌──────────────────────────────┐  │
│  │  Swift Menu Bar App  │────▶│  Python FastAPI Backend       │  │
│  │  (Screen Monitor +   │◀────│  (localhost:8420)             │  │
│  │   Notification UI)   │     │                              │  │
│  │  ~25MB RAM           │     │  ├── SenticNet Pipeline      │  │
│  └──────────────────────┘     │  ├── JITAI Decision Engine   │  │
│                               │  ├── Whoop Service           │  │
│  ┌──────────────────────┐     │  ├── MLX Model Inference     │  │
│  │  OpenClaw Gateway    │────▶│  ├── Memory (Mem0 + PG)      │  │
│  │  (Telegram/WhatsApp) │◀────│  └── XAI Explanation Engine  │  │
│  │  Optional interface  │     │  ~500MB RAM (with models)    │  │
│  └──────────────────────┘     └──────────────────────────────┘  │
│                                         │                       │
│                               ┌─────────▼──────────┐           │
│                               │  PostgreSQL + pgvec │           │
│                               │  SQLite (cache)     │           │
│                               └────────────────────┘            │
│                                         │                       │
│                               ┌─────────▼──────────┐           │
│                               │  Whoop Cloud API    │           │
│                               │  SenticNet Cloud    │           │
│                               └────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. REPOSITORY STRUCTURE

```
adhd-second-brain/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml                    # PostgreSQL + pgvector
│
├── backend/                              # Python FastAPI backend
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── main.py                           # FastAPI app entry point
│   ├── config.py                         # Settings & env vars
│   │
│   ├── api/                              # REST API routes
│   │   ├── __init__.py
│   │   ├── screen.py                     # POST /screen/activity
│   │   ├── chat.py                       # POST /chat/message
│   │   ├── whoop.py                      # GET /whoop/morning-briefing
│   │   ├── insights.py                   # GET /insights/daily, /weekly
│   │   ├── interventions.py              # GET /interventions/current
│   │   └── health.py                     # GET /health
│   │
│   ├── services/                         # Business logic
│   │   ├── __init__.py
│   │   ├── senticnet_pipeline.py         # 13-API orchestration
│   │   ├── senticnet_client.py           # HTTP client for SenticNet APIs
│   │   ├── activity_classifier.py        # App/URL categorization
│   │   ├── adhd_metrics.py               # Context switch rate, focus score, etc.
│   │   ├── jitai_engine.py               # Just-in-Time Adaptive Intervention engine
│   │   ├── xai_explainer.py              # Concept bottleneck + counterfactual explanations
│   │   ├── whoop_service.py              # Whoop API client + data processing
│   │   ├── chat_processor.py             # Venting chat processing pipeline
│   │   ├── morning_briefing.py           # Morning briefing generation
│   │   ├── mlx_inference.py              # On-device LLM via MLX
│   │   └── memory_service.py             # Mem0 wrapper + pattern storage
│   │
│   ├── models/                           # Pydantic data models
│   │   ├── __init__.py
│   │   ├── screen_activity.py
│   │   ├── senticnet_result.py
│   │   ├── adhd_state.py
│   │   ├── intervention.py
│   │   ├── whoop_data.py
│   │   ├── chat_message.py
│   │   └── explanation.py
│   │
│   ├── db/                               # Database layer
│   │   ├── __init__.py
│   │   ├── database.py                   # PostgreSQL + pgvector connection
│   │   ├── migrations/                   # Alembic migrations
│   │   └── repositories/
│   │       ├── activity_repo.py
│   │       ├── intervention_repo.py
│   │       ├── whoop_repo.py
│   │       └── pattern_repo.py
│   │
│   ├── knowledge/                        # Static knowledge bases
│   │   ├── app_categories.json           # App name → category mapping
│   │   ├── url_categories.json           # Domain → category mapping
│   │   ├── adhd_interventions.json       # Evidence-based intervention library
│   │   └── barkley_ef_model.json         # Barkley's 5 EF deficit domains
│   │
│   └── tests/
│       ├── test_senticnet_pipeline.py
│       ├── test_jitai_engine.py
│       ├── test_activity_classifier.py
│       └── test_adhd_metrics.py
│
├── swift-app/                            # Native macOS menu bar app
│   ├── Package.swift
│   ├── ADHDSecondBrain/
│   │   ├── App.swift                     # @main entry, NSApplication setup
│   │   ├── AppDelegate.swift             # Menu bar, status item, permissions
│   │   ├── Info.plist                    # LSUIElement = true (no dock icon)
│   │   │
│   │   ├── Monitors/
│   │   │   ├── ScreenMonitor.swift       # NSWorkspace + CGWindowList
│   │   │   ├── BrowserMonitor.swift      # AppleScript URL extraction
│   │   │   ├── IdleMonitor.swift         # IOHIDSystem idle detection
│   │   │   └── MonitorCoordinator.swift  # Combines all monitors
│   │   │
│   │   ├── Networking/
│   │   │   ├── BackendClient.swift       # HTTP client to Python backend
│   │   │   └── Models.swift              # Codable structs matching API
│   │   │
│   │   ├── UI/
│   │   │   ├── MenuBarView.swift         # Status bar menu
│   │   │   ├── InterventionPopup.swift   # Non-intrusive notification popup
│   │   │   ├── DashboardWindow.swift     # Detailed stats window
│   │   │   ├── OnboardingView.swift      # Permission setup wizard
│   │   │   └── FocusSessionView.swift    # Pomodoro-style focus mode
│   │   │
│   │   └── Utilities/
│   │       ├── Permissions.swift         # TCC permission checks
│   │       └── Logger.swift
│   │
│   └── ADHDSecondBrainTests/
│
├── openclaw-skills/                      # OpenClaw custom skills
│   ├── adhd-vent/
│   │   └── SKILL.md                      # Venting chat skill
│   ├── morning-briefing/
│   │   └── SKILL.md                      # Whoop morning briefing skill
│   ├── focus-check/
│   │   └── SKILL.md                      # On-demand focus status skill
│   └── weekly-review/
│       └── SKILL.md                      # Weekly ADHD pattern review
│
├── dashboard/                            # Optional web dashboard (React)
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── FocusTimeline.jsx         # Daily focus/distraction timeline
│   │   │   ├── EmotionRadar.jsx          # Hourglass emotion visualization
│   │   │   ├── WhoopCard.jsx             # Recovery/sleep/HRV display
│   │   │   ├── InterventionLog.jsx       # Past interventions & effectiveness
│   │   │   └── WeeklyReport.jsx          # Weekly pattern summary
│   │   └── hooks/
│   │       └── useBackendAPI.js
│   └── vite.config.js
│
├── scripts/
│   ├── setup.sh                          # One-command project setup
│   ├── start.sh                          # Launch all services
│   ├── seed_categories.py                # Populate app/URL categories
│   └── test_senticnet_keys.py            # Validate API keys
│
└── docs/
    ├── ARCHITECTURE.md
    ├── SENTICNET_MAPPING.md              # How each API maps to ADHD
    ├── XAI_FRAMEWORK.md                  # Explainability design doc
    └── WHOOP_INTEGRATION.md
```

---

## 3. PHASE 1: PYTHON BACKEND

### Priority: BUILD THIS FIRST. Everything depends on it.

### 3.1 FastAPI Application Setup

**File: `backend/main.py`**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api import screen, chat, whoop, insights, interventions, health
from db.database import init_db
from services.memory_service import init_memory
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_memory()
    yield

app = FastAPI(
    title="ADHD Second Brain Backend",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(screen.router, prefix="/screen", tags=["screen"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(whoop.router, prefix="/whoop", tags=["whoop"])
app.include_router(insights.router, prefix="/insights", tags=["insights"])
app.include_router(interventions.router, prefix="/interventions", tags=["interventions"])
app.include_router(health.router, tags=["health"])
```

**File: `backend/config.py`**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://adhd:adhd@localhost:5432/adhd_brain"
    SQLITE_PATH: str = "./data/cache.db"

    # SenticNet API Keys (from sentic.txt)
    SENTICNET_BASE_URL: str = "https://sentic.net/api"
    SENTICNET_LANG: str = "en"
    SENTIC_CONCEPT_PARSING: str = "<YOUR_CONCEPT_PARSING_KEY>"
    SENTIC_SUBJECTIVITY: str = "<YOUR_SUBJECTIVITY_DETECTION_KEY>"
    SENTIC_POLARITY: str = "<YOUR_POLARITY_CLASSIFICATION_KEY>"
    SENTIC_INTENSITY: str = "<YOUR_INTENSITY_RANKING_KEY>"
    SENTIC_EMOTION: str = "<YOUR_EMOTION_RECOGNITION_KEY>"
    SENTIC_ASPECT: str = "<YOUR_ASPECT_EXTRACTION_KEY>"
    SENTIC_PERSONALITY: str = "<YOUR_PERSONALITY_PREDICTION_KEY>"
    SENTIC_SARCASM: str = "<YOUR_SARCASM_IDENTIFICATION_KEY>"
    SENTIC_DEPRESSION: str = "<YOUR_DEPRESSION_CATEGORIZATION_KEY>"
    SENTIC_TOXICITY: str = "<YOUR_TOXICITY_SPOTTING_KEY>"
    SENTIC_ENGAGEMENT: str = "<YOUR_ENGAGEMENT_MEASUREMENT_KEY>"
    SENTIC_WELLBEING: str = "<YOUR_WELL_BEING_ASSESSMENT_KEY>"
    SENTIC_ENSEMBLE: str = "<YOUR_ENSEMBLE_KEY>"

    # Whoop
    WHOOP_CLIENT_ID: str = ""
    WHOOP_CLIENT_SECRET: str = ""
    WHOOP_REDIRECT_URI: str = "http://localhost:8420/whoop/callback"
    WHOOP_ACCESS_TOKEN: str = ""  # After OAuth flow
    WHOOP_REFRESH_TOKEN: str = ""

    # LLM
    ANTHROPIC_API_KEY: str = ""       # Claude for complex coaching
    OPENAI_API_KEY: str = ""          # GPT-4o-mini for frequent tasks
    MLX_MODEL_PATH: str = "./models/llama-3.2-3b-instruct-4bit"

    # Memory
    MEM0_API_KEY: str = ""            # Or self-hosted

    # App
    BACKEND_PORT: int = 8420
    LOG_LEVEL: str = "INFO"
    INTERVENTION_COOLDOWN_SECONDS: int = 300  # 5 min between interventions

    class Config:
        env_file = ".env"

settings = Settings()
```

### 3.2 Screen Activity Endpoint

This is the primary endpoint the Swift app calls every 2-3 seconds.

**File: `backend/api/screen.py`**
```python
from fastapi import APIRouter, BackgroundTasks
from models.screen_activity import ScreenActivityInput, ScreenActivityResponse
from services.activity_classifier import classify_activity
from services.adhd_metrics import update_metrics, get_current_state
from services.jitai_engine import evaluate_intervention_need

router = APIRouter()

@router.post("/activity", response_model=ScreenActivityResponse)
async def report_activity(
    activity: ScreenActivityInput,
    background_tasks: BackgroundTasks
):
    """
    Called by Swift app every 2-3 seconds with current screen state.
    Returns immediate classification + any pending intervention.
    Must respond in <100ms to not block the Swift monitor loop.
    """
    # Step 1: Classify the activity (rule-based, <5ms)
    category = classify_activity(
        app_name=activity.app_name,
        window_title=activity.window_title,
        url=activity.url
    )

    # Step 2: Update rolling ADHD metrics (in-memory, <1ms)
    metrics = update_metrics(
        app_name=activity.app_name,
        category=category,
        timestamp=activity.timestamp,
        is_idle=activity.is_idle
    )

    # Step 3: Check if intervention is needed (rule engine, <2ms)
    intervention = evaluate_intervention_need(metrics)

    # Step 4: Background tasks (async, don't block response)
    background_tasks.add_task(persist_activity, activity, category, metrics)

    if intervention and intervention.requires_senticnet:
        background_tasks.add_task(
            enrich_intervention_with_senticnet,
            intervention,
            activity.window_title
        )

    return ScreenActivityResponse(
        category=category,
        metrics=metrics.to_summary(),
        intervention=intervention
    )
```

### 3.3 Chat/Venting Endpoint

**File: `backend/api/chat.py`**
```python
from fastapi import APIRouter
from models.chat_message import ChatInput, ChatResponse
from services.chat_processor import process_vent_message

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def process_message(message: ChatInput):
    """
    Process a venting/chat message through the full SenticNet pipeline
    + LLM reasoning. Called by OpenClaw skill or direct UI.

    Pipeline:
    1. SenticNet emotion recognition → identify emotional state
    2. SenticNet depression + toxicity → safety check
    3. SenticNet intensity → escalation detection
    4. SenticNet subjectivity → route to emotional vs practical support
    5. LLM generates response using SenticNet context
    6. Store in memory for pattern tracking
    """
    return await process_vent_message(
        text=message.text,
        user_context=message.context,
        conversation_id=message.conversation_id
    )
```

---

## 4. PHASE 2: NATIVE SWIFT MENU BAR APP

### 4.1 Core Architecture

The Swift app is a lightweight, event-driven menu bar agent. It does NOT do any ML inference or heavy processing — it captures screen state and sends it to the Python backend.

**File: `swift-app/ADHDSecondBrain/Info.plist`** — Key entries:
```xml
<key>LSUIElement</key>
<true/>  <!-- No dock icon, menu bar only -->
<key>NSScreenCaptureUsageDescription</key>
<string>ADHD Second Brain needs screen access to monitor your focus patterns and detect distraction.</string>
<key>NSAppleEventsUsageDescription</key>
<string>ADHD Second Brain needs automation access to read browser URLs for activity tracking.</string>
```

### 4.2 Screen Monitor Implementation

**File: `swift-app/ADHDSecondBrain/Monitors/ScreenMonitor.swift`**

Key implementation details for Claude Code:

```swift
import Cocoa
import AppKit

class ScreenMonitor: ObservableObject {
    @Published var currentApp: String = ""
    @Published var currentTitle: String = ""
    @Published var currentURL: String? = nil
    @Published var isIdle: Bool = false

    private var appSwitchObserver: NSObjectProtocol?
    private var pollingTimer: Timer?
    private let backendClient: BackendClient

    // CRITICAL: Use NSWorkspace notification for app switches (event-driven, zero CPU)
    func startMonitoring() {
        // 1. App switch detection — event-driven, not polling
        appSwitchObserver = NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification,
            object: nil,
            queue: .main
        ) { [weak self] notification in
            guard let app = notification.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication else { return }
            self?.handleAppSwitch(app)
        }

        // 2. Window title polling — every 2 seconds
        //    (titles change without app switches, e.g. switching browser tabs)
        pollingTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { [weak self] _ in
            self?.captureCurrentState()
        }
    }

    private func captureCurrentState() {
        // Get active window info via CGWindowList
        // REQUIRES: Screen Recording permission
        guard let windowList = CGWindowListCopyWindowInfo(
            [.optionOnScreenOnly, .excludeDesktopElements],
            kCGNullWindowID
        ) as? [[String: Any]] else { return }

        // Find the frontmost window
        if let frontWindow = windowList.first(where: { ($0["kCGWindowLayer"] as? Int) == 0 }) {
            let title = frontWindow["kCGWindowName"] as? String ?? ""
            let owner = frontWindow["kCGWindowOwnerName"] as? String ?? ""

            // Extract browser URL if applicable
            var url: String? = nil
            let browsers = ["Google Chrome", "Safari", "Firefox", "Brave Browser", "Arc", "Microsoft Edge"]
            if browsers.contains(owner) {
                url = BrowserMonitor.getActiveTabURL(browser: owner)
            }

            // Send to backend
            Task {
                await backendClient.reportActivity(
                    appName: owner,
                    windowTitle: title,
                    url: url,
                    isIdle: isIdle
                )
            }
        }
    }
}
```

**File: `swift-app/ADHDSecondBrain/Monitors/BrowserMonitor.swift`**

```swift
import Foundation

class BrowserMonitor {
    /// Extract active tab URL via AppleScript
    /// REQUIRES: Automation permission for each browser
    static func getActiveTabURL(browser: String) -> String? {
        let script: String
        switch browser {
        case "Google Chrome", "Brave Browser", "Microsoft Edge":
            // Chrome-based browsers share the same AppleScript API
            script = """
            tell application "\(browser)"
                return URL of active tab of front window
            end tell
            """
        case "Safari":
            script = """
            tell application "Safari"
                return URL of front document
            end tell
            """
        case "Arc":
            script = """
            tell application "Arc"
                return URL of active tab of front window
            end tell
            """
        default:
            return nil  // Firefox requires AXUIElement fallback
        }

        let appleScript = NSAppleScript(source: script)
        var error: NSDictionary?
        let result = appleScript?.executeAndReturnError(&error)
        return result?.stringValue
    }
}
```

**File: `swift-app/ADHDSecondBrain/Monitors/IdleMonitor.swift`**

```swift
import IOKit

class IdleMonitor {
    /// Returns seconds since last keyboard/mouse input
    /// REQUIRES: No special permissions
    static func getIdleTime() -> TimeInterval {
        var iterator: io_iterator_t = 0
        guard IOServiceGetMatchingServices(
            kIOMainPortDefault,
            IOServiceMatching("IOHIDSystem"),
            &iterator
        ) == KERN_SUCCESS else { return 0 }

        let entry = IOIteratorNext(iterator)
        defer {
            IOObjectRelease(entry)
            IOObjectRelease(iterator)
        }

        var unmanagedDict: Unmanaged<CFMutableDictionary>?
        guard IORegistryEntryCreateCFProperties(
            entry, &unmanagedDict, kCFAllocatorDefault, 0
        ) == KERN_SUCCESS else { return 0 }

        guard let dict = unmanagedDict?.takeRetainedValue() as? [String: Any],
              let idleTime = dict["HIDIdleTime"] as? Int64 else { return 0 }

        return TimeInterval(idleTime) / 1_000_000_000 // nanoseconds to seconds
    }
}
```

### 4.3 Intervention Popup UI

**File: `swift-app/ADHDSecondBrain/UI/InterventionPopup.swift`**

Design principles for ADHD notifications:
- Max 2-3 sentences (working memory deficits)
- 2-3 action choices max (decision fatigue)
- Non-modal, non-blocking (doesn't steal focus)
- Slides in from top-right corner, auto-dismisses in 15 seconds
- "Dismiss" button that triggers a 5-minute cooldown
- Uses system `NSPanel` with `.nonactivatingPanel` style mask so it doesn't steal focus

```swift
import SwiftUI

struct InterventionCard: View {
    let intervention: Intervention
    let onAction: (InterventionAction) -> Void
    let onDismiss: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Emotion acknowledgment first (validate before suggesting)
            Text(intervention.acknowledgment)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.secondary)

            // Short suggestion
            Text(intervention.suggestion)
                .font(.system(size: 15, weight: .semibold))
                .foregroundColor(.primary)

            // 2-3 action choices as buttons
            HStack(spacing: 8) {
                ForEach(intervention.actions, id: \.id) { action in
                    Button(action.emoji + " " + action.label) {
                        onAction(action)
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }

                Spacer()

                Button("Not now") {
                    onDismiss()
                }
                .foregroundColor(.secondary)
                .font(.system(size: 12))
            }
        }
        .padding(16)
        .frame(width: 340)
        .background(.ultraThinMaterial)
        .cornerRadius(12)
        .shadow(radius: 8)
    }
}
```

### 4.4 macOS Permissions Onboarding

The app must request 3 permissions on first launch. Guide the user through each:

```swift
class PermissionsChecker {
    // 1. Screen Recording — needed for CGWindowListCopyWindowInfo to return window titles
    static var hasScreenRecording: Bool {
        CGPreflightScreenCaptureAccess()
    }
    static func requestScreenRecording() {
        CGRequestScreenCaptureAccess()
    }

    // 2. Accessibility — needed for AXUIElement window observation
    static var hasAccessibility: Bool {
        AXIsProcessTrusted()
    }
    static func requestAccessibility() {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue(): true] as CFDictionary
        AXIsProcessTrustedWithOptions(options)
    }

    // 3. Automation — needed for AppleScript browser URL extraction
    //    This is per-app, granted when first AppleScript runs
    //    No pre-check available; handle errors gracefully
}
```

---

## 5. PHASE 3: SENTICNET PIPELINE

### 5.1 SenticNet HTTP Client

**File: `backend/services/senticnet_client.py`**

```python
import httpx
import asyncio
from typing import Optional
from config import settings

class SenticNetClient:
    """
    HTTP client for SenticNet's 13 REST APIs.

    API format: sentic.net/api/{LANG}/{KEY}.py?text={TEXT}
    - TEXT: URL-encoded, max ~1000 words (8000 chars server limit)
    - Illegal chars: & # ; { } → replace with : or remove
    - Keys are case-sensitive and IP-locked
    """

    BASE_URL = "https://sentic.net/api"

    # Map API names to keys from config
    API_KEYS = {
        "concept_parsing":    settings.SENTIC_CONCEPT_PARSING,
        "subjectivity":       settings.SENTIC_SUBJECTIVITY,
        "polarity":           settings.SENTIC_POLARITY,
        "intensity":          settings.SENTIC_INTENSITY,
        "emotion":            settings.SENTIC_EMOTION,
        "aspect":             settings.SENTIC_ASPECT,
        "personality":        settings.SENTIC_PERSONALITY,
        "sarcasm":            settings.SENTIC_SARCASM,
        "depression":         settings.SENTIC_DEPRESSION,
        "toxicity":           settings.SENTIC_TOXICITY,
        "engagement":         settings.SENTIC_ENGAGEMENT,
        "wellbeing":          settings.SENTIC_WELLBEING,
        "ensemble":           settings.SENTIC_ENSEMBLE,
    }

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.lang = settings.SENTICNET_LANG

    def _sanitize_text(self, text: str) -> str:
        """Remove illegal characters per SenticNet API spec."""
        for char in ['&', '#', ';', '{', '}']:
            text = text.replace(char, ':')
        return text[:8000]  # Server limit

    async def call_api(self, api_name: str, text: str) -> dict:
        """Call a single SenticNet API and return parsed JSON."""
        key = self.API_KEYS[api_name]
        sanitized = self._sanitize_text(text)
        url = f"{self.BASE_URL}/{self.lang}/{key}.py"
        response = await self.client.get(url, params={"text": sanitized})
        response.raise_for_status()
        return response.json()

    async def call_multiple(self, api_names: list[str], text: str) -> dict:
        """Call multiple APIs concurrently for the same text."""
        tasks = [self.call_api(name, text) for name in api_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            name: result for name, result in zip(api_names, results)
            if not isinstance(result, Exception)
        }
```

### 5.2 SenticNet Pipeline Orchestrator

**File: `backend/services/senticnet_pipeline.py`**

```python
from services.senticnet_client import SenticNetClient
from models.senticnet_result import (
    SenticNetFullResult,
    EmotionProfile,
    SafetyFlags,
    ADHDRelevantSignals
)

class SenticNetPipeline:
    """
    Orchestrates all 13 SenticNet APIs in a structured pipeline.

    For CHAT/VENTING: Runs full pipeline (all 13 APIs)
    For SCREEN MONITORING: Runs lightweight subset (emotion + engagement + wellbeing)
    For SAFETY CHECKS: Runs depression + toxicity + intensity only
    """

    def __init__(self):
        self.client = SenticNetClient()

    async def full_analysis(self, text: str) -> SenticNetFullResult:
        """Full 13-API analysis for chat/venting messages."""

        # Tier 1: Safety-critical (run first, fail fast)
        safety = await self.client.call_multiple(
            ["depression", "toxicity", "intensity"], text
        )
        safety_flags = self._check_safety(safety)
        if safety_flags.is_critical:
            return self._emergency_result(safety_flags, text)

        # Tier 2: Core emotional analysis
        emotional = await self.client.call_multiple(
            ["emotion", "polarity", "subjectivity", "sarcasm"], text
        )

        # Tier 3: ADHD-specific signals
        adhd_relevant = await self.client.call_multiple(
            ["engagement", "wellbeing", "concept_parsing", "aspect"], text
        )

        # Tier 4: Deep analysis (run only if needed)
        deep = await self.client.call_multiple(
            ["personality", "ensemble"], text
        )

        return SenticNetFullResult(
            emotion_profile=self._build_emotion_profile(emotional),
            safety_flags=safety_flags,
            adhd_signals=self._build_adhd_signals(adhd_relevant, safety),
            concepts=adhd_relevant.get("concept_parsing", {}),
            aspects=adhd_relevant.get("aspect", {}),
            personality=deep.get("personality", {}),
            ensemble=deep.get("ensemble", {}),
            raw_results={**safety, **emotional, **adhd_relevant, **deep}
        )

    async def lightweight_analysis(self, text: str) -> dict:
        """Quick analysis for window titles during screen monitoring.
        Only runs 3 APIs to keep latency < 500ms."""
        return await self.client.call_multiple(
            ["emotion", "engagement", "intensity"], text
        )

    async def safety_check(self, text: str) -> SafetyFlags:
        """Fast safety-only check for escalation detection."""
        results = await self.client.call_multiple(
            ["depression", "toxicity", "intensity"], text
        )
        return self._check_safety(results)

    def _check_safety(self, results: dict) -> SafetyFlags:
        """
        Safety thresholds (calibrate during eval):
        - Depression > 70 AND Toxicity > 60 → CRITICAL (show resources)
        - Depression > 70 OR Intensity < -80 → HIGH (gentle check-in)
        - Toxicity > 50 (self-directed) → MODERATE (validate feelings)
        """
        depression_score = self._extract_score(results.get("depression", {}))
        toxicity_score = self._extract_score(results.get("toxicity", {}))
        intensity_score = self._extract_score(results.get("intensity", {}))

        is_critical = depression_score > 70 and toxicity_score > 60
        is_high = depression_score > 70 or intensity_score < -80
        is_moderate = toxicity_score > 50

        return SafetyFlags(
            level="critical" if is_critical else "high" if is_high else "moderate" if is_moderate else "normal",
            depression_score=depression_score,
            toxicity_score=toxicity_score,
            intensity_score=intensity_score,
            is_critical=is_critical
        )

    def _build_emotion_profile(self, emotional: dict) -> EmotionProfile:
        """Map SenticNet Hourglass emotions to ADHD-relevant states."""
        emotion_data = emotional.get("emotion", {})
        sarcasm_score = self._extract_score(emotional.get("sarcasm", {}))
        polarity = emotional.get("polarity", {})
        subjectivity = emotional.get("subjectivity", {})

        return EmotionProfile(
            primary_emotion=emotion_data.get("label", "neutral"),
            hourglass_dimensions={
                "pleasantness": emotion_data.get("pleasantness", 0),
                "attention": emotion_data.get("attention", 0),
                "sensitivity": emotion_data.get("sensitivity", 0),
                "aptitude": emotion_data.get("aptitude", 0),
            },
            polarity=polarity.get("label", "neutral"),
            polarity_score=self._extract_score(polarity),
            is_subjective=subjectivity.get("label") == "SUBJECTIVE",
            sarcasm_score=sarcasm_score,
            sarcasm_detected=sarcasm_score > 60
        )

    def _build_adhd_signals(self, adhd: dict, safety: dict) -> ADHDRelevantSignals:
        """Extract ADHD-specific signals from SenticNet outputs."""
        engagement = self._extract_score(adhd.get("engagement", {}))
        wellbeing = self._extract_score(adhd.get("wellbeing", {}))
        intensity = self._extract_score(safety.get("intensity", {}))

        return ADHDRelevantSignals(
            engagement_score=engagement,
            wellbeing_score=wellbeing,
            intensity_score=intensity,
            # ADHD pattern detection:
            is_disengaged=engagement < -30,
            is_overwhelmed=intensity > 70 and wellbeing < -20,
            is_frustrated=intensity < -50 and engagement < 0,
            emotional_dysregulation=abs(intensity) > 80
        )

    def _extract_score(self, result: dict) -> float:
        """Extract numeric score from SenticNet API response.
        API returns vary — adapt parsing to actual response format."""
        if isinstance(result, (int, float)):
            return float(result)
        if isinstance(result, dict):
            for key in ["score", "value", "intensity", "confidence"]:
                if key in result:
                    return float(result[key])
        return 0.0
```

---

## 6. PHASE 4: EXPLAINABLE AI & JITAI ENGINE

### 6.1 ADHD Metrics Calculator

**File: `backend/services/adhd_metrics.py`**

```python
from collections import deque
from datetime import datetime, timedelta
from dataclasses import dataclass, field

@dataclass
class ADHDMetrics:
    """Rolling ADHD behavioral metrics computed from screen data."""

    # Core metrics (updated every 2 seconds)
    context_switch_rate_5min: float = 0.0     # switches per 5 minutes
    focus_score: float = 0.0                   # 0-100, % time in 15+ min uninterrupted sessions
    distraction_ratio: float = 0.0             # 0-1, time in distracting vs productive apps
    current_streak_minutes: float = 0.0        # minutes on current app/task
    hyperfocus_detected: bool = False           # 3+ hrs on single non-priority task

    # Derived states
    behavioral_state: str = "unknown"          # focused | multitasking | distracted | hyperfocused | idle

    # Thresholds (calibrate per user over time)
    HIGH_SWITCH_RATE: float = 12.0             # >12 switches/5min = high distraction
    LOW_FOCUS_SCORE: float = 30.0              # <30% focused time = intervention needed
    HYPERFOCUS_THRESHOLD_MINUTES: float = 180  # 3 hours

class MetricsEngine:
    """
    In-memory rolling window metrics engine.
    Stores last 30 minutes of activity for real-time computation.
    """

    def __init__(self):
        self.activity_log: deque = deque(maxlen=900)  # 30 min at 2s intervals
        self.app_switches: deque = deque(maxlen=150)  # last 5 min of switches
        self.current_app: str = ""
        self.current_app_start: datetime = datetime.now()
        self.session_start: datetime = datetime.now()
        self.category_time: dict[str, float] = {}  # category → seconds today

    def update(self, app_name: str, category: str, timestamp: datetime, is_idle: bool) -> ADHDMetrics:
        """Called every 2 seconds with new screen state."""

        # Detect app switch
        if app_name != self.current_app and not is_idle:
            duration = (timestamp - self.current_app_start).total_seconds()
            self.app_switches.append(timestamp)
            self.current_app = app_name
            self.current_app_start = timestamp

        # Log activity
        self.activity_log.append({
            "app": app_name,
            "category": category,
            "timestamp": timestamp,
            "is_idle": is_idle
        })

        # Accumulate category time
        self.category_time[category] = self.category_time.get(category, 0) + 2

        # Compute metrics
        return self._compute_metrics(timestamp, is_idle)

    def _compute_metrics(self, now: datetime, is_idle: bool) -> ADHDMetrics:
        metrics = ADHDMetrics()

        # Context switch rate (last 5 minutes)
        five_min_ago = now - timedelta(minutes=5)
        recent_switches = sum(1 for t in self.app_switches if t > five_min_ago)
        metrics.context_switch_rate_5min = recent_switches

        # Current streak
        metrics.current_streak_minutes = (now - self.current_app_start).total_seconds() / 60

        # Focus score: % of last 30 min in sessions ≥ 15 min on productive apps
        # (simplified — real implementation needs session detection)
        productive_seconds = sum(
            self.category_time.get(cat, 0)
            for cat in ["development", "writing", "research", "communication"]
        )
        total_seconds = sum(self.category_time.values()) or 1
        metrics.focus_score = (productive_seconds / total_seconds) * 100

        # Distraction ratio
        distracting_seconds = sum(
            self.category_time.get(cat, 0)
            for cat in ["social_media", "entertainment", "news", "shopping"]
        )
        metrics.distraction_ratio = distracting_seconds / total_seconds

        # Hyperfocus detection
        metrics.hyperfocus_detected = (
            metrics.current_streak_minutes > metrics.HYPERFOCUS_THRESHOLD_MINUTES
        )

        # Behavioral state
        if is_idle:
            metrics.behavioral_state = "idle"
        elif metrics.hyperfocus_detected:
            metrics.behavioral_state = "hyperfocused"
        elif metrics.context_switch_rate_5min > metrics.HIGH_SWITCH_RATE:
            metrics.behavioral_state = "distracted"
        elif metrics.focus_score > 60:
            metrics.behavioral_state = "focused"
        else:
            metrics.behavioral_state = "multitasking"

        return metrics
```

### 6.2 Activity Classifier

**File: `backend/services/activity_classifier.py`**

```python
import json
from pathlib import Path

# Load classification dictionaries at module level
APP_CATEGORIES = json.loads(
    (Path(__file__).parent.parent / "knowledge" / "app_categories.json").read_text()
)
URL_CATEGORIES = json.loads(
    (Path(__file__).parent.parent / "knowledge" / "url_categories.json").read_text()
)

def classify_activity(app_name: str, window_title: str, url: str | None) -> str:
    """
    4-layer activity classifier. Each layer is faster than the next.
    Returns one of: development, writing, research, communication,
    social_media, entertainment, news, shopping, productivity, other

    Layer 1: Rule-based app name matching (~70% of cases, <1ms)
    Layer 2: URL domain lookup (~20% of cases, <1ms)
    Layer 3: Window title keyword matching (~8% of cases, <2ms)
    Layer 4: MLX model fallback (~2% of cases, ~200ms) — called async
    """

    # Layer 1: App name lookup
    app_lower = app_name.lower()
    if app_lower in APP_CATEGORIES:
        return APP_CATEGORIES[app_lower]

    # Layer 2: URL domain lookup
    if url:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "")
        # Check exact domain
        if domain in URL_CATEGORIES:
            return URL_CATEGORIES[domain]
        # Check parent domain (e.g., "mail.google.com" → "google.com")
        parts = domain.split(".")
        if len(parts) > 2:
            parent = ".".join(parts[-2:])
            if parent in URL_CATEGORIES:
                return URL_CATEGORIES[parent]

    # Layer 3: Window title keywords
    title_lower = window_title.lower()
    keyword_map = {
        "development": ["vscode", "terminal", "github", "stack overflow", "localhost", "debug", "pull request"],
        "writing": ["docs.google", "notion", "word", "overleaf", "grammarly", "draft"],
        "communication": ["mail", "gmail", "outlook", "slack", "teams", "discord", "zoom", "meet"],
        "social_media": ["twitter", "x.com", "instagram", "facebook", "reddit", "tiktok", "linkedin feed"],
        "entertainment": ["youtube", "netflix", "spotify", "twitch", "gaming", "steam"],
        "research": ["arxiv", "scholar", "pubmed", "wikipedia", "library"],
        "news": ["news", "bbc", "cnn", "nytimes", "guardian"],
    }
    for category, keywords in keyword_map.items():
        if any(kw in title_lower for kw in keywords):
            return category

    # Layer 4: Return "other" — MLX fallback runs async in background
    return "other"
```

**File: `backend/knowledge/app_categories.json`** (starter — expand this):
```json
{
    "visual studio code": "development",
    "code": "development",
    "xcode": "development",
    "terminal": "development",
    "iterm2": "development",
    "warp": "development",
    "cursor": "development",
    "pycharm": "development",
    "intellij idea": "development",
    "sublime text": "development",
    "postman": "development",
    "docker desktop": "development",
    "figma": "design",
    "sketch": "design",
    "adobe photoshop": "design",
    "notion": "productivity",
    "obsidian": "productivity",
    "todoist": "productivity",
    "things": "productivity",
    "linear": "productivity",
    "jira": "productivity",
    "microsoft word": "writing",
    "pages": "writing",
    "google docs": "writing",
    "overleaf": "writing",
    "slack": "communication",
    "microsoft teams": "communication",
    "discord": "communication",
    "zoom": "communication",
    "facetime": "communication",
    "messages": "communication",
    "mail": "communication",
    "spotify": "entertainment",
    "music": "entertainment",
    "apple tv": "entertainment",
    "vlc": "entertainment",
    "safari": "browser",
    "google chrome": "browser",
    "firefox": "browser",
    "arc": "browser",
    "brave browser": "browser",
    "microsoft edge": "browser",
    "finder": "system",
    "system preferences": "system",
    "system settings": "system",
    "activity monitor": "system"
}
```

**File: `backend/knowledge/url_categories.json`** (starter):
```json
{
    "github.com": "development",
    "stackoverflow.com": "development",
    "gitlab.com": "development",
    "npmjs.com": "development",
    "pypi.org": "development",
    "docs.python.org": "development",
    "developer.mozilla.org": "development",
    "docs.google.com": "writing",
    "notion.so": "productivity",
    "linear.app": "productivity",
    "figma.com": "design",
    "twitter.com": "social_media",
    "x.com": "social_media",
    "instagram.com": "social_media",
    "facebook.com": "social_media",
    "reddit.com": "social_media",
    "tiktok.com": "social_media",
    "linkedin.com": "social_media",
    "youtube.com": "entertainment",
    "netflix.com": "entertainment",
    "twitch.tv": "entertainment",
    "spotify.com": "entertainment",
    "arxiv.org": "research",
    "scholar.google.com": "research",
    "pubmed.ncbi.nlm.nih.gov": "research",
    "wikipedia.org": "research",
    "amazon.com": "shopping",
    "shopee.sg": "shopping",
    "lazada.sg": "shopping"
}
```

### 6.3 JITAI Decision Engine

**File: `backend/services/jitai_engine.py`**

```python
from datetime import datetime, timedelta
from models.intervention import Intervention, InterventionAction
from models.adhd_state import ADHDMetrics

class JITAIEngine:
    """
    Just-in-Time Adaptive Intervention engine.
    Implements Barkley's 5 Executive Function deficit domains:
    1. Self-management to time
    2. Self-organization / problem solving
    3. Self-restraint (inhibition)
    4. Self-motivation
    5. Self-regulation of emotion

    Rules:
    - DO intervene: at natural transition points, escalating frustration, user seeks help
    - DO NOT interrupt: during focus/flow, within cooldown, during meetings, DND mode
    - Max 2-3 sentences per intervention
    - Max 2-3 action choices
    - Validate before suggesting ("I notice..." before "Try...")
    - Use upward framing (what WILL help, not what went WRONG)
    """

    def __init__(self):
        self.last_intervention_time: datetime | None = None
        self.cooldown_seconds: int = 300  # 5 min default
        self.dismissed_count: int = 0
        self.dnd_mode: bool = False

    def evaluate(self, metrics: ADHDMetrics, emotion_context: dict | None = None) -> Intervention | None:
        """Evaluate whether an intervention should be delivered."""

        # Hard blocks — never interrupt
        if self.dnd_mode:
            return None
        if self.last_intervention_time and \
           (datetime.now() - self.last_intervention_time).total_seconds() < self.cooldown_seconds:
            return None
        if metrics.behavioral_state == "focused":
            return None

        # Rule 1: Distraction spiral (Self-restraint deficit)
        if (metrics.context_switch_rate_5min > 12 and
            metrics.distraction_ratio > 0.5):
            return Intervention(
                type="distraction_spiral",
                ef_domain="self_restraint",
                acknowledgment="Looks like things are scattered right now — that's okay.",
                suggestion="A 2-minute reset could help you refocus. What feels right?",
                actions=[
                    InterventionAction(id="breathe", emoji="🫁", label="Breathing exercise"),
                    InterventionAction(id="task_pick", emoji="🎯", label="Pick one task"),
                    InterventionAction(id="break", emoji="☕", label="Take a break"),
                ],
                requires_senticnet=False
            )

        # Rule 2: Sustained disengagement (Self-motivation deficit)
        if (metrics.behavioral_state == "distracted" and
            metrics.current_streak_minutes > 20 and
            metrics.distraction_ratio > 0.7):
            return Intervention(
                type="sustained_disengagement",
                ef_domain="self_motivation",
                acknowledgment="It's been a while since your last focused stretch.",
                suggestion="Sometimes the hardest part is just starting. What's the smallest step you could take?",
                actions=[
                    InterventionAction(id="tiny_task", emoji="🪜", label="5-min micro-task"),
                    InterventionAction(id="body_double", emoji="👥", label="Find a body double"),
                    InterventionAction(id="reward_first", emoji="🎁", label="Set a reward"),
                ],
                requires_senticnet=False
            )

        # Rule 3: Hyperfocus on wrong task (Self-management to time)
        if metrics.hyperfocus_detected:
            return Intervention(
                type="hyperfocus_check",
                ef_domain="self_management_time",
                acknowledgment="You've been deeply focused for 3+ hours — that's impressive focus!",
                suggestion="Quick check: is this the most important thing right now?",
                actions=[
                    InterventionAction(id="yes_continue", emoji="✅", label="Yes, keep going"),
                    InterventionAction(id="switch_task", emoji="🔄", label="Switch to priority"),
                    InterventionAction(id="time_box", emoji="⏰", label="Set 30min timer"),
                ],
                requires_senticnet=False
            )

        # Rule 4: Emotional escalation (Self-regulation of emotion)
        if emotion_context and emotion_context.get("emotional_dysregulation"):
            return Intervention(
                type="emotional_escalation",
                ef_domain="self_regulation_emotion",
                acknowledgment="Things seem intense right now. That's a valid feeling.",
                suggestion="Would any of these help you process what you're feeling?",
                actions=[
                    InterventionAction(id="vent", emoji="💬", label="Vent to me"),
                    InterventionAction(id="ground", emoji="🌿", label="Grounding exercise"),
                    InterventionAction(id="walk", emoji="🚶", label="Take a walk"),
                ],
                requires_senticnet=True
            )

        return None

    def record_response(self, intervention_id: str, action_taken: str | None, dismissed: bool):
        """Track intervention effectiveness for adaptive calibration."""
        self.last_intervention_time = datetime.now()
        if dismissed:
            self.dismissed_count += 1
            # Adaptive cooldown: increase if user keeps dismissing
            if self.dismissed_count >= 3:
                self.cooldown_seconds = min(self.cooldown_seconds * 1.5, 1800)  # max 30 min
        else:
            self.dismissed_count = 0
            self.cooldown_seconds = 300  # reset to default
```

### 6.4 XAI Explanation Engine

**File: `backend/services/xai_explainer.py`**

```python
class ConceptBottleneckExplainer:
    """
    Generates human-readable explanations using SenticNet's concept-level outputs.

    Architecture: Concept Bottleneck Model
    Raw data → Feature extraction → SenticNet concept activations → Behavioral prediction → Explanation

    Three explanation types:
    1. WHAT: "Your switching pattern shows signs of attention fragmentation"
    2. WHY:  "SenticNet detected frustration (0.82) and overwhelm (0.71) in your recent activity"
    3. HOW:  "If you take a 5-min break, your focus pattern typically improves by ~40%"
    """

    def explain_intervention(
        self,
        intervention_type: str,
        metrics: dict,
        senticnet_result: dict | None = None
    ) -> dict:
        """Generate an explainable justification for a JITAI intervention."""

        explanation = {
            "what": self._explain_what(intervention_type, metrics),
            "why": self._explain_why(intervention_type, metrics, senticnet_result),
            "how": self._explain_how(intervention_type, metrics),
            "concepts": [],  # SenticNet concepts that contributed
            "confidence": 0.0,
        }

        if senticnet_result:
            explanation["concepts"] = senticnet_result.get("concepts", [])
            explanation["hourglass_state"] = senticnet_result.get("emotion_profile", {}).get("hourglass_dimensions", {})

        return explanation

    def _explain_what(self, intervention_type: str, metrics: dict) -> str:
        templates = {
            "distraction_spiral": f"You've switched apps {metrics.get('context_switch_rate_5min', 0):.0f} times in the last 5 minutes, "
                                  f"with {metrics.get('distraction_ratio', 0)*100:.0f}% of time on non-work apps.",
            "sustained_disengagement": f"You've been away from focused work for {metrics.get('current_streak_minutes', 0):.0f} minutes.",
            "hyperfocus_check": f"You've been on the same task for {metrics.get('current_streak_minutes', 0)/60:.1f} hours.",
            "emotional_escalation": "Your recent activity patterns suggest emotional intensity is rising.",
        }
        return templates.get(intervention_type, "A pattern was detected in your activity.")

    def _explain_why(self, intervention_type: str, metrics: dict, senticnet: dict | None) -> str:
        if senticnet and senticnet.get("emotion_profile"):
            emotion = senticnet["emotion_profile"].get("primary_emotion", "")
            intensity = senticnet.get("adhd_signals", {}).get("intensity_score", 0)
            return (f"Emotional analysis detected {emotion} (intensity: {abs(intensity):.0f}/100). "
                    f"This maps to executive function challenges with focus and task initiation.")
        return "This pattern is common in ADHD and relates to executive function differences."

    def _explain_how(self, intervention_type: str, metrics: dict) -> str:
        """Counterfactual explanation: what would improve things."""
        counterfactuals = {
            "distraction_spiral": "Research shows a 2-minute breathing reset can reduce context switching by ~40%.",
            "sustained_disengagement": "Starting with a 5-minute micro-task often breaks the avoidance cycle.",
            "hyperfocus_check": "Time-boxing the remaining work can preserve your focus while protecting other priorities.",
            "emotional_escalation": "Acknowledging the emotion (even briefly) helps regulate the prefrontal cortex response.",
        }
        return counterfactuals.get(intervention_type, "")
```

---

## 7. PHASE 5: WHOOP INTEGRATION

**File: `backend/services/whoop_service.py`**

```python
import httpx
from datetime import datetime, date
from config import settings

class WhoopService:
    """
    Whoop API v2 client.
    Base URL: https://api.prod.whoop.com/developer/
    Auth: OAuth 2.0 Authorization Code flow
    Key endpoints: /v1/recovery, /v1/cycle, /v1/sleep
    """

    BASE_URL = "https://api.prod.whoop.com/developer"

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {settings.WHOOP_ACCESS_TOKEN}"}
        )

    async def get_latest_recovery(self) -> dict:
        """Get most recent recovery data (HRV, resting HR, recovery score)."""
        response = await self.client.get("/v1/recovery", params={"limit": 1})
        response.raise_for_status()
        data = response.json()
        if data.get("records"):
            return data["records"][0]
        return {}

    async def get_latest_sleep(self) -> dict:
        """Get most recent sleep data (stages, disturbances, performance)."""
        response = await self.client.get("/v1/activity/sleep", params={"limit": 1})
        response.raise_for_status()
        data = response.json()
        if data.get("records"):
            return data["records"][0]
        return {}

    async def get_latest_cycle(self) -> dict:
        """Get most recent cycle (strain, calories)."""
        response = await self.client.get("/v1/cycle", params={"limit": 1})
        response.raise_for_status()
        data = response.json()
        if data.get("records"):
            return data["records"][0]
        return {}

    async def generate_morning_briefing(self) -> dict:
        """
        Generate ADHD-tailored morning briefing from overnight Whoop data.

        Maps Whoop metrics to ADHD executive function predictions:
        - Recovery < 33% → reduce cognitive demands, more breaks, written lists
        - Recovery 34-66% → normal pacing, extra structure
        - Recovery > 66% → optimal day for challenging, creative work
        - Low SWS → working memory issues predicted, use written over verbal
        - High disturbances → fragmented attention likely, shorter focus blocks
        - Low HRV → emotional regulation may be harder today
        """
        recovery = await self.get_latest_recovery()
        sleep = await self.get_latest_sleep()
        cycle = await self.get_latest_cycle()

        score = recovery.get("score", {})
        recovery_pct = score.get("recovery_score", 50)
        hrv = score.get("hrv_rmssd_milli", 0)
        rhr = score.get("resting_heart_rate", 0)

        sleep_data = sleep.get("score", {})
        sleep_performance = sleep_data.get("sleep_performance_percentage", 0)
        disturbances = sleep_data.get("disturbance_count", 0)
        sws_ms = sleep_data.get("total_slow_wave_sleep_time_milli", 0)
        rem_ms = sleep_data.get("total_rem_sleep_time_milli", 0)
        total_ms = sleep_data.get("total_in_bed_time_milli", 1)

        sws_pct = (sws_ms / total_ms) * 100 if total_ms > 0 else 0
        rem_pct = (rem_ms / total_ms) * 100 if total_ms > 0 else 0

        # Determine recovery tier
        if recovery_pct >= 67:
            tier = "green"
            focus_recommendation = "Great recovery — today is optimal for deep, challenging work."
            focus_block_minutes = 45
        elif recovery_pct >= 34:
            tier = "yellow"
            focus_recommendation = "Moderate recovery — pace yourself with structured focus blocks."
            focus_block_minutes = 25
        else:
            tier = "red"
            focus_recommendation = "Low recovery — prioritize easy tasks, take frequent breaks, use written lists."
            focus_block_minutes = 15

        # Sleep-specific ADHD recommendations
        sleep_notes = []
        if sws_pct < 15:
            sleep_notes.append("Low deep sleep → working memory may be affected. Write things down today.")
        if disturbances > 5:
            sleep_notes.append(f"{disturbances} sleep disturbances → attention may fragment easier. Use shorter focus blocks.")
        if hrv < 40:  # Rough threshold; should use personal baseline
            sleep_notes.append("Low HRV → emotional regulation may be harder today. Give yourself extra grace.")

        return {
            "date": date.today().isoformat(),
            "recovery_score": recovery_pct,
            "recovery_tier": tier,
            "hrv_rmssd": hrv,
            "resting_hr": rhr,
            "sleep_performance": sleep_performance,
            "sws_percentage": round(sws_pct, 1),
            "rem_percentage": round(rem_pct, 1),
            "disturbance_count": disturbances,
            "focus_recommendation": focus_recommendation,
            "recommended_focus_block_minutes": focus_block_minutes,
            "sleep_notes": sleep_notes,
            "strain_yesterday": cycle.get("score", {}).get("strain", 0),
        }
```

### Whoop OAuth Flow

**File: `backend/api/whoop.py`**
```python
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
import httpx
from config import settings

router = APIRouter()

@router.get("/auth")
async def whoop_auth():
    """Step 1: Redirect user to Whoop OAuth consent screen."""
    params = {
        "client_id": settings.WHOOP_CLIENT_ID,
        "redirect_uri": settings.WHOOP_REDIRECT_URI,
        "response_type": "code",
        "scope": "read:recovery read:sleep read:cycles read:profile read:body_measurement",
        "state": "adhd_brain_auth"
    }
    auth_url = "https://api.prod.whoop.com/oauth/oauth2/auth"
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{auth_url}?{query}")

@router.get("/callback")
async def whoop_callback(code: str, state: str):
    """Step 2: Exchange authorization code for access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.prod.whoop.com/oauth/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.WHOOP_REDIRECT_URI,
                "client_id": settings.WHOOP_CLIENT_ID,
                "client_secret": settings.WHOOP_CLIENT_SECRET,
            }
        )
        tokens = response.json()
        # Store tokens securely (in .env or encrypted keychain)
        # TODO: Implement secure token storage
        return {"status": "authenticated", "expires_in": tokens.get("expires_in")}

@router.get("/morning-briefing")
async def morning_briefing():
    """Generate ADHD-tailored morning briefing from Whoop data."""
    from services.whoop_service import WhoopService
    service = WhoopService()
    return await service.generate_morning_briefing()
```

---

## 8. PHASE 6: MEMORY SYSTEM

**File: `backend/services/memory_service.py`**

```python
from mem0 import Memory
from config import settings

class MemoryService:
    """
    Dual-layer memory system:

    Layer 1 — Mem0 (conversational memory):
      Stores user preferences, emotional patterns, intervention responses,
      and conversational context. Used for personalizing LLM responses.

    Layer 2 — PostgreSQL + pgvector (behavioral patterns):
      Time-series of screen activities, SenticNet analyses, intervention
      outcomes, and Whoop data. Used for trend analysis and weekly reviews.
    """

    def __init__(self):
        self.mem0 = Memory.from_config({
            "llm": {
                "provider": "openai",
                "config": {"model": "gpt-4o-mini", "api_key": settings.OPENAI_API_KEY}
            },
            "embedder": {
                "provider": "openai",
                "config": {"model": "text-embedding-3-small", "api_key": settings.OPENAI_API_KEY}
            },
            "vector_store": {
                "provider": "pgvector",
                "config": {
                    "dbname": "adhd_brain",
                    "user": "adhd",
                    "password": "adhd",
                    "host": "localhost",
                    "port": 5432,
                    "collection_name": "adhd_memories"
                }
            }
        })
        self.user_id = "adhd_user"  # Single-user system

    async def add_conversation_memory(self, messages: list[dict], metadata: dict = None):
        """Store conversation context after chat/vent session."""
        self.mem0.add(messages, user_id=self.user_id, metadata=metadata or {})

    async def add_pattern_memory(self, pattern: str, metadata: dict = None):
        """Store detected behavioral pattern."""
        self.mem0.add(
            [{"role": "system", "content": f"Behavioral pattern detected: {pattern}"}],
            user_id=self.user_id,
            metadata={"type": "pattern", **(metadata or {})}
        )

    async def search_relevant_context(self, query: str, limit: int = 5) -> list:
        """Retrieve relevant memories for LLM context injection."""
        results = self.mem0.search(query, user_id=self.user_id, limit=limit)
        return results

    async def get_intervention_history(self, intervention_type: str) -> list:
        """Get history of a specific intervention type and user responses."""
        results = self.mem0.search(
            f"intervention {intervention_type} response",
            user_id=self.user_id,
            limit=10
        )
        return results
```

---

## 9. PHASE 7: ON-DEVICE LLM (Apple MLX)

**File: `backend/services/mlx_inference.py`**

```python
"""
On-device LLM inference using Apple MLX framework.
Models run on Apple Silicon unified memory — no GPU transfer overhead.

Primary model: Llama 3.2 3B Instruct (4-bit, ~1.8GB)
Fast model: Llama 3.2 1B Instruct (4-bit, ~700MB)

Install:
  pip install mlx-lm
  mlx_lm.convert --hf-path meta-llama/Llama-3.2-3B-Instruct -q 4bit
"""

from mlx_lm import load, generate

class MLXInference:
    def __init__(self):
        # Load models on startup (takes ~5-10 seconds, then instant inference)
        self.model_3b, self.tokenizer_3b = load("mlx-community/Llama-3.2-3B-Instruct-4bit")
        # Optionally load 1B for fast classification
        # self.model_1b, self.tokenizer_1b = load("mlx-community/Llama-3.2-1B-Instruct-4bit")

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        senticnet_context: dict | None = None,
        max_tokens: int = 300,
        temperature: float = 0.7
    ) -> str:
        """Generate a response using on-device Llama with SenticNet context."""

        # Build prompt with SenticNet data injected as structured context
        context_section = ""
        if senticnet_context:
            context_section = f"""
<senticnet_analysis>
Emotion: {senticnet_context.get('primary_emotion', 'unknown')}
Intensity: {senticnet_context.get('intensity_score', 0)}/100
Engagement: {senticnet_context.get('engagement_score', 0)}/100
Wellbeing: {senticnet_context.get('wellbeing_score', 0)}/100
Safety level: {senticnet_context.get('safety_level', 'normal')}
Key concepts: {', '.join(senticnet_context.get('concepts', [])[:5])}
</senticnet_analysis>
"""

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{system_prompt}
{context_section}
<|eot_id|><|start_header_id|>user<|end_header_id|>
{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

        response = generate(
            self.model_3b,
            self.tokenizer_3b,
            prompt=prompt,
            max_tokens=max_tokens,
            temp=temperature
        )
        return response

    def classify_window_title(self, title: str) -> str:
        """Fast classification of ambiguous window titles using 1B model."""
        prompt = f"""Classify this window title into exactly one category.
Categories: development, writing, research, communication, social_media, entertainment, news, shopping, productivity, other
Window title: "{title}"
Category:"""

        result = generate(
            self.model_3b,  # Use 3B if 1B not loaded
            self.tokenizer_3b,
            prompt=prompt,
            max_tokens=5,
            temp=0.0
        )
        return result.strip().lower().split()[0]
```

---

## 10. PHASE 8: OPENCLAW INTEGRATION

### 10.1 Venting Chat Skill

**File: `openclaw-skills/adhd-vent/SKILL.md`**

```markdown
---
name: adhd-vent
description: Process venting messages through SenticNet affective computing pipeline for ADHD emotional regulation support
---

## ADHD Emotional Regulation Support

You are an empathetic ADHD coach. When the user vents or shares emotions:

1. Call the ADHD Second Brain backend to process their message:
   ```
   curl -X POST http://localhost:8420/chat/message \
     -H "Content-Type: application/json" \
     -d '{"text": "<USER_MESSAGE>", "conversation_id": "<SESSION_ID>", "context": {"source": "openclaw"}}'
   ```

2. The backend returns a structured response with:
   - SenticNet emotion analysis (emotion, intensity, engagement, wellbeing)
   - Safety flags (depression/toxicity checks)
   - Suggested response with XAI explanation
   - Recommended actions

3. Deliver the response following these ADHD communication rules:
   - Under 2-3 sentences (working memory deficits)
   - Validate before suggesting
   - Offer 2-3 choices maximum
   - Use upward framing

4. If safety flags indicate CRITICAL level:
   - Do NOT try to be a therapist
   - Acknowledge their pain
   - Provide crisis resources (988 Suicide & Crisis Lifeline)
   - Encourage professional support

5. Remember emotional patterns across sessions for personalization.
```

### 10.2 Morning Briefing Skill

**File: `openclaw-skills/morning-briefing/SKILL.md`**

```markdown
---
name: morning-briefing
description: Deliver ADHD-tailored morning briefing using Whoop physiological data
---

## Morning ADHD Briefing

Every morning (configure via HEARTBEAT.md), fetch the morning briefing:

```
curl http://localhost:8420/whoop/morning-briefing
```

Format the response as a concise, ADHD-friendly morning message:

### Green Recovery (67-100%):
"Good morning! 🟢 Your body recovered well (score: X%). Deep sleep was solid.
Today's a great day for challenging work. Try 45-min focus blocks.
HRV: Xms | Sleep: X% performance"

### Yellow Recovery (34-66%):
"Morning! 🟡 Moderate recovery today (X%). [any sleep notes]
Pace yourself — 25-min focus blocks with breaks. Structure is your friend today.
HRV: Xms | Sleep: X% performance"

### Red Recovery (0-33%):
"Hey, take it easy today. 🔴 Recovery is low (X%). [sleep notes]
Stick to easy tasks, take frequent breaks, and write everything down.
Recommended: 15-min focus blocks. Be kind to yourself.
HRV: Xms | Sleep: X% performance"

Always end with one specific, actionable recommendation.
```

### 10.3 OpenClaw HEARTBEAT.md Configuration

```markdown
## Every morning at 7:30 AM:
- Fetch Whoop morning briefing from localhost:8420/whoop/morning-briefing
- Deliver formatted ADHD morning briefing to user

## Every 30 minutes during active hours (9 AM - 10 PM):
- Check localhost:8420/insights/current for any pending alerts
- Only message if there's something actionable

## Every Sunday at 8 PM:
- Fetch weekly review from localhost:8420/insights/weekly
- Deliver formatted weekly ADHD pattern summary
```

---

## 11. PHASE 9: FRONTEND DASHBOARD

This is optional but valuable for FYP demonstration. A simple React dashboard showing real-time metrics.

**Key components to build:**

1. **FocusTimeline.jsx** — Horizontal timeline showing today's activity color-coded by category (green=focused, red=distracted, yellow=multitasking, gray=idle). Similar to Rize's daily view.

2. **EmotionRadar.jsx** — Recharts radar chart showing current Hourglass of Emotions state (4 axes: Pleasantness, Attention, Sensitivity, Aptitude).

3. **WhoopCard.jsx** — Card displaying recovery score (with green/yellow/red color), HRV, sleep performance, and today's recommended focus block length.

4. **MetricsCard.jsx** — Real-time display of context switch rate, focus score, distraction ratio, current streak time.

5. **InterventionLog.jsx** — List of today's interventions, what was suggested, and what the user chose. Shows intervention effectiveness trends.

API endpoint for dashboard: `GET http://localhost:8420/insights/dashboard`

---

## 12. DATA MODELS & SCHEMAS

### PostgreSQL Schema (via Alembic migration)

```sql
-- Activity log (partitioned by date for performance)
CREATE TABLE activities (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    app_name VARCHAR(255),
    window_title TEXT,
    url TEXT,
    category VARCHAR(50),
    is_idle BOOLEAN DEFAULT FALSE,
    metrics JSONB  -- snapshot of ADHDMetrics at this point
);
CREATE INDEX idx_activities_timestamp ON activities(timestamp DESC);

-- SenticNet analysis results
CREATE TABLE senticnet_analyses (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(20),  -- 'chat', 'screen', 'journal'
    input_text TEXT,
    emotion_profile JSONB,
    safety_flags JSONB,
    adhd_signals JSONB,
    concepts JSONB,
    raw_results JSONB
);

-- Intervention history
CREATE TABLE interventions (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    type VARCHAR(50),
    ef_domain VARCHAR(50),
    suggestion TEXT,
    actions JSONB,
    explanation JSONB,
    user_action VARCHAR(50),  -- which button they clicked, or 'dismissed'
    dismissed BOOLEAN DEFAULT FALSE,
    effectiveness_rating INTEGER  -- 1-5, optional self-report
);
CREATE INDEX idx_interventions_type ON interventions(type, timestamp DESC);

-- Whoop data snapshots
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

-- Chat/vent conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    role VARCHAR(20),  -- 'user' or 'assistant'
    content TEXT,
    senticnet_analysis JSONB,
    source VARCHAR(20)  -- 'openclaw', 'dashboard', 'swift_app'
);

-- pgvector for semantic search (used by Mem0)
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 13. API CONTRACTS

### Full API Endpoint Summary

| Method | Endpoint | Purpose | Latency Target |
|--------|----------|---------|----------------|
| POST | `/screen/activity` | Report screen state (called every 2s) | <100ms |
| POST | `/chat/message` | Process venting/chat message | <3s |
| GET | `/whoop/auth` | Start Whoop OAuth flow | redirect |
| GET | `/whoop/callback` | OAuth callback | <1s |
| GET | `/whoop/morning-briefing` | Generate morning briefing | <2s |
| GET | `/insights/current` | Current ADHD state + metrics | <50ms |
| GET | `/insights/daily` | Today's summary | <500ms |
| GET | `/insights/weekly` | Weekly pattern review | <2s |
| GET | `/insights/dashboard` | Full dashboard data | <500ms |
| GET | `/interventions/current` | Any pending intervention | <50ms |
| POST | `/interventions/{id}/respond` | Record user response | <100ms |
| GET | `/health` | Backend health check | <10ms |

---

## 14. CONFIGURATION FILES

### docker-compose.yml
```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: adhd_brain
      POSTGRES_USER: adhd
      POSTGRES_PASSWORD: adhd
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### .env.example
```bash
# Database
DATABASE_URL=postgresql+asyncpg://adhd:adhd@localhost:5432/adhd_brain

# SenticNet (from sentic.txt — keep confidential)
SENTIC_CONCEPT_PARSING=<YOUR_CONCEPT_PARSING_KEY>
SENTIC_SUBJECTIVITY=<YOUR_SUBJECTIVITY_DETECTION_KEY>
SENTIC_POLARITY=<YOUR_POLARITY_CLASSIFICATION_KEY>
SENTIC_INTENSITY=<YOUR_INTENSITY_RANKING_KEY>
SENTIC_EMOTION=<YOUR_EMOTION_RECOGNITION_KEY>
SENTIC_ASPECT=<YOUR_ASPECT_EXTRACTION_KEY>
SENTIC_PERSONALITY=<YOUR_PERSONALITY_PREDICTION_KEY>
SENTIC_SARCASM=<YOUR_SARCASM_IDENTIFICATION_KEY>
SENTIC_DEPRESSION=<YOUR_DEPRESSION_CATEGORIZATION_KEY>
SENTIC_TOXICITY=<YOUR_TOXICITY_SPOTTING_KEY>
SENTIC_ENGAGEMENT=<YOUR_ENGAGEMENT_MEASUREMENT_KEY>
SENTIC_WELLBEING=<YOUR_WELL_BEING_ASSESSMENT_KEY>
SENTIC_ENSEMBLE=<YOUR_ENSEMBLE_KEY>

# Whoop (register at developer.whoop.com)
WHOOP_CLIENT_ID=
WHOOP_CLIENT_SECRET=
WHOOP_ACCESS_TOKEN=
WHOOP_REFRESH_TOKEN=

# LLMs
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Memory
MEM0_API_KEY=
```

---

## 15. ENVIRONMENT & DEPENDENCIES

### Python Backend — `requirements.txt`
```
fastapi==0.115.*
uvicorn[standard]==0.34.*
httpx==0.28.*
pydantic==2.*
pydantic-settings==2.*
asyncpg==0.30.*
sqlalchemy[asyncio]==2.*
alembic==1.14.*
pgvector==0.3.*
mem0ai==0.1.*
mlx-lm==0.21.*
senticnet==1.*
python-dotenv==1.*
```

### Swift App — `Package.swift` dependencies
```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ADHDSecondBrain",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "ADHDSecondBrain",
            path: "ADHDSecondBrain"
        ),
    ]
)
// Note: No external Swift dependencies needed.
// All APIs used (NSWorkspace, CGWindowList, IOKit, AppleScript) are system frameworks.
```

### System Requirements
```
- macOS 14+ (Sonoma) on Apple Silicon (M1/M2/M3/M4)
- Minimum 8GB RAM (16GB recommended for MLX models)
- Python 3.11+
- Node.js 22+ (only if using OpenClaw)
- PostgreSQL 16 + pgvector (via Docker)
- Xcode 15+ (for Swift app compilation)
```

### Setup Script — `scripts/setup.sh`
```bash
#!/bin/bash
set -e

echo "=== ADHD Second Brain Setup ==="

# 1. Start PostgreSQL
echo "Starting PostgreSQL..."
docker compose up -d postgres
sleep 3

# 2. Python environment
echo "Setting up Python backend..."
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Database migrations
echo "Running migrations..."
alembic upgrade head

# 4. Download MLX models (optional, ~2GB)
echo "Downloading Llama 3.2 3B (4-bit) for on-device inference..."
python -c "from mlx_lm import load; load('mlx-community/Llama-3.2-3B-Instruct-4bit')"

# 5. Validate SenticNet keys
echo "Testing SenticNet API keys..."
python ../scripts/test_senticnet_keys.py

echo "=== Setup complete! ==="
echo "Run: cd backend && uvicorn main:app --port 8420 --reload"
```

---

## 16. TESTING STRATEGY

### Unit Tests (pytest)
```
backend/tests/
├── test_senticnet_client.py      # Mock HTTP, test sanitization, error handling
├── test_senticnet_pipeline.py    # Test tier routing, safety thresholds
├── test_activity_classifier.py   # Test all 4 layers with known apps/URLs
├── test_adhd_metrics.py          # Test metric computation, state transitions
├── test_jitai_engine.py          # Test intervention rules, cooldowns, adaptive behavior
├── test_xai_explainer.py         # Test explanation generation
├── test_whoop_service.py         # Mock Whoop API, test morning briefing logic
└── test_chat_processor.py        # Test full chat pipeline
```

### Integration Tests
```
- Test Swift → Backend round-trip (POST /screen/activity with sample data)
- Test SenticNet API calls with real keys (mark as @slow, skip in CI)
- Test Whoop OAuth flow end-to-end
- Test OpenClaw skill → Backend → Response pipeline
```

### Key Test Scenarios for ADHD Metrics
```python
# test_jitai_engine.py

def test_distraction_spiral_triggers_intervention():
    """12+ switches in 5 min + >50% distraction ratio = intervention"""
    metrics = ADHDMetrics(
        context_switch_rate_5min=15,
        distraction_ratio=0.65,
        behavioral_state="distracted"
    )
    intervention = engine.evaluate(metrics)
    assert intervention is not None
    assert intervention.type == "distraction_spiral"
    assert len(intervention.actions) <= 3

def test_focused_state_blocks_intervention():
    """Never interrupt someone who is focused"""
    metrics = ADHDMetrics(
        context_switch_rate_5min=2,
        focus_score=85,
        behavioral_state="focused"
    )
    intervention = engine.evaluate(metrics)
    assert intervention is None

def test_cooldown_prevents_spam():
    """No intervention within cooldown period after last one"""
    engine.record_response("test", "breathe", dismissed=False)
    metrics = ADHDMetrics(context_switch_rate_5min=20, distraction_ratio=0.8, behavioral_state="distracted")
    intervention = engine.evaluate(metrics)
    assert intervention is None  # within 5-min cooldown

def test_adaptive_cooldown_on_dismissals():
    """Cooldown increases after repeated dismissals"""
    for _ in range(3):
        engine.record_response("test", None, dismissed=True)
    assert engine.cooldown_seconds > 300  # increased from default
```

---

## 17. BUILD ORDER & CRITICAL PATH

### Phase 1 (Week 1-2): Foundation
```
1. Set up repo, docker-compose, .env
2. Create FastAPI skeleton with all route stubs
3. Implement POST /screen/activity with in-memory metrics
4. Implement activity_classifier.py (Layers 1-3, no ML)
5. Implement adhd_metrics.py (MetricsEngine)
6. Test with curl: curl -X POST localhost:8420/screen/activity -d '{"app_name":"Chrome","window_title":"YouTube","url":"youtube.com"}'
```

### Phase 2 (Week 2-3): SenticNet Pipeline
```
7. Implement senticnet_client.py
8. Write test_senticnet_keys.py to validate all 13 API keys
9. Implement senticnet_pipeline.py (full + lightweight + safety)
10. Implement POST /chat/message with full pipeline
11. Test: curl -X POST localhost:8420/chat/message -d '{"text":"I am so frustrated I cant focus on anything"}'
```

### Phase 3 (Week 3-4): JITAI + XAI
```
12. Implement jitai_engine.py with all 4 intervention rules
13. Implement xai_explainer.py
14. Wire JITAI into POST /screen/activity (return interventions)
15. Write comprehensive unit tests for JITAI rules
```

### Phase 4 (Week 4-5): Swift Menu Bar App
```
16. Create Xcode project with LSUIElement=true
17. Implement ScreenMonitor.swift (NSWorkspace + CGWindowList)
18. Implement BrowserMonitor.swift (AppleScript)
19. Implement IdleMonitor.swift
20. Implement BackendClient.swift (HTTP to localhost:8420)
21. Implement InterventionPopup.swift
22. Implement OnboardingView.swift (permissions wizard)
23. Test end-to-end: Swift captures → Backend processes → Intervention appears
```

### Phase 5 (Week 5-6): Whoop + Memory
```
24. Register Whoop developer app, get client ID/secret
25. Implement Whoop OAuth flow
26. Implement whoop_service.py + morning briefing
27. Set up Mem0 with PostgreSQL/pgvector
28. Implement memory_service.py
29. Wire memory into chat processor (context injection)
```

### Phase 6 (Week 6-7): MLX + OpenClaw
```
30. Install MLX, download Llama 3.2 3B
31. Implement mlx_inference.py
32. Wire MLX into chat_processor for response generation
33. Install OpenClaw, create custom skills
34. Test venting flow: Telegram → OpenClaw → Backend → Response
35. Configure HEARTBEAT.md for morning briefings
```

### Phase 7 (Week 7-8): Dashboard + Polish
```
36. Build React dashboard (FocusTimeline, EmotionRadar, WhoopCard)
37. Implement GET /insights/dashboard endpoint
38. End-to-end testing of all flows
39. Performance optimization (response times, memory usage)
40. Demo preparation
```

---

## IMPORTANT NOTES FOR CLAUDE CODE

1. **Start with the Python backend.** Everything else depends on it. The Swift app and OpenClaw are just interfaces that call the backend.

2. **SenticNet API keys expire after ~1 month** and are IP-locked. Test them early and request new ones if needed.

3. **The Swift app must be distributed outside the Mac App Store** because Screen Recording permission requires the `com.apple.security.temporary-exception.apple-events` entitlement which is blocked in sandbox.

4. **The SenticNet API response format may vary per endpoint.** The `_extract_score()` method in senticnet_pipeline.py needs to be adapted based on actual API responses. Test each of the 13 endpoints individually first and log raw responses.

5. **macOS Sequoia (15+) re-prompts for Accessibility/Screen Recording monthly.** Build clear re-authorization UX into the Swift app.

6. **For the FYP report**: Every SenticNet API call and JITAI decision should be logged with timestamps. This provides the evaluation data needed for the report's results chapter.

7. **Safety is non-negotiable.** The depression/toxicity safety check runs FIRST in every pipeline. If critical, skip all other processing and show crisis resources immediately. Never try to be a therapist.

8. **ADHD-friendly UX principles** apply to EVERYTHING: short text, 2-3 choices max, validate before suggesting, no guilt/shame framing, upward counterfactuals only.
