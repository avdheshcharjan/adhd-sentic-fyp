import SwiftUI

/// Blur transition modifier ported from DynamicNotchKit.
/// Enables `.transition(.blur)` for content entering/exiting the notch.
struct BlurModifier: ViewModifier {
    let isActive: Bool
    let intensity: CGFloat

    func body(content: Content) -> some View {
        content.blur(radius: isActive ? intensity : 0)
    }
}

extension AnyTransition {
    /// Content blurs in/out during transition.
    static func blur(intensity: CGFloat = 10) -> AnyTransition {
        .modifier(
            active: BlurModifier(isActive: true, intensity: intensity),
            identity: BlurModifier(isActive: false, intensity: intensity)
        )
    }

    // MARK: - Notch-specific compound transitions

    /// Expanded content: blurs + scales from top + fades.
    static var notchExpand: AnyTransition {
        .blur(intensity: 8)
            .combined(with: .scale(scale: 0.6, anchor: .top))
            .combined(with: .opacity)
    }

    /// Compact content: blurs + scales horizontally + fades.
    static var notchCompact: AnyTransition {
        .blur(intensity: 6)
            .combined(with: .scale(scale: 0.85, anchor: .top))
            .combined(with: .opacity)
    }

    /// Ambient/glanceable content: lighter blur + fade.
    static var notchAmbient: AnyTransition {
        .blur(intensity: 4)
            .combined(with: .opacity)
    }
}
