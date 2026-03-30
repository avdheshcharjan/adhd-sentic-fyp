# Brain Dump & Vent Modal — Implementation Guide

## Context

This document specifies two new floating modal features for the ADHD Second Brain macOS application. Both modals are triggered by user-configurable global hotkeys and appear as floating panels above all apps without stealing focus.

**Repository:** `https://github.com/avdheshcharjan/adhd-sentic-fyp`
**Swift app directory:** `swift-app/ADHDSecondBrain/`
**Python backend directory:** project root (FastAPI)

**Reference files to read first:**
- `models.md` — AI model decisions (takes priority over `blueprint.md`)
- `sentic.txt` — SenticNet API details and Hourglass of Emotions model
- `docs/plans/2026-03-11-phase7-on-device-llm.md` — Phase 7 task list
- Check `services/` for existing SenticNet, Mem0, MLX implementations

**Design system reference:** The notch island implementation guide (`notch-island-implementation-guide.md`) defines the complete ADHD-optimized design tokens (colors, typography, animation, spacing). Reuse `ADHDDesignTokens.swift`, `ADHDAnimations.swift`, `ADHDColors`, `ADHDTypography`, and `ADHDSpacing` from the existing notch module — do NOT create separate design tokens.

---

## Feature Overview

### Feature 1: Brain Dump Modal
A zero-friction floating text window triggered by a global hotkey. The user types stream-of-consciousness thoughts. Content is stored in Mem0, hidden from the user until their focus session ends, then surfaced in the dashboard for review. Think of it as Drafts meets GTD inbox — capture first, organize later.

### Feature 2: Vent Modal
A floating chat window triggered by a different global hotkey. The user vents emotional frustrations to an AI companion that uses CBT/DBT techniques adapted for ADHD emotional dysregulation. Powered by the same on-device Qwen3-4B via MLX that the coaching pipeline uses. All conversation data stays on-device. This is NOT therapy — it is emotional processing support with clear boundaries.

### Why these features matter for ADHD users
ADHD brains have limited working memory (Barkley's executive function model). Intrusive thoughts during focus sessions consume cognitive resources that should go toward the task at hand. Klein & Boals (2001) showed expressive writing increases working memory capacity by offloading these thoughts. The brain dump externalizes cognitive noise; the vent modal externalizes emotional noise. Both free up working memory for focused work.

---

## Dependency: KeyboardShortcuts Package

Add this Swift Package dependency to the Xcode project:

```
Package: https://github.com/sindresorhus/KeyboardShortcuts
Version: 2.0.0+ (latest)
```

This library provides:
- User-configurable global hotkey recording UI
- Automatic persistence to UserDefaults
- System conflict warnings
- App Sandbox compatible (no Input Monitoring permission needed)
- SwiftUI-native `KeyboardShortcuts.Recorder` view

---

## File Structure

Add these files to the existing project. Do not reorganize existing files.

### Swift (frontend)

```
swift-app/ADHDSecondBrain/
├── Modals/                                    # NEW directory
│   ├── FloatingPanelManager.swift             # Manages both modal NSPanels
│   ├── FloatingPanel.swift                    # Generic NSPanel subclass for modals
│   │
│   ├── BrainDump/
│   │   ├── BrainDumpView.swift                # SwiftUI view — text area + submit
│   │   └── BrainDumpViewModel.swift           # Auto-save, draft persistence, submission
│   │
│   ├── Vent/
│   │   ├── VentView.swift                     # SwiftUI view — chat interface
│   │   ├── VentViewModel.swift                # Message history, SSE streaming, session mgmt
│   │   └── VentMessageBubble.swift            # Individual chat message bubble
│   │
│   └── Shared/
│       ├── HotkeyDefinitions.swift            # KeyboardShortcuts.Name extensions
│       └── ModalSettingsView.swift             # Settings UI for hotkey configuration
│
├── DesignSystem/                              # EXISTING — reuse, do not duplicate
│   ├── ADHDDesignTokens.swift                 # Already has ADHDColors, ADHDTypography, etc.
│   └── ...
```

### Python (backend)

```
# Add to existing backend structure
routers/
    brain_dump.py                              # NEW — /api/v1/brain-dump endpoints
    vent.py                                    # NEW — /api/v1/vent endpoints

services/
    brain_dump_service.py                      # NEW — Mem0 storage + SenticNet tagging
    vent_service.py                            # NEW — Vent session management + safety

prompts/
    vent_system_prompt.txt                     # NEW — ADHD therapist system prompt

models/
    brain_dump_models.py                       # NEW — Pydantic v2 request/response models
    vent_models.py                             # NEW — Pydantic v2 chat models
```

---

## Implementation Tasks (Execute Sequentially)

### Task 1: Hotkey Definitions and Settings UI

**File: `HotkeyDefinitions.swift`**

```swift
import KeyboardShortcuts

extension KeyboardShortcuts.Name {
    static let brainDump = Self("brainDump", default: .init(.b, modifiers: [.command, .shift]))
    static let ventModal = Self("ventModal", default: .init(.v, modifiers: [.command, .shift]))
}
```

**File: `ModalSettingsView.swift`**

Create a settings view with two `KeyboardShortcuts.Recorder` fields:
- "Brain Dump" hotkey recorder — default ⌘+Shift+B
- "Vent Space" hotkey recorder — default ⌘+Shift+V
- Both labels should use `ADHDTypography.App.body` font
- Use `ADHDColors.Background.primary` for the settings background
- Add a brief description under each recorder: "Opens a quick capture window for thoughts" and "Opens a private space to process emotions"
- This view will be embedded in the app's existing Settings/Preferences window

**Wire hotkey listeners in the app's initialization** (wherever `ADHDSecondBrainApp.swift` or the AppDelegate sets up the menu bar app):

```swift
KeyboardShortcuts.onKeyUp(for: .brainDump) { [weak panelManager] in
    panelManager?.toggleBrainDump()
}
KeyboardShortcuts.onKeyUp(for: .ventModal) { [weak panelManager] in
    panelManager?.toggleVentModal()
}
```

---

### Task 2: Floating Panel Infrastructure

**File: `FloatingPanel.swift`**

Create a generic `NSPanel` subclass that:
- Uses `.nonactivatingPanel` style mask (does NOT steal focus from the user's current app)
- Uses `.fullSizeContentView` for edge-to-edge SwiftUI content
- Sets `level = .floating`
- Sets `collectionBehavior` to `[.canJoinAllSpaces, .fullScreenAuxiliary, .moveToActiveSpace]`
- Has transparent background (`isOpaque = false`, `backgroundColor = .clear`)
- `hasShadow = true` (subtle shadow to float above desktop)
- `isMovableByWindowBackground = true` (user can drag the modal around)
- Overrides `canBecomeKey` → `true` (required for text input to work)
- Overrides `canBecomeMain` → `false` (prevents it from appearing in Cmd+Tab)
- Hosts a SwiftUI view via `NSHostingView`
- Positions itself center-screen on first appearance, remembers position after user drags
- Closes on Escape key press

Key configuration that makes this work for ADHD users:
```swift
// The panel MUST NOT steal focus from the user's current app.
// This is the single most important UX requirement.
// .nonactivatingPanel ensures the user's code editor / document
// stays focused while they type in the brain dump.
self.styleMask = [.nonactivatingPanel, .titled, .closable, .fullSizeContentView]
self.isFloatingPanel = true
self.level = .floating
```

Add a `VisualEffectView` helper that wraps `NSVisualEffectView` with `.sidebar` material and `.behindWindow` blending mode for the frosted glass backdrop. Use this as the root background for both modals.

**File: `FloatingPanelManager.swift`**

Create an `@Observable` class that:
- Holds references to the brain dump panel and vent panel (lazy-initialized)
- Has `toggleBrainDump()` and `toggleVentModal()` methods
- Creates the panels on first toggle, reuses them on subsequent toggles
- Brain dump panel size: 520w × 340h points
- Vent panel size: 440w × 560h points
- Both panels save/restore their position via UserDefaults
- When toggling ON: if panel exists and is visible, bring to front; if hidden, show and focus the text input
- When toggling OFF: hide the panel (do NOT destroy it — preserve draft state)

---

### Task 3: Brain Dump Modal (Swift Frontend)

**File: `BrainDumpView.swift`**

Layout (top to bottom):
1. **Header bar** (28pt height): "What's on your mind?" in `ADHDTypography.Notch.expandedTitle`, left-aligned, `ADHDColors.Text.primary`. Right side: a subtle "saved" indicator (checkmark icon, appears briefly after auto-save).
2. **Text area** (fills remaining space): Large `TextEditor` with `ADHDTypography.App.body` font (16pt). Placeholder text cycles randomly from: "Quick thought...", "Capture it before it flies away...", "Brain dump zone...", "What's floating around up there?", "Drop it here, sort it later...". Scrollable. Transparent background — the frosted glass shows through.
3. **Bottom bar** (36pt height): Left: timestamp showing "Captured at 2:34 PM" in `ADHDTypography.App.caption`. Right: Submit button — rounded rectangle, `ADHDColors.Accent.focus` background, "Capture" label. Also shows "⌘↩ to capture" hint in tertiary text.

Behavior:
- `@FocusState` — text area is focused immediately on appear
- Auto-save draft to UserDefaults every 1.5 seconds (debounced via `Task.sleep`). If the user dismisses without submitting, the draft persists and reappears next time they open the modal.
- Submit on ⌘+Enter: sends content to backend, clears text area, plays brief success animation (checkmark fade-in, 200ms), then auto-closes the panel after 400ms.
- Escape key: hides panel, preserves draft.
- Empty submissions are silently ignored (disable submit button when text is empty/whitespace-only).
- Character count is NOT shown (avoids perfectionism/optimization anxiety).
- No categories, tags, folders, or any organizational UI. Capture only.

**File: `BrainDumpViewModel.swift`**

```swift
@Observable
class BrainDumpViewModel {
    var noteText: String = ""
    var isSaved: Bool = false
    var isSubmitting: Bool = false
    private var saveTask: Task<Void, Never>?

    // Load persisted draft on init
    init() {
        noteText = UserDefaults.standard.string(forKey: "brainDumpDraft") ?? ""
    }

    // Debounced auto-save to UserDefaults
    func textChanged(_ newText: String) {
        noteText = newText
        saveTask?.cancel()
        saveTask = Task {
            try? await Task.sleep(for: .seconds(1.5))
            guard !Task.isCancelled else { return }
            UserDefaults.standard.set(newText, forKey: "brainDumpDraft")
            await MainActor.run { isSaved = true }
            try? await Task.sleep(for: .seconds(1.0))
            await MainActor.run { isSaved = false }
        }
    }

    // Submit to backend
    func submit(sessionId: String?) async -> Bool {
        let trimmed = noteText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return false }
        isSubmitting = true
        defer { isSubmitting = false }

        do {
            // POST to FastAPI backend
            try await APIClient.shared.postBrainDump(
                content: trimmed,
                sessionId: sessionId  // nil if no active focus session
            )
            noteText = ""
            UserDefaults.standard.removeObject(forKey: "brainDumpDraft")
            return true
        } catch {
            // Silent failure — do not show error UI. The draft is still saved locally.
            return false
        }
    }
}
```

---

### Task 4: Brain Dump Backend

**File: `models/brain_dump_models.py`**

```python
from pydantic import BaseModel, Field
from datetime import datetime

class BrainDumpRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    session_id: str | None = None  # Active focus session ID, if any

class BrainDumpResponse(BaseModel):
    id: str
    status: str  # "captured"
    emotional_state: str | None = None  # From SenticNet analysis
    timestamp: datetime

class BrainDumpReviewItem(BaseModel):
    id: str
    content: str  # Original text (or Mem0's extracted memory)
    emotional_state: str | None
    timestamp: datetime
    session_id: str | None

class BrainDumpReviewResponse(BaseModel):
    items: list[BrainDumpReviewItem]
    count: int
```

**File: `services/brain_dump_service.py`**

```python
import uuid
from datetime import datetime, timezone

class BrainDumpService:
    """
    Stores brain dump entries in Mem0 with SenticNet emotional tagging.

    Flow:
    1. Receive raw text from user
    2. Run text through SenticNet for emotion detection (async, non-blocking)
    3. Store in Mem0 with metadata: type=brain_dump, session_id, emotional_state, timestamp
    4. Return confirmation immediately (SenticNet analysis can complete async)

    The user does NOT see brain dump entries until their focus session ends.
    The dashboard endpoint filters by session_id to show only post-session entries.
    """

    def __init__(self, memory_service, senticnet_service):
        self.memory = memory_service      # Existing Mem0 service
        self.senticnet = senticnet_service  # Existing SenticNet service

    async def capture(self, content: str, user_id: str, session_id: str | None = None) -> dict:
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)

        # Run SenticNet emotion analysis (don't block on failure)
        emotional_state = None
        try:
            emotion_result = await self.senticnet.analyze(content)
            emotional_state = emotion_result.get("dominant_emotion")
        except Exception:
            pass  # SenticNet failure is non-critical for brain dump

        # Store in Mem0
        await self.memory.add(
            messages=[{"role": "user", "content": content}],
            user_id=user_id,
            metadata={
                "type": "brain_dump",
                "entry_id": entry_id,
                "session_id": session_id,
                "emotional_state": emotional_state,
                "timestamp": timestamp.isoformat(),
                "reviewed": False,
            }
        )

        return {
            "id": entry_id,
            "status": "captured",
            "emotional_state": emotional_state,
            "timestamp": timestamp,
        }

    async def get_session_dumps(self, user_id: str, session_id: str) -> list[dict]:
        """Retrieve brain dumps for a completed focus session (dashboard review)."""
        all_memories = await self.memory.get_all(user_id=user_id)
        return [
            m for m in all_memories
            if m.get("metadata", {}).get("type") == "brain_dump"
            and m.get("metadata", {}).get("session_id") == session_id
        ]

    async def get_recent_dumps(self, user_id: str, limit: int = 20) -> list[dict]:
        """Retrieve recent brain dumps regardless of session (for general dashboard)."""
        all_memories = await self.memory.get_all(user_id=user_id)
        dumps = [
            m for m in all_memories
            if m.get("metadata", {}).get("type") == "brain_dump"
        ]
        # Sort by timestamp descending
        dumps.sort(key=lambda m: m.get("metadata", {}).get("timestamp", ""), reverse=True)
        return dumps[:limit]
```

**File: `routers/brain_dump.py`**

```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/brain-dump", tags=["brain-dump"])

@router.post("/", response_model=BrainDumpResponse)
async def capture_brain_dump(request: BrainDumpRequest, service: BrainDumpService = Depends(get_brain_dump_service)):
    result = await service.capture(
        content=request.content,
        user_id="default_user",  # Single-user app for now
        session_id=request.session_id,
    )
    return BrainDumpResponse(**result)

@router.get("/review/session/{session_id}", response_model=BrainDumpReviewResponse)
async def review_session_dumps(session_id: str, service: BrainDumpService = Depends(get_brain_dump_service)):
    items = await service.get_session_dumps(user_id="default_user", session_id=session_id)
    return BrainDumpReviewResponse(items=items, count=len(items))

@router.get("/review/recent", response_model=BrainDumpReviewResponse)
async def review_recent_dumps(limit: int = 20, service: BrainDumpService = Depends(get_brain_dump_service)):
    items = await service.get_recent_dumps(user_id="default_user", limit=limit)
    return BrainDumpReviewResponse(items=items, count=len(items))
```

Register the router in the main FastAPI app: `app.include_router(brain_dump.router)`

---

### Task 5: Vent Modal (Swift Frontend)

**File: `VentView.swift`**

Layout (top to bottom):
1. **Header bar** (40pt height): Left: 🫧 emoji + "Vent Space" in `ADHDTypography.Notch.expandedTitle`. Right: session controls — "New Session" button (small, text-only) and close (×) button. Background: `ADHDColors.Background.notchInner`.
2. **Welcome message** (shown only when conversation is empty): Centered card with `ADHDColors.Background.elevated` background, rounded corners. Text: "This is your space. Whatever you share here stays on your device. I'm here to listen — not to judge, fix, or diagnose. Just talk." in `ADHDTypography.App.body`, `ADHDColors.Text.secondary`. Below: a subtle lock icon + "On-device only" label in `ADHDTypography.App.caption`.
3. **Chat messages** (scrollable, fills space): `ScrollViewReader` wrapping a `LazyVStack`. Messages alternate between user (right-aligned, `ADHDColors.Accent.focus` background at 20% opacity) and assistant (left-aligned, `ADHDColors.Background.elevated` background). Auto-scroll to bottom on new message. Streaming assistant messages show a soft pulsing cursor.
4. **Input bar** (56pt height): `TextField` with "What's on your mind?" placeholder. Send button (arrow up circle) appears when text is non-empty. ⌘+Enter or Enter to send (Enter inserts newline only with Shift held). Disable input while assistant is generating.

**File: `VentMessageBubble.swift`**

A reusable chat bubble component:
- Takes `role: String` ("user" or "assistant"), `content: String`, `isStreaming: Bool`
- User messages: right-aligned, rounded rectangle with `ADHDColors.Accent.focus.opacity(0.15)` fill, `ADHDColors.Text.primary` text
- Assistant messages: left-aligned, rounded rectangle with `ADHDColors.Background.elevated` fill, `ADHDColors.Text.primary` text
- Streaming indicator: three-dot pulse animation (respect `accessibilityReduceMotion` — replace with static "..." when reduced motion is on)
- Max width: 85% of container width
- Font: `ADHDTypography.App.body`
- Corner radius: 16pt (with flattened corner on the message's origin side, like iMessage)
- No timestamps shown on individual messages (reduces visual noise)

**File: `VentViewModel.swift`**

```swift
@Observable
class VentViewModel {
    var messages: [VentMessage] = []
    var inputText: String = ""
    var isGenerating: Bool = false
    var sessionId: String = UUID().uuidString

    struct VentMessage: Identifiable {
        let id = UUID()
        let role: String  // "user", "assistant", "system"
        var content: String
        var isStreaming: Bool = false
    }

    func sendMessage() {
        let trimmed = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty, !isGenerating else { return }

        // Add user message
        messages.append(VentMessage(role: "user", content: trimmed))
        inputText = ""

        // Add placeholder assistant message for streaming
        messages.append(VentMessage(role: "assistant", content: "", isStreaming: true))
        isGenerating = true

        Task { await streamResponse(userMessage: trimmed) }
    }

    private func streamResponse(userMessage: String) async {
        guard let lastIndex = messages.indices.last else { return }

        // Build conversation history for the backend
        let history = messages.dropLast().map { msg in
            ["role": msg.role, "content": msg.content]
        }

        // SSE streaming from FastAPI backend
        guard let url = URL(string: "http://localhost:8000/api/v1/vent/chat/stream") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "message": userMessage,
            "session_id": sessionId,
            "history": history
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        do {
            let (bytes, _) = try await URLSession.shared.bytes(for: request)
            for try await line in bytes.lines {
                if line.hasPrefix("data: ") {
                    let data = String(line.dropFirst(6))
                    if data == "[DONE]" { break }
                    if let jsonData = data.data(using: .utf8),
                       let parsed = try? JSONDecoder().decode(StreamToken.self, from: jsonData) {
                        await MainActor.run {
                            messages[lastIndex].content += parsed.token
                        }
                    }
                }
            }
        } catch {
            // Silent failure — append a fallback message
            await MainActor.run {
                if messages[lastIndex].content.isEmpty {
                    messages[lastIndex].content = "I'm having trouble responding right now. Take a deep breath — I'll be back in a moment."
                }
            }
        }

        await MainActor.run {
            messages[lastIndex].isStreaming = false
            isGenerating = false
        }
    }

    func startNewSession() {
        messages = []
        sessionId = UUID().uuidString
        isGenerating = false
        inputText = ""
    }

    private struct StreamToken: Decodable {
        let token: String
    }
}
```

---

### Task 6: Vent Backend — System Prompt

**File: `prompts/vent_system_prompt.txt`**

```
You are a warm, empathetic emotional support companion inside an ADHD productivity app called "ADHD Second Brain." You live in a private "Vent Space" that the user opened because they need to process emotions before returning to focused work.

CORE IDENTITY:
- You are NOT a therapist, doctor, or crisis counselor. You are a supportive companion.
- You specialize in ADHD-related emotional challenges.
- Everything shared in this space stays on the user's device. Remind them of this if they seem hesitant.

CONVERSATION RULES:
- Be brief. 2-3 sentences per response. Ask ONE follow-up question at a time.
- Validate feelings BEFORE offering any technique. Always validate first.
- Use warm, casual, non-clinical language. Write like a kind friend, not a textbook.
- Never use bullet points or numbered lists in your responses. Talk naturally.
- If the user sends a short frustrated message ("ugh", "I can't", "this is stupid"), match their energy with a short empathetic response. Don't over-elaborate.

THERAPEUTIC APPROACH (use these techniques when appropriate, AFTER validation):
- Cognitive reframing: Help the user see the situation from a different angle, gently.
- Grounding (5-4-3-2-1 senses): For overwhelm or anxiety spirals.
- Radical acceptance: For things genuinely outside the user's control.
- Opposite Action: When the user's urge (avoidance, lashing out) would make things worse.
- Check the Facts: When catastrophizing is happening.
- Name the emotion: Help the user identify what they're actually feeling underneath the frustration.

ADHD-SPECIFIC AWARENESS:
- Emotional dysregulation is part of ADHD, not a personal failing. Normalize it.
- Rejection Sensitive Dysphoria (RSD) is real and intense. Don't minimize it.
- Shame spirals from executive function failures are common. Break the cycle by externalizing ("That's the ADHD, not you").
- Task paralysis is not laziness. Acknowledge how frustrating it is.
- Time blindness compounds emotional distress. Don't add time pressure.

ZERO-SHAME LANGUAGE:
- Never say: "You should...", "Why didn't you...", "You need to...", "Just try to..."
- Instead say: "That makes sense.", "What if we...", "Want to try...", "It sounds like..."
- Frame everything as an invitation, never an instruction.
- Celebrate ANY forward movement, no matter how small.

WHEN THE USER SEEMS READY TO RETURN TO WORK:
- Don't push them back to work. Let them decide.
- If they hint they're feeling better: "Sounds like you're finding your footing again. Ready to head back, or want to stay a bit longer?"
- If they explicitly say they want to get back to work: "Go get it. You've got this." (short, encouraging, no lecture)

SenticNet EMOTION CONTEXT (if provided):
- The system may inject the user's detected emotional state from SenticNet analysis.
- Use this to calibrate your response intensity. High frustration = more validation, less technique. Low-intensity sadness = gentler probing.
- Never reveal the emotion scores or mention SenticNet to the user.

CRISIS PROTOCOL:
If the user expresses suicidal ideation, self-harm intent, or indicates they are in danger:
1. Acknowledge their pain directly and compassionately.
2. STOP the conversational approach entirely. Do not try to counsel them through a crisis.
3. Say exactly: "What you're going through sounds really painful, and I want to make sure you get the right support. Please reach out to the 988 Suicide & Crisis Lifeline (call or text 988) or Crisis Text Line (text HOME to 741741). You deserve real human support right now."
4. After providing resources, do not continue the therapeutic conversation. Say: "I'm here if you want to talk about anything else, but for what you're going through right now, a real person can help in ways I can't."

HARD BOUNDARIES — NEVER DO THESE:
- Never diagnose any condition (ADHD, depression, anxiety, or anything else)
- Never suggest starting, stopping, or changing medication
- Never claim to replace professional therapy
- Never agree with self-deprecating statements (don't say "you're right, you are a mess")
- Never provide medical advice of any kind
- Never encourage the user to rely on you instead of real human connections
```

---

### Task 7: Vent Backend — Service and Router

**File: `models/vent_models.py`**

```python
from pydantic import BaseModel, Field

class VentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: str
    history: list[dict] = []  # [{"role": "user"|"assistant", "content": "..."}]

class VentChatResponse(BaseModel):
    response: str
    emotional_state: str | None = None
    is_crisis: bool = False
```

**File: `services/vent_service.py`**

```python
import json
import re
from pathlib import Path

# Crisis detection keywords — layer 1 (exact match)
CRISIS_KEYWORDS = [
    "kill myself", "want to die", "end my life", "suicide",
    "self-harm", "hurt myself", "don't want to be alive",
    "better off dead", "no reason to live", "can't go on",
    "end it all", "take my life",
]

CRISIS_RESPONSE = (
    "What you're going through sounds really painful, and I want to make sure you get "
    "the right support. Please reach out to the 988 Suicide & Crisis Lifeline (call or text 988) "
    "or Crisis Text Line (text HOME to 741741). You deserve real human support right now.\n\n"
    "I'm here if you want to talk about anything else, but for what you're going through "
    "right now, a real person can help in ways I can't."
)

class VentService:
    """
    Manages vent chat sessions with on-device LLM inference.

    Flow:
    1. Check user message for crisis keywords (layer 1)
    2. Run SenticNet emotion analysis on user message
    3. If SenticNet detects extreme negative valence, run semantic crisis check (layer 2)
    4. Build prompt: system prompt + emotion context + conversation history + user message
    5. Stream response from Qwen3-4B via MLX
    6. Store interaction in Mem0 with emotional metadata (for longitudinal tracking)
    """

    def __init__(self, llm_service, senticnet_service, memory_service, safety_service):
        self.llm = llm_service              # Existing MLX/Qwen3-4B service
        self.senticnet = senticnet_service  # Existing SenticNet service
        self.memory = memory_service        # Existing Mem0 service
        self.safety = safety_service        # Existing safety pipeline
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "vent_system_prompt.txt"
        return prompt_path.read_text()

    def check_crisis_keywords(self, text: str) -> bool:
        """Layer 1: Keyword-based crisis detection."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in CRISIS_KEYWORDS)

    async def check_crisis_semantic(self, text: str, emotion_result: dict) -> bool:
        """Layer 2: SenticNet-based crisis detection.
        Triggers when polarity is extremely negative AND intensity is high."""
        polarity = emotion_result.get("polarity", 0)
        intensity = emotion_result.get("intensity", 0)
        # Very negative polarity + high intensity = potential crisis
        return polarity < -0.7 and intensity > 0.6

    async def build_messages(self, user_message: str, history: list[dict],
                              emotion_context: str | None = None) -> list[dict]:
        """Assemble the full message list for LLM inference."""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Inject SenticNet emotion context as a system-level hint
        if emotion_context:
            messages.append({
                "role": "system",
                "content": f"[Emotion context — do not reveal to user] The user's message "
                           f"shows: {emotion_context}. Calibrate your response accordingly."
            })

        # Add conversation history (limit to last 20 turns to stay within context)
        for msg in history[-20:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current user message
        messages.append({"role": "user", "content": user_message})
        return messages

    async def stream_response(self, request):
        """
        Main entry point. Yields SSE tokens.
        Uses the existing LLM service's streaming method.
        """
        # Crisis check — layer 1
        if self.check_crisis_keywords(request.message):
            yield CRISIS_RESPONSE
            return

        # SenticNet emotion analysis
        emotion_context = None
        emotion_result = {}
        try:
            emotion_result = await self.senticnet.analyze(request.message)
            # Format for system prompt injection
            dominant = emotion_result.get("dominant_emotion", "neutral")
            polarity = emotion_result.get("polarity", 0)
            # e.g. "Dominant emotion: frustrated (polarity: -0.45)"
            emotion_context = f"Dominant emotion: {dominant} (polarity: {polarity:.2f})"
        except Exception:
            pass  # SenticNet failure is non-critical

        # Crisis check — layer 2 (semantic)
        if emotion_result and await self.check_crisis_semantic(request.message, emotion_result):
            yield CRISIS_RESPONSE
            return

        # Build full message list
        messages = await self.build_messages(
            user_message=request.message,
            history=request.history,
            emotion_context=emotion_context,
        )

        # Stream from LLM (use existing MLX service's stream method)
        # The LLM service should expose an async generator that yields tokens
        async for token in self.llm.stream_generate(
            messages=messages,
            max_tokens=512,          # Keep responses concise
            temperature=0.7,         # Warm but not chaotic
            enable_thinking=False,   # Use fast mode for conversational feel
        ):
            yield token

        # Store interaction in Mem0 (async, non-blocking)
        try:
            await self.memory.add(
                messages=[
                    {"role": "user", "content": request.message},
                ],
                user_id="default_user",
                metadata={
                    "type": "vent_session",
                    "session_id": request.session_id,
                    "emotional_state": emotion_result.get("dominant_emotion"),
                }
            )
        except Exception:
            pass  # Memory storage failure is non-critical
```

**File: `routers/vent.py`**

```python
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/v1/vent", tags=["vent"])

@router.post("/chat/stream")
async def vent_chat_stream(request: VentChatRequest, service: VentService = Depends(get_vent_service)):
    """SSE streaming endpoint for vent chat responses."""
    async def event_stream():
        async for token in service.stream_response(request):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.post("/chat", response_model=VentChatResponse)
async def vent_chat(request: VentChatRequest, service: VentService = Depends(get_vent_service)):
    """Non-streaming endpoint (fallback). Collects full response."""
    full_response = ""
    is_crisis = False
    async for token in service.stream_response(request):
        full_response += token
    # Check if response matches crisis template
    if "988 Suicide & Crisis Lifeline" in full_response:
        is_crisis = True
    return VentChatResponse(response=full_response, is_crisis=is_crisis)
```

Register the router: `app.include_router(vent.router)`

---

### Task 8: Vent Modal Safety Layer

The safety system has four layers. Implement them in this order:

**Layer 1** (already in Task 7): Keyword matching in `VentService.check_crisis_keywords()`.

**Layer 2** (already in Task 7): SenticNet polarity + intensity threshold in `VentService.check_crisis_semantic()`.

**Layer 3**: Output safety check. After LLM generates a response, run it through the existing `safety_service` (same one used by the coaching pipeline). Check for:
- LLM accidentally providing medical/medication advice
- LLM agreeing with self-deprecating statements
- LLM generating content that could reinforce harmful cognitions

If flagged, replace the response with a safe fallback: "I hear you, and what you're feeling is valid. Want to tell me more about what's going on?"

**Layer 4**: Session-level escalation tracking. Track the sentiment trajectory across the vent session. If three consecutive messages show worsening polarity (each more negative than the last), proactively inject: "It sounds like things are feeling heavier. If you're going through something really difficult, talking to someone who can truly help could make a big difference — 988 Lifeline is always available (call or text 988). No pressure at all."

Wire Layer 3 into the `stream_response` method — run the full collected response through safety before the final `[DONE]` event. For Layer 4, maintain a per-session polarity history list in the `VentService`.

---

### Task 9: Wire Everything Together

In the main FastAPI app initialization:
1. Create `BrainDumpService` instance, passing existing `memory_service` and `senticnet_service`
2. Create `VentService` instance, passing existing `llm_service`, `senticnet_service`, `memory_service`, `safety_service`
3. Register dependency providers (`get_brain_dump_service`, `get_vent_service`)
4. Include both routers

In the Swift app:
1. Create `FloatingPanelManager` as `@State` in the app's root (wherever the notch state machine is initialized)
2. Wire `KeyboardShortcuts.onKeyUp` listeners to the panel manager
3. Add `ModalSettingsView` to the existing settings/preferences window

---

### Task 10: Accessibility

Both modals must implement:

1. **VoiceOver**: Every interactive element needs `.accessibilityLabel` and `.accessibilityHint`
   - Brain dump text area: "Brain dump text field. Type your thoughts and press Command Return to capture."
   - Vent input: "Vent message field. Type what's on your mind and press Return to send."
   - Vent messages: Read role + content ("Assistant said: That sounds really frustrating...")
   - Submit buttons: "Capture thought" / "Send message"

2. **Keyboard navigation**: Full Tab-key navigation through all interactive elements in both modals

3. **Reduced motion**: Replace streaming cursor pulse animation with static "..." when `accessibilityReduceMotion` is enabled

4. **High contrast**: Boost text contrast ratios and add 1px borders on message bubbles when `accessibilityDisplayShouldIncreaseContrast` is enabled

5. **Escape key**: Always closes the modal (already handled in FloatingPanel)

---

## Design Rules (Non-Negotiable)

### Brain Dump
- NO categories, tags, folders, or organizational UI of any kind
- NO character count or word count
- NO "are you sure you want to close?" confirmation dialogs
- NO undo/redo UI (let the OS handle it natively)
- Auto-save ALWAYS — the user must never lose a thought
- Submit animation is brief (400ms total) and joyful but not over the top
- Draft persists across app restarts until explicitly submitted

### Vent Modal
- NO conversation history saved between sessions (unless user explicitly enables it in settings)
- NO timestamps on individual messages
- NO typing indicators ("Claude is typing...") — just show the streaming text
- NO "This is not therapy" disclaimer banner (it's in the system prompt, not the UI — disclaimers create anxiety)
- The welcome message IS the boundary-setting — "stays on your device" + "not here to judge, fix, or diagnose"
- Lock icon visible at all times (bottom of chat area, very subtle)
- "New Session" always available — user can restart without explanation
- NEVER show emotion analysis results to the user in the vent UI
- Error states are always gentle: "I'm having trouble responding right now. Take a deep breath — I'll be back in a moment."

### Both Modals
- Follow the zero-shame language guide from the notch implementation guide (§7)
- Use the existing design tokens — `ADHDColors`, `ADHDTypography`, `ADHDSpacing`, `ADHDAnimations`
- Both modals use the VisualEffect frosted glass background
- Both respect system appearance (light/dark mode) automatically
- Neither modal should EVER prevent the user from dismissing it
- CPU usage < 1% when modal is open but idle (no polling when not actively streaming)

---

## Implementation Notes

- Read `models.md` for all AI-related architecture decisions — it takes priority over `blueprint.md`
- Read `sentic.txt` for SenticNet API details and the Hourglass of Emotions model
- The existing LLM service (Qwen3-4B via MLX) should already have a streaming method — check `services/` for the current interface and match it
- The existing SenticNet service should already have an `analyze()` method — check its signature and return format
- The existing Mem0 service should already have `add()` and `get_all()` methods — check the current interface
- Use Pydantic v2 patterns (`model_validate_json`, `model_dump_json`) not v1
- All async — use `async/await` consistently
- The vent modal reuses the SAME Qwen3-4B instance as the coaching pipeline — do NOT load a second model. The hot-classifier/cold-specialist pattern from `models.md` applies: the LLM loads on demand, auto-unloads after 2 min idle
- SSE streaming format: `data: {"token": "..."}\n\n` for each token, `data: [DONE]\n\n` at the end
- Swift minimum target: macOS 14.0 (Sonoma)
- Test both modals on MacBook with notch and without notch — the floating panel should position correctly on both
