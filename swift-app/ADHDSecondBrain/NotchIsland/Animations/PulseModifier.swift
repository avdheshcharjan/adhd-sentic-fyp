import SwiftUI

struct PulseModifier: ViewModifier {
    let color: Color
    let isActive: Bool
    let tier: InterventionTier
    @State private var glowOpacity: Double = 0.3
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func body(content: Content) -> some View {
        content
            .shadow(
                color: color.opacity(glowOpacity),
                radius: isActive ? glowRadius : 0
            )
            .onAppear {
                guard isActive, !reduceMotion else {
                    glowOpacity = isActive ? 0.6 : 0.3
                    return
                }
                withAnimation(pulseAnimation) {
                    glowOpacity = 0.8
                }
            }
            .onChange(of: isActive) { _, active in
                if active && !reduceMotion {
                    withAnimation(pulseAnimation) {
                        glowOpacity = 0.8
                    }
                } else {
                    glowOpacity = active ? 0.6 : 0.3
                }
            }
    }

    private var glowRadius: CGFloat {
        switch tier {
        case .passive: 0
        case .gentle: 4
        case .timeSensitive: 6
        case .actionRequired: 8
        case .critical: 10
        }
    }

    private var pulseAnimation: Animation {
        tier >= .actionRequired
            ? ADHDAnimations.urgentPulse
            : ADHDAnimations.gentlePulse
    }
}

extension View {
    func interventionPulse(
        color: Color,
        isActive: Bool,
        tier: InterventionTier
    ) -> some View {
        modifier(PulseModifier(
            color: color, isActive: isActive, tier: tier
        ))
    }
}
