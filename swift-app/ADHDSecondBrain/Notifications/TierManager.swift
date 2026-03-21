import Cocoa
import UserNotifications

/// Orchestrates the 5-tier calm notification architecture.
///
/// Tier 1: Ambient color shift on menu bar icon (user may not notice)
/// Tier 2: Gentle pulse animation on menu bar icon
/// Tier 3: Non-activating overlay panel (doesn't steal focus)
/// Tier 4: Toast notification with optional sound
/// Tier 5: Full notification (reserved for safety + hard deadlines only)
///
/// Anti-pattern #9: NEVER deliver more than 3 interventions per 90-minute block.
@MainActor
class TierManager {
    static let shared = TierManager()

    // MARK: - State

    private var queuedIntervention: Intervention?
    private var queuedSince: Date?
    private var onAction: ((String) -> Void)?
    private var onDismiss: (() -> Void)?

    /// Maximum time an intervention stays queued before being downgraded/discarded
    private let maxQueueTime: TimeInterval = 300 // 5 minutes

    private var tickTimer: Timer?

    // MARK: - Public API

    func start() {
        tickTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.tick()
        }
    }

    func stop() {
        tickTimer?.invalidate()
        tickTimer = nil
        queuedIntervention = nil
        queuedSince = nil
    }

    /// Queue an intervention for delivery at the next breakpoint.
    /// Immediately shows Tier 1 (ambient color) as a passive indicator.
    func queue(
        _ intervention: Intervention,
        onAction: @escaping (String) -> Void,
        onDismiss: @escaping () -> Void
    ) {
        self.queuedIntervention = intervention
        self.queuedSince = Date()
        self.onAction = onAction
        self.onDismiss = onDismiss

        // Start ambient indicator immediately (Tier 1)
        let color = AmbientMenuBar.color(forTier: intervention.notificationTier ?? 1)
        AmbientMenuBar.shared.setIndicator(color: color, pulse: false)
    }

    /// Deliver the queued intervention immediately (called when a breakpoint is detected).
    func deliverIfQueued() {
        guard let intervention = queuedIntervention,
              let onAction = onAction,
              let onDismiss = onDismiss else { return }

        let tier = intervention.notificationTier ?? 3

        switch tier {
        case 1:
            // Already showing via ambient color — just keep it
            let color = AmbientMenuBar.color(forTier: 1)
            AmbientMenuBar.shared.setIndicator(color: color, pulse: false)

        case 2:
            // Add pulse animation to menu bar icon
            let color = AmbientMenuBar.color(forTier: 2)
            AmbientMenuBar.shared.setIndicator(color: color, pulse: true)

        case 3:
            // Non-activating overlay panel (CalmOverlayPanel)
            CalmOverlayPanel.shared.show(
                intervention: intervention,
                onAction: { actionId in
                    onAction(actionId)
                    AmbientMenuBar.shared.clear()
                },
                onDismiss: {
                    onDismiss()
                    AmbientMenuBar.shared.clear()
                }
            )

        case 4:
            // System toast notification
            sendUserNotification(intervention: intervention)
            AmbientMenuBar.shared.clear()

        case 5:
            // Full notification — safety critical only
            CalmOverlayPanel.shared.show(
                intervention: intervention,
                onAction: { actionId in
                    onAction(actionId)
                    AmbientMenuBar.shared.clear()
                },
                onDismiss: {
                    onDismiss()
                    AmbientMenuBar.shared.clear()
                }
            )
            sendUserNotification(intervention: intervention)

        default:
            break
        }

        clearQueue()
    }

    /// Deliver an intervention immediately without queueing (for breakpoint-coincident delivery).
    func deliver(
        _ intervention: Intervention,
        onAction: @escaping (String) -> Void,
        onDismiss: @escaping () -> Void
    ) {
        self.queuedIntervention = intervention
        self.queuedSince = Date()
        self.onAction = onAction
        self.onDismiss = onDismiss
        deliverIfQueued()
    }

    // MARK: - Private

    /// Called every second — handles timeout upgrades and downgrades.
    private func tick() {
        guard let queuedSince = queuedSince, queuedIntervention != nil else { return }

        let elapsed = Date().timeIntervalSince(queuedSince)

        // After 2 minutes queued, upgrade to gentle pulse (Tier 2)
        if elapsed > 120 {
            let color = AmbientMenuBar.color(forTier: 2)
            AmbientMenuBar.shared.setIndicator(color: color, pulse: true)
        }

        // After 5 minutes queued with no breakpoint, downgrade to ambient-only
        // and clear the queue (the moment passed)
        if elapsed > maxQueueTime {
            AmbientMenuBar.shared.clear()
            onDismiss?()
            clearQueue()
        }
    }

    private func clearQueue() {
        queuedIntervention = nil
        queuedSince = nil
        onAction = nil
        onDismiss = nil
    }

    /// Send a macOS user notification (Tier 4-5).
    private func sendUserNotification(intervention: Intervention) {
        let content = UNMutableNotificationContent()
        content.title = "ADHD Second Brain"
        content.subtitle = intervention.acknowledgment
        content.body = intervention.suggestion
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: content,
            trigger: nil
        )

        UNUserNotificationCenter.current().add(request)
    }
}
