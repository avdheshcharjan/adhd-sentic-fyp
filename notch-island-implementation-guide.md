# ADHD Second Brain — Dynamic Island Notch Widget Implementation Guide

## Claude Code Prompt: Build the Notch UI Module

**Repository:** `https://github.com/avdheshcharjan/adhd-sentic-fyp`
**Target directory:** `swift-app/ADHDSecondBrain/`
**Inspired by:** `https://github.com/TheBoredTeam/boring.notch` (MIT → GPL-3.0)
**Package dependency:** `https://github.com/MrKai77/DynamicNotchKit` (SwiftUI notch abstraction)

---

## 1. Design Philosophy — "Calm Companion, Not Taskmaster"

Every design decision in this widget follows one rule: **assume the user arrives already overwhelmed.** The notch is not a productivity dashboard — it is a peripheral awareness surface that graduates from ambient presence to focused interaction only when the user explicitly invites it.

### Core Design Principles

| Principle | What It Means for Code |
|---|---|
| **Calm Technology** | Default state is near-invisible. Information radiates outward from periphery to center only on demand. |
| **Zero-Shame Interactions** | No red badges, no "overdue" labels, no streak counters. Every message is an invitation, never an obligation. |
| **Sensory Goldilocks** | Muted palettes, brief animations (100–300ms), generous spacing. Enough dopamine to engage, never enough to overwhelm. |
| **Re-entry First** | Every state must instantly communicate where the user is and what to do next. Auto-save everything. |
| **Progressive Disclosure** | Show one thing at a time. Complexity layers behind hover → click → expand. |
| **Time Visibility** | ADHD users have time-blindness. Always show time context (remaining, elapsed, next event) without pressure. |

---

## 2. Design System — ADHD-Optimized Tokens

### 2.1 Color Palette

All colors are defined as SwiftUI `Color` extensions using asset catalogs with automatic light/dark/warm variants. **Never use pure black (#000) or pure white (#FFF).**

```swift
// MARK: - ADHDDesignTokens.swift

import SwiftUI

struct ADHDColors {
    // === BACKGROUNDS ===
    // Light mode: warm off-whites. Dark mode: Apple-aligned dark grays.
    // Warm mode: sepia-tinted for evening use (reduces blue light).
    
    struct Background {
        static let primary    = Color("bg-primary")    // Light: #F6F9F9 | Dark: #1C1C1E | Warm: #F2E6D6
        static let secondary  = Color("bg-secondary")  // Light: #EAE6D2 | Dark: #2C2C2E | Warm: #E8D9C5
        static let elevated   = Color("bg-elevated")   // Light: #FFFFFF → #FAFAFA | Dark: #3A3A3C | Warm: #F0E4D4
        static let notch      = Color("bg-notch")      // Always: #000000 (matches hardware notch)
        static let notchInner = Color("bg-notch-inner") // Light: #1C1C1E | Dark: #1C1C1E | Warm: #2A2420
    }
    
    // === TEXT ===
    // Contrast ratio targets: primary 10:1, secondary 7:1, tertiary 4.5:1
    // Never exceed 15:1 (causes halation for ADHD/dyslexic users)
    
    struct Text {
        static let primary   = Color("text-primary")   // Light: #2A363B | Dark: #E5E5E7 | Warm: #3D2E1F
        static let secondary = Color("text-secondary") // Light: #6C757D | Dark: #8E8E93 | Warm: #7A6B5D
        static let tertiary  = Color("text-tertiary")  // Light: #ADB5BD | Dark: #636366 | Warm: #A89888
        static let inverse   = Color("text-inverse")   // Light: #E5E5E7 | Dark: #2A363B | Warm: #F2E6D6
    }
    
    // === SEMANTIC ACCENTS ===
    // Max saturation: 60% on HSL scale. Large surfaces cap at 40%.
    // All accents have a "soft" variant (15% opacity over background) for fills.
    
    struct Accent {
        static let focus    = Color("accent-focus")    // Light: #457B9D | Dark: #7FB3D5 | Warm: #5A8FA8
        static let success  = Color("accent-success")  // Light: #73C8A9 | Dark: #B8EBD0 | Warm: #8ABF9F
        static let warmth   = Color("accent-warmth")   // Light: #FFE3B4 | Dark: #F0D3A4 | Warm: #F5D8A0
        static let alert    = Color("accent-alert")    // Light: #FF6F61 | Dark: #FF8A80 | Warm: #D4735E
        static let calm     = Color("accent-calm")     // Light: #B8C9E0 | Dark: #5C7A9E | Warm: #C4B8A0
    }
    
    // === INTERVENTION ESCALATION COLORS ===
    // Maps to the 5-tier notification urgency system.
    // Ordered from ambient (barely visible) to critical (demands attention).
    
    struct Intervention {
        static let dormant   = Color("intervention-dormant")   // Transparent / no glow
        static let ambient   = Color("intervention-ambient")   // #457B9D @ 15% opacity
        static let gentle    = Color("intervention-gentle")    // #FFE3B4 @ 40% opacity (warm glow)
        static let timely    = Color("intervention-timely")    // #FF6F61 @ 30% opacity (soft coral)
        static let critical  = Color("intervention-critical")  // #FF6F61 @ 60% opacity (pulsing)
    }
    
    // === EMOTION STATE COLORS ===
    // Mapped from SenticNet emotion output. Used for notch edge glow.
    // These shift the notch border to reflect detected emotional state.
    
    struct Emotion {
        static let joyful       = Color("emotion-joyful")       // #73C8A9 (sage green)
        static let focused      = Color("emotion-focused")      // #457B9D (steel blue)
        static let frustrated   = Color("emotion-frustrated")   // #FF8A80 (soft coral)
        static let anxious      = Color("emotion-anxious")      // #FFE3B4 (warm amber)
        static let disengaged   = Color("emotion-disengaged")   // #8E8E93 (neutral gray)
        static let overwhelmed  = Color("emotion-overwhelmed")  // #B8C9E0 (muted lavender-blue)
    }
}
```

### 2.2 Typography

**Primary font: Lexend** — research-backed for ADHD readability with optimized letter shapes and spacing. Falls back to SF Pro (macOS system font) which also has excellent readability.

```swift
struct ADHDTypography {
    // Lexend must be bundled in the app target.
    // If Lexend unavailable, SF Pro Rounded is the fallback.
    
    static let fontFamily = "Lexend"
    static let fallbackFamily = "SF Pro Rounded"
    
    // === SCALE ===
    // Minimum 14px anywhere. Body at 16px. Generous line heights (1.5x).
    // Letter spacing: +0.3pt for body, +0.5pt for captions.
    
    struct Notch {
        static let glanceTitle   = Font.custom(fontFamily, size: 13).weight(.semibold)
        static let glanceBody    = Font.custom(fontFamily, size: 11).weight(.regular)
        static let glanceCaption = Font.custom(fontFamily, size: 10).weight(.medium)
        static let expandedTitle = Font.custom(fontFamily, size: 16).weight(.semibold)
        static let expandedBody  = Font.custom(fontFamily, size: 14).weight(.regular)
        static let timer         = Font.custom(fontFamily, size: 28).weight(.light).monospacedDigit()
        static let timerSmall    = Font.custom(fontFamily, size: 18).weight(.light).monospacedDigit()
    }
    
    struct App {
        static let headline     = Font.custom(fontFamily, size: 22).weight(.semibold)
        static let subheadline  = Font.custom(fontFamily, size: 17).weight(.medium)
        static let body         = Font.custom(fontFamily, size: 16).weight(.regular)
        static let caption      = Font.custom(fontFamily, size: 13).weight(.regular)
        static let tiny         = Font.custom(fontFamily, size: 11).weight(.medium)
    }
    
    // === LINE HEIGHT ===
    static let lineSpacingBody: CGFloat = 6      // ~1.5x at 16px
    static let lineSpacingCaption: CGFloat = 4   // ~1.4x at 13px
    static let letterSpacingBody: CGFloat = 0.3
    static let letterSpacingCaption: CGFloat = 0.5
}
```

### 2.3 Animation Tokens

```swift
struct ADHDAnimations {
    // === DURATION RULES ===
    // Immediate feedback: ≤100ms (button press, toggle)
    // Simple transitions: 200–300ms (fade, color shift)
    // Modal/expand: 300–500ms (notch state changes)
    // NEVER exceed 1 second for any animation.
    
    static let micro: Double     = 0.1    // Button feedback
    static let fast: Double      = 0.2    // Color changes, opacity fades
    static let standard: Double  = 0.3    // Notch expand/collapse
    static let slow: Double      = 0.5    // Full panel reveal
    
    // === SPRING PRESETS ===
    // Use spring for all spatial animations (position, size).
    // Use easeOut for entering elements, easeIn for exiting.
    
    static let notchSpring = Animation.spring(response: 0.35, dampingFraction: 0.75, blendDuration: 0)
    static let gentleBounce = Animation.spring(response: 0.4, dampingFraction: 0.7, blendDuration: 0)
    static let subtleEase = Animation.easeOut(duration: standard)
    static let fadeIn = Animation.easeOut(duration: fast)
    static let fadeOut = Animation.easeIn(duration: fast)
    
    // === GLOW PULSE (for intervention escalation) ===
    // Gentle: 3-second cycle, subtle. Critical: 1.5-second cycle, more visible.
    static let gentlePulse = Animation.easeInOut(duration: 3.0).repeatForever(autoreverses: true)
    static let urgentPulse = Animation.easeInOut(duration: 1.5).repeatForever(autoreverses: true)
    
    // === REDUCED MOTION ===
    // When @Environment(\.accessibilityReduceMotion) is true:
    // Replace all spatial animations with opacity fades at `fast` duration.
    // Replace pulse/glow with static color at peak intensity.
    // Replace spring with linear.
}
```

### 2.4 Spacing & Layout

```swift
struct ADHDSpacing {
    // 4px base grid. ADHD-friendly = generous whitespace.
    static let xxs: CGFloat = 2
    static let xs: CGFloat  = 4
    static let sm: CGFloat  = 8
    static let md: CGFloat  = 12
    static let lg: CGFloat  = 16
    static let xl: CGFloat  = 24
    static let xxl: CGFloat = 32
    static let xxxl: CGFloat = 48
    
    // Notch-specific
    static let notchPaddingH: CGFloat = 12   // Horizontal padding inside notch
    static let notchPaddingV: CGFloat = 8    // Vertical padding inside notch
    static let notchCornerRadius: CGFloat = 16
    static let notchExpandedWidth: CGFloat = 380
    static let notchExpandedHeight: CGFloat = 260
    static let notchGlanceWidth: CGFloat = 280
    static let notchGlanceHeight: CGFloat = 36
    
    // Card layout (for expanded panel)
    static let cardCornerRadius: CGFloat = 12
    static let cardPadding: CGFloat = 12
    static let cardSpacing: CGFloat = 8
}
```

---

## 3. Five-State Notch Architecture

The notch widget operates as a **finite state machine** with five states, each with distinct visual treatment and interaction surface.

### 3.1 State Definitions

```swift
// MARK: - NotchState.swift

enum NotchState: Equatable {
    /// App running but notch looks like hardware. Only a tiny colored dot
    /// on the edge indicates the app is active.
    case dormant
    
    /// Minimal indicators flank the notch edges:
    /// left: current task name (truncated), right: countdown to next event.
    /// Appears automatically when a task is active or event is within 30min.
    case ambient
    
    /// On hover: notch widens slightly to show a single-line summary.
    /// Current task + time remaining + emotion color glow on border.
    /// Disappears when mouse leaves notch area.
    case glanceable
    
    /// On click or long-hover (500ms): full panel drops below notch.
    /// Contains: task list, timer, quick-capture, calendar, brain dump.
    /// Stays open until click-away or Escape key.
    case expanded
    
    /// Triggered by intervention engine. Notch border pulses with
    /// escalation color. Auto-shows glanceable content.
    /// Responds to intervention tier (gentle → critical).
    case alert(InterventionTier)
}

enum InterventionTier: Int, Comparable {
    case passive = 0    // Colored dot only
    case gentle = 1     // Warm glow around notch, 3s pulse
    case timeSensitive = 2  // Notch briefly widens with countdown
    case actionRequired = 3 // Widget auto-shows with gentle bounce
    case critical = 4       // Persistent glow + optional sound
    
    static func < (lhs: InterventionTier, rhs: InterventionTier) -> Bool {
        lhs.rawValue < rhs.rawValue
    }
}
```

### 3.2 State Transition Diagram

```
                    ┌──────────────────────────────────────────┐
                    │              DORMANT                      │
                    │  (tiny dot on notch edge)                │
                    └──────┬──────────────────┬────────────────┘
                           │                  │
                    task starts         intervention fires
                    or event < 30min         │
                           │                  │
                    ┌──────▼──────┐    ┌──────▼──────┐
                    │   AMBIENT   │    │    ALERT    │
                    │ (edge text) │    │ (pulsing    │
                    └──────┬──────┘    │  glow)      │
                           │           └──────┬──────┘
                     mouse hover              │
                           │           user acknowledges
                    ┌──────▼──────┐           │
                    │ GLANCEABLE  │◄──────────┘
                    │ (wider bar) │
                    └──────┬──────┘
                           │
                     click / 500ms hover
                           │
                    ┌──────▼──────┐
                    │  EXPANDED   │
                    │ (full panel)│
                    └─────────────┘
```

### 3.3 Transition Rules

```swift
// MARK: - NotchStateMachine.swift

@Observable
class NotchStateMachine {
    private(set) var currentState: NotchState = .dormant
    private(set) var previousState: NotchState = .dormant
    
    // ADHD-specific: don't transition too fast. Debounce hover for 150ms
    // to prevent accidental expansion during rapid mouse movement.
    private var hoverDebounceTask: Task<Void, Never>?
    
    // Track if user is in hyperfocus (from JITAI engine).
    // When true, suppress all alerts below .actionRequired tier.
    var isHyperfocused: Bool = false
    
    // Track current emotion from SenticNet pipeline
    var currentEmotion: EmotionState = .neutral
    
    func transition(to newState: NotchState) {
        // Rule: Never interrupt expanded state with ambient.
        // Rule: Only .critical alerts can override expanded.
        guard shouldTransition(from: currentState, to: newState) else { return }
        
        withAnimation(ADHDAnimations.notchSpring) {
            previousState = currentState
            currentState = newState
        }
    }
    
    private func shouldTransition(from: NotchState, to: NotchState) -> Bool {
        switch (from, to) {
        case (.expanded, .ambient):   return false  // Don't collapse to ambient
        case (.expanded, .dormant):   return false  // Must explicitly close
        case (.expanded, .alert(let tier)) where tier < .critical:
            return false  // Only critical interrupts expanded
        case (_, .alert(let tier)):
            // Suppress non-critical alerts during hyperfocus
            return !isHyperfocused || tier >= .actionRequired
        default: return true
        }
    }
}
```

---

## 4. SwiftUI Component Architecture

### 4.1 File Structure

```
swift-app/ADHDSecondBrain/
├── App/
│   └── ADHDSecondBrainApp.swift          # @main entry, NSApplication delegate
│
├── NotchIsland/
│   ├── NotchWindow.swift                  # NSPanel subclass, positions at notch
│   ├── NotchContainerView.swift           # Root SwiftUI view, routes by state
│   ├── NotchStateMachine.swift            # State management (§3.3)
│   ├── NotchViewModel.swift               # Bridges backend data → UI state
│   │
│   ├── States/
│   │   ├── DormantView.swift              # Tiny indicator dot
│   │   ├── AmbientView.swift              # Edge-flanking text labels
│   │   ├── GlanceableView.swift           # Expanded bar with task + timer
│   │   ├── ExpandedPanelView.swift        # Full dropdown panel
│   │   └── AlertOverlayView.swift         # Pulsing glow + intervention message
│   │
│   ├── Components/
│   │   ├── TaskCardView.swift             # Single task card (expanded panel)
│   │   ├── TimerRingView.swift            # Circular progress ring (Pomodoro)
│   │   ├── QuickCaptureField.swift        # Brain dump text input
│   │   ├── EmotionGlowBorder.swift        # SenticNet emotion → border color
│   │   ├── CalendarStripView.swift        # Horizontal scrolling events
│   │   ├── InterventionBanner.swift       # Coaching message from JITAI
│   │   ├── ProgressRingView.swift         # Cumulative progress (no streaks!)
│   │   └── NotchShapeView.swift           # The notch-matching bezier path
│   │
│   └── Animations/
│       ├── PulseModifier.swift            # Glow pulse for alerts
│       ├── SpringExpand.swift             # Notch width/height spring anim
│       └── ReducedMotionWrapper.swift     # Respects accessibilityReduceMotion
│
├── DesignSystem/
│   ├── ADHDDesignTokens.swift             # Colors, typography, spacing (§2)
│   ├── ADHDAnimations.swift               # Animation presets (§2.3)
│   ├── ColorSchemeManager.swift           # Light/Dark/Warm mode switching
│   ├── ThemeEnvironmentKey.swift          # Custom environment key for theme
│   └── Assets.xcassets/                   # Color sets with light/dark/warm variants
│       ├── bg-primary.colorset/
│       ├── bg-secondary.colorset/
│       ├── accent-focus.colorset/
│       ├── ...
│       └── emotion-*.colorset/
│
├── Services/
│   ├── BackendBridge.swift                # HTTP client → FastAPI backend
│   ├── NotchPositionCalculator.swift      # Detects notch position on screen
│   ├── HoverTracker.swift                 # Mouse tracking near notch region
│   └── KeyboardShortcutManager.swift      # Global hotkeys (⌘+Shift+N etc.)
│
└── Models/
    ├── TaskItem.swift                     # Current task from backend
    ├── EmotionState.swift                 # SenticNet emotion mapping
    ├── InterventionMessage.swift          # JITAI coaching message
    └── FocusSession.swift                 # Pomodoro/focus session state
```

### 4.2 Core Window Setup (Inspired by boring.notch)

```swift
// MARK: - NotchWindow.swift
// Creates an NSPanel that overlays the notch area.
// Key patterns borrowed from boring.notch:
//   - .nonactivatingPanel (doesn't steal focus)
//   - .fullScreenAuxiliary (visible in fullscreen)
//   - Transparent background
//   - Positioned using NSScreen.main frame + notch geometry

import SwiftUI
import AppKit

class NotchWindow: NSPanel {
    init() {
        super.init(
            contentRect: .zero,
            styleMask: [.borderless, .nonactivatingPanel, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        
        // Window behavior (matches boring.notch approach)
        self.isFloatingPanel = true
        self.level = .statusBar + 1          // Above menu bar
        self.collectionBehavior = [
            .canJoinAllSpaces,                // Visible on all desktops
            .fullScreenAuxiliary,             // Visible in fullscreen apps
            .stationary                       // Doesn't move with Exposé
        ]
        self.isOpaque = false
        self.backgroundColor = .clear
        self.hasShadow = false
        self.ignoresMouseEvents = false       // We need hover/click
        self.acceptsMouseMovedEvents = true
        
        // Position at notch
        positionAtNotch()
    }
    
    func positionAtNotch() {
        guard let screen = NSScreen.main else { return }
        let screenFrame = screen.frame
        let notchWidth: CGFloat = 180  // Approximate MacBook notch width
        
        let x = screenFrame.midX - (notchWidth / 2)
        let y = screenFrame.maxY - 38  // Top of screen minus notch height
        
        self.setFrame(
            NSRect(x: x, y: y, width: notchWidth, height: 38),
            display: true
        )
    }
    
    // Expand the window frame when transitioning to wider states
    func expandTo(width: CGFloat, height: CGFloat, animated: Bool = true) {
        guard let screen = NSScreen.main else { return }
        let screenFrame = screen.frame
        let x = screenFrame.midX - (width / 2)
        let y = screenFrame.maxY - height
        
        let newFrame = NSRect(x: x, y: y, width: width, height: height)
        
        if animated {
            NSAnimationContext.runAnimationGroup { ctx in
                ctx.duration = ADHDAnimations.standard
                ctx.timingFunction = CAMediaTimingFunction(name: .easeOut)
                self.animator().setFrame(newFrame, display: true)
            }
        } else {
            self.setFrame(newFrame, display: true)
        }
    }
}
```

### 4.3 Root Container View

```swift
// MARK: - NotchContainerView.swift

import SwiftUI

struct NotchContainerView: View {
    @State private var stateMachine = NotchStateMachine()
    @StateObject private var viewModel = NotchViewModel()
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        ZStack {
            // Notch shape background (always present, matches hardware)
            NotchShapeView()
                .fill(ADHDColors.Background.notch)
            
            // Emotion-reactive border glow
            if stateMachine.currentState != .dormant {
                EmotionGlowBorder(emotion: viewModel.currentEmotion)
            }
            
            // State-specific content
            Group {
                switch stateMachine.currentState {
                case .dormant:
                    DormantView(hasActiveTask: viewModel.hasActiveTask)
                    
                case .ambient:
                    AmbientView(
                        taskName: viewModel.currentTaskName,
                        nextEventCountdown: viewModel.nextEventCountdown
                    )
                    
                case .glanceable:
                    GlanceableView(
                        task: viewModel.currentTask,
                        timeRemaining: viewModel.focusTimeRemaining,
                        emotion: viewModel.currentEmotion
                    )
                    
                case .expanded:
                    ExpandedPanelView(viewModel: viewModel)
                    
                case .alert(let tier):
                    AlertOverlayView(
                        tier: tier,
                        message: viewModel.currentIntervention,
                        onAcknowledge: {
                            stateMachine.transition(to: .glanceable)
                        }
                    )
                }
            }
            .transition(
                reduceMotion
                    ? .opacity.animation(ADHDAnimations.fadeIn)
                    : .asymmetric(
                        insertion: .scale(scale: 0.95).combined(with: .opacity),
                        removal: .scale(scale: 0.98).combined(with: .opacity)
                    ).animation(ADHDAnimations.notchSpring)
            )
        }
        .onHover { hovering in
            handleHover(hovering)
        }
        .onTapGesture {
            handleTap()
        }
        .environment(stateMachine)
    }
    
    private func handleHover(_ hovering: Bool) {
        if hovering && stateMachine.currentState == .ambient {
            stateMachine.transition(to: .glanceable)
        } else if !hovering && stateMachine.currentState == .glanceable {
            // Debounce: wait 300ms before collapsing back
            Task {
                try? await Task.sleep(for: .milliseconds(300))
                if stateMachine.currentState == .glanceable {
                    stateMachine.transition(to: .ambient)
                }
            }
        }
    }
    
    private func handleTap() {
        switch stateMachine.currentState {
        case .glanceable:
            stateMachine.transition(to: .expanded)
        case .expanded:
            break // Tap inside expanded does nothing; click-away closes
        default:
            stateMachine.transition(to: .expanded)
        }
    }
}
```

---

## 5. Key Component Specs

### 5.1 Emotion Glow Border

The notch border color subtly reflects the user's detected emotional state from SenticNet. This provides peripheral emotional awareness without demanding attention.

```swift
// MARK: - EmotionGlowBorder.swift
// Maps SenticNet emotion output → notch border glow color.
// Uses a smooth 2-second transition between emotion states.
// Glow radius: 4px ambient, 8px during alert states.

struct EmotionGlowBorder: View {
    let emotion: EmotionState
    @State private var glowOpacity: Double = 0.4
    
    var glowColor: Color {
        switch emotion {
        case .joyful:      return ADHDColors.Emotion.joyful
        case .focused:     return ADHDColors.Emotion.focused
        case .frustrated:  return ADHDColors.Emotion.frustrated
        case .anxious:     return ADHDColors.Emotion.anxious
        case .disengaged:  return ADHDColors.Emotion.disengaged
        case .overwhelmed: return ADHDColors.Emotion.overwhelmed
        case .neutral:     return .clear
        }
    }
    
    var body: some View {
        NotchShapeView()
            .stroke(glowColor.opacity(glowOpacity), lineWidth: 2)
            .shadow(color: glowColor.opacity(glowOpacity * 0.6), radius: 6)
            .animation(.easeInOut(duration: 2.0), value: emotion)
    }
}
```

### 5.2 Intervention Banner (Zero-Shame Language)

```swift
// MARK: - InterventionBanner.swift
// CRITICAL: All text must follow zero-shame language rules.
// ❌ "You missed 3 tasks"  → ✅ "3 tasks waiting for you"
// ❌ "Overdue"             → ✅ "Ready when you are"
// ❌ "You forgot"          → ✅ "Quick reminder"
// ❌ "Warning"             → ✅ "Heads up"
// ❌ "You've been off task"→ ✅ "Want to refocus?"

struct InterventionBanner: View {
    let message: InterventionMessage
    let onDismiss: () -> Void
    let onAccept: () -> Void
    
    var body: some View {
        HStack(spacing: ADHDSpacing.md) {
            // Emoji icon (warm, non-threatening)
            Text(message.emoji)
                .font(.system(size: 20))
            
            VStack(alignment: .leading, spacing: ADHDSpacing.xxs) {
                Text(message.title)
                    .font(ADHDTypography.Notch.glanceTitle)
                    .foregroundColor(ADHDColors.Text.inverse)
                
                Text(message.body)
                    .font(ADHDTypography.Notch.glanceBody)
                    .foregroundColor(ADHDColors.Text.inverse.opacity(0.8))
                    .lineLimit(2)
            }
            
            Spacer()
            
            // Action buttons: soft, rounded, inviting
            Button(action: onAccept) {
                Text(message.actionLabel) // e.g. "Let's go" not "Start now"
                    .font(ADHDTypography.Notch.glanceCaption)
                    .padding(.horizontal, ADHDSpacing.sm)
                    .padding(.vertical, ADHDSpacing.xs)
                    .background(ADHDColors.Accent.focus.opacity(0.3))
                    .cornerRadius(ADHDSpacing.sm)
            }
            .buttonStyle(.plain)
            
            // Always provide a dismiss option. Never force interaction.
            Button(action: onDismiss) {
                Image(systemName: "xmark")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(ADHDColors.Text.inverse.opacity(0.5))
            }
            .buttonStyle(.plain)
        }
        .padding(ADHDSpacing.notchPaddingH)
    }
}
```

### 5.3 Timer Ring (Time Visibility for Time-Blindness)

```swift
// MARK: - TimerRingView.swift
// Shows elapsed time as a filling ring around a central time display.
// Uses percent-COMPLETE framing (never percent-remaining).
// Color shifts: focus-blue → success-green as session progresses.

struct TimerRingView: View {
    let elapsed: TimeInterval
    let total: TimeInterval
    let label: String  // e.g. "Focus" or "Break"
    
    private var progress: Double {
        guard total > 0 else { return 0 }
        return min(elapsed / total, 1.0)
    }
    
    private var timeString: String {
        let remaining = max(total - elapsed, 0)
        let minutes = Int(remaining) / 60
        let seconds = Int(remaining) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    private var ringColor: Color {
        // Gradual transition from focus-blue to success-green
        if progress < 0.75 {
            return ADHDColors.Accent.focus
        } else {
            return ADHDColors.Accent.success
        }
    }
    
    var body: some View {
        ZStack {
            // Background ring (track)
            Circle()
                .stroke(ADHDColors.Background.elevated.opacity(0.3), lineWidth: 4)
            
            // Progress ring
            Circle()
                .trim(from: 0, to: progress)
                .stroke(ringColor, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .animation(.linear(duration: 1), value: progress)
            
            // Center text
            VStack(spacing: 0) {
                Text(timeString)
                    .font(ADHDTypography.Notch.timerSmall)
                    .foregroundColor(ADHDColors.Text.inverse)
                    .monospacedDigit()
                
                Text(label)
                    .font(ADHDTypography.Notch.glanceCaption)
                    .foregroundColor(ADHDColors.Text.inverse.opacity(0.6))
            }
        }
        .frame(width: 56, height: 56)
    }
}
```

### 5.4 Quick Capture (Brain Dump)

```swift
// MARK: - QuickCaptureField.swift
// One-tap text entry for brain dumps. Captures thought → sends to backend
// → Mem0 stores it. No categorization required. Zero friction.
// Placeholder rotates through encouraging prompts.

struct QuickCaptureField: View {
    @State private var captureText: String = ""
    @FocusState private var isFocused: Bool
    let onSubmit: (String) -> Void
    
    private let placeholders = [
        "Quick thought...",
        "What's on your mind?",
        "Capture it before it flies away...",
        "Drop a thought here...",
        "Brain dump zone..."
    ]
    
    @State private var currentPlaceholder: String = ""
    
    var body: some View {
        HStack(spacing: ADHDSpacing.sm) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 14))
                .foregroundColor(ADHDColors.Accent.calm)
            
            TextField(currentPlaceholder, text: $captureText)
                .font(ADHDTypography.Notch.expandedBody)
                .foregroundColor(ADHDColors.Text.inverse)
                .textFieldStyle(.plain)
                .focused($isFocused)
                .onSubmit {
                    guard !captureText.trimmingCharacters(in: .whitespaces).isEmpty else { return }
                    onSubmit(captureText)
                    captureText = ""
                    // Brief success feedback
                }
            
            if !captureText.isEmpty {
                Button(action: {
                    onSubmit(captureText)
                    captureText = ""
                }) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(ADHDColors.Accent.focus)
                }
                .buttonStyle(.plain)
                .transition(.scale.combined(with: .opacity))
            }
        }
        .padding(ADHDSpacing.sm)
        .background(ADHDColors.Background.notchInner.opacity(0.5))
        .cornerRadius(ADHDSpacing.sm)
        .onAppear {
            currentPlaceholder = placeholders.randomElement() ?? placeholders[0]
        }
    }
}
```

---

## 6. Expanded Panel Layout

The expanded panel is the richest interaction surface. It follows a **card-based layout with maximum 4 visible items** to respect ADHD working memory limits.

```
┌──────────────────────────────────────────┐
│            [notch shape top]             │
├──────────────────────────────────────────┤
│                                          │
│  ┌─────────┐  ┌─────────────────────┐   │
│  │  Timer   │  │  Current Task       │   │
│  │  Ring    │  │  "Write Chapter 3"  │   │
│  │  23:41   │  │  ████████░░ 75%     │   │
│  └─────────┘  └─────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  🧠 Quick thought...            │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  📅 Next: Supervisor Meeting 2pm │   │
│  │  📅 FYP Demo Prep         4:30pm │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌────────┐ ┌────────┐ ┌────────────┐  │
│  │☀️ Calm │ │⚡ Focus│ │🌙 Wind Down│  │
│  └────────┘ └────────┘ └────────────┘  │
│                                          │
└──────────────────────────────────────────┘
```

**Bottom row = Mode switcher.** Three emotional/functional modes:
- **Calm** (overwhelmed recovery): Muted colors, slower animations, minimal info
- **Focus** (active work): Full task context, timer prominent, quick capture ready
- **Wind Down** (evening): Warm sepia tones, reflection prompts, progress summary

---

## 7. Notification Language Guide

Every string displayed in the notch must pass this checklist:

| ❌ Never Use | ✅ Use Instead | Why |
|---|---|---|
| "You missed..." | "Waiting for you..." | Avoids blame, reduces RSD trigger |
| "Overdue" | "Ready when you are" | Removes time pressure |
| "Warning" | "Heads up" | Less threatening |
| "Failed" / "Incomplete" | "In progress" | Maintains possibility |
| "You should..." | "Want to...?" | Preserves autonomy |
| "X days streak!" | "X sessions this month" | Cumulative, not consecutive |
| "You only did X" | "You did X today" | Celebrates what happened |
| "Don't forget" | "Quick reminder" | Neutral, not accusatory |
| "Time's up!" | "Session complete" | Accomplished, not punished |
| "You've been distracted for..." | "Want to refocus?" | Non-judgmental invitation |

---

## 8. Backend Integration Points

The notch widget communicates with the existing FastAPI backend via these endpoints:

```swift
// MARK: - BackendBridge.swift

struct BackendBridge {
    let baseURL: URL  // e.g. http://localhost:8000
    
    // === DATA THE NOTCH READS ===
    
    /// GET /api/v1/tasks/current → TaskItem?
    /// Returns the currently active task (if any)
    func fetchCurrentTask() async throws -> TaskItem?
    
    /// GET /api/v1/focus/session → FocusSession?
    /// Returns active Pomodoro/focus session state
    func fetchFocusSession() async throws -> FocusSession?
    
    /// GET /api/v1/calendar/upcoming?limit=3 → [CalendarEvent]
    /// Returns next 3 calendar events
    func fetchUpcomingEvents() async throws -> [CalendarEvent]
    
    /// GET /api/v1/emotion/current → EmotionState
    /// Returns latest SenticNet emotion analysis result
    func fetchEmotionState() async throws -> EmotionState
    
    /// GET /api/v1/interventions/pending → InterventionMessage?
    /// Returns queued JITAI intervention (if any)
    func fetchPendingIntervention() async throws -> InterventionMessage?
    
    /// GET /api/v1/progress/today → DailyProgress
    /// Returns cumulative progress stats (no streaks!)
    func fetchDailyProgress() async throws -> DailyProgress
    
    // === ACTIONS THE NOTCH SENDS ===
    
    /// POST /api/v1/capture {"text": "...", "source": "notch_quick_capture"}
    /// Brain dump capture → stored in Mem0
    func sendQuickCapture(_ text: String) async throws
    
    /// POST /api/v1/interventions/{id}/acknowledge
    /// User acknowledged/dismissed an intervention
    func acknowledgeIntervention(_ id: String) async throws
    
    /// POST /api/v1/focus/toggle
    /// Start/pause/stop focus session from notch
    func toggleFocusSession() async throws
    
    /// POST /api/v1/tasks/{id}/complete
    /// Mark task complete (triggers micro-celebration animation)
    func completeTask(_ id: String) async throws
}
```

**Polling strategy:** The notch polls the backend every **5 seconds** for emotion + intervention updates, every **30 seconds** for calendar/task updates. Use WebSocket upgrade path for future real-time push.

---

## 9. Accessibility Requirements

```swift
// Every view must implement these checks:

// 1. Reduced Motion
@Environment(\.accessibilityReduceMotion) var reduceMotion
// When true: replace springs with opacity fades, disable pulse, disable glow animation

// 2. Increase Contrast
@Environment(\.accessibilityDisplayShouldIncreaseContrast) var highContrast
// When true: boost text contrast to 12:1, add 1px borders on cards

// 3. Reduce Transparency
@Environment(\.accessibilityReduceTransparency) var reduceTransparency
// When true: use solid backgrounds instead of blur/opacity effects

// 4. VoiceOver
// Every interactive element needs .accessibilityLabel and .accessibilityHint
// Timer ring: "Focus timer: 23 minutes 41 seconds remaining"
// Emotion glow: "Current mood: focused" (read from SenticNet)
// Quick capture: "Brain dump text field. Type a thought and press return to save."

// 5. Keyboard Navigation
// ⌘+Shift+N → Toggle notch expanded/collapsed
// Escape → Close expanded panel
// Tab → Cycle through interactive elements in expanded panel
// Return → Submit quick capture or acknowledge intervention
```

---

## 10. Implementation Order for Claude Code

Execute these tasks sequentially. Each depends on the previous.

### Phase A: Foundation (Tasks 1–3)

**Task 1: Design System Files**
```
Create ADHDDesignTokens.swift, ADHDAnimations.swift, and Assets.xcassets
with all color sets (light/dark variants). Include Lexend font files in bundle.
```

**Task 2: NotchWindow + Positioning**
```
Create NotchWindow.swift NSPanel that positions correctly over the hardware
notch. Test on both notch and non-notch Mac displays. Include
NotchPositionCalculator.swift for multi-display support.
```

**Task 3: State Machine + Container**
```
Create NotchStateMachine.swift and NotchContainerView.swift.
Wire up state transitions with animation. Create stub views for all 5 states.
```

### Phase B: State Views (Tasks 4–7)

**Task 4: DormantView + AmbientView**
```
Dormant: tiny colored dot (6px circle) at right edge of notch.
Ambient: task name (left, truncated 20 chars) + countdown (right).
Both use Lexend font, respect dark mode.
```

**Task 5: GlanceableView**
```
Wider bar (280px) showing: task name, timer ring (small), emotion border glow.
Appears on hover with 150ms debounce. Spring animation for width expansion.
```

**Task 6: ExpandedPanelView**
```
Full panel (380×260px) with card layout per §6 diagram.
Timer ring, current task card, quick capture field, calendar strip, mode switcher.
Click-away or Escape to dismiss.
```

**Task 7: AlertOverlayView**
```
Pulsing glow border mapped to InterventionTier colors.
InterventionBanner with zero-shame language.
Acknowledge button + dismiss button. Auto-transitions to glanceable after ack.
```

### Phase C: Integration (Tasks 8–10)

**Task 8: BackendBridge**
```
HTTP client connecting to FastAPI backend endpoints per §8.
5-second polling for emotion/intervention, 30-second for tasks/calendar.
Error handling: silent retry, never show error UI in notch.
```

**Task 9: Emotion Glow + SenticNet**
```
Wire EmotionState from backend → EmotionGlowBorder color mapping.
Smooth 2-second cross-fade between emotion states.
```

**Task 10: Keyboard Shortcuts + Accessibility**
```
Register global hotkeys (⌘+Shift+N). Implement all accessibility
requirements from §9. VoiceOver labels, reduced motion fallbacks,
high contrast mode.
```

---

## 11. Gamification Rules (Non-Negotiable)

The progress system in the expanded panel MUST follow these rules:

- ✅ **Cumulative counters**: "47 tasks this month", "12 focus sessions this week"
- ✅ **Micro-celebrations**: 150ms checkmark animation on task completion, optional confetti on milestones
- ✅ **Variable rewards**: Occasional encouraging messages ("You're on a roll today!") appear randomly, not on every completion
- ✅ **XP that never expires**: Accumulated effort is permanent
- ❌ **NO consecutive streaks**: No "Day 12" counters anywhere
- ❌ **NO leaderboards**: No social comparison
- ❌ **NO countdown pressure**: Timers show remaining time, never "hurry" language
- ❌ **NO decay/penalties**: Missing a day has zero visual consequence
- ❌ **NO red badges/numbers**: Use dots (not numbers) for pending items, in calm colors

---

## 12. Visual Mode Specifications

### Calm Mode (Overwhelm Recovery)
- Background: warmest palette variant
- Animations: disabled or 50% speed
- Content: only current task + breathing exercise option
- Timer: hidden (removes time pressure)
- Emotion glow: blue-lavender regardless of actual emotion

### Focus Mode (Active Work)
- Background: standard palette
- Animations: normal
- Content: full task context, timer prominent, quick capture ready
- Timer: visible with progress ring
- Emotion glow: reflects actual SenticNet state

### Wind Down Mode (Evening)
- Background: warm/sepia palette
- Animations: 75% speed, extra gentle
- Content: daily progress summary, reflection prompt, next-day prep
- Timer: shows "time until bedtime" if set
- Emotion glow: amber/warm tones only

---

## 13. Testing Checklist

Before marking any task complete, verify:

- [ ] Works on MacBook with notch (M1 Pro/M2 Pro/M3 Pro/M4)
- [ ] Works on Mac without notch (simulated notch overlay, like boring.notch)
- [ ] Light mode, dark mode, and warm mode all render correctly
- [ ] Reduced Motion: all animations replaced with opacity fades
- [ ] High Contrast: text meets 12:1 ratio, borders visible
- [ ] VoiceOver: every element has label + hint
- [ ] No text ever uses shame language (check against §7 table)
- [ ] No streak counters, no red badges, no decay penalties anywhere
- [ ] Timer ring shows percent-complete, not percent-remaining
- [ ] CPU usage < 2% during dormant/ambient states (match boring.notch benchmark)
- [ ] Memory usage < 30MB for notch module alone
- [ ] All transitions complete in < 500ms
- [ ] Quick capture auto-saves on every keystroke (never lose a thought)
