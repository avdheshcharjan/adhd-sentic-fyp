import Cocoa
import SwiftUI

class AppDelegate: NSObject, NSApplicationDelegate {

    // MARK: - Public Properties

    let coordinator = MonitorCoordinator()

    // MARK: - Lifecycle

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Check permissions on launch
        if !Permissions.hasScreenRecording || !Permissions.hasAccessibility {
            // Show onboarding
            NSApp.sendAction(Selector(("showSettingsWindow:")), to: nil, from: nil)
        }

        // Start monitoring if we have permissions
        if Permissions.hasScreenRecording {
            coordinator.startMonitoring()
        }
    }

    func applicationWillTerminate(_ notification: Notification) {
        coordinator.stopMonitoring()
    }
}
