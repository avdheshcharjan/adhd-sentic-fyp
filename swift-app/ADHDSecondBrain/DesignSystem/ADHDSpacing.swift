import AppKit
import Foundation

enum ADHDSpacing {
    static let xxs: CGFloat = 2
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 12
    static let lg: CGFloat = 16
    static let xl: CGFloat = 24
    static let xxl: CGFloat = 32
    static let xxxl: CGFloat = 48

    // Notch-specific — hardware-aware dimensions
    static let notchPaddingH: CGFloat = 12
    static let notchPaddingV: CGFloat = 8
    static let notchCornerRadius: CGFloat = 16
    static let notchExpandedWidth: CGFloat = 380
    static let notchExpandedHeight: CGFloat = 280
    static let notchGlanceWidth: CGFloat = 300
    static let notchGlanceHeight: CGFloat = 44

    /// Hardware notch height from the primary screen's safe area insets.
    /// On 14"/16" MBP and M2+ Air this is ~37pt (74px at 2x).
    /// Falls back to 37 if no notch detected but we still want the overlay.
    static var hardwareNotchHeight: CGFloat {
        let insetTop = NSScreen.screens.first?.safeAreaInsets.top ?? 0
        return insetTop > 0 ? insetTop : 37
    }

    /// Hardware notch width — Apple doesn't expose this directly.
    /// Measured value: ~180pt on all current notch Macs.
    static let hardwareNotchWidth: CGFloat = 180

    // Card layout
    static let cardCornerRadius: CGFloat = 12
    static let cardPadding: CGFloat = 12 // =30 hacky solution for padding issue
    static let cardSpacing: CGFloat = 8
}
