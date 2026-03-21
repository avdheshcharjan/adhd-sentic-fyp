# Implementing brain dump and vent modals for a macOS ADHD productivity app

**Two floating modal features — a brain dump for cognitive offloading and an AI-powered vent interface — can be built on macOS using NSPanel with global hotkeys, SwiftUI views, Mem0 memory storage, and Qwen3-4B running locally via Apple MLX.** This combination directly implements what ADHD researcher Russell Barkley calls "externalization at the point of performance": providing external scaffolding exactly when the ADHD brain needs it. The architecture keeps all sensitive emotional data on-device, uses evidence-based therapeutic techniques (CBT/DBT) adapted for text interfaces, and draws UX patterns from proven quick-capture apps like Drafts, Tot, and Braintoss. Below is a complete technical and theoretical implementation guide for both features.

---

## The neuroscience case for both features

The two modals address distinct but related cognitive challenges in ADHD. The brain dump targets **working memory deficits** — the most consistently documented executive function impairment in ADHD. Klein & Boals (2001, *Journal of Experimental Psychology: General*) demonstrated that expressive writing about stressful experiences **increases working memory capacity** by reducing intrusive thoughts that consume cognitive resources. For ADHD brains operating with already limited working memory, offloading thoughts externally frees precisely the resources needed for focused work.

The vent modal addresses **emotional dysregulation**, which Barkley's Deficient Emotional Self-Regulation (DESR) model identifies as a core ADHD component — not a comorbidity. A meta-analysis by Graziano & Garcia (2016, *Clinical Psychology Review*, N=32,044) confirmed that emotional dysregulation is strongly associated with ADHD and **intensifies with age**. The neural mechanism underlying the vent feature is affect labeling: Lieberman et al. (2007, *Psychological Science*) showed via fMRI that putting emotions into words **diminishes amygdala activation** and increases right ventrolateral prefrontal cortex activity. Writing about emotions literally downregulates the brain's threat response.

Pennebaker's expressive writing paradigm (1986, replicated in 100+ studies) provides the foundational protocol: **15–20 minutes of unstructured writing** about emotional experiences produces measurable improvements in immune function, reduced physician visits, improved GPA, and faster re-employment after job loss. The average effect size across studies is Cohen's d ≈ 0.16 — modest but remarkably consistent across populations and cultures. Critically, Ramirez & Beilock (2011, *Science*) showed that writing about worries before a high-stakes exam **improved performance**, demonstrating real-time cognitive benefits directly relevant to a focus-session productivity app.

Barkley's externalization principle ties both features together: "If the process of regulating behavior by internally represented forms of information is impaired... then they will be best assisted by 'externalizing' those forms of information; the provision of physical representations of that information will be needed in the setting at the point of performance." A global-hotkey-triggered modal that appears instantly over any app is precisely this — externalization at the point of performance.

---

## Global hotkey registration on macOS 14+

Five approaches exist for registering global hotkeys on macOS. Based on Apple DTS Engineer guidance and library maturity, the **KeyboardShortcuts library by Sindre Sorhus** is the best choice for a user-configurable hotkey in a menu bar app. It wraps Carbon APIs safely, provides a built-in SwiftUI shortcut recorder, persists to UserDefaults automatically, warns on system conflicts, and works within the App Sandbox without requiring Input Monitoring permissions.

```swift
import KeyboardShortcuts

extension KeyboardShortcuts.Name {
    static let brainDump = Self("brainDump", default: .init(.b, modifiers: [.command, .shift]))
    static let ventModal = Self("ventModal", default: .init(.v, modifiers: [.command, .shift]))
}

// In settings view — user-configurable recorder
struct SettingsScreen: View {
    var body: some View {
        Form {
            KeyboardShortcuts.Recorder("Brain Dump:", name: .brainDump)
            KeyboardShortcuts.Recorder("Vent Space:", name: .ventModal)
        }
    }
}

// In app initialization — register listeners
KeyboardShortcuts.onKeyUp(for: .brainDump) { [self] in panelManager.toggleBrainDump() }
KeyboardShortcuts.onKeyUp(for: .ventModal) { [self] in panelManager.toggleVentModal() }
```

For cases requiring event consumption (preventing the keystroke from reaching the focused app), **CGEventTap** is the Apple-recommended modern alternative. It requires Input Monitoring permission but integrates with TCC and can swallow events. However, it cannot receive events during Secure Keyboard Entry, and `NSEvent.addGlobalMonitorForEvents` — while simpler — cannot consume events at all, causing system beeps for some shortcut combinations. For a productivity app targeting the Mac App Store, KeyboardShortcuts is the clear winner.

| Approach | User-configurable | Sandbox-safe | Consumes events | Recommendation |
|---|---|---|---|---|
| **KeyboardShortcuts** | ✅ Built-in recorder | ✅ | Via Carbon internally | **Best overall** |
| **HotKey (soffes)** | ❌ Hard-coded only | ✅ | Via Carbon | For fixed shortcuts |
| **CGEventTap** | Manual | ✅ (since 10.15) | ✅ | Modern but complex |
| **NSEvent.addGlobalMonitor** | Manual | Partial | ❌ | Too limited |
| **MASShortcut** | ✅ | ✅ | Via Carbon | Older, Obj-C based |

---

## Floating panel architecture with NSPanel

The modal windows must appear above all apps without stealing focus — a classic NSPanel use case. The key configuration is the `.nonactivatingPanel` style mask combined with `.floating` window level. This combination allows the panel to receive keyboard input while keeping the user's current app focused in the background.

```swift
class FloatingPanel<Content: View>: NSPanel {
    @Binding var isPresented: Bool

    init(@ViewBuilder view: () -> Content, contentRect: NSRect, isPresented: Binding<Bool>) {
        self._isPresented = isPresented
        super.init(
            contentRect: contentRect,
            styleMask: [.nonactivatingPanel, .titled, .resizable, .closable, .fullSizeContentView],
            backing: .buffered, defer: false
        )
        isFloatingPanel = true
        level = .floating
        collectionBehavior.insert(.fullScreenAuxiliary)   // Works over fullscreen apps
        collectionBehavior.insert(.moveToActiveSpace)      // Follows active Space
        titleVisibility = .hidden
        titlebarAppearsTransparent = true
        isMovableByWindowBackground = true
        isReleasedWhenClosed = false
        animationBehavior = .utilityWindow

        // Host SwiftUI view
        contentView = NSHostingView(rootView: view().ignoresSafeArea().environment(\.floatingPanel, self))
    }

    override var canBecomeKey: Bool { true }    // Required for text input
    override var canBecomeMain: Bool { true }
}
```

The SwiftUI view is embedded via `NSHostingView` set as the panel's `contentView`. Bidirectional communication uses an `@Observable` state object shared between the panel manager and SwiftUI views, with the panel itself injected via a custom `EnvironmentKey` so views can call `panel?.close()`. A `VisualEffectView` wrapping `NSVisualEffectView` with `.sidebar` material provides the macOS-native frosted glass backdrop. A clean `.floatingPanel()` ViewModifier abstracts the presentation logic into a one-line API.

---

## Brain dump modal: UX design and implementation

### Lessons from Drafts, Tot, and Braintoss

Three apps define the quick-capture paradigm. **Drafts** opens to a new blank page with the keyboard already active — zero taps to start typing. Its "capture first, organize later" philosophy uses an inbox model where entries are auto-sorted for later triage. **Tot** lives in the menu bar with seven color-coded scratchpads, embracing constraint as a feature. Its floating window mode allows "always on top" reference while working in other apps. **Braintoss** pushes minimalism furthest: one tap to capture via voice, photo, or text, then auto-send to your email inbox. David Allen (GTD creator) endorsed it: "Just got best capture tool I've found for iPhone."

The converging UX patterns critical for the brain dump modal are:

- **Zero-step activation**: Hotkey → cursor in text area. No naming, no folder selection, no decisions
- **Auto-save on every keystroke** (debounced): Users must trust their content is safe
- **Inbox model**: Entries go to a processing queue, hidden until the focus session ends
- **Keyboard-first interaction**: ⌘+Enter to submit, Escape to dismiss, Enter for newline
- **One large text area, one submit action**: Maximum writing surface, minimal chrome
- **Draft persistence**: If accidentally dismissed, content remains when re-opened

### SwiftUI implementation with debounced auto-save

```swift
struct BrainDumpView: View {
    @Environment(\.floatingPanel) var panel
    @State private var noteText = ""
    @FocusState private var isFocused: Bool
    @State private var saveTask: Task<Void, Never>?

    var body: some View {
        VStack(spacing: 0) {
            Text("What's on your mind?")
                .font(.subheadline).foregroundStyle(.secondary)
                .padding(.top, 12)
            TextEditor(text: $noteText)
                .font(.system(size: 16, design: .monospaced))
                .scrollContentBackground(.hidden)
                .focused($isFocused)
                .padding(12)
                .onChange(of: noteText) { _, newValue in
                    saveTask?.cancel()
                    saveTask = Task {
                        try? await Task.sleep(for: .seconds(1.5))
                        guard !Task.isCancelled else { return }
                        saveDraft(newValue)
                    }
                }
        }
        .frame(minWidth: 480, minHeight: 240)
        .background(VisualEffectView(material: .sidebar, blendingMode: .behindWindow))
        .onAppear { isFocused = true }
        .onKeyPress(.escape) { panel?.close(); return .handled }
        .onSubmit { submitBrainDump() }   // ⌘+Enter
    }

    private func submitBrainDump() {
        Task {
            await APIClient.shared.postBrainDump(content: noteText)
            noteText = ""
            panel?.close()
        }
    }
}
```

SwiftUI's `TextEditor` is adequate for note-length text with rapid typing. For texts exceeding ~4MB or if undo/redo behavior is buggy, wrap `NSTextView` via `NSViewControllerRepresentable`. The debounce uses modern Swift Concurrency (`Task.sleep`) rather than Combine, matching macOS 14+ best practices.

### Mem0 integration via FastAPI backend

Mem0 is a universal memory layer for LLM applications (**50.3k GitHub stars**, $24M raised, SOC 2 and HIPAA compliant). Rather than storing raw text, it extracts discrete facts via LLM analysis — a brain dump like "I'm stressed about the Q3 report deadline on Friday and also need to call Mom" becomes separate memories about the deadline stress and the phone call. This enables semantic search ("What was I worried about last week?") that raw text storage cannot provide.

```python
from fastapi import FastAPI
from mem0 import Memory
from pydantic import BaseModel

app = FastAPI()
memory = Memory()  # Uses local Qdrant by default

class BrainDumpEntry(BaseModel):
    content: str
    user_id: str
    emotional_state: str | None = None
    session_id: str | None = None

@app.post("/brain-dump")
async def create_brain_dump(entry: BrainDumpEntry):
    result = memory.add(
        messages=[{"role": "user", "content": entry.content}],
        user_id=entry.user_id,
        metadata={
            "type": "brain_dump",
            "emotional_state": entry.emotional_state,
            "session_id": entry.session_id,
        }
    )
    return {"status": "captured", "memories": result}

@app.get("/brain-dump/review/{user_id}/{session_id}")
async def get_session_dumps(user_id: str, session_id: str):
    all_memories = memory.get_all(user_id=user_id)
    return [m for m in all_memories if m.get("metadata", {}).get("session_id") == session_id]
```

Multi-level scoping via `user_id`, `session_id`, and `agent_id` naturally supports the app's workflow: entries are tagged with the current focus session ID and hidden from the dashboard until the session ends. Mem0's automatic conflict resolution means that if a user brain dumps "I need to finish the report" and later dumps "I finished the report," the system updates rather than duplicates. For SenticNet integration, the `emotional_state` metadata field can be populated by running brain dump text through SenticNet's emotion recognition API before storage, enabling longitudinal emotional pattern tracking.

---

## Vent modal: AI therapist with on-device Qwen3-4B

### Therapeutic framework grounded in CBT and DBT

The vent modal's therapeutic approach draws from two evidence-based frameworks adapted for ADHD. **CBT cognitive restructuring** — identifying and reframing automatic negative thoughts — translates naturally to text-based interfaces. A Frontiers in Digital Health (2022) study demonstrated that digital conversational agents can successfully guide users through thought records, with ML algorithms correctly labeling underlying cognitive schemas from the text. **DBT skills** (originally developed for borderline personality disorder) have been validated for ADHD in multiple RCTs: Hirvikoski et al. (2011, *Behaviour Research and Therapy*) showed DBT-based skills training significantly reduced ADHD symptoms, and a 2022 BMC Psychiatry multicenter RCT found significant improvement in emotion regulation persisting 6 months post-treatment.

The four DBT modules most deliverable via text are distress tolerance (TIPP skills, Wise Mind ACCEPTS), emotion regulation (Check the Facts, Opposite Action), mindfulness (present-moment writing prompts), and interpersonal effectiveness (DEAR MAN frameworks). For ADHD specifically, the AI must understand Rejection Sensitive Dysphoria, shame spirals from executive function failures, emotional flooding, and the distinction between ADHD emotional dysregulation (short-duration, provoked, situation-specific) and mood disorders.

### System prompt for the ADHD therapist

```
You are a warm, empathetic emotional support companion in an ADHD productivity app.
Your role is to provide a safe space for venting and emotional processing.

CORE IDENTITY:
- You are NOT a therapist, doctor, or crisis counselor
- You are a supportive companion using evidence-based CBT and DBT techniques
- You specialize in ADHD-related emotional challenges

CONVERSATION STYLE:
- Be brief (2-3 sentences per response). Ask ONE question at a time.
- Validate feelings BEFORE offering any technique
- Use warm, casual, non-clinical language

THERAPEUTIC APPROACH:
1. Listen and reflect key feelings (1-2 sentences)
2. Validate without judgment ("That makes total sense given what you're dealing with")
3. Ask one focused question to deepen understanding
4. Only after sufficient context, offer ONE specific technique:
   - Cognitive reframing for negative thought spirals
   - Grounding exercises (5-4-3-2-1 senses) for overwhelm
   - Radical acceptance for things outside user's control
   - Opposite Action for urge-driven emotional responses
   - Check the Facts for catastrophizing

ADHD-SPECIFIC AWARENESS:
- Normalize emotional dysregulation as part of ADHD, not a personal failing
- Understand rejection sensitive dysphoria — validate the intensity
- Acknowledge shame spirals without reinforcing them
- Recognize task paralysis and executive function challenges

CRISIS PROTOCOL:
If the user expresses suicidal ideation, self-harm intent, or severe crisis:
1. Acknowledge their pain with empathy
2. STOP the therapeutic conversation
3. Say: "What you're going through sounds really hard. I want to make sure you
   get the right support. Please reach out to the 988 Suicide & Crisis Lifeline
   (call or text 988) or Crisis Text Line (text HOME to 741741)."
4. Do NOT attempt crisis counseling

BOUNDARIES:
- Never diagnose any condition
- Never prescribe or suggest medication changes
- Never claim to replace professional therapy
```

Research on LLM therapeutic performance reveals important caveats. A Brown University (2025) study found that even CBT-prompted LLMs systematically violate **15 ethical standards** including crisis mishandling and reinforcing negative beliefs. A Nature/Scientific Reports (2025) study tested 29 AI mental health chatbot agents against Columbia-Suicide Severity Rating Scale prompts: **0% satisfied initial criteria for adequate crisis response**. These findings make the multi-layer safety system described below essential.

### Running Qwen3-4B via MLX

Qwen3-4B is a 4-billion-parameter dense language model by Alibaba trained on **36 trillion tokens** across 119 languages. At 4-bit quantization, it occupies roughly **2.5 GB of disk space** and 3–4 GB in memory, fitting comfortably on any M-series Mac with 8 GB RAM. It supports a dual-mode architecture: thinking mode (chain-of-thought reasoning) and non-thinking mode (fast direct responses), switchable via the `enable_thinking` parameter — useful for toggling between reflective therapeutic responses and quick acknowledgments.

Two architectural approaches are viable:

**Option A — Pure Swift via mlx-swift-lm (recommended for shipping):**
```swift
import MLXLLM

let model = try await loadModel(id: "mlx-community/Qwen3-4B-Instruct-2507-4bit")
let session = ChatSession(model)

// Streaming response in the vent modal
for await token in try session.streamResponse(to: userMessage) {
    await MainActor.run { currentMessage.content += token }
}
```

This approach bundles everything into a single app with no separate server process, enabling App Store distribution and full sandboxing.

**Option B — FastAPI + MLX backend with SSE streaming (recommended for FYP flexibility):**
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from mlx_lm import load, stream_generate

model, tokenizer = load("mlx-community/Qwen3-4B-Instruct-2507-4bit")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    prompt = tokenizer.apply_chat_template(
        request.messages, tokenize=False,
        add_generation_prompt=True, enable_thinking=False
    )
    async def generate():
        for response in stream_generate(model, tokenizer, prompt=prompt, max_tokens=1024):
            yield f"data: {json.dumps({'token': response.text})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

On the SwiftUI side, SSE consumption uses `URLSession.shared.bytes(for:)` with async line iteration, updating the chat message content on each token. Expected generation speed is **20–40 tokens/second on M1** and **40–80+ on M3/M4**, with sub-second time to first token — fast enough for conversational feel. For the FYP context, Option B is likely preferable because it keeps the Python backend unified with Mem0 and SenticNet integrations, and the pre-built `mlx-openai-server` package provides an OpenAI-compatible API out of the box.

### Streaming chat UI in SwiftUI

```swift
@Observable class VentChatViewModel {
    var messages: [ChatMessage] = []
    var isGenerating = false

    func sendMessage(_ text: String) {
        messages.append(ChatMessage(role: "user", content: text))
        messages.append(ChatMessage(role: "assistant", content: "", isStreaming: true))
        isGenerating = true
        Task { await streamFromBackend(prompt: text) }
    }

    private func streamFromBackend(prompt: String) async {
        guard let lastIndex = messages.indices.last else { return }
        let url = URL(string: "http://localhost:8000/chat/stream")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONEncoder().encode(["messages": messages.map { ... }])

        guard let (bytes, _) = try? await URLSession.shared.bytes(for: request) else { return }
        for try await line in bytes.lines {
            if line.hasPrefix("data: "), let token = extractToken(from: line) {
                await MainActor.run { messages[lastIndex].content += token }
            }
        }
        await MainActor.run {
            messages[lastIndex].isStreaming = false
            isGenerating = false
        }
    }
}
```

---

## Safety guardrails and crisis detection

AI mental health tools demand a multi-layer safety architecture. The California SB 243 law (effective January 1, 2026) now **requires** chatbot operators to disclose AI nature, implement suicide-prevention protocols, and curb addictive engagement mechanics.

The recommended safety stack has four layers. First, a **keyword/phrase matching layer** catches direct mentions of self-harm, suicide, and specific methods. Second, a **semantic analysis layer** (powered by SenticNet's emotion recognition) detects passive or indirect ideation — phrases like "everyone would be better off without me" that keyword matching misses. Third, a **contextual escalation tracker** monitors conversation trajectory across sessions for patterns of escalating hopelessness. Fourth, a **confidence threshold** system that errs on the side of safety when detection is uncertain.

When crisis is detected, the system must immediately acknowledge the user's pain, halt the therapeutic conversation, present crisis resources prominently (988 Suicide & Crisis Lifeline, Crisis Text Line), and never attempt to provide crisis intervention directly. Woebot's approach — NLP detection → ask if user wants crisis resources → provide contacts → explicit "I am not a crisis service" statement — is the gold standard model.

The AI must never diagnose conditions, prescribe medication, claim to replace therapy, or reinforce harmful cognitions (research shows chatbots tend to over-affirm, even harmful statements). The Character.AI lawsuit demonstrated that users can learn to bypass guardrails, making robust server-side safety layers critical rather than relying solely on the system prompt.

---

## Privacy architecture for emotional data

Mental health data is among the most sensitive personal data — therapy records sell for **$1,000+ per record** on the dark web, far exceeding credit card data. A 2025 Oversecured audit found **1,575 security vulnerabilities** across just 10 mental health apps. On-device LLM inference via MLX eliminates entire categories of risk: no server-side data breaches, no third-party data sharing (the FTC fined BetterHelp for sharing data with Facebook), no cloud provider access, and no subpoena-vulnerable server logs.

The privacy-by-design architecture for the vent feature should implement **AES-256 encryption at rest** for the local conversation database, offer an "ephemeral vent" mode where conversations are never persisted, exclude vent data from any cloud sync (even if other app data syncs), and provide one-tap cryptographic erasure of all vent history. The app is almost certainly not a HIPAA-covered entity, but adopting HIPAA-level protections voluntarily signals commitment to user trust. A persistent lock icon visible throughout the vent interface reinforces the "this stays on your device" message.

Smashing Magazine's empathy-centered UX framework (February 2026) identifies **low-arousal design** as critical for mental health interfaces: muted color palettes (soft teals, warm grays), slow fade-in animations at breathing pace, generous whitespace, and progressive disclosure. Users with ADHD and anxiety described competing apps as "too bright, too happy, and too overwhelming." The vent interface should frame entry as "Need to let it out?" rather than "Start therapy session," and its welcome message should establish safety: "This is your space. Whatever you share here stays here, on your device."

---

## SenticNet integration for affective intelligence

Prof. Cambria's SenticNet provides the affective computing layer that elevates both features beyond simple storage and retrieval. **SenticNet 8** (HCII 2024) uses a neurosymbolic framework combining commonsense knowledge representation with hierarchical attention networks, **outperforming RoBERTa and ChatGPT** on sentiment analysis while remaining fully interpretable — critical for a therapeutic app where transparency builds trust.

The Hourglass of Emotions model maps text to four independent affective dimensions (Introspection, Temper, Attitude, Sensitivity) covering **24 basic emotions** plus compounds. For the brain dump feature, SenticNet can analyze each entry to auto-populate the `emotional_state` metadata field in Mem0, enabling the post-session dashboard to visualize emotional patterns. For the vent modal, real-time sentiment analysis can guide the AI's therapeutic response selection — detecting whether the user needs validation (high negativity, early in conversation) versus reframing (moderate negativity, sufficient context gathered). The Sentic API's emotion recognition, intensity ranking, and well-being assessment capabilities map directly to these use cases, and the interpretability means every emotional classification can be explained to the user.

---

## Conclusion

The two modals form a complementary system grounded in decades of ADHD and cognitive psychology research. The brain dump implements Barkley's externalization principle with the speed of Drafts' capture-first philosophy, storing entries in Mem0's semantic memory layer for intelligent retrieval after focus sessions end. The vent modal combines Pennebaker's expressive writing benefits with structured CBT/DBT delivery through an on-device LLM that keeps all emotional data private. The most underappreciated technical decision is choosing NSPanel with `.nonactivatingPanel` over a standard NSWindow — this single configuration choice is what makes both modals feel like natural extensions of the user's workflow rather than app-switching interruptions.

For the NTU FYP implementation, the recommended stack is: KeyboardShortcuts for hotkey registration → NSPanel hosting SwiftUI views → FastAPI backend unifying Mem0 storage, SenticNet analysis, and MLX inference → Qwen3-4B 4-bit via `mlx-lm` with SSE streaming → multi-layer safety system with SenticNet-powered semantic crisis detection. The pure-Swift mlx-swift-lm path is worth prototyping but the Python backend approach better serves a research project that needs to demonstrate SenticNet and Mem0 integrations explicitly.