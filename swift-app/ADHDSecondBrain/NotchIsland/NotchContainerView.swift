import SwiftUI

/// Root view for the notch widget.
///
/// Architecture follows boring.notch + DynamicNotchKit:
/// - Fixed-size canvas, content pinned to top
/// - NotchShape mask with animatable corner radii
/// - Black background with padding(-50) for bounce overshoot
/// - Different springs for open (bouncy) vs close (damped)
/// - Blur + scale + opacity compound transitions
/// - `.compositingGroup()` to prevent constraint cycles
/// - Haptic feedback on hover
/// - Gesture-driven scale on drag
struct NotchContainerView: View {
    var stateMachine: NotchStateMachine
    var viewModel: NotchViewModel
    var onConnectCalendar: (() -> Void)?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    // Hover state (boring.notch pattern)
    @State private var isHovering = false
    @State private var hoverTask: Task<Void, Never>?

    // Gesture scale (boring.notch drag-to-open pattern)
    @State private var gestureProgress: CGFloat = 0

    var body: some View {
        VStack(spacing: 0) {
            notchBody
            Spacer(minLength: 0)
        }
        .frame(
            maxWidth: .infinity,
            maxHeight: .infinity,
            alignment: .top
        )
    }

    // MARK: - Notch Body

    private var notchBody: some View {
        ZStack(alignment: .top) {
            // Black background (extends beyond bounds for bouncy overshoot)
            Rectangle()
                .foregroundStyle(.black)
                .padding(-50)

            // Emotion glow border (behind content, inside mask)
            if stateMachine.currentState != .dormant {
                EmotionGlowBorder(emotion: viewModel.currentEmotion)
            }

            // State-specific content
            notchContent
        }
        .frame(width: currentWidth, height: currentHeight)
        .clipShape(currentNotchShape)
        // Top edge seam cover (DynamicNotchKit/boring.notch pattern)
        .overlay(alignment: .top) {
            Rectangle()
                .fill(.black)
                .frame(height: 1)
                .padding(.horizontal, currentNotchShape.topCornerRadius)
        }
        // Shadow (controlled by SwiftUI, not NSPanel)
        .shadow(
            color: .black.opacity(isHovering ? 0.6 : 0.4),
            radius: isHovering ? 16 : 10,
            y: isHovering ? 8 : 5
        )
        // Gesture-driven scale (boring.notch pull-to-expand)
        .scaleEffect(
            x: 1.0 + gestureProgress * 0.01,
            y: 1.0 + gestureProgress * 0.01,
            anchor: .top
        )
        // Hover shadow animates independently of state transitions
        .animation(.smooth(duration: 0.3), value: isHovering)
        // Flatten rendering to prevent constraint cycles
        .compositingGroup()
        // Interactions
        .onHover { handleHover($0) }
        .onTapGesture { handleTap() }
        .gesture(dragGesture)
    }

    // MARK: - Content Router

    @ViewBuilder
    private var notchContent: some View {
        // Each case gets .zIndex(1) so SwiftUI keeps the outgoing view
        // in the render tree long enough for removal transitions to animate.
        switch stateMachine.currentState {
        case .dormant:
            DormantView(hasActiveTask: viewModel.hasActiveTask)
                .transition(reduceMotion ? .opacity : .notchAmbient)
                .zIndex(1)
        case .ambient:
            AmbientView(
                taskName: viewModel.currentTaskName,
                nextEventCountdown: viewModel.nextEventCountdown
            )
            .transition(reduceMotion ? .opacity : .notchAmbient)
            .zIndex(1)
        case .glanceable:
            GlanceableView(
                task: viewModel.currentTask,
                timeRemaining: viewModel.focusTimeRemaining,
                emotion: viewModel.currentEmotion
            )
            .transition(reduceMotion ? .opacity : .notchCompact)
            .zIndex(1)
        case .expanded:
            ExpandedPanelView(
                viewModel: viewModel,
                onConnectCalendar: onConnectCalendar
            )
            .transition(reduceMotion ? .opacity : .notchExpand)
            .zIndex(1)
        case .alert(let tier):
            AlertOverlayView(
                tier: tier,
                message: viewModel.currentIntervention,
                onAcknowledge: {
                    stateMachine.transition(to: .glanceable)
                }
            )
            .transition(reduceMotion ? .opacity : .notchCompact)
            .zIndex(1)
        }
    }

    // MARK: - Shape per State

    private var currentNotchShape: NotchShape {
        switch stateMachine.currentState {
        case .dormant, .ambient:
            .closed
        case .glanceable, .alert:
            .glance
        case .expanded:
            .open
        }
    }

    // MARK: - Size per State

    private var currentWidth: CGFloat {
        switch stateMachine.currentState {
        case .dormant: 180
        case .ambient: 200
        case .glanceable: ADHDSpacing.notchGlanceWidth
        case .expanded: ADHDSpacing.notchExpandedWidth
        case .alert: ADHDSpacing.notchGlanceWidth
        }
    }

    private var currentHeight: CGFloat {
        switch stateMachine.currentState {
        case .dormant: 32
        case .ambient: 32
        case .glanceable: ADHDSpacing.notchGlanceHeight
        case .expanded: ADHDSpacing.notchExpandedHeight
        case .alert: ADHDSpacing.notchGlanceHeight + 60
        }
    }

    // MARK: - Hover (0.3s dwell to expand, 0.3s delay to collapse)

    private func handleHover(_ hovering: Bool) {
        hoverTask?.cancel()

        if hovering {
            // Dwell: wait 0.3s before expanding (prevents accidental triggers)
            hoverTask = Task { @MainActor in
                try? await Task.sleep(for: .milliseconds(300))
                guard !Task.isCancelled else { return }

                isHovering = true

                // Haptic feedback
                if !reduceMotion {
                    NSHapticFeedbackManager.defaultPerformer
                        .perform(.alignment, performanceTime: .default)
                }

                // Dormant → glanceable (skip ambient)
                if stateMachine.currentState == .dormant
                    || stateMachine.currentState == .ambient {
                    stateMachine.transition(to: .glanceable)
                }
            }
        } else {
            // Collapse: 0.3s delay before hiding
            hoverTask = Task { @MainActor in
                try? await Task.sleep(for: .milliseconds(300))
                guard !Task.isCancelled else { return }

                isHovering = false

                // Collapse to dormant (unless expanded or alert)
                if stateMachine.currentState == .glanceable
                    || stateMachine.currentState == .ambient {
                    stateMachine.transition(to: .dormant)
                }
            }
        }
    }

    // MARK: - Tap

    private func handleTap() {
        switch stateMachine.currentState {
        case .expanded:
            break // Click-away handled externally
        default:
            stateMachine.transition(to: .expanded)
        }
    }

    // MARK: - Drag Gesture (boring.notch pull-to-expand)

    private var dragGesture: some Gesture {
        DragGesture(minimumDistance: 5)
            .onChanged { value in
                let pull = max(0, value.translation.height)
                gestureProgress = min(pull / 3, 15)

                // Pull threshold triggers expand
                if pull > 40 && stateMachine.currentState != .expanded {
                    stateMachine.transition(to: .expanded)
                    gestureProgress = 0
                }
            }
            .onEnded { _ in
                withAnimation(ADHDAnimations.interactiveSpring) {
                    gestureProgress = 0
                }
            }
    }
}
