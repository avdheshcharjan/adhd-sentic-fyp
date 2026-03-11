import Cocoa
import ApplicationServices
import Combine

/// Monitors the frontmost application and window title using Accessibility API only.
///
/// CRITICAL DESIGN DECISION (supplement Section 2):
/// Uses AXUIElement (Accessibility API) instead of CGWindowListCopyWindowInfo (Screen Recording).
/// This removes the Screen Recording permission entirely — the app now needs ONLY
/// Accessibility permission, which does NOT have monthly re-authorization on Sequoia.
///
/// Anti-pattern #6: NEVER use Screen Recording permission for core monitoring.
class ScreenMonitor: ObservableObject {

    // MARK: - Published State

    struct ScreenState: Equatable {
        let appName: String
        let windowTitle: String
        let bundleIdentifier: String?
    }

    @Published private(set) var currentState: ScreenState?
    @Published private(set) var previousApp: String = ""

    // MARK: - Private Properties

    private var workspaceObserver: Any?
    private var axObserver: AXObserver?
    private var currentPID: pid_t = 0

    // MARK: - Callbacks

    /// Called when an app switch occurs (from → to)
    var onAppSwitch: ((String, String) -> Void)?

    // MARK: - Public API

    func start() {
        // 1. App switch detection — event-driven, zero CPU cost
        //    REQUIRES: Nothing (NSWorkspace is public API)
        workspaceObserver = NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification,
            object: nil,
            queue: .main
        ) { [weak self] notification in
            guard let app = notification.userInfo?[NSWorkspace.applicationUserInfoKey]
                    as? NSRunningApplication else { return }
            self?.handleAppSwitch(app)
        }

        // 2. Capture initial state + set up AX observer for title changes
        if let frontApp = NSWorkspace.shared.frontmostApplication {
            handleAppSwitch(frontApp)
        }
    }

    func stop() {
        if let observer = workspaceObserver {
            NSWorkspace.shared.notificationCenter.removeObserver(observer)
            workspaceObserver = nil
        }
        removeAXObserver()
    }

    // MARK: - App Switch Handling

    private func handleAppSwitch(_ app: NSRunningApplication) {
        let appName = app.localizedName ?? "Unknown"
        let oldApp = currentState?.appName ?? ""

        // Notify about the app switch
        if !oldApp.isEmpty && oldApp != appName {
            previousApp = oldApp
            onAppSwitch?(oldApp, appName)
        }

        // Re-attach AX observer to new app's PID
        let pid = app.processIdentifier
        if pid != currentPID {
            currentPID = pid
            removeAXObserver()
            setupAXObserver(for: pid)
        }

        // Capture window title via AX API
        let title = getWindowTitle(for: pid)
        let state = ScreenState(
            appName: appName,
            windowTitle: title,
            bundleIdentifier: app.bundleIdentifier
        )

        DispatchQueue.main.async {
            self.currentState = state
        }
    }

    // MARK: - AX Observer (Window Title Changes)

    /// Sets up an AXObserver to get notified when the focused window's title changes.
    /// This fires when switching browser tabs, changing document titles, etc.
    /// REQUIRES: Accessibility permission ONLY (no monthly re-auth on Sequoia)
    private func setupAXObserver(for pid: pid_t) {
        var observer: AXObserver?

        // The callback must be a C function pointer — use a static context
        let callback: AXObserverCallback = { (_, element, notification, refcon) in
            guard let refcon = refcon else { return }
            let monitor = Unmanaged<ScreenMonitor>.fromOpaque(refcon).takeUnretainedValue()
            monitor.handleAXTitleChange()
        }

        guard AXObserverCreate(pid, callback, &observer) == .success,
              let observer = observer else { return }

        let appElement = AXUIElementCreateApplication(pid)
        let refcon = Unmanaged.passUnretained(self).toOpaque()

        // Watch for title changes and focused window changes
        AXObserverAddNotification(observer, appElement,
                                  kAXFocusedWindowChangedNotification as CFString, refcon)
        AXObserverAddNotification(observer, appElement,
                                  kAXTitleChangedNotification as CFString, refcon)

        CFRunLoopAddSource(CFRunLoopGetCurrent(),
                           AXObserverGetRunLoopSource(observer),
                           .defaultMode)
        self.axObserver = observer
    }

    private func removeAXObserver() {
        if let observer = axObserver {
            CFRunLoopRemoveSource(CFRunLoopGetCurrent(),
                                  AXObserverGetRunLoopSource(observer),
                                  .defaultMode)
            axObserver = nil
        }
    }

    private func handleAXTitleChange() {
        let title = getWindowTitle(for: currentPID)
        guard let current = currentState, title != current.windowTitle else { return }

        let state = ScreenState(
            appName: current.appName,
            windowTitle: title,
            bundleIdentifier: current.bundleIdentifier
        )

        DispatchQueue.main.async {
            self.currentState = state
        }
    }

    // MARK: - AX Title Extraction

    /// Reads the frontmost window title using AXUIElement (Accessibility API).
    /// No Screen Recording permission needed.
    private func getWindowTitle(for pid: pid_t) -> String {
        let appElement = AXUIElementCreateApplication(pid)

        // Get the focused window
        var focusedWindow: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(
            appElement,
            kAXFocusedWindowAttribute as CFString,
            &focusedWindow
        )

        guard result == .success, let window = focusedWindow else {
            return ""
        }

        // Get the window title
        var titleValue: CFTypeRef?
        AXUIElementCopyAttributeValue(
            window as! AXUIElement,
            kAXTitleAttribute as CFString,
            &titleValue
        )

        return titleValue as? String ?? ""
    }

    deinit {
        stop()
    }
}
