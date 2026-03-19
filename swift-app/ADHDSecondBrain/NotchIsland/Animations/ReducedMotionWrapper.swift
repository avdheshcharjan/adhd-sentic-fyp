import SwiftUI

/// Applies reduced motion-safe animations.
struct ReducedMotionWrapper: ViewModifier {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    let animation: Animation
    let reducedAnimation: Animation

    init(
        _ animation: Animation,
        reduced: Animation = .easeOut(duration: ADHDAnimations.fast)
    ) {
        self.animation = animation
        self.reducedAnimation = reduced
    }

    func body(content: Content) -> some View {
        content.animation(
            reduceMotion ? reducedAnimation : animation,
            value: UUID()
        )
    }
}
