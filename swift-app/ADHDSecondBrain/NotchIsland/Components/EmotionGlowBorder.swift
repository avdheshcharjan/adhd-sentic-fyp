import SwiftUI

/// Subtle border glow reflecting the user's emotional state from SenticNet.
/// Uses NotchShape for correct masking against the notch bezier path.
struct EmotionGlowBorder: View {
    let emotion: EmotionState
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        NotchShape.glance
            .stroke(emotion.color.opacity(0.4), lineWidth: 2)
            .shadow(color: emotion.color.opacity(0.25), radius: 6)
            .animation(
                reduceMotion ? nil : .easeInOut(duration: 2.0),
                value: emotion
            )
            .accessibilityHidden(true)
    }
}
