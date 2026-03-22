import Foundation
import Combine

// MARK: - Intervention Action Notifications

extension Notification.Name {
    static let openBrainDump = Notification.Name("openBrainDump")
    static let openVentModal = Notification.Name("openVentModal")
}

/// Combines ScreenMonitor, BrowserMonitor, IdleMonitor, and TransitionDetector
/// into a unified event-driven data stream that reports to the Python backend.
///
/// Key change from blueprint: Uses TransitionDetector + TierManager for
/// breakpoint-aware intervention delivery (supplement Sections 4 & 5).
class MonitorCoordinator: ObservableObject {

    // MARK: - Published State

    @Published var latestCategory: String = "unknown"
    @Published var latestMetrics: ADHDMetrics = ADHDMetrics()
    @Published var latestIntervention: Intervention? = nil
    @Published var isMonitoring: Bool = false

    // MARK: - Private Properties

    private let screenMonitor = ScreenMonitor()
    private let transitionDetector = TransitionDetector()
    private let backendClient = BackendClient()
    private var cancellables = Set<AnyCancellable>()
    private var wasIdle = false
    private static let iso8601Formatter = ISO8601DateFormatter()

    // MARK: - Public API

    func startMonitoring() {
        guard !isMonitoring else { return }
        isMonitoring = true

        // Wire up app switch notifications from ScreenMonitor to TransitionDetector
        screenMonitor.onAppSwitch = { [weak self] from, to in
            self?.transitionDetector.recordAppSwitch(from: from, to: to)

            // If there's a queued intervention, check if this breakpoint allows delivery
            if self?.transitionDetector.checkBreakpoint() == true {
                Task { @MainActor in
                    TierManager.shared.deliverIfQueued()
                }
            }
        }

        screenMonitor.start()

        // React to every screen state change from the ScreenMonitor
        screenMonitor.$currentState
            .compactMap { $0 }
            .removeDuplicates { prev, next in
                prev.appName == next.appName && prev.windowTitle == next.windowTitle
            }
            .sink { [weak self] state in
                self?.reportActivity(state: state)
            }
            .store(in: &cancellables)
    }

    func stopMonitoring() {
        isMonitoring = false
        screenMonitor.stop()
        cancellables.removeAll()
    }

    func toggleMonitoring() {
        if isMonitoring {
            stopMonitoring()
        } else {
            startMonitoring()
        }
    }

    // MARK: - Private Methods

    private func reportActivity(state: ScreenMonitor.ScreenState) {
        // Track idle transitions for the TransitionDetector
        let currentlyIdle = IdleMonitor.isIdle
        if currentlyIdle && !wasIdle {
            transitionDetector.recordIdleStart()
        } else if !currentlyIdle && wasIdle {
            transitionDetector.recordIdleResume()
            // Idle resume is a breakpoint — try to deliver queued interventions
            if transitionDetector.checkBreakpoint() {
                Task { @MainActor in
                    TierManager.shared.deliverIfQueued()
                }
            }
        }
        wasIdle = currentlyIdle

        // Extract browser URL if the active app is a browser
        let url: String?
        if BrowserMonitor.isBrowser(bundleIdentifier: state.bundleIdentifier) {
            url = BrowserMonitor.getActiveTabURL(bundleIdentifier: state.bundleIdentifier)

            // Record tab switch for burst detection
            if let url = url {
                transitionDetector.recordTabSwitch(urlOrTitle: url)
                // Check for tab burst breakpoint
                if transitionDetector.checkBreakpoint() {
                    Task { @MainActor in
                        TierManager.shared.deliverIfQueued()
                    }
                }
            }
        } else {
            url = nil
        }

        let request = ScreenActivityRequest(
            appName: state.appName,
            windowTitle: state.windowTitle,
            url: url,
            isIdle: currentlyIdle,
            timestamp: Self.iso8601Formatter.string(from: Date())
        )

        Task {
            do {
                let response = try await backendClient.reportActivity(request)

                await MainActor.run {
                    self.latestCategory = response.category
                    self.latestMetrics = response.metrics
                    self.latestIntervention = response.intervention
                }

                // Handle intervention via TierManager + TransitionDetector
                if let intervention = response.intervention {
                    await MainActor.run {
                        self.handleIntervention(intervention)
                    }
                }
            } catch {
                print("Backend unreachable: \(error.localizedDescription)")
            }
        }
    }

    /// Route intervention through TransitionDetector + TierManager.
    /// Anti-pattern #4: NEVER interrupt productive hyperfocus.
    @MainActor
    private func handleIntervention(_ intervention: Intervention) {
        // Hard block: never interrupt deep focus
        if transitionDetector.shouldSuppressIntervention() {
            return
        }

        let actionHandler: (String) -> Void = { [weak self] actionId in
            self?.respondToIntervention(interventionType: intervention.type, actionId: actionId)
        }
        let dismissHandler: () -> Void = { [weak self] in
            self?.respondToIntervention(interventionType: intervention.type, actionId: nil)
        }

        // If we're at a breakpoint, deliver immediately
        if transitionDetector.checkBreakpoint() {
            TierManager.shared.deliver(intervention, onAction: actionHandler, onDismiss: dismissHandler)
        } else {
            // Queue for next breakpoint (shows Tier 1 ambient indicator immediately)
            TierManager.shared.queue(intervention, onAction: actionHandler, onDismiss: dismissHandler)
        }
    }

    private func respondToIntervention(interventionType: String, actionId: String?) {
        // Handle action-specific side effects
        if let actionId {
            switch actionId {
            case "brain_dump":
                NotificationCenter.default.post(name: .openBrainDump, object: nil)
            case "vent":
                NotificationCenter.default.post(name: .openVentModal, object: nil)
            default:
                break
            }
        }

        Task {
            try? await backendClient.respondToIntervention(
                interventionId: interventionType,
                actionTaken: actionId ?? "dismissed",
                dismissed: actionId == nil
            )
        }
    }
}
