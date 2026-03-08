import Cocoa
import Combine

/// Monitors the frontmost application and window title using NSWorkspace notifications
/// and CGWindowList polling every 2 seconds.
class ScreenMonitor: ObservableObject {

    // MARK: - Published State

    struct ScreenState {
        let appName: String
        let windowTitle: String
        let bundleIdentifier: String?
    }

    @Published private(set) var currentState: ScreenState?

    // MARK: - Private Properties

    private var pollingTimer: Timer?
    private var workspaceObserver: Any?

    // MARK: - Public API

    func start() {
        // Event-driven: observe app switches (zero CPU when idle)
        workspaceObserver = NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification,
            object: nil,
            queue: .main
        ) { [weak self] notification in
            self?.captureCurrentState()
        }

        // Polling: capture window title changes every 2 seconds
        // (tab switches in browsers don't trigger app switch notifications)
        pollingTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { [weak self] _ in
            self?.captureCurrentState()
        }

        // Capture initial state
        captureCurrentState()
    }

    func stop() {
        pollingTimer?.invalidate()
        pollingTimer = nil

        if let observer = workspaceObserver {
            NSWorkspace.shared.notificationCenter.removeObserver(observer)
            workspaceObserver = nil
        }
    }

    // MARK: - Private Methods

    /// Captures the current frontmost app and window title.
    /// Uses CGWindowListCopyWindowInfo which requires Screen Recording permission.
    private func captureCurrentState() {
        guard let frontApp = NSWorkspace.shared.frontmostApplication else { return }

        let appName = frontApp.localizedName ?? "Unknown"
        let bundleId = frontApp.bundleIdentifier
        let windowTitle = getFrontmostWindowTitle(for: frontApp.processIdentifier) ?? ""

        let state = ScreenState(
            appName: appName,
            windowTitle: windowTitle,
            bundleIdentifier: bundleId
        )

        DispatchQueue.main.async {
            self.currentState = state
        }
    }

    /// Reads the frontmost window title using CGWindowListCopyWindowInfo.
    /// Returns nil if Screen Recording permission is not granted.
    private func getFrontmostWindowTitle(for pid: pid_t) -> String? {
        let options: CGWindowListOption = [.optionOnScreenOnly, .excludeDesktopElements]
        guard let windowList = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] else {
            return nil
        }

        // Find the frontmost window belonging to this application
        for window in windowList {
            guard let ownerPID = window[kCGWindowOwnerPID as String] as? pid_t,
                  ownerPID == pid,
                  let layer = window[kCGWindowLayer as String] as? Int,
                  layer == 0 // Normal window layer
            else { continue }

            return window[kCGWindowName as String] as? String
        }

        return nil
    }

    deinit {
        stop()
    }
}
