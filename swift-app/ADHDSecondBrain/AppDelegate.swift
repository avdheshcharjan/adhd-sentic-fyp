import Cocoa
import SwiftUI
import UserNotifications

class AppDelegate: NSObject, NSApplicationDelegate {

    // MARK: - Public Properties

    let coordinator = MonitorCoordinator()

    // MARK: - Private Properties

    private var permissionTimer: Timer?

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
    }

    func applicationWillTerminate(_ notification: Notification) {
        permissionTimer?.invalidate()
        coordinator.stopMonitoring()
        TierManager.shared.stop()
    }
}
