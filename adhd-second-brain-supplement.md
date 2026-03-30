# ADHD Second Brain — Supplementary Design & HCI Specification
## Research-Driven Updates to `adhd-second-brain-blueprint.md`

> **Companion to**: `adhd-second-brain-blueprint.md` (core architecture) + `architecture-diagram.mermaid`
> **Purpose**: This document adds new subsystems, modifies existing ones, and provides code-ready implementations for every research-backed design decision. It does NOT duplicate the blueprint — it extends it.
> **Rule**: Where this document conflicts with the blueprint, THIS document takes priority (it represents design improvements based on deeper research).

---

## TABLE OF CONTENTS

1. [New Files to Add to Repository](#1-new-files-to-add-to-repository)
2. [CRITICAL UPDATE: Replace Screen Monitor Strategy](#2-critical-update-replace-screen-monitor-strategy)
3. [NEW SYSTEM: ADHD Onboarding & Diagnostic Calibration](#3-new-system-adhd-onboarding--diagnostic-calibration)
4. [NEW SYSTEM: Transition-Point Detection Engine](#4-new-system-transition-point-detection-engine)
5. [NEW SYSTEM: Five-Tier Calm Notification Architecture](#5-new-system-five-tier-calm-notification-architecture)
6. [NEW SYSTEM: Hyperfocus Classifier](#6-new-system-hyperfocus-classifier)
7. [NEW SYSTEM: Ecological Momentary Assessment (EMA)](#7-new-system-ecological-momentary-assessment)
8. [NEW SYSTEM: Adaptive Frequency Learning (Contextual Bandits)](#8-new-system-adaptive-frequency-learning)
9. [NEW SYSTEM: Gamification & Reward Engine](#9-new-system-gamification--reward-engine)
10. [NEW SYSTEM: Digital Phenotyping Collector](#10-new-system-digital-phenotyping-collector)
11. [UPDATES TO: JITAI Engine (from blueprint Section 6)](#11-updates-to-jitai-engine)
12. [UPDATES TO: SenticNet Pipeline — Hourglass ADHD Mapping](#12-updates-to-senticnet-pipeline)
13. [UPDATES TO: XAI Explainer — Concept Bottleneck with User Correction](#13-updates-to-xai-explainer)
14. [UPDATES TO: Swift UI Layer — ADHD-Specific UX](#14-updates-to-swift-ui-layer)
15. [NEW: Privacy Architecture (Singapore PDPA)](#15-new-privacy-architecture)
16. [NEW: Safety Escalation Protocol](#16-new-safety-escalation-protocol)
17. [UPDATED: Database Schema Additions](#17-updated-database-schema-additions)
18. [UPDATED: API Endpoint Additions](#18-updated-api-endpoint-additions)
19. [UPDATED: Build Order & Critical Path](#19-updated-build-order)
20. [Anti-Patterns: Things That Must NEVER Be Built](#20-anti-patterns)

---

## 1. NEW FILES TO ADD TO REPOSITORY

Add these to the repo structure defined in blueprint Section 2:

```
adhd-second-brain/
├── backend/
│   ├── api/
│   │   ├── onboarding.py              # NEW: ADHD profile setup + ASRS
│   │   ├── ema.py                     # NEW: Ecological Momentary Assessment
│   │   └── gamification.py            # NEW: Streaks, XP, rewards
│   │
│   ├── services/
│   │   ├── transition_detector.py     # NEW: Breakpoint detection engine
│   │   ├── hyperfocus_classifier.py   # NEW: Productive vs unproductive
│   │   ├── notification_tier.py       # NEW: 5-tier calm escalation
│   │   ├── adaptive_frequency.py      # NEW: Thompson Sampling bandits
│   │   ├── onboarding_service.py      # NEW: ASRS scoring + profile gen
│   │   ├── ema_service.py             # NEW: EMA prompt scheduling
│   │   ├── gamification_service.py    # NEW: XP, streaks, rewards
│   │   ├── phenotype_collector.py     # NEW: Digital phenotyping
│   │   └── privacy_service.py         # NEW: PDPA data management
│   │
│   ├── models/
│   │   ├── adhd_profile.py            # NEW: Diagnostic + subtype + severity
│   │   ├── transition_event.py        # NEW: Breakpoint data
│   │   ├── notification_tier.py       # NEW: Tier levels
│   │   ├── ema_response.py            # NEW: EMA data models
│   │   └── gamification.py            # NEW: XP, streaks, rewards
│   │
│   └── knowledge/
│       ├── asrs_v1_1.json             # NEW: ASRS-v1.1 questions + scoring
│       ├── brief_a_mapping.json       # NEW: BRIEF-A subscale → EF domain map
│       ├── subtype_profiles.json      # NEW: ADHD-PI vs ADHD-C intervention profiles
│       ├── intervention_library.json  # EXPANDED: Now includes tier + timing metadata
│       └── ema_questions.json         # NEW: EMA item bank
│
├── swift-app/ADHDSecondBrain/
│   ├── Monitors/
│   │   ├── TransitionDetector.swift   # NEW: Breakpoint detection
│   │   └── PhenotypeCollector.swift   # NEW: Keystroke/mouse metrics
│   │
│   ├── UI/
│   │   ├── AmbientMenuBar.swift       # NEW: Color-shifting icon (Tier 1-2)
│   │   ├── CalmOverlayPanel.swift     # NEW: NSPanel non-activating (Tier 3)
│   │   ├── OnboardingFlow.swift       # EXPANDED: ASRS + permissions + calibration
│   │   ├── EMAPromptView.swift        # NEW: Quick daily check-in slider UI
│   │   ├── ProgressView.swift         # NEW: Gamification stats display
│   │   └── PrivacyDashboard.swift     # NEW: Data transparency panel
│   │
│   └── Notifications/
│       └── TierManager.swift          # NEW: Orchestrates 5-tier escalation
```

---

## 2. CRITICAL UPDATE: REPLACE SCREEN MONITOR STRATEGY

**This replaces blueprint Section 4.2 (ScreenMonitor.swift)**

The blueprint uses `CGWindowListCopyWindowInfo` which requires **Screen Recording** permission — triggering macOS Sequoia's monthly re-authorization popup. For ADHD users who struggle with administrative tasks, this is unacceptable.

### New Strategy: Accessibility API Only (No Screen Recording)

```swift
// File: swift-app/ADHDSecondBrain/Monitors/ScreenMonitor.swift
// REPLACES the version in blueprint Section 4.2

import Cocoa
import ApplicationServices

class ScreenMonitor: ObservableObject {
    @Published var currentApp: String = ""
    @Published var currentTitle: String = ""
    @Published var currentURL: String? = nil

    private var appSwitchObserver: NSObjectProtocol?
    private var axObserver: AXObserver?
    private let backendClient: BackendClient
    private let transitionDetector: TransitionDetector

    func startMonitoring() {
        // 1. App switch detection — event-driven, zero CPU cost
        //    REQUIRES: Nothing (NSWorkspace is public API)
        appSwitchObserver = NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification,
            object: nil,
            queue: .main
        ) { [weak self] notification in
            guard let app = notification.userInfo?[NSWorkspace.applicationUserInfoKey]
                    as? NSRunningApplication else { return }
            self?.handleAppSwitch(app)
        }

        // 2. Window title changes — via AXObserver (Accessibility API)
        //    REQUIRES: Accessibility permission ONLY (no monthly re-auth)
        //    This fires when the focused window's title changes (e.g., switching browser tabs)
        setupAXObserver()
    }

    private func setupAXObserver() {
        guard let frontApp = NSWorkspace.shared.frontmostApplication else { return }
        let pid = frontApp.processIdentifier

        var observer: AXObserver?
        let callback: AXObserverCallback = { _, element, notification, refcon in
            guard let refcon = refcon else { return }
            let monitor = Unmanaged<ScreenMonitor>.fromOpaque(refcon).takeUnretainedValue()
            monitor.handleTitleChange(element: element)
        }

        AXObserverCreate(pid, callback, &observer)
        guard let observer = observer else { return }

        let appElement = AXUIElementCreateApplication(pid)
        let refcon = Unmanaged.passUnretained(self).toOpaque()

        AXObserverAddNotification(observer, appElement, kAXFocusedWindowChangedNotification as CFString, refcon)
        AXObserverAddNotification(observer, appElement, kAXTitleChangedNotification as CFString, refcon)

        CFRunLoopAddSource(CFRunLoopGetCurrent(), AXObserverGetRunLoopSource(observer), .defaultMode)
        self.axObserver = observer
    }

    private func handleTitleChange(element: AXUIElement) {
        var titleValue: CFTypeRef?
        AXUIElementCopyAttributeValue(element, kAXTitleAttribute as CFString, &titleValue)
        let title = titleValue as? String ?? ""

        if title != currentTitle {
            currentTitle = title
            captureAndReport()
        }
    }

    private func handleAppSwitch(_ app: NSRunningApplication) {
        let appName = app.localizedName ?? "Unknown"
        let previousApp = currentApp
        currentApp = appName

        // Re-attach AX observer to new app's PID
        setupAXObserver()

        // Notify transition detector of app switch
        transitionDetector.recordAppSwitch(
            from: previousApp,
            to: appName,
            timestamp: Date()
        )

        captureAndReport()
    }

    private func captureAndReport() {
        // Get window title via AX API (no Screen Recording needed)
        let appElement = AXUIElementCreateSystemWide()
        var focusedWindow: CFTypeRef?
        AXUIElementCopyAttributeValue(appElement, kAXFocusedApplicationAttribute as CFString, &focusedWindow)

        // Browser URL extraction (same as blueprint — AppleScript, unchanged)
        var url: String? = nil
        let browsers = ["Google Chrome", "Safari", "Brave Browser", "Arc", "Microsoft Edge"]
        if browsers.contains(currentApp) {
            url = BrowserMonitor.getActiveTabURL(browser: currentApp)
        }

        // Report to backend
        Task {
            let response = await backendClient.reportActivity(
                appName: currentApp,
                windowTitle: currentTitle,
                url: url,
                isIdle: false
            )

            // Handle intervention if returned — but ONLY if transition detector approves
            if let intervention = response?.intervention {
                if transitionDetector.isAtBreakpoint() {
                    TierManager.shared.deliver(intervention)
                } else {
                    TierManager.shared.queue(intervention)  // Deliver at next breakpoint
                }
            }
        }
    }
}
```

**Why this matters**: This removes the Screen Recording permission entirely. The app now needs ONLY Accessibility permission, which does NOT have monthly re-authorization on Sequoia. Window titles are read via `AXUIElementCopyAttributeValue(kAXTitleAttribute)` instead of `CGWindowListCopyWindowInfo(kCGWindowName)`. Same data, no monthly popup.

**Permissions the app now needs (reduced from blueprint):**
- Accessibility — AX API for window titles (one-time grant, no re-auth)
- Automation — AppleScript for browser URLs (per-app, granted on first use)
- That's it. No Screen Recording.

---

## 3. NEW SYSTEM: ADHD ONBOARDING & DIAGNOSTIC CALIBRATION

### 3.1 Onboarding User Flow

The onboarding has **4 screens**, each designed for ADHD attention spans (under 60 seconds per screen):

```
Screen 1: Welcome + ASRS-v1.1 Screener (6 items, ~2 min)
    ↓
Screen 2: ADHD Profile Setup (subtype, medication, optional BRIEF-A upload)
    ↓
Screen 3: macOS Permissions (Accessibility + Automation only)
    ↓
Screen 4: Whoop Connect (optional) + "Calibration starts now" message
    ↓
14-day silent calibration period begins
```

### 3.2 In-App ASRS-v1.1 Screener

The WHO ASRS-v1.1 6-item screener is freely available for clinical use. It takes under 2 minutes.

**File: `backend/knowledge/asrs_v1_1.json`**
```json
{
  "name": "ASRS-v1.1 Screener",
  "version": "1.1",
  "items": [
    {
      "id": 1,
      "domain": "inattention",
      "text": "How often do you have difficulty concentrating on what people say to you, even when they are speaking to you directly?",
      "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"],
      "scoring": {
        "threshold_type": "dark_shading",
        "dark_starts_at": "Sometimes"
      }
    },
    {
      "id": 2,
      "domain": "inattention",
      "text": "How often do you have trouble wrapping up the final details of a project, once the challenging parts have been done?",
      "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"],
      "scoring": {
        "threshold_type": "dark_shading",
        "dark_starts_at": "Sometimes"
      }
    },
    {
      "id": 3,
      "domain": "inattention",
      "text": "How often do you have difficulty getting things in order when you have to do a task that requires organization?",
      "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"],
      "scoring": {
        "threshold_type": "dark_shading",
        "dark_starts_at": "Sometimes"
      }
    },
    {
      "id": 4,
      "domain": "hyperactivity",
      "text": "When you have a task that requires a lot of thought, how often do you avoid or delay getting started?",
      "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"],
      "scoring": {
        "threshold_type": "dark_shading",
        "dark_starts_at": "Often"
      }
    },
    {
      "id": 5,
      "domain": "hyperactivity",
      "text": "How often do you fidget or squirm with your hands or feet when you have to sit down for a long time?",
      "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"],
      "scoring": {
        "threshold_type": "dark_shading",
        "dark_starts_at": "Sometimes"
      }
    },
    {
      "id": 6,
      "domain": "hyperactivity",
      "text": "How often do you feel overly active and compelled to do things, like you were driven by a motor?",
      "options": ["Never", "Rarely", "Sometimes", "Often", "Very Often"],
      "scoring": {
        "threshold_type": "dark_shading",
        "dark_starts_at": "Often"
      }
    }
  ],
  "scoring_method": "Count items where response falls in dark-shaded zone. 4+ = screen positive (sensitivity 68.7%, specificity 99.5%). Sum of all items 0-24 for severity.",
  "severity_bands": {
    "low_negative": [0, 9],
    "high_negative": [10, 13],
    "low_positive": [14, 17],
    "high_positive": [18, 24]
  },
  "citation": "Kessler RC, et al. The WHO Adult ADHD Self-Report Scale (ASRS). Psychol Med. 2005;35(2):245-56."
}
```

### 3.3 ADHD Profile Data Model

**File: `backend/models/adhd_profile.py`**
```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import date

class ADHDSubtype(str, Enum):
    PREDOMINANTLY_INATTENTIVE = "ADHD-PI"    # Primarily focus/organization issues
    PREDOMINANTLY_HYPERACTIVE = "ADHD-HI"    # Primarily impulsivity/restlessness
    COMBINED = "ADHD-C"                       # Both
    UNSPECIFIED = "unspecified"               # User unsure or undiagnosed

class MedicationType(str, Enum):
    NONE = "none"
    METHYLPHENIDATE = "methylphenidate"       # Ritalin, Concerta
    AMPHETAMINE = "amphetamine"               # Adderall, Vyvanse
    ATOMOXETINE = "atomoxetine"               # Strattera (non-stimulant)
    OTHER_STIMULANT = "other_stimulant"
    OTHER_NONSTIMULANT = "other_nonstimulant"

class ADHDProfile(BaseModel):
    """
    Created during onboarding. Used to calibrate every other system.
    This is the SINGLE SOURCE OF TRUTH for user-specific ADHD parameters.
    """
    # From ASRS screener (required)
    asrs_total_score: int = Field(ge=0, le=24)
    asrs_dark_count: int = Field(ge=0, le=6)  # Items in "dark shaded" zone
    asrs_severity: str  # low_negative | high_negative | low_positive | high_positive
    asrs_inattention_score: int = Field(ge=0, le=12)  # Sum of items 1-3
    asrs_hyperactivity_score: int = Field(ge=0, le=12) # Sum of items 4-6

    # User-reported (optional but valuable)
    subtype: ADHDSubtype = ADHDSubtype.UNSPECIFIED
    diagnosed: bool = False
    diagnosis_date: Optional[date] = None

    # Medication (critical for HRV/physiological baseline calibration)
    medication_type: MedicationType = MedicationType.NONE
    medication_dose_mg: Optional[float] = None
    medication_time: Optional[str] = None  # "08:00" — when they typically take it
    medication_active_hours: float = 0  # 0 = not medicated, 4-12 typical

    # Optional clinical data upload
    brief_a_bri_tscore: Optional[int] = None  # Behavioral Regulation Index T-score
    brief_a_mi_tscore: Optional[int] = None   # Metacognition Index T-score
    brief_a_gec_tscore: Optional[int] = None  # Global Executive Composite T-score
    # T-score >= 65 = clinically significant

    # Derived calibration parameters (set by system, not user)
    intervention_sensitivity: float = 1.0  # 0.5 = less frequent, 2.0 = more frequent
    max_interventions_per_90min: int = 3   # Hard cap, adapts based on severity
    focus_block_default_minutes: int = 25  # Adjusts based on severity + Whoop recovery
    calibration_complete: bool = False
    calibration_start_date: Optional[date] = None

    def compute_derived_parameters(self):
        """Set intervention parameters based on ASRS severity + subtype."""

        # Severity → intervention sensitivity
        sensitivity_map = {
            "low_negative": 0.5,   # Mild: fewer, gentler interventions
            "high_negative": 0.75,
            "low_positive": 1.0,   # Standard
            "high_positive": 1.5,  # More frequent check-ins
        }
        self.intervention_sensitivity = sensitivity_map.get(self.asrs_severity, 1.0)

        # Subtype → focus block duration
        if self.subtype == ADHDSubtype.PREDOMINANTLY_INATTENTIVE:
            self.focus_block_default_minutes = 20  # Shorter blocks for inattentive
            self.max_interventions_per_90min = 3
        elif self.subtype == ADHDSubtype.PREDOMINANTLY_HYPERACTIVE:
            self.focus_block_default_minutes = 15  # Even shorter, needs movement breaks
            self.max_interventions_per_90min = 4
        elif self.subtype == ADHDSubtype.COMBINED:
            self.focus_block_default_minutes = 15
            self.max_interventions_per_90min = 4

        # BRIEF-A overrides if available (more granular)
        if self.brief_a_mi_tscore and self.brief_a_mi_tscore >= 65:
            # High Metacognition deficit → needs more organizational scaffolding
            self.intervention_sensitivity *= 1.2
        if self.brief_a_bri_tscore and self.brief_a_bri_tscore >= 65:
            # High Behavioral Regulation deficit → needs more emotional regulation support
            pass  # Handled by SenticNet emotion routing, not frequency
```

### 3.4 Onboarding API Endpoint

**File: `backend/api/onboarding.py`**
```python
from fastapi import APIRouter
from models.adhd_profile import ADHDProfile, ADHDSubtype, MedicationType

router = APIRouter()

@router.post("/asrs-screener")
async def submit_asrs(responses: list[int]):
    """
    Accept ASRS-v1.1 responses (6 items, each 0-4).
    Returns severity band + recommended profile settings.
    """
    import json
    from pathlib import Path

    asrs_data = json.loads(
        (Path(__file__).parent.parent / "knowledge" / "asrs_v1_1.json").read_text()
    )

    total_score = sum(responses)
    dark_count = 0
    for i, resp in enumerate(responses):
        item = asrs_data["items"][i]
        threshold = ["Never", "Rarely", "Sometimes", "Often", "Very Often"].index(
            item["scoring"]["dark_starts_at"]
        )
        if resp >= threshold:
            dark_count += 1

    # Determine severity band
    severity = "low_negative"
    for band, (low, high) in asrs_data["severity_bands"].items():
        if low <= total_score <= high:
            severity = band
            break

    return {
        "total_score": total_score,
        "dark_count": dark_count,
        "screen_positive": dark_count >= 4,
        "severity": severity,
        "inattention_score": sum(responses[:3]),
        "hyperactivity_score": sum(responses[3:]),
    }

@router.post("/profile")
async def create_profile(profile: ADHDProfile):
    """Create or update ADHD profile. Computes derived calibration parameters."""
    profile.compute_derived_parameters()
    # Store in database
    # ... (implementation follows standard pattern from blueprint)
    return {"status": "profile_created", "profile": profile}

@router.post("/diagnostic-upload")
async def upload_diagnostic(
    brief_a_bri: int | None = None,
    brief_a_mi: int | None = None,
    brief_a_gec: int | None = None,
):
    """
    Optional: User uploads T-scores from clinical BRIEF-A assessment.
    These override ASRS-derived parameters for higher precision.

    T-scores are standardized (mean=50, SD=10).
    >= 65 = clinically significant (1.5 SD above mean)
    >= 70 = highly elevated
    """
    updates = {}
    if brief_a_bri is not None:
        updates["brief_a_bri_tscore"] = brief_a_bri
    if brief_a_mi is not None:
        updates["brief_a_mi_tscore"] = brief_a_mi
    if brief_a_gec is not None:
        updates["brief_a_gec_tscore"] = brief_a_gec
    # Update profile in database, recompute derived parameters
    return {"status": "diagnostic_data_added", "updates": updates}
```

---

## 4. NEW SYSTEM: TRANSITION-POINT DETECTION ENGINE

This is the core mechanism that solves the 23-minute interruption paradox.

**File: `backend/services/transition_detector.py`**
```python
from datetime import datetime, timedelta
from collections import deque
from enum import Enum

class BreakpointType(str, Enum):
    APP_SWITCH = "app_switch"             # User switched applications
    TAB_BURST = "tab_burst"               # 3+ tab switches in 30 seconds
    IDLE_RESUME = "idle_resume"           # Returned from idle (>30s)
    FILE_SAVE = "file_save"               # Detected save operation in title
    DISTRACTION_ENTRY = "distraction_entry"  # Just opened a distracting app
    SESSION_END = "session_end"           # Focus session timer expired

class TransitionDetector:
    """
    Detects natural task breakpoints for intervention delivery.

    Based on Iqbal & Bailey (CHI 2008): delivering notifications at coarse
    breakpoints reduces frustration and resumption lag. Their models achieved
    69-87% accuracy using UI event streams.

    RULES:
    - Interventions are ONLY delivered at detected breakpoints
    - If no breakpoint occurs within 5 minutes of trigger, downgrade to Tier 1 (ambient)
    - NEVER interrupt during sustained single-app focus
    """

    def __init__(self):
        self.recent_events: deque = deque(maxlen=100)
        self.current_app: str = ""
        self.current_app_since: datetime = datetime.now()
        self.last_breakpoint: datetime | None = None
        self.queued_intervention: dict | None = None

    def record_app_switch(self, from_app: str, to_app: str, timestamp: datetime):
        """Record an application switch event."""
        self.recent_events.append({
            "type": "app_switch",
            "from": from_app,
            "to": to_app,
            "timestamp": timestamp,
        })
        self.current_app = to_app
        self.current_app_since = timestamp
        self.last_breakpoint = timestamp

    def record_tab_switch(self, url_or_title: str, timestamp: datetime):
        """Record a browser tab switch."""
        self.recent_events.append({
            "type": "tab_switch",
            "target": url_or_title,
            "timestamp": timestamp,
        })

    def record_idle_start(self, timestamp: datetime):
        self.recent_events.append({"type": "idle_start", "timestamp": timestamp})

    def record_idle_end(self, timestamp: datetime):
        self.recent_events.append({"type": "idle_end", "timestamp": timestamp})
        self.last_breakpoint = timestamp

    def is_at_breakpoint(self) -> bool:
        """
        Returns True if the user is currently at a natural task boundary.
        Called by the Swift UI layer before delivering any intervention.
        """
        if not self.last_breakpoint:
            return False

        # A breakpoint is "fresh" for 10 seconds after detection
        seconds_since = (datetime.now() - self.last_breakpoint).total_seconds()
        return seconds_since < 10.0

    def detect_breakpoint_type(self) -> BreakpointType | None:
        """Analyze recent events to classify the current breakpoint type."""
        if not self.recent_events:
            return None

        now = datetime.now()
        last_event = self.recent_events[-1]

        # App switch is always a coarse breakpoint
        if last_event["type"] == "app_switch":
            return BreakpointType.APP_SWITCH

        # 3+ tab switches in 30 seconds = "tab burst" (user is scanning, not focused)
        recent_tabs = [
            e for e in self.recent_events
            if e["type"] == "tab_switch" and (now - e["timestamp"]).total_seconds() < 30
        ]
        if len(recent_tabs) >= 3:
            return BreakpointType.TAB_BURST

        # Return from idle
        if last_event["type"] == "idle_end":
            return BreakpointType.IDLE_RESUME

        return None

    def get_focus_duration_seconds(self) -> float:
        """How long the user has been on the current app without switching."""
        return (datetime.now() - self.current_app_since).total_seconds()

    def should_suppress_intervention(self) -> bool:
        """
        Returns True if the user is in deep focus and should NOT be interrupted.
        This is the HARD BLOCK — no intervention of any tier passes through.
        """
        focus_seconds = self.get_focus_duration_seconds()

        # Deep focus: 15+ minutes on a single productive app
        if focus_seconds > 900:  # 15 minutes
            return True

        return False
```

---

## 5. NEW SYSTEM: FIVE-TIER CALM NOTIFICATION ARCHITECTURE

**This replaces the single `InterventionPopup.swift` from blueprint Section 4.3.**

### 5.1 Tier Manager (Backend)

**File: `backend/services/notification_tier.py`**
```python
from enum import IntEnum
from models.adhd_profile import ADHDProfile

class NotificationTier(IntEnum):
    """
    Five escalation levels. Lower tiers require less attention.

    Tier 1: Ambient color shift on menu bar icon (user may not notice)
    Tier 2: Gentle pulse animation on menu bar icon
    Tier 3: Non-activating overlay panel (doesn't steal focus)
    Tier 4: Toast notification with optional sound
    Tier 5: Full notification (reserved for safety + hard deadlines only)
    """
    AMBIENT_COLOR = 1
    GENTLE_PULSE = 2
    OVERLAY_PANEL = 3
    TOAST_NOTIFICATION = 4
    FULL_NOTIFICATION = 5

def select_tier(
    intervention_type: str,
    behavioral_state: str,
    minutes_since_last_intervention: float,
    whoop_recovery_tier: str,
    adhd_profile: ADHDProfile,
) -> NotificationTier:
    """
    Select the appropriate notification tier based on context.

    Core principle: use the MINIMUM tier that will be effective.
    """

    # Safety escalation — always Tier 5
    if intervention_type == "safety_critical":
        return NotificationTier.FULL_NOTIFICATION

    # Hyperfocus wellbeing check (4+ hours) — Tier 3 maximum
    if intervention_type == "hyperfocus_wellbeing":
        return NotificationTier.OVERLAY_PANEL

    # Low Whoop recovery day — be gentler, use Tier 1-2
    if whoop_recovery_tier == "red":
        return NotificationTier.AMBIENT_COLOR

    # First intervention of the session — start gentle
    if minutes_since_last_intervention > 60:
        return NotificationTier.AMBIENT_COLOR

    # If user is actively distracted (scrolling social media), Tier 3 is appropriate
    if behavioral_state == "distracted":
        return NotificationTier.OVERLAY_PANEL

    # Repeated disengagement — escalate to Tier 3
    if intervention_type == "sustained_disengagement" and minutes_since_last_intervention < 30:
        return NotificationTier.OVERLAY_PANEL

    # Default: ambient awareness
    return NotificationTier.GENTLE_PULSE
```

### 5.2 Swift Tier Manager

**File: `swift-app/ADHDSecondBrain/Notifications/TierManager.swift`**
```swift
import Cocoa

class TierManager {
    static let shared = TierManager()

    private var queuedIntervention: Intervention?
    private var queuedSince: Date?
    private let maxQueueTime: TimeInterval = 300  // 5 min max queue before downgrade

    /// Queue an intervention for delivery at next breakpoint
    func queue(_ intervention: Intervention) {
        queuedIntervention = intervention
        queuedSince = Date()

        // Start ambient indicator immediately (Tier 1)
        // This doesn't interrupt — just shifts the menu bar icon color
        AmbientMenuBar.shared.setIndicator(
            color: intervention.urgencyColor,
            pulse: false
        )
    }

    /// Deliver queued intervention (called when TransitionDetector signals a breakpoint)
    func deliverIfQueued() {
        guard let intervention = queuedIntervention else { return }

        let tier = intervention.notificationTier

        switch tier {
        case 1:
            // Already showing via ambient color — just keep it
            AmbientMenuBar.shared.setIndicator(color: intervention.urgencyColor, pulse: false)

        case 2:
            // Add pulse animation to menu bar icon
            AmbientMenuBar.shared.setIndicator(color: intervention.urgencyColor, pulse: true)

        case 3:
            // Non-activating overlay panel
            CalmOverlayPanel.shared.show(intervention: intervention)

        case 4:
            // System toast notification
            sendUserNotification(intervention)

        case 5:
            // Full notification — safety critical only
            CalmOverlayPanel.shared.show(intervention: intervention)
            sendUserNotification(intervention)

        default:
            break
        }

        queuedIntervention = nil
    }

    /// Called every second — handles timeout downgrades
    func tick() {
        guard let queuedSince = queuedSince, queuedIntervention != nil else { return }

        let elapsed = Date().timeIntervalSince(queuedSince)

        // After 2 minutes queued, upgrade to gentle pulse (Tier 2)
        if elapsed > 120 {
            AmbientMenuBar.shared.setIndicator(
                color: queuedIntervention?.urgencyColor ?? .orange,
                pulse: true
            )
        }

        // After 5 minutes queued with no breakpoint, downgrade to ambient-only
        // and clear the queue (the moment passed)
        if elapsed > maxQueueTime {
            AmbientMenuBar.shared.setIndicator(color: .clear, pulse: false)
            queuedIntervention = nil
            self.queuedSince = nil
        }
    }
}
```

### 5.3 Non-Activating Overlay Panel (Tier 3)

**File: `swift-app/ADHDSecondBrain/UI/CalmOverlayPanel.swift`**
```swift
import Cocoa
import SwiftUI

/// A floating panel that displays interventions WITHOUT stealing keyboard focus.
/// The user's cursor stays in their current app. They can glance at the panel
/// and either click an action or ignore it entirely.
class CalmOverlayPanel {
    static let shared = CalmOverlayPanel()

    private var panel: NSPanel?
    private var dismissTimer: Timer?

    func show(intervention: Intervention) {
        // Dismiss any existing panel
        dismiss()

        // Create NSPanel with non-activating behavior
        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 340, height: 160),
            styleMask: [.nonactivatingPanel, .titled, .closable],
            backing: .buffered,
            defer: false
        )

        // CRITICAL: These flags prevent focus stealing
        panel.level = .floating
        panel.isFloatingPanel = true
        panel.becomesKeyOnlyIfNeeded = true
        panel.hidesOnDeactivate = false
        panel.collectionBehavior = [.canJoinAllSpaces, .transient]

        // Position: top-right corner, below menu bar
        if let screen = NSScreen.main {
            let screenFrame = screen.visibleFrame
            panel.setFrameOrigin(NSPoint(
                x: screenFrame.maxX - 356,
                y: screenFrame.maxY - 176
            ))
        }

        // SwiftUI content
        let contentView = NSHostingView(rootView: InterventionCard(
            intervention: intervention,
            onAction: { [weak self] action in
                self?.handleAction(action, intervention: intervention)
            },
            onDismiss: { [weak self] in
                self?.dismiss()
                // Record dismissal for adaptive frequency learning
                Task {
                    await BackendClient.shared.recordInterventionResponse(
                        interventionId: intervention.id,
                        action: nil,
                        dismissed: true
                    )
                }
            }
        ))
        panel.contentView = contentView

        // Subtle slide-in animation
        panel.alphaValue = 0
        panel.orderFront(nil)
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.3
            panel.animator().alphaValue = 1.0
        }

        self.panel = panel

        // Auto-dismiss after 15 seconds (ADHD: short attention window)
        dismissTimer = Timer.scheduledTimer(withTimeInterval: 15.0, repeats: false) { [weak self] _ in
            self?.dismiss()
        }
    }

    func dismiss() {
        dismissTimer?.invalidate()
        NSAnimationContext.runAnimationGroup({ context in
            context.duration = 0.2
            panel?.animator().alphaValue = 0
        }, completionHandler: { [weak self] in
            self?.panel?.orderOut(nil)
            self?.panel = nil
        })
    }

    private func handleAction(_ action: InterventionAction, intervention: Intervention) {
        dismiss()
        Task {
            await BackendClient.shared.recordInterventionResponse(
                interventionId: intervention.id,
                action: action.id,
                dismissed: false
            )
        }
    }
}
```

---

## 6. NEW SYSTEM: HYPERFOCUS CLASSIFIER

**File: `backend/services/hyperfocus_classifier.py`**
```python
from datetime import datetime
from services.activity_classifier import classify_activity

class HyperfocusType:
    PRODUCTIVE = "productive"       # Deep work on a priority task — PROTECT THIS
    UNPRODUCTIVE = "unproductive"   # Doom-scrolling, gaming, rabbit holes — gently redirect
    AMBIGUOUS = "ambiguous"         # Research that might be relevant or might be a rabbit hole

class HyperfocusClassifier:
    """
    Detects and classifies hyperfocus episodes.

    Detection criteria (all must be true):
    - Single application focus for 45+ minutes
    - Low input variability (consistent typing/mouse patterns)
    - Minimal tab/window switching
    - No idle gaps > 60 seconds

    Classification uses app category + user's stated priorities + time of day.

    CRITICAL RULE: Productive hyperfocus is NEVER interrupted except for:
    - 4+ hour wellbeing check (hydration, posture, movement)
    - Hard calendar deadlines within 15 minutes
    - Safety-critical depression/toxicity threshold
    """

    # App categories that count as productive (from activity_classifier)
    PRODUCTIVE_CATEGORIES = {
        "development", "writing", "research", "design", "productivity"
    }

    # App categories that are always unproductive hyperfocus
    UNPRODUCTIVE_CATEGORIES = {
        "social_media", "entertainment", "shopping", "news"
    }

    def classify(
        self,
        current_app: str,
        app_category: str,
        session_duration_minutes: float,
        recent_switch_count: int,
        time_of_day: int,  # hour 0-23
        user_priority_apps: list[str] | None = None,
    ) -> dict:
        """
        Returns classification + recommended action.
        Only call this when session_duration_minutes >= 45.
        """

        if session_duration_minutes < 45:
            return {"type": None, "action": "none"}

        # Classify based on app category
        if app_category in self.PRODUCTIVE_CATEGORIES:
            focus_type = HyperfocusType.PRODUCTIVE
        elif app_category in self.UNPRODUCTIVE_CATEGORIES:
            focus_type = HyperfocusType.UNPRODUCTIVE
        elif app_category == "browser":
            # Browsers are ambiguous — could be research or rabbit hole
            focus_type = HyperfocusType.AMBIGUOUS
        else:
            focus_type = HyperfocusType.AMBIGUOUS

        # Override: user's priority apps are always productive
        if user_priority_apps and current_app.lower() in [a.lower() for a in user_priority_apps]:
            focus_type = HyperfocusType.PRODUCTIVE

        # Time-of-day modifier: late night (11 PM - 5 AM) makes everything more suspect
        if time_of_day >= 23 or time_of_day < 5:
            if focus_type == HyperfocusType.AMBIGUOUS:
                focus_type = HyperfocusType.UNPRODUCTIVE

        # Determine recommended action
        actions = {
            HyperfocusType.PRODUCTIVE: {
                "action": "protect",
                "suppress_interventions": True,
                "wellbeing_check_at_minutes": 240,  # 4 hours
                "ambient_indicator": "in_the_zone",  # Green glow on menu bar
                "time_display": True,  # Show elapsed time for time-blind awareness
            },
            HyperfocusType.UNPRODUCTIVE: {
                "action": "gentle_redirect",
                "suppress_interventions": False,
                "tier_sequence": [1, 2, 3],  # Escalate: ambient → pulse → overlay
                "tier_timing_minutes": [30, 60, 90],  # When to escalate
                "message_tone": "compassionate",  # Never shaming
            },
            HyperfocusType.AMBIGUOUS: {
                "action": "check_in",
                "suppress_interventions": False,
                "tier": 3,  # Overlay panel asking "Is this the right task?"
                "check_in_at_minutes": 60,
            },
        }

        return {
            "type": focus_type,
            "session_minutes": session_duration_minutes,
            "app": current_app,
            "category": app_category,
            **actions[focus_type],
        }
```

---

## 7. NEW SYSTEM: ECOLOGICAL MOMENTARY ASSESSMENT (EMA)

Brief daily self-reports that calibrate the passive monitoring models.

**File: `backend/services/ema_service.py`**
```python
from datetime import datetime, time

class EMAService:
    """
    Delivers 2 brief check-ins per day at natural breakpoints:
    - Mid-morning (10-11 AM, at first detected breakpoint in window)
    - End-of-day (5-6 PM, at first detected breakpoint in window)

    Each check-in: 3-5 slider items, takes < 45 seconds.
    Compliance target: 70-85% (research shows this is achievable with ADHD).
    """

    EMA_ITEMS = [
        {
            "id": "focus",
            "text": "How focused have you felt today?",
            "scale": [0, 100],
            "anchors": ["Scattered", "Laser focused"],
            "always_show": True,
        },
        {
            "id": "mood",
            "text": "How's your mood right now?",
            "scale": [0, 100],
            "anchors": ["Low", "Great"],
            "always_show": True,
        },
        {
            "id": "energy",
            "text": "Energy level?",
            "scale": [0, 100],
            "anchors": ["Running on empty", "Fully charged"],
            "always_show": True,
        },
        {
            "id": "task_satisfaction",
            "text": "How satisfied are you with what you accomplished?",
            "scale": [0, 100],
            "anchors": ["Not at all", "Very satisfied"],
            "always_show": False,  # Only in end-of-day check-in
        },
        {
            "id": "overwhelm",
            "text": "How overwhelmed do you feel?",
            "scale": [0, 100],
            "anchors": ["Calm", "Drowning"],
            "always_show": False,  # Rotated in every other day
        },
    ]

    def get_ema_prompt(self, time_of_day: str) -> dict:
        """
        Returns the EMA prompt appropriate for the time of day.
        time_of_day: "morning" or "evening"
        """
        items = [item for item in self.EMA_ITEMS if item["always_show"]]

        if time_of_day == "evening":
            items.append(next(i for i in self.EMA_ITEMS if i["id"] == "task_satisfaction"))

        # Rotate optional items (one per day)
        day_of_year = datetime.now().timetuple().tm_yday
        optional_items = [i for i in self.EMA_ITEMS if not i["always_show"] and i["id"] != "task_satisfaction"]
        if optional_items:
            items.append(optional_items[day_of_year % len(optional_items)])

        return {
            "type": f"ema_{time_of_day}",
            "items": items,
            "estimated_seconds": len(items) * 8,  # ~8 seconds per slider
            "reward_type": "insight",  # Show a personalized insight after completion
        }

    def process_ema_response(self, responses: dict[str, int], timestamp: datetime) -> dict:
        """
        Process EMA responses. Returns calibration updates for the system.

        These responses serve as GROUND TRUTH for concept bottleneck predictions:
        - If the system predicted "distracted" but user reports focus=80, recalibrate
        - If SenticNet says engagement=-40 but user reports mood=90, adjust weights
        """
        calibration_signals = []

        if responses.get("focus", 50) < 30 and responses.get("overwhelm", 50) > 70:
            calibration_signals.append("user_confirms_overwhelmed")

        if responses.get("energy", 50) < 25:
            calibration_signals.append("low_energy_self_report")

        return {
            "responses": responses,
            "timestamp": timestamp.isoformat(),
            "calibration_signals": calibration_signals,
        }
```

---

## 8. NEW SYSTEM: ADAPTIVE FREQUENCY LEARNING

**File: `backend/services/adaptive_frequency.py`**
```python
import random
import math
from collections import defaultdict

class ThompsonSamplingBandit:
    """
    Contextual bandit using Thompson Sampling for adaptive intervention frequency.

    Arms: [deliver_intervention, skip_intervention]
    Context: time_of_day, app_category, minutes_since_last, whoop_recovery, ema_focus
    Reward: user_returned_to_productive_task_within_5min (binary)

    This learns WHEN to intervene, not WHAT to suggest.
    The JITAI engine decides WHAT; this decides IF/WHEN.

    Cold start: Use population-level priors from ADHD known-group data.
    Personalization kicks in after ~50-100 decision points (2-4 weeks).
    """

    def __init__(self):
        # Beta distribution parameters per context bucket
        # key: context_hash → {"alpha": successes+1, "beta": failures+1}
        self.arms = defaultdict(lambda: {"alpha": 2, "beta": 2})  # Weak prior

    def _context_key(self, context: dict) -> str:
        """Discretize context into buckets for the bandit."""
        hour_bucket = context.get("hour", 12) // 4  # 6 buckets: 0-3, 4-7, ...
        recovery = "high" if context.get("whoop_recovery", 50) > 66 else "low" if context.get("whoop_recovery", 50) < 34 else "mid"
        recency = "recent" if context.get("minutes_since_last", 60) < 30 else "not_recent"
        return f"{hour_bucket}_{recovery}_{recency}"

    def should_deliver(self, context: dict) -> bool:
        """
        Sample from posterior to decide whether to deliver intervention.
        Returns True if we should deliver, False if we should skip.
        """
        key = self._context_key(context)
        arm = self.arms[key]

        # Thompson Sampling: draw from Beta distribution
        sampled_reward = random.betavariate(arm["alpha"], arm["beta"])

        # Deliver if sampled reward > 0.5 (better than random)
        return sampled_reward > 0.5

    def update(self, context: dict, success: bool):
        """
        Update the model based on outcome.
        success = True if user returned to productive task within 5 min
        """
        key = self._context_key(context)
        if success:
            self.arms[key]["alpha"] += 1
        else:
            self.arms[key]["beta"] += 1

    def get_stats(self) -> dict:
        """Return current learned parameters for debugging/logging."""
        return {
            key: {
                "expected_reward": arm["alpha"] / (arm["alpha"] + arm["beta"]),
                "n_observations": arm["alpha"] + arm["beta"] - 4,  # subtract prior
            }
            for key, arm in self.arms.items()
        }
```

---

## 9. NEW SYSTEM: GAMIFICATION & REWARD ENGINE

**File: `backend/services/gamification_service.py`**
```python
from datetime import datetime, date

class GamificationService:
    """
    Gamification designed for ADHD reward sensitivity.

    Key principles:
    - Variable reward schedules (dopamine is about anticipation, not receipt)
    - Rotate reward types every 2 weeks (combat hedonic adaptation)
    - NEVER use punishment (no streak-breaking shame, no lost progress)
    - "Forgiveness mechanics" for missed days
    - Immediate micro-rewards after productive behaviors

    Based on: ADHD interest-based nervous system (PINCH model:
    Passion, Interest, Novelty, Challenge, Urgency)
    """

    # XP amounts for different behaviors
    XP_TABLE = {
        "focus_15min": 10,           # 15 minutes of uninterrupted focused work
        "focus_30min": 25,           # Bonus for 30 min
        "focus_60min": 60,           # Big bonus for full hour
        "intervention_accepted": 15, # Followed through on a suggestion
        "ema_completed": 20,         # Completed daily check-in
        "vent_session": 10,          # Used the venting chat (emotional regulation practice)
        "morning_briefing_read": 5,  # Checked Whoop morning briefing
        "break_taken": 10,           # Actually took a suggested break
    }

    def award_xp(self, behavior: str, timestamp: datetime) -> dict:
        """Award XP for a positive behavior. Returns reward feedback."""
        base_xp = self.XP_TABLE.get(behavior, 5)

        # Variable multiplier (1.0 to 2.0) — ADHD brains love surprises
        import random
        multiplier = random.choice([1.0, 1.0, 1.0, 1.5, 2.0])  # 40% chance of bonus
        total_xp = int(base_xp * multiplier)

        reward = {
            "xp_earned": total_xp,
            "behavior": behavior,
            "was_bonus": multiplier > 1.0,
            "bonus_message": "Nice bonus!" if multiplier > 1.0 else None,
            "timestamp": timestamp.isoformat(),
        }

        return reward

    def get_daily_summary(self, user_date: date) -> dict:
        """
        Daily progress summary. Framed positively — always highlights
        what was accomplished, never what was missed.
        """
        # TODO: Pull from database
        return {
            "date": user_date.isoformat(),
            "total_xp_today": 0,  # Sum from DB
            "focus_minutes_today": 0,  # From metrics engine
            "streak_days": 0,  # Consecutive days with any activity
            "streak_forgiveness_remaining": 2,  # Can miss 2 days without breaking streak
            "level": 1,
            "next_level_xp": 500,
        }
```

---

## 10. NEW SYSTEM: DIGITAL PHENOTYPING COLLECTOR

**File: `backend/services/phenotype_collector.py`**
```python
from dataclasses import dataclass
from collections import deque
from datetime import datetime

@dataclass
class DesktopPhenotypeSnapshot:
    """
    Passive behavioral signals collected every 30 seconds.
    These form the user's "digital phenotype" for ADHD pattern detection.

    Based on: King's College ART study digital markers (notification response d=1.05,
    response time variability d=0.84) + Cell 2024 wearable phenotyping study.
    """
    timestamp: datetime

    # App context signals
    app_switches_last_5min: int
    unique_apps_last_5min: int
    current_session_seconds: float
    category_distribution: dict  # {"development": 120, "social_media": 45, ...}

    # Input pattern signals (collected in Swift, sent with each /screen/activity call)
    typing_speed_wpm: float | None = None       # Words per minute (if typing detected)
    typing_error_rate: float | None = None       # Backspace ratio
    mouse_distance_px: float | None = None       # Total mouse travel in last 30s
    mouse_idle_ratio: float | None = None        # % of last 30s with no mouse movement
    scroll_events_count: int | None = None       # Scroll actions in last 30s

    # Derived ADHD-specific phenotype features
    session_duration_bimodality: float | None = None  # High = ADHD-typical very-short + very-long sessions
    switch_regularity: float | None = None        # CV of inter-switch intervals (high CV = ADHD marker)
    time_of_day_hour: int = 0
    is_medicated_window: bool = False             # Based on medication_time + active_hours from profile

class PhenotypeCollector:
    """
    Aggregates raw phenotype snapshots into 15-minute summaries for storage.
    Only summaries are persisted (privacy: no raw keystroke data stored).
    """

    def __init__(self):
        self.raw_buffer: deque = deque(maxlen=30)  # ~15 min at 30s intervals

    def add_snapshot(self, snapshot: DesktopPhenotypeSnapshot):
        self.raw_buffer.append(snapshot)

    def compute_15min_summary(self) -> dict:
        """Aggregate buffered snapshots into a privacy-safe summary."""
        if not self.raw_buffer:
            return {}

        snapshots = list(self.raw_buffer)

        # Average metrics
        avg_switches = sum(s.app_switches_last_5min for s in snapshots) / len(snapshots)
        avg_session = sum(s.current_session_seconds for s in snapshots) / len(snapshots)
        typing_speeds = [s.typing_speed_wpm for s in snapshots if s.typing_speed_wpm]
        avg_typing = sum(typing_speeds) / len(typing_speeds) if typing_speeds else None

        # Variability metrics (ADHD markers)
        import statistics
        switch_times = [s.app_switches_last_5min for s in snapshots]
        switch_cv = (statistics.stdev(switch_times) / statistics.mean(switch_times)
                     if len(switch_times) > 1 and statistics.mean(switch_times) > 0
                     else 0)

        summary = {
            "period_start": snapshots[0].timestamp.isoformat(),
            "period_end": snapshots[-1].timestamp.isoformat(),
            "avg_switches_per_5min": round(avg_switches, 1),
            "avg_session_seconds": round(avg_session, 0),
            "switch_variability_cv": round(switch_cv, 3),
            "avg_typing_wpm": round(avg_typing, 1) if avg_typing else None,
            "is_medicated": snapshots[-1].is_medicated_window,
        }

        self.raw_buffer.clear()
        return summary
```

---

## 11. UPDATES TO: JITAI ENGINE

**These modifications apply to `jitai_engine.py` from blueprint Section 6.3.**

### Add to the `__init__` method:
```python
# NEW: Wire in the new subsystems
self.transition_detector = TransitionDetector()
self.hyperfocus_classifier = HyperfocusClassifier()
self.adaptive_bandit = ThompsonSamplingBandit()
self.adhd_profile: ADHDProfile | None = None  # Loaded at startup
self.intervention_count_this_block: int = 0
self.block_start_time: datetime = datetime.now()
```

### Replace the `evaluate` method's entry point:
```python
def evaluate(self, metrics: ADHDMetrics, emotion_context: dict | None = None) -> Intervention | None:
    # === NEW GATE 0: Transition detector must approve delivery ===
    # The JITAI engine can DECIDE an intervention is needed,
    # but the intervention is QUEUED, not delivered, until a breakpoint.
    # The Swift layer calls transition_detector.is_at_breakpoint() before showing.

    # === NEW GATE 1: Hyperfocus protection ===
    if metrics.current_streak_minutes > 45:
        hf = self.hyperfocus_classifier.classify(
            current_app=metrics.current_app,
            app_category=metrics.current_category,
            session_duration_minutes=metrics.current_streak_minutes,
            recent_switch_count=metrics.context_switch_rate_5min,
            time_of_day=datetime.now().hour,
        )
        if hf["type"] == "productive" and hf.get("suppress_interventions"):
            return None  # NEVER interrupt productive hyperfocus

    # === NEW GATE 2: Per-block cap (max 3 per 90 min) ===
    if self.adhd_profile:
        max_per_block = self.adhd_profile.max_interventions_per_90min
    else:
        max_per_block = 3

    if self.intervention_count_this_block >= max_per_block:
        minutes_in_block = (datetime.now() - self.block_start_time).total_seconds() / 60
        if minutes_in_block < 90:
            return None  # Cap reached, wait for next block
        else:
            # Reset block
            self.intervention_count_this_block = 0
            self.block_start_time = datetime.now()

    # === NEW GATE 3: Adaptive bandit decides IF to deliver ===
    context = {
        "hour": datetime.now().hour,
        "whoop_recovery": metrics.whoop_recovery_score or 50,
        "minutes_since_last": self._minutes_since_last(),
    }
    if not self.adaptive_bandit.should_deliver(context):
        return None  # Bandit says skip this opportunity

    # === Original JITAI rules follow (from blueprint) ===
    # ... (keep existing rules for distraction_spiral, sustained_disengagement,
    #      hyperfocus_check, emotional_escalation)
    # But now each returned intervention gets a notification_tier assigned:

    intervention = self._evaluate_rules(metrics, emotion_context)  # Original logic
    if intervention:
        intervention.notification_tier = select_tier(
            intervention_type=intervention.type,
            behavioral_state=metrics.behavioral_state,
            minutes_since_last_intervention=self._minutes_since_last(),
            whoop_recovery_tier=metrics.whoop_recovery_tier or "yellow",
            adhd_profile=self.adhd_profile or ADHDProfile(asrs_total_score=14, asrs_dark_count=4, asrs_severity="low_positive", asrs_inattention_score=7, asrs_hyperactivity_score=7),
        )
        self.intervention_count_this_block += 1

    return intervention
```

---

## 12. UPDATES TO: SENTICNET PIPELINE

**Add Hourglass → ADHD state mapping to `senticnet_pipeline.py` from blueprint Section 5.2.**

### New method in SenticNetPipeline class:
```python
def map_hourglass_to_adhd_state(self, hourglass: dict) -> dict:
    """
    Map SenticNet Hourglass of Emotions dimensions to ADHD-relevant states.

    Hourglass dimensions (each -1 to +1):
    - Introspection: Joy (+) ↔ Sadness (-)
    - Temper: Calmness (+) ↔ Anger (-)
    - Attitude: Pleasantness (+) ↔ Disgust (-)
    - Sensitivity: Eagerness (+) ↔ Fear (-)

    ADHD state interpretations:
    - Low Introspection + Low Sensitivity = boredom-driven disengagement
    - Low Temper + Low Introspection = frustration spiral (core ADHD trigger)
    - High Attitude negativity = shame/RSD (Rejection Sensitive Dysphoria)
    - High Sensitivity + High Introspection = productive flow (don't interrupt!)
    - Rapid oscillation across Temper/Introspection = emotional dysregulation
    """
    introspection = hourglass.get("introspection", 0)  # joy ↔ sadness
    temper = hourglass.get("temper", 0)                 # calm ↔ anger
    attitude = hourglass.get("attitude", 0)             # pleasant ↔ disgust
    sensitivity = hourglass.get("sensitivity", 0)       # eager ↔ fear

    adhd_states = {
        "boredom_disengagement": introspection < -0.3 and sensitivity < -0.2,
        "frustration_spiral": temper < -0.4 and introspection < -0.2,
        "shame_rsd": attitude < -0.5,
        "productive_flow": sensitivity > 0.3 and introspection > 0.3,
        "emotional_dysregulation": abs(temper) > 0.6 or abs(introspection) > 0.7,
        "anxiety_comorbid": sensitivity < -0.5 and temper < 0,
    }

    # Primary state = first True state in priority order
    primary = "neutral"
    for state, is_active in adhd_states.items():
        if is_active:
            primary = state
            break

    return {
        "primary_adhd_state": primary,
        "all_states": {k: v for k, v in adhd_states.items() if v},
        "hourglass_raw": hourglass,
        "recommended_ef_domain": self._map_state_to_ef_domain(primary),
    }

def _map_state_to_ef_domain(self, state: str) -> str:
    """Map ADHD emotional state to Barkley's EF deficit domain for intervention selection."""
    mapping = {
        "boredom_disengagement": "self_motivation",
        "frustration_spiral": "self_regulation_emotion",
        "shame_rsd": "self_regulation_emotion",
        "productive_flow": "none",  # Don't intervene!
        "emotional_dysregulation": "self_regulation_emotion",
        "anxiety_comorbid": "self_regulation_emotion",
        "neutral": "none",
    }
    return mapping.get(state, "none")
```

---

## 13. UPDATES TO: XAI EXPLAINER — CONCEPT BOTTLENECK WITH USER CORRECTION

**Extends `xai_explainer.py` from blueprint Section 6.4.**

### Add user correction mechanism:
```python
class ConceptBottleneckExplainer:
    # ... (keep existing methods from blueprint)

    # NEW: Concept definitions that users can correct
    CONCEPT_DEFINITIONS = {
        "emotional_valence": {
            "source": "senticnet_polarity",
            "label": "Mood",
            "description": "Whether your recent writing/activity feels positive or negative",
            "user_correctable": True,
        },
        "frustration_level": {
            "source": "senticnet_temper + keyboard_error_rate",
            "label": "Frustration",
            "description": "Signs of frustration in your activity patterns",
            "user_correctable": True,
        },
        "attention_consistency": {
            "source": "mouse_entropy + switch_rate + typing_variance",
            "label": "Focus stability",
            "description": "How steady your attention has been",
            "user_correctable": True,
        },
        "physiological_readiness": {
            "source": "whoop_recovery + hr_trend",
            "label": "Energy level",
            "description": "Your body's readiness based on Whoop data",
            "user_correctable": False,  # Physiological data is objective
        },
    }

    def generate_user_explanation(
        self,
        intervention_type: str,
        concept_activations: dict,
        tier: int,
    ) -> dict:
        """
        Generate a 3-tier progressive disclosure explanation.

        Tier 1 (always shown): Traffic light indicator + 1 emoji
        Tier 2 (tap to expand): One-sentence concept explanation
        Tier 3 (tap again): Full technical detail with correction option

        Based on research: Herm et al. (2023) found concept-level explanations
        minimize cognitive load while maintaining trust. For ADHD users,
        auto-expanding explanations cause information overload.
        """
        # Tier 1: Traffic light
        urgency_color = "amber" if tier <= 3 else "red"
        emoji = self._get_emoji(intervention_type)

        # Tier 2: One sentence
        active_concepts = [
            self.CONCEPT_DEFINITIONS[k]["label"]
            for k, v in concept_activations.items()
            if abs(v) > 0.5 and k in self.CONCEPT_DEFINITIONS
        ]
        sentence = self._build_sentence(intervention_type, active_concepts)

        # Tier 3: Detailed breakdown with correction
        details = []
        for concept_id, value in concept_activations.items():
            if concept_id in self.CONCEPT_DEFINITIONS:
                defn = self.CONCEPT_DEFINITIONS[concept_id]
                details.append({
                    "concept": defn["label"],
                    "value": value,
                    "description": defn["description"],
                    "can_correct": defn["user_correctable"],
                    "correction_prompt": f"Am I wrong about your {defn['label'].lower()}?" if defn["user_correctable"] else None,
                })

        return {
            "tier_1": {"color": urgency_color, "emoji": emoji},
            "tier_2": {"sentence": sentence},
            "tier_3": {"concepts": details},
        }

    def apply_user_correction(self, concept_id: str, user_value: float) -> dict:
        """
        User corrects a concept prediction.
        Example: System says frustration=0.8, user says "I'm not frustrated, I'm excited"

        This feeds back into the Concept Bottleneck Model to improve future predictions.
        Correction is stored and used as training signal.
        """
        return {
            "concept": concept_id,
            "system_prediction": None,  # Will be filled by caller
            "user_correction": user_value,
            "timestamp": datetime.now().isoformat(),
            "action": "recalibrate_concept_weights",
        }

    def _get_emoji(self, intervention_type: str) -> str:
        return {
            "distraction_spiral": "🌀",
            "sustained_disengagement": "💤",
            "hyperfocus_check": "⏰",
            "emotional_escalation": "🌊",
            "wellbeing_check": "💧",
        }.get(intervention_type, "💡")

    def _build_sentence(self, intervention_type: str, active_concepts: list[str]) -> str:
        concept_str = " and ".join(active_concepts[:2])  # Max 2 concepts in sentence
        templates = {
            "distraction_spiral": f"Your {concept_str} suggest your attention is jumping around.",
            "sustained_disengagement": f"Your {concept_str} show you've been away from focused work for a while.",
            "emotional_escalation": f"Your {concept_str} indicate things are feeling intense.",
        }
        return templates.get(intervention_type, f"Noticing some changes in your {concept_str}.")
```

---

## 14. UPDATES TO: SWIFT UI — ADHD-SPECIFIC UX

### Ambient Menu Bar Icon

**File: `swift-app/ADHDSecondBrain/UI/AmbientMenuBar.swift`**
```swift
import Cocoa

class AmbientMenuBar {
    static let shared = AmbientMenuBar()

    private var statusItem: NSStatusItem?
    private var pulseTimer: Timer?
    private var currentColor: NSColor = .systemGreen

    // Color meanings (warm spectrum, avoiding blue — ADHD has blue perception deficits):
    // Green = focused / in the zone
    // Yellow-green = mild drift detected
    // Amber = moderate distraction
    // Orange = sustained off-task
    // Red = safety concern only

    func setup(statusItem: NSStatusItem) {
        self.statusItem = statusItem
        setIndicator(color: .systemGreen, pulse: false)
    }

    func setIndicator(color: NSColor, pulse: Bool) {
        currentColor = color

        // Draw a small circle icon with the given color
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size, flipped: false) { rect in
            color.setFill()
            let circle = NSBezierPath(ovalIn: rect.insetBy(dx: 3, dy: 3))
            circle.fill()
            return true
        }
        image.isTemplate = false  // Use actual colors, not system tinting
        statusItem?.button?.image = image

        // Pulse animation
        pulseTimer?.invalidate()
        if pulse {
            pulseTimer = Timer.scheduledTimer(withTimeInterval: 1.5, repeats: true) { [weak self] _ in
                self?.animatePulse()
            }
        }
    }

    private func animatePulse() {
        guard let button = statusItem?.button else { return }
        NSAnimationContext.runAnimationGroup({ ctx in
            ctx.duration = 0.75
            button.animator().alphaValue = 0.4
        }, completionHandler: {
            NSAnimationContext.runAnimationGroup({ ctx in
                ctx.duration = 0.75
                button.animator().alphaValue = 1.0
            })
        })
    }
}
```

### EMA Prompt View

**File: `swift-app/ADHDSecondBrain/UI/EMAPromptView.swift`**
```swift
import SwiftUI

struct EMAPromptView: View {
    let items: [EMAItem]
    let onComplete: ([String: Int]) -> Void
    @State private var responses: [String: Double] = [:]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Quick check-in")
                .font(.system(size: 15, weight: .semibold))

            ForEach(items, id: \.id) { item in
                VStack(alignment: .leading, spacing: 4) {
                    Text(item.text)
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)

                    HStack {
                        Text(item.anchorLow)
                            .font(.system(size: 10))
                            .foregroundColor(.secondary)
                            .frame(width: 60, alignment: .leading)

                        Slider(
                            value: Binding(
                                get: { responses[item.id] ?? 50 },
                                set: { responses[item.id] = $0 }
                            ),
                            in: 0...100
                        )
                        .tint(.orange)

                        Text(item.anchorHigh)
                            .font(.system(size: 10))
                            .foregroundColor(.secondary)
                            .frame(width: 60, alignment: .trailing)
                    }
                }
            }

            Button("Done") {
                let intResponses = responses.mapValues { Int($0) }
                onComplete(intResponses)
            }
            .buttonStyle(.borderedProminent)
            .tint(.orange)
            .frame(maxWidth: .infinity, alignment: .trailing)
        }
        .padding(16)
        .frame(width: 320)
    }
}
```

---

## 15. PRIVACY ARCHITECTURE (SINGAPORE PDPA)

### Data Minimization Rules:
```
1. NEVER store raw window titles longer than 24 hours
   → Store only: app_name + category + duration
   → Window titles are processed in memory, then discarded

2. NEVER store raw text from venting/chat longer than needed
   → Process through SenticNet → store only sentic vectors
   → Raw text deleted after LLM response generated

3. NEVER store keystroke-level data
   → Aggregate to typing_speed_wpm + error_rate every 30 seconds
   → Raw key events never leave the Swift app process

4. Store only 15-minute behavioral summaries (from PhenotypeCollector)

5. All data encrypted at rest (SQLite: SQLCipher, PostgreSQL: pgcrypto)

6. User can export all data as JSON (GET /privacy/export)

7. User can delete all data (DELETE /privacy/all-data)

8. Data auto-expires: behavioral data after 30 days, summaries after 90 days

9. ADHD diagnostic data (ASRS scores, BRIEF-A T-scores) stored separately
   from behavioral data, with stronger access controls

10. SenticNet API calls: text sent to external API (sentic.net)
    → User must consent to this specifically during onboarding
    → Option to use offline senticnet package instead (no network calls)
```

---

## 16. SAFETY ESCALATION PROTOCOL

### Three-Tier Safety System (adds to blueprint Section 5 safety check):

```python
# In senticnet_pipeline.py, update _check_safety:

SAFETY_TIERS = {
    "green": {
        "description": "Normal operation",
        "action": "continue",
    },
    "yellow": {
        "description": "Concerning pattern detected",
        "criteria": "depression > 50 OR toxicity > 40 OR intensity < -60",
        "action": "gentle_checkin",
        "message": "Hey, I'm noticing things have been tough. Want to talk about it, or would a break help?",
        "show_resources": False,
    },
    "red": {
        "description": "Crisis indicators",
        "criteria": "depression > 70 AND toxicity > 60, OR intensity < -80 AND depression > 50",
        "action": "show_resources_immediately",
        "message": "I care about you. If you're going through a hard time, these people can help:",
        "resources": [
            {"name": "SOS 24-hour CareText", "contact": "text HOME to 1-767-4357", "region": "SG"},
            {"name": "IMH Mental Health Helpline", "contact": "6389-2222", "region": "SG"},
            {"name": "National Care Hotline", "contact": "1800-202-6868", "region": "SG"},
            {"name": "Samaritans of Singapore", "contact": "1800-221-4444", "region": "SG"},
        ],
        "system_behavior": [
            "Pause ALL monitoring-based interventions",
            "Disable gamification (no XP, no streaks)",
            "Only show safety resources + compassionate messages",
            "Resume normal operation ONLY when user explicitly requests it",
        ],
    },
}
```

---

## 17. UPDATED DATABASE SCHEMA ADDITIONS

**Add these tables to the PostgreSQL schema from blueprint Section 12:**

```sql
-- ADHD Profile (from onboarding)
CREATE TABLE adhd_profiles (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    asrs_total_score INTEGER NOT NULL,
    asrs_dark_count INTEGER NOT NULL,
    asrs_severity VARCHAR(20) NOT NULL,
    asrs_inattention_score INTEGER NOT NULL,
    asrs_hyperactivity_score INTEGER NOT NULL,
    subtype VARCHAR(20) DEFAULT 'unspecified',
    diagnosed BOOLEAN DEFAULT FALSE,
    medication_type VARCHAR(30) DEFAULT 'none',
    medication_dose_mg FLOAT,
    medication_time TIME,
    medication_active_hours FLOAT DEFAULT 0,
    brief_a_bri_tscore INTEGER,
    brief_a_mi_tscore INTEGER,
    brief_a_gec_tscore INTEGER,
    intervention_sensitivity FLOAT DEFAULT 1.0,
    max_interventions_per_90min INTEGER DEFAULT 3,
    focus_block_default_minutes INTEGER DEFAULT 25,
    calibration_complete BOOLEAN DEFAULT FALSE,
    calibration_start_date DATE
);

-- EMA Responses
CREATE TABLE ema_responses (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    time_of_day VARCHAR(10),  -- 'morning' or 'evening'
    focus_score INTEGER,
    mood_score INTEGER,
    energy_score INTEGER,
    task_satisfaction_score INTEGER,
    overwhelm_score INTEGER,
    calibration_signals JSONB
);

-- Digital Phenotype Summaries (15-min aggregates)
CREATE TABLE phenotype_summaries (
    id BIGSERIAL PRIMARY KEY,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    avg_switches_per_5min FLOAT,
    avg_session_seconds FLOAT,
    switch_variability_cv FLOAT,
    avg_typing_wpm FLOAT,
    is_medicated BOOLEAN,
    summary_data JSONB
);
CREATE INDEX idx_phenotype_time ON phenotype_summaries(period_start DESC);

-- Gamification
CREATE TABLE gamification_events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    behavior VARCHAR(50),
    xp_earned INTEGER,
    was_bonus BOOLEAN DEFAULT FALSE,
    daily_total INTEGER,
    streak_days INTEGER
);

-- Bandit learning state (persisted for restart recovery)
CREATE TABLE bandit_state (
    context_key VARCHAR(100) PRIMARY KEY,
    alpha FLOAT DEFAULT 2.0,
    beta FLOAT DEFAULT 2.0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User concept corrections (for CBM retraining)
CREATE TABLE concept_corrections (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    concept_id VARCHAR(50),
    system_prediction FLOAT,
    user_correction FLOAT,
    context JSONB
);
```

---

## 18. UPDATED API ENDPOINT ADDITIONS

| Method | Endpoint | Purpose | New? |
|--------|----------|---------|------|
| POST | `/onboarding/asrs-screener` | Submit ASRS-v1.1 responses | NEW |
| POST | `/onboarding/profile` | Create ADHD profile | NEW |
| POST | `/onboarding/diagnostic-upload` | Upload BRIEF-A T-scores | NEW |
| GET | `/onboarding/profile` | Get current profile | NEW |
| GET | `/ema/prompt` | Get current EMA prompt | NEW |
| POST | `/ema/response` | Submit EMA responses | NEW |
| GET | `/gamification/daily` | Get daily XP/streak summary | NEW |
| POST | `/gamification/award` | Award XP for behavior | NEW |
| POST | `/xai/correct-concept` | Submit user concept correction | NEW |
| GET | `/privacy/export` | Export all user data as JSON | NEW |
| DELETE | `/privacy/all-data` | Delete all user data | NEW |
| GET | `/privacy/dashboard` | Get data inventory summary | NEW |

---

## 19. UPDATED BUILD ORDER

**Insert these into the blueprint's Phase 1-7 schedule:**

### Phase 0 (before everything — Day 1):
```
0a. Implement ASRS-v1.1 screener endpoint + scoring
0b. Implement ADHDProfile model + compute_derived_parameters()
0c. Create onboarding API routes
```

### Phase 1 (Week 1-2) — ADD to existing:
```
AFTER blueprint step 5 (adhd_metrics.py), ADD:
5a. Implement transition_detector.py
5b. Implement hyperfocus_classifier.py
5c. Implement notification_tier.py (select_tier function)
```

### Phase 3 (Week 3-4) — MODIFY existing:
```
REPLACE blueprint step 12 with:
12. Implement UPDATED jitai_engine.py with all new gates
    (transition detection, hyperfocus protection, per-block cap, bandit)
12a. Implement adaptive_frequency.py (Thompson Sampling)
12b. Implement Hourglass → ADHD state mapping in senticnet_pipeline.py
```

### Phase 4 (Week 4-5) — ADD to Swift work:
```
AFTER blueprint step 21 (InterventionPopup), ADD:
21a. Implement AmbientMenuBar.swift (Tier 1-2)
21b. Implement CalmOverlayPanel.swift (Tier 3, NSPanel non-activating)
21c. Implement TierManager.swift (orchestration)
21d. Implement TransitionDetector.swift (client-side breakpoint signaling)
21e. REPLACE ScreenMonitor.swift with AX-only version (Section 2 of this doc)
21f. Implement EMAPromptView.swift
```

### Phase 5 (Week 5-6) — ADD:
```
AFTER blueprint step 29 (memory), ADD:
29a. Implement ema_service.py + EMA API endpoints
29b. Implement gamification_service.py + API endpoints
29c. Implement phenotype_collector.py
29d. Implement privacy endpoints (export, delete)
```

---

## 20. ANTI-PATTERNS: THINGS THAT MUST NEVER BE BUILT

These are evidence-based design prohibitions. None of the following should ever be built.

```
1. NEVER use variable-ratio notification schedules
   (creates addictive checking behavior — the opposite of what ADHD users need)

2. NEVER show streak-breaking penalties
   ("You lost your 12-day streak!" causes shame spirals in ADHD users)
   → Use "forgiveness mechanics" instead: streaks survive 2 missed days

3. NEVER auto-expand explanations
   (information overload for ADHD working memory deficits)
   → Progressive disclosure ONLY: user pulls deeper info when ready

4. NEVER interrupt productive hyperfocus
   (the 23-minute recovery cost is devastating for ADHD)
   → Exception: 4hr wellbeing check, hard deadlines, safety only

5. NEVER use guilt/shame framing in intervention messages
   ("You've wasted 2 hours" → "Ready to switch gears?")
   → Always upward counterfactuals, never downward

6. NEVER use Screen Recording permission for core monitoring
   (macOS Sequoia monthly re-auth is unacceptable UX for ADHD users)
   → Use Accessibility API (AXUIElement) only

7. NEVER store raw text or keystroke data
   (privacy violation + unnecessary for the system's function)
   → Process in memory, store only aggregate features

8. NEVER show more than 3 action choices per intervention
   (decision fatigue is heightened in ADHD)

9. NEVER deliver more than 3 interventions per 90-minute block
   (dose-response research shows diminishing returns after 3)

10. NEVER use blue as a primary UI color for ADHD-relevant indicators
    (ADHD population shows blue spectrum perception deficits)
    → Use warm spectrum: green → amber → orange → red
```

---

## HOW TO USE THESE THREE FILES TOGETHER

Reading order:

1. **`adhd-second-brain-blueprint.md`** = the core architecture, repo structure, all base service implementations, database schema, API contracts, config, setup scripts
2. **`architecture-diagram.mermaid`** = visual component diagram of the system
3. **`adhd-second-brain-supplement.md`** (this file) = research-driven design improvements that UPDATE and EXTEND the blueprint

**Rule**: Read all three files. Where the supplement modifies a blueprint section, the supplement takes priority. Where the supplement adds new systems, add them to the repo structure and build order as specified. The anti-patterns in Section 20 are absolute constraints — never violate them.
