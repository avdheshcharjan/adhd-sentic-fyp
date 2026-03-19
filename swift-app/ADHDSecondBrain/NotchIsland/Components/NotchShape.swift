import SwiftUI

/// Notch shape drawn with quad-curve corners matching Apple's hardware notch.
///
/// Ported from DynamicNotchKit's `NotchShape.swift`.
/// Uses quadratic Bézier curves (not circular arcs) for the squircle-like
/// corners that match Apple's design language.
///
/// Both corner radii are animatable, so the shape morphs smoothly
/// between closed (tight, small) and open (larger, more rounded) states.
struct NotchShape: Shape {
    var topCornerRadius: CGFloat
    var bottomCornerRadius: CGFloat

    var animatableData: AnimatablePair<CGFloat, CGFloat> {
        get { AnimatablePair(topCornerRadius, bottomCornerRadius) }
        set {
            topCornerRadius = newValue.first
            bottomCornerRadius = newValue.second
        }
    }

    func path(in rect: CGRect) -> Path {
        let topR = topCornerRadius
        let bottomR = bottomCornerRadius

        var path = Path()

        // Start at top-left
        path.move(to: CGPoint(x: rect.minX, y: rect.minY))

        // Top-left quad curve (ear) — pulls inward
        path.addQuadCurve(
            to: CGPoint(x: rect.minX + topR, y: rect.minY + topR),
            control: CGPoint(x: rect.minX + topR, y: rect.minY)
        )

        // Left side straight down
        path.addLine(
            to: CGPoint(x: rect.minX + topR, y: rect.maxY - bottomR)
        )

        // Bottom-left quad curve
        path.addQuadCurve(
            to: CGPoint(x: rect.minX + topR + bottomR, y: rect.maxY),
            control: CGPoint(x: rect.minX + topR, y: rect.maxY)
        )

        // Bottom edge
        path.addLine(
            to: CGPoint(x: rect.maxX - topR - bottomR, y: rect.maxY)
        )

        // Bottom-right quad curve
        path.addQuadCurve(
            to: CGPoint(x: rect.maxX - topR, y: rect.maxY - bottomR),
            control: CGPoint(x: rect.maxX - topR, y: rect.maxY)
        )

        // Right side straight up
        path.addLine(
            to: CGPoint(x: rect.maxX - topR, y: rect.minY + topR)
        )

        // Top-right quad curve (ear)
        path.addQuadCurve(
            to: CGPoint(x: rect.maxX, y: rect.minY),
            control: CGPoint(x: rect.maxX - topR, y: rect.minY)
        )

        path.closeSubpath()
        return path
    }
}

// MARK: - Presets

extension NotchShape {
    /// Closed/dormant notch — tight, small corners.
    static let closed = NotchShape(topCornerRadius: 6, bottomCornerRadius: 14)

    /// Open/expanded notch — larger, more rounded.
    static let open = NotchShape(topCornerRadius: 19, bottomCornerRadius: 24)

    /// Glanceable/ambient — between closed and open.
    static let glance = NotchShape(topCornerRadius: 10, bottomCornerRadius: 18)
}
