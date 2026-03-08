import Foundation
import Combine

/// Combines ScreenMonitor, BrowserMonitor, and IdleMonitor into a unified
/// 2-second data stream that reports to the Python backend.
class MonitorCoordinator: ObservableObject {

    // MARK: - Published State

    @Published var latestCategory: String = "unknown"
    @Published var latestMetrics: ADHDMetrics = ADHDMetrics()
    @Published var latestIntervention: Intervention? = nil
    @Published var isMonitoring: Bool = false

    // MARK: - Private Properties

    private let screenMonitor = ScreenMonitor()
    private let backendClient = BackendClient()
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Public API

    func startMonitoring() {
        guard !isMonitoring else { return }
        isMonitoring = true

        screenMonitor.start()

        // React to every screen state change from the ScreenMonitor
        screenMonitor.$currentState
            .compactMap { $0 }
            .removeDuplicates { prev, next in
                // Deduplicate: only send if something actually changed
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
        // Extract browser URL if the active app is a browser
        let url: String?
        if BrowserMonitor.isBrowser(bundleIdentifier: state.bundleIdentifier) {
            url = BrowserMonitor.getActiveTabURL(bundleIdentifier: state.bundleIdentifier)
        } else {
            url = nil
        }

        let request = ScreenActivityRequest(
            appName: state.appName,
            windowTitle: state.windowTitle,
            url: url,
            isIdle: IdleMonitor.isIdle,
            timestamp: ISO8601DateFormatter().string(from: Date())
        )

        Task {
            do {
                let response = try await backendClient.reportActivity(request)

                await MainActor.run {
                    self.latestCategory = response.category
                    self.latestMetrics = response.metrics
                    self.latestIntervention = response.intervention
                }

                // Show intervention popup if one was returned
                if let intervention = response.intervention {
                    await MainActor.run {
                        InterventionPopup.show(intervention: intervention) { actionId in
                            self.respondToIntervention(
                                interventionType: intervention.type,
                                actionId: actionId
                            )
                        }
                    }
                }
            } catch {
                // Backend unreachable — silently skip, continue monitoring
                // In production: buffer to SQLite and retry
                print("⚠ Backend unreachable: \(error.localizedDescription)")
            }
        }
    }

    private func respondToIntervention(interventionType: String, actionId: String?) {
        Task {
            try? await backendClient.respondToIntervention(
                interventionId: interventionType,
                actionTaken: actionId ?? "dismissed",
                dismissed: actionId == nil
            )
        }
    }
}
