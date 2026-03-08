import SwiftUI
import AppKit

/// Non-modal, non-focus-stealing intervention popup.
///
/// ADHD UX principles:
/// - Max 2–3 sentences (working memory deficits)
/// - 2–3 action buttons (decision fatigue)
/// - Slides in from top-right, never steals focus
/// - Auto-dismisses after 15 seconds
/// - "Not now" triggers cooldown
class InterventionPopup {

    private static var currentPanel: NSPanel?
    private static var dismissTimer: Timer?

    /// Show an intervention popup.
    /// - Parameters:
    ///   - intervention: The intervention data from the backend
    ///   - onAction: Callback with the selected action ID, or nil if dismissed
    static func show(intervention: Intervention, onAction: @escaping (String?) -> Void) {
        // Dismiss any existing popup
        dismiss()

        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 360, height: 240),
            styleMask: [.nonactivatingPanel, .titled, .closable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )

        panel.isFloatingPanel = true
        panel.level = .floating
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.isMovableByWindowBackground = true
        panel.titlebarAppearsTransparent = true
        panel.titleVisibility = .hidden
        panel.backgroundColor = .clear

        // Position: top-right corner with padding
        if let screen = NSScreen.main {
            let screenFrame = screen.visibleFrame
            let panelX = screenFrame.maxX - 360 - 20
            let panelY = screenFrame.maxY - 240 - 20
            panel.setFrameOrigin(NSPoint(x: panelX, y: panelY))
        }

        let contentView = InterventionCardView(
            intervention: intervention,
            onAction: { actionId in
                onAction(actionId)
                dismiss()
            },
            onDismiss: {
                onAction(nil)
                dismiss()
            }
        )

        panel.contentView = NSHostingView(rootView: contentView)
        panel.orderFrontRegardless()
        currentPanel = panel

        // Slide-in animation
        panel.alphaValue = 0
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.3
            panel.animator().alphaValue = 1
        }

        // Auto-dismiss after 15 seconds
        dismissTimer = Timer.scheduledTimer(withTimeInterval: 15, repeats: false) { _ in
            onAction(nil)
            dismiss()
        }
    }

    static func dismiss() {
        dismissTimer?.invalidate()
        dismissTimer = nil

        if let panel = currentPanel {
            NSAnimationContext.runAnimationGroup({ context in
                context.duration = 0.2
                panel.animator().alphaValue = 0
            }, completionHandler: {
                panel.close()
            })
            currentPanel = nil
        }
    }
}

// MARK: - SwiftUI Card View

/// The visual content of the intervention popup.
struct InterventionCardView: View {
    let intervention: Intervention
    let onAction: (String) -> Void
    let onDismiss: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Acknowledgment
            Text(intervention.acknowledgment)
                .font(.system(.body, design: .rounded))
                .foregroundColor(.primary)
                .lineLimit(3)

            // Suggestion
            Text(intervention.suggestion)
                .font(.system(.callout, design: .rounded))
                .foregroundColor(.secondary)
                .lineLimit(2)

            // Action Buttons
            HStack(spacing: 10) {
                ForEach(intervention.actions) { action in
                    Button {
                        onAction(action.id)
                    } label: {
                        HStack(spacing: 4) {
                            Text(action.emoji)
                            Text(action.label)
                                .font(.caption.bold())
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 8))
                    }
                    .buttonStyle(.plain)
                }
            }

            // Dismiss
            HStack {
                Spacer()
                Button("Not now") {
                    onDismiss()
                }
                .font(.caption)
                .foregroundColor(.secondary)
                .buttonStyle(.plain)
            }
        }
        .padding(20)
        .frame(width: 340)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(.ultraThickMaterial)
                .shadow(color: .black.opacity(0.2), radius: 20, y: 10)
        )
    }
}
