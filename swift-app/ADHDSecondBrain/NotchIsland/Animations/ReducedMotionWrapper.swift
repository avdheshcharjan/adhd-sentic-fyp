import SwiftUI

/// Applies reduced motion-safe animations keyed on an equatable value.
struct ReducedMotionWrapper<V: Equatable>: ViewModifier {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    let animation: Animation
    let reducedAnimation: Animation
    let value: V

    init(
        _ animation: Animation,
        value: V,
        reduced: Animation = .easeOut(duration: ADHDAnimations.fast)
    ) {
        self.animation = animation
        self.value = value
        self.reducedAnimation = reduced
    }

    func body(content: Content) -> some View {
        content.animation(
            reduceMotion ? reducedAnimation : animation,
            value: value
        )
    }
}
