import SwiftUI

/// Emotion/alert glow border drawn only on left, bottom, and right edges — never the top.
///
/// Normal states use the user's detected emotion color (defaulting to steel-blue #457B9D).
/// Alert state overrides with red-coral #FF6F61 regardless of emotion.
///
/// The "top-only excluded" effect is achieved by masking the stroke to the bottom 60%
/// of the notch shape using a gradient mask, which matches the Paper design spec exactly.
struct EmotionGlowBorder: View {
    let emotion: EmotionState
    let notchState: NotchState
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        ZStack {
            // Primary border stroke on the notch shape for the current state
            borderShape
                .stroke(borderColor.opacity(borderOpacity), lineWidth: 2)
                // Mask away the top edge: gradient fades to clear at top,
                // full opacity at roughly 20% down — matching left/bottom/right only spec.
                .mask(
                    LinearGradient(
                        stops: [
                            .init(color: .clear, location: 0.0),
                            .init(color: .clear, location: 0.08),
                            .init(color: .black, location: 0.20),
                            .init(color: .black, location: 1.0),
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )

            // Outer glow shadow layer
            borderShape
                .stroke(borderColor.opacity(glowOpacity), lineWidth: 2)
                .blur(radius: glowRadius)
                .mask(
                    LinearGradient(
                        stops: [
                            .init(color: .clear, location: 0.0),
                            .init(color: .clear, location: 0.08),
                            .init(color: .black, location: 0.20),
                            .init(color: .black, location: 1.0),
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
        }
        .animation(
            reduceMotion ? nil : .easeInOut(duration: 2.0),
            value: emotion
        )
        .animation(
            reduceMotion ? nil : .easeInOut(duration: 0.3),
            value: isAlertState
        )
        .accessibilityHidden(true)
    }

    // MARK: - Shape per State

    private var borderShape: NotchShape {
        switch notchState {
        case .dormant, .ambient:
            .closed
        case .glanceable, .alert:
            .glance
        case .expanded:
            .open
        }
    }

    // MARK: - Color per State

    private var isAlertState: Bool {
        if case .alert = notchState { return true }
        return false
    }

    /// Border stroke color:
    /// - Alert: rgba(255,111,97,0.35) — red coral
    /// - Normal: rgba(69,123,157,0.35) — steel blue, or emotion color if set
    private var borderColor: Color {
        if isAlertState {
            return ADHDColors.Accent.alert
        }
        // Use emotion color when available; fall back to steel-blue focus accent
        let emotionColor = emotion.color
        // EmotionState.neutral returns .clear — fall back to focus accent
        if emotion == .neutral {
            return ADHDColors.Accent.focus
        }
        return emotionColor
    }

    private var borderOpacity: Double {
        isAlertState ? 0.35 : 0.35
    }

    private var glowOpacity: Double {
        isAlertState ? 0.20 : 0.20
    }

    private var glowRadius: CGFloat {
        isAlertState ? 10 : 6
    }
}
