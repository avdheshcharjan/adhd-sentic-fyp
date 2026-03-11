import Cocoa

/// Ambient menu bar icon that shifts color and pulses to indicate focus state.
///
/// Color meanings (warm spectrum — anti-pattern #10: NEVER use blue):
/// - Green: focused / in the zone
/// - Yellow-green: mild drift detected
/// - Amber: moderate distraction
/// - Orange: sustained off-task
/// - Red: safety concern only
///
/// Tier 1: Color shift only (user may not notice)
/// Tier 2: Gentle pulse animation added
class AmbientMenuBar {
    static let shared = AmbientMenuBar()

    private var statusItem: NSStatusItem?
    private var pulseTimer: Timer?
    private var currentColor: NSColor = .systemGreen

    func setup(statusItem: NSStatusItem) {
        self.statusItem = statusItem
        setIndicator(color: .systemGreen, pulse: false)
    }

    /// Update the menu bar icon color and optional pulse.
    /// - Parameters:
    ///   - color: The indicator color (warm spectrum only)
    ///   - pulse: Whether to animate a pulse (Tier 2)
    func setIndicator(color: NSColor, pulse: Bool) {
        currentColor = color
        updateIcon(color: color)

        pulseTimer?.invalidate()
        pulseTimer = nil

        if pulse {
            pulseTimer = Timer.scheduledTimer(withTimeInterval: 1.5, repeats: true) { [weak self] _ in
                self?.animatePulse()
            }
        }
    }

    /// Clear all indicators (return to default state).
    func clear() {
        setIndicator(color: .systemGreen, pulse: false)
    }

    // MARK: - Convenience Colors

    /// Color for an intervention's urgency level.
    static func color(forTier tier: Int) -> NSColor {
        switch tier {
        case 1: return .systemYellow       // Ambient awareness
        case 2: return .systemOrange       // Gentle alert
        case 3: return .systemOrange       // Overlay
        case 4, 5: return .systemRed       // Urgent / safety
        default: return .systemGreen       // All clear
        }
    }

    // MARK: - Private

    private func updateIcon(color: NSColor) {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size, flipped: false) { rect in
            // Draw brain-shaped circle with indicator color
            color.setFill()
            let circle = NSBezierPath(ovalIn: rect.insetBy(dx: 3, dy: 3))
            circle.fill()
            return true
        }
        image.isTemplate = false // Use actual colors, not system tinting
        statusItem?.button?.image = image
    }

    private func animatePulse() {
        guard let button = statusItem?.button else { return }
        NSAnimationContext.runAnimationGroup({ ctx in
            ctx.duration = 0.75
            button.animator().alphaValue = 0.4
        }, completionHandler: {
            NSAnimationContext.runAnimationGroup({ ctx in
                ctx.duration = 0.75
                button.animator().alphaValue = 1.0
            })
        })
    }
}
