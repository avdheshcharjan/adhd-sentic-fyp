# Phase 2: Native Swift Menu Bar App

> **Timeline**: Week 4–5 (after backend is stable)  
> **Dependencies**: Phase 1 (Backend must be running on `localhost:8420`)  
> **Requirements**: Xcode 15+, macOS 14+ (Sonoma), Apple Silicon

---

## Overview

The Swift app is a **lightweight, event-driven menu bar agent**. It does NOT do any ML inference or heavy processing — it captures screen state and sends it to the Python backend. The app lives exclusively in the menu bar (no dock icon) and delivers non-intrusive intervention popups.

### Design Principles
- **Minimal footprint** — ~25MB RAM, near-zero CPU when idle
- **Event-driven** — app switch via `NSWorkspace` notification (not polling)
- **ADHD-friendly notifications** — max 2–3 sentences, 2–3 action choices, non-modal
- **Non-intrusive** — `NSPanel` with `.nonactivatingPanel` (never steals focus)
- **Auto-dismiss** — interventions slide in from top-right, dismiss in 15 seconds

---

## Key Files to Create

### Project Configuration

| File | Purpose |
|------|---------|
| `swift-app/Package.swift` | SPM package definition, macOS 14+ target |
| `swift-app/ADHDSecondBrain/Info.plist` | `LSUIElement = true` (no dock icon), permission descriptions |

### Core Monitors

| File | Purpose |
|------|---------|
| `Monitors/ScreenMonitor.swift` | Main screen capture via `NSWorkspace` + `CGWindowList` |
| `Monitors/BrowserMonitor.swift` | AppleScript URL extraction for Safari, Chrome, Arc, etc. |
| `Monitors/IdleMonitor.swift` | `IOHIDSystem` idle time detection |
| `Monitors/MonitorCoordinator.swift` | Combines all monitors into unified data stream |

### Networking

| File | Purpose |
|------|---------|
| `Networking/BackendClient.swift` | HTTP client to Python backend (localhost:8420) |
| `Networking/Models.swift` | Codable structs matching API request/response models |

### UI Components

| File | Purpose |
|------|---------|
| `UI/MenuBarView.swift` | Status bar menu (focus score, quick actions) |
| `UI/InterventionPopup.swift` | Non-intrusive notification card |
| `UI/DashboardWindow.swift` | Detailed stats window (optional) |
| `UI/OnboardingView.swift` | Permission setup wizard |
| `UI/FocusSessionView.swift` | Pomodoro-style focus mode |

### Utilities

| File | Purpose |
|------|---------|
| `Utilities/Permissions.swift` | TCC permission checks (Screen Recording, Accessibility) |
| `Utilities/Logger.swift` | Structured logging |

### App Entry

| File | Purpose |
|------|---------|
| `App.swift` | `@main` entry, `NSApplication` setup |
| `AppDelegate.swift` | Menu bar, status item, permissions |

---

## Implementation Details

### 1. Screen Monitor (`ScreenMonitor.swift`)

Two-pronged capture strategy:

**Event-driven** (app switches):
- `NSWorkspace.didActivateApplicationNotification` — fires on every app switch
- Zero CPU cost when no switches occur
- Captures `NSRunningApplication` info

**Polling** (window titles, every 2 seconds):
- Window titles change without app switches (e.g., switching browser tabs)
- Uses `CGWindowListCopyWindowInfo` to get frontmost window
- **Requires**: Screen Recording permission

```
Capture Flow:
Timer (2s) → CGWindowList → Extract title + owner
           → Check if owner is a browser → AppleScript URL extraction
           → Send to BackendClient.reportActivity()
```

### 2. Browser URL Monitor (`BrowserMonitor.swift`)

Uses AppleScript to extract the active tab URL from supported browsers:

| Browser | Method | Notes |
|---------|--------|-------|
| Google Chrome | `URL of active tab of front window` | Chrome-based API |
| Brave Browser | Same as Chrome | Chrome-based |
| Microsoft Edge | Same as Chrome | Chrome-based |
| Safari | `URL of front document` | Different API |
| Arc | `URL of active tab of front window` | Chrome-based |
| Firefox | ⚠️ Not supported | Use AXUIElement fallback |

**Requires**: Automation permission (granted per-browser on first AppleScript run)

### 3. Idle Monitor (`IdleMonitor.swift`)

- Uses `IOKit` / `IOHIDSystem` to get seconds since last keyboard/mouse input
- No special permissions required
- Returns `TimeInterval` in seconds (converted from nanoseconds)
- Threshold: >60s idle → flag as idle in activity reports

### 4. Intervention Popup UI

**ADHD UX Requirements**:

| Principle | Implementation |
|-----------|---------------|
| Short text | Max 2–3 sentences (working memory deficits) |
| Limited choices | 2–3 action buttons (decision fatigue) |
| Non-modal | `NSPanel` with `.nonactivatingPanel` — doesn't steal focus |
| Non-blocking | Slides in from top-right corner |
| Auto-dismiss | Disappears after 15 seconds |
| Cooldown | "Not now" triggers 5-minute cooldown |
| Validate first | Acknowledgment text before suggestion |
| Upward framing | What WILL help, not what went WRONG |

**Card Structure**:
```
┌──────────────────────────────────────┐
│ Looks like things are scattered      │  ← Acknowledgment
│ right now — that's okay.             │
│                                      │
│ A 2-minute reset could help you      │  ← Suggestion
│ refocus. What feels right?           │
│                                      │
│ 🫁 Breathing  🎯 Pick task  ☕ Break │  ← Actions
│                                      │
│                          Not now     │  ← Dismiss
└──────────────────────────────────────┘
```

### 5. macOS Permissions (3 Required)

| Permission | Why Needed | Check Method | Request Method |
|------------|-----------|--------------|----------------|
| **Screen Recording** | `CGWindowListCopyWindowInfo` returns window titles | `CGPreflightScreenCaptureAccess()` | `CGRequestScreenCaptureAccess()` |
| **Accessibility** | `AXUIElement` window observation | `AXIsProcessTrusted()` | `AXIsProcessTrustedWithOptions()` |
| **Automation** | AppleScript browser URL extraction | No pre-check | Granted on first AppleScript run |

> ⚠️ **macOS Sequoia (15+)** re-prompts for Accessibility/Screen Recording monthly. Build clear re-authorization UX.

---

## Networking

### Backend Communication (`BackendClient.swift`)

```
POST http://localhost:8420/screen/activity
Content-Type: application/json

{
    "app_name": "Google Chrome",
    "window_title": "youtube.com - Funny Cats",
    "url": "https://youtube.com/watch?v=abc",
    "is_idle": false,
    "timestamp": "2026-03-08T12:00:00Z"
}

Response (< 100ms):
{
    "category": "entertainment",
    "metrics": { "focus_score": 45.2, "context_switch_rate_5min": 8 },
    "intervention": null  // or Intervention object
}
```

### Error Handling
- Backend unreachable → buffer activities in SQLite, retry on reconnection
- Timeout after 5s → skip this report, continue monitoring
- Log all communication failures for debugging

---

## Info.plist Key Entries

```xml
<key>LSUIElement</key>
<true/>  <!-- No dock icon, menu bar only -->

<key>NSScreenCaptureUsageDescription</key>
<string>ADHD Second Brain needs screen access to monitor your focus patterns.</string>

<key>NSAppleEventsUsageDescription</key>
<string>ADHD Second Brain needs automation access to read browser URLs.</string>
```

---

## Distribution Note

> ⚠️ The app **must be distributed outside the Mac App Store** because Screen Recording permission requires the `com.apple.security.temporary-exception.apple-events` entitlement which is blocked in sandbox.

---

## Verification Checklist

- [ ] App builds and runs as menu bar-only (no dock icon)
- [ ] Screen Recording permission granted and working
- [ ] `CGWindowListCopyWindowInfo` returns window titles
- [ ] Browser URL extraction works for Safari and Chrome
- [ ] Idle detection reports correct idle seconds
- [ ] Activity reports sent to backend every 2 seconds
- [ ] Intervention popups appear without stealing focus
- [ ] Popups auto-dismiss after 15 seconds
- [ ] "Not now" triggers cooldown
- [ ] Onboarding wizard guides through all 3 permissions

---

## Next Phase

→ [Phase 3: SenticNet Pipeline](PHASE_3_SENTICNET_PIPELINE.md) (backend work, can be parallel)
