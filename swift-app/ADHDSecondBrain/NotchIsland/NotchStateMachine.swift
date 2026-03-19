import SwiftUI
import Observation

@Observable
class NotchStateMachine {
    private(set) var currentState: NotchState = .dormant
    private(set) var previousState: NotchState = .dormant

    var isHyperfocused: Bool = false
    var currentEmotion: EmotionState = .neutral

    /// Transition with direction-aware animation (DynamicNotchKit pattern).
    /// withAnimation wraps the state mutation so SwiftUI's .transition() modifiers
    /// receive the animation transaction — without this, removal transitions are instant.
    func transition(to newState: NotchState) {
        guard shouldTransition(from: currentState, to: newState) else { return }

        let animation = animationFor(from: currentState, to: newState)
        withAnimation(animation) {
            previousState = currentState
            currentState = newState
        }
    }

    /// Pick spring based on direction: opening gets bouncy, closing gets damped.
    private func animationFor(from: NotchState, to: NotchState) -> Animation {
        let toOrdinal = to.ordinal
        let fromOrdinal = from.ordinal
        if toOrdinal > fromOrdinal {
            return ADHDAnimations.openSpring   // expanding
        } else {
            return ADHDAnimations.closeSpring  // collapsing
        }
    }

    private func shouldTransition(
        from: NotchState, to: NotchState
    ) -> Bool {
        switch (from, to) {
        // Expanded can only close to glanceable (via escape/click-away)
        // or be interrupted by critical alerts
        case (.expanded, .dormant): return false
        case (.expanded, .ambient): return false
        case (.expanded, .alert(let tier)) where tier < .critical:
            return false
        case (_, .alert(let tier)):
            return !isHyperfocused || tier >= .actionRequired
        default: return true
        }
    }
}
