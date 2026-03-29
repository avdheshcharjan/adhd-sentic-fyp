import AppKit

struct NotchGeometry {
    let origin: CGPoint
    let notchWidth: CGFloat
    let notchHeight: CGFloat
    let hasHardwareNotch: Bool
}

enum NotchPositionCalculator {

    /// Detects notch geometry on the given screen.
    /// Falls back to a simulated notch region for non-notch displays.
    static func geometry(for screen: NSScreen) -> NotchGeometry {
        let frame = screen.frame
        let safeArea = screen.safeAreaInsets

        let hasNotch = safeArea.top > 0
        let notchWidth: CGFloat = ADHDSpacing.hardwareNotchWidth
        let notchHeight: CGFloat = hasNotch ? safeArea.top : ADHDSpacing.hardwareNotchHeight

        let x = frame.midX - (notchWidth / 2)
        let y = frame.maxY - notchHeight

        return NotchGeometry(
            origin: CGPoint(x: x, y: y),
            notchWidth: notchWidth,
            notchHeight: notchHeight,
            hasHardwareNotch: hasNotch
        )
    }

    /// Returns the frame for the notch window at its default (dormant) size.
    static func dormantFrame(for screen: NSScreen) -> NSRect {
        let geo = geometry(for: screen)
        return NSRect(
            x: geo.origin.x,
            y: geo.origin.y,
            width: geo.notchWidth,
            height: geo.notchHeight
        )
    }

    /// Returns a centered frame at the top of the screen for expanded states.
    static func expandedFrame(
        for screen: NSScreen,
        width: CGFloat,
        height: CGFloat
    ) -> NSRect {
        let frame = screen.frame
        let x = frame.midX - (width / 2)
        let y = frame.maxY - height
        return NSRect(x: x, y: y, width: width, height: height)
    }
}
