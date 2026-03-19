import SwiftUI

enum ADHDAnimations {
    static let micro: Double = 0.1
    static let fast: Double = 0.2
    static let standard: Double = 0.3
    static let slow: Double = 0.5

    // MARK: - Notch Springs (boring.notch pattern)
    // Open: bouncy (0.8 damping — slight overshoot, playful)
    // Close: critically damped (1.0 — snaps shut, no bounce)

    static let openSpring = Animation.spring(
        response: 0.42, dampingFraction: 0.8, blendDuration: 0
    )
    static let closeSpring = Animation.spring(
        response: 0.45, dampingFraction: 1.0, blendDuration: 0
    )

    // DynamicNotchKit bouncy variant
    static let bouncyOpen = Animation.bouncy(duration: 0.4)
    static let smoothClose = Animation.smooth(duration: 0.4)
    static let snappyConvert = Animation.snappy(duration: 0.4)

    // Interactive spring for gesture-driven actions
    static let interactiveSpring = Animation.interactiveSpring(
        response: 0.38, dampingFraction: 0.8, blendDuration: 0
    )

    // Legacy presets (still used by some views)
    static let notchSpring = openSpring
    static let gentleBounce = Animation.spring(
        response: 0.4, dampingFraction: 0.7, blendDuration: 0
    )
    static let subtleEase = Animation.easeOut(duration: standard)
    static let fadeIn = Animation.easeOut(duration: fast)
    static let fadeOut = Animation.easeIn(duration: fast)

    // MARK: - Glow Pulse (intervention escalation)

    static let gentlePulse = Animation.easeInOut(duration: 3.0)
        .repeatForever(autoreverses: true)
    static let urgentPulse = Animation.easeInOut(duration: 1.5)
        .repeatForever(autoreverses: true)
}
