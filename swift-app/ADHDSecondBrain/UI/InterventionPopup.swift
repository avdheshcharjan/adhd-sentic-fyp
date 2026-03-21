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

    private static let panelWidth: CGFloat = 380
    private static let panelHeight: CGFloat = 240

    /// Show an intervention popup.
    /// - Parameters:
    ///   - intervention: The intervention data from the backend
    ///   - onAction: Callback with the selected action ID, or nil if dismissed
    static func show(intervention: Intervention, onAction: @escaping (String?) -> Void) {
        // Dismiss any existing popup
        dismiss()

        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: panelWidth, height: panelHeight),
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
            let panelX = screenFrame.maxX - panelWidth - 20
            let panelY = screenFrame.maxY - panelHeight - 20
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

/// The visual content of the intervention popup, matching the Paper canvas exactly.
struct InterventionCardView: View {
    let intervention: Intervention
    let onAction: (String) -> Void
    let onDismiss: () -> Void

    var body: some View {
        ZStack(alignment: .top) {
            // Card background
            RoundedRectangle(cornerRadius: 16)
                .fill(ADHDColors.Background.secondary)
                // Outer drop shadow
                .shadow(color: Color.black.opacity(0.5), radius: 48, x: 0, y: 16)
                // Inset border simulated via overlay — SwiftUI has no native inset shadow
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .strokeBorder(Color.white.opacity(0.06), lineWidth: 1)
                )

            // Card content
            VStack(alignment: .leading, spacing: 16) {
                // 1. Title + body group
                VStack(alignment: .leading, spacing: 6) {
                    Text(intervention.acknowledgment)
                        .font(Font.custom("Lexend-SemiBold", size: 17))
                        .foregroundColor(ADHDColors.Text.primary)
                        .lineSpacing(24 - 17) // line-height 24px → leading = 24 − 17 = 7
                        .fixedSize(horizontal: false, vertical: true)

                    Text(intervention.suggestion)
                        .font(Font.custom("Lexend-Regular", size: 13))
                        .foregroundColor(ADHDColors.Text.secondary)
                        .lineSpacing(20 - 13) // line-height 20px → leading = 20 − 13 = 7
                        .fixedSize(horizontal: false, vertical: true)
                }

                // 2. Action buttons
                HStack(spacing: 8) {
                    ForEach(intervention.actions) { action in
                        Button {
                            onAction(action.id)
                        } label: {
                            Text(action.label)
                                .font(Font.custom("Lexend-Medium", size: 13))
                                .foregroundColor(ADHDColors.Accent.focusLight)
                                .padding(.vertical, 8)
                                .padding(.horizontal, 16)
                                .background(
                                    ADHDColors.Accent.focusLight.opacity(0.1),
                                    in: Capsule()
                                )
                        }
                        .buttonStyle(.plain)
                    }
                }

                // 3. "Not now" dismiss — right-aligned
                HStack {
                    Spacer()
                    Button("Not now") {
                        onDismiss()
                    }
                    .font(Font.custom("Lexend-Regular", size: 12))
                    .foregroundColor(ADHDColors.Text.tertiary)
                    .buttonStyle(.plain)
                }
            }
            .padding(24)

            // Top accent bar: 3px warm amber gradient, absolute at top
            GeometryReader { geometry in
                LinearGradient(
                    colors: [ADHDColors.Accent.warmth, ADHDColors.Accent.warmth.opacity(0)],
                    startPoint: .leading,
                    endPoint: .trailing
                )
                .frame(height: 3)
                .clipShape(
                    // Only round the top two corners to align with the card
                    UnevenRoundedRectangle(
                        topLeadingRadius: 16,
                        bottomLeadingRadius: 0,
                        bottomTrailingRadius: 0,
                        topTrailingRadius: 16
                    )
                )
                // Stretch to card width
                .frame(width: geometry.size.width)
            }
            .frame(height: 3)
        }
        .frame(width: 380)
    }
}

// MARK: - UnevenRoundedRectangle back-compat

/// Availability shim: UnevenRoundedRectangle requires macOS 13+.
/// The project targets macOS 13+ (Ventura) per the Notch Island feature set,
/// so this is safe. Throw at compile time if that ever changes.
@available(macOS 13.0, *)
private typealias _UnevenRoundedRectangle = UnevenRoundedRectangle
