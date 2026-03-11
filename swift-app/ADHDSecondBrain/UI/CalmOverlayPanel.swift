import Cocoa
import SwiftUI

/// A floating panel that displays interventions WITHOUT stealing keyboard focus.
///
/// Tier 3 in the 5-tier calm notification architecture (supplement Section 5.3).
/// The user's cursor stays in their current app. They can glance at the panel
/// and either click an action or ignore it entirely.
///
/// Uses NSPanel with .nonactivatingPanel style mask so it doesn't steal focus.
class CalmOverlayPanel {
    static let shared = CalmOverlayPanel()

    private var panel: NSPanel?
    private var dismissTimer: Timer?

    /// Show an intervention as a non-activating overlay.
    /// - Parameters:
    ///   - intervention: The intervention to display
    ///   - onAction: Called when user taps an action button
    ///   - onDismiss: Called when user dismisses or panel auto-dismisses
    func show(
        intervention: Intervention,
        onAction: @escaping (String) -> Void,
        onDismiss: @escaping () -> Void
    ) {
        dismiss()

        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 360, height: 200),
            styleMask: [.nonactivatingPanel, .titled, .closable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )

        // CRITICAL: These flags prevent focus stealing
        panel.level = .floating
        panel.isFloatingPanel = true
        panel.becomesKeyOnlyIfNeeded = true
        panel.hidesOnDeactivate = false
        panel.collectionBehavior = [.canJoinAllSpaces, .transient]
        panel.titlebarAppearsTransparent = true
        panel.titleVisibility = .hidden
        panel.backgroundColor = .clear
        panel.isMovableByWindowBackground = true

        // Position: top-right corner, below menu bar
        if let screen = NSScreen.main {
            let screenFrame = screen.visibleFrame
            panel.setFrameOrigin(NSPoint(
                x: screenFrame.maxX - 376,
                y: screenFrame.maxY - 216
            ))
        }

        let contentView = InterventionCardView(
            intervention: intervention,
            onAction: { [weak self] actionId in
                onAction(actionId)
                self?.dismiss()
            },
            onDismiss: { [weak self] in
                onDismiss()
                self?.dismiss()
            }
        )
        panel.contentView = NSHostingView(rootView: contentView)

        // Subtle slide-in animation
        panel.alphaValue = 0
        panel.orderFront(nil)
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.3
            panel.animator().alphaValue = 1.0
        }

        self.panel = panel

        // Auto-dismiss after 15 seconds (ADHD: short attention window)
        // Anti-pattern #8: max 3 action choices, auto-dismiss keeps it brief
        dismissTimer = Timer.scheduledTimer(withTimeInterval: 15.0, repeats: false) { [weak self] _ in
            onDismiss()
            self?.dismiss()
        }
    }

    func dismiss() {
        dismissTimer?.invalidate()
        dismissTimer = nil

        guard let panel = panel else { return }
        NSAnimationContext.runAnimationGroup({ context in
            context.duration = 0.2
            panel.animator().alphaValue = 0
        }, completionHandler: { [weak self] in
            panel.orderOut(nil)
            self?.panel = nil
        })
    }
}
