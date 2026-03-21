import Cocoa
import SwiftUI
import UserNotifications

class AppDelegate: NSObject, NSApplicationDelegate {

    // MARK: - Public Properties

    let coordinator = MonitorCoordinator()

    // MARK: - Private Properties

    private var permissionTimer: Timer?
    private var notchWindow: NotchWindow?
    private var notchCoordinator: NotchCoordinator?
    private var keyboardManager: KeyboardShortcutManager?
    // HoverTracker removed: hover is handled entirely by NotchContainerView's
    // .onHover with 0.3s dwell/collapse delays. The dual system caused conflicts.

    // MARK: - Lifecycle

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Request notification permissions for Tier 4-5
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }

        // Start monitoring if we already have Accessibility permission
        if Permissions.hasAccessibility {
            coordinator.startMonitoring()
        } else {
            // Poll for permission grant so monitoring starts as soon as the user enables it
            permissionTimer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { [weak self] timer in
                guard let self else { return }
                if Permissions.hasAccessibility {
                    timer.invalidate()
                    self.permissionTimer = nil
                    self.coordinator.startMonitoring()
                }
            }
        }

        // Start the tier manager tick loop
        TierManager.shared.start()

        // Launch the Notch Island widget
        setupNotchIsland()
    }

    func applicationWillTerminate(_ notification: Notification) {
        permissionTimer?.invalidate()
        coordinator.stopMonitoring()
        TierManager.shared.stop()
        teardownNotchIsland()
    }

    // MARK: - Notch Island Setup

    private func setupNotchIsland() {
        let notchCoord = NotchCoordinator()
        self.notchCoordinator = notchCoord

        let containerView = NotchContainerView(
            stateMachine: notchCoord.stateMachine,
            viewModel: notchCoord.viewModel,
            onConnectCalendar: { [weak notchCoord] in
                notchCoord?.openGoogleCalendarAuth()
            }
        )

        // NSHostingView with no manual constraints (DynamicNotchKit pattern).
        // Setting it as contentView lets AppKit manage the frame automatically.
        let hostingView = NSHostingView(rootView: containerView)

        let window = NotchWindow(contentView: hostingView)
        window.showWithFade()
        self.notchWindow = window

        // Start data polling
        notchCoord.start()

        // Keyboard shortcuts
        let kbd = KeyboardShortcutManager(
            stateMachine: notchCoord.stateMachine
        )
        kbd.register()
        self.keyboardManager = kbd

        // Hover is handled by NotchContainerView's .onHover modifier
    }

    private func teardownNotchIsland() {
        notchCoordinator?.stop()
        keyboardManager?.unregister()
        // HoverTracker removed — hover handled by SwiftUI
        notchWindow?.close()
    }
}
