import SwiftUI

/// Emotion/alert glow border drawn only on left, bottom, and right edges — never the top.
///
/// Normal states use the user's detected emotion color (defaulting to steel-blue #457B9D).
/// Alert state overrides with red-coral #FF6F61 regardless of emotion.
/// Off-task state pulses the border red with a 1.2s breathing animation.
///
/// Uses an inner-shadow technique for uniform glow on all edges:
/// 1. Inverted shape (full rect minus notch shape) as an overlay
/// 2. `.shadow()` on the inverted shape projects inward uniformly
/// 3. Clipped to the notch shape so only the inner border glow is visible
/// 4. Gradient mask hides the top edge
struct EmotionGlowBorder: View {
    let emotion: EmotionState
    let notchState: NotchState
    var isOffTask: Bool = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var pulsePhase: Bool = false

    var body: some View {
        ZStack {
            // Uniform inner glow: an inverted shape projects shadow inward
            Rectangle()
                .fill(.clear)
                .overlay {
                    // Inverted shape: a large rect with the notch shape cut out.
                    // The shadow of this cutout projects inward uniformly.
                    Rectangle()
                        .fill(.black)
                        .padding(-20) // Extend beyond bounds
                        .mask(
                            // Subtract the notch shape from a full rect
                            Canvas { context, size in
                                // Fill everything
                                context.fill(
                                    Path(CGRect(origin: .zero, size: size)),
                                    with: .color(.white)
                                )
                                // Cut out the notch shape (EvenOdd rule)
                                let insetRect = CGRect(origin: .zero, size: size)
                                context.blendMode = .destinationOut
                                context.fill(
                                    borderShape.path(in: insetRect),
                                    with: .color(.white)
                                )
                            }
                            .compositingGroup()
                        )
                        .shadow(color: borderColor.opacity(borderOpacity), radius: borderBlur, x: 0, y: 0)
                        .shadow(color: borderColor.opacity(glowOpacity), radius: glowRadius, x: 0, y: 0)
                }
                .clipShape(borderShape)
                .mask(edgeMask)
        }
        .animation(
            reduceMotion ? nil : .easeInOut(duration: 2.0),
            value: emotion
        )
        .animation(
            reduceMotion ? nil : .easeInOut(duration: 0.3),
            value: isAlertState
        )
        .onChange(of: isOffTask) { _, offTask in
            if offTask && !reduceMotion {
                withAnimation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true)) {
                    pulsePhase = true
                }
            } else {
                withAnimation(.easeInOut(duration: 0.3)) {
                    pulsePhase = false
                }
            }
        }
        .accessibilityHidden(true)
    }

    // MARK: - Edge Mask

    private var edgeMask: some View {
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

    /// Border color:
    /// - Off-task: red coral #FF6F61
    /// - Alert: red coral #FF6F61
    /// - Normal: steel blue or emotion color
    private var borderColor: Color {
        if isOffTask || isAlertState {
            return ADHDColors.Accent.alert
        }
        if emotion == .neutral {
            return ADHDColors.Accent.focus
        }
        return emotion.color
    }

    private var borderOpacity: Double {
        if isOffTask {
            return pulsePhase ? 0.60 : 0.20
        }
        return isAlertState ? 0.45 : 0.40
    }

    private var borderBlur: CGFloat {
        // Tight blur for the crisp border line
        if isOffTask {
            return pulsePhase ? 3 : 1.5
        }
        return 2
    }

    private var glowOpacity: Double {
        if isOffTask {
            return pulsePhase ? 0.35 : 0.08
        }
        return isAlertState ? 0.25 : 0.20
    }

    private var glowRadius: CGFloat {
        if isOffTask {
            return pulsePhase ? 12 : 4
        }
        return isAlertState ? 10 : 6
    }
}
