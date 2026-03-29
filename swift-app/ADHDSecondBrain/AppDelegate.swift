import Cocoa
import SwiftUI
import UserNotifications
import KeyboardShortcuts

@MainActor
class AppDelegate: NSObject, NSApplicationDelegate {

    // MARK: - Public Properties

    let coordinator = MonitorCoordinator()

    // MARK: - Private Properties

    private var permissionTimer: Timer?
    private var notchWindow: NotchWindow?
    private var notchCoordinator: NotchCoordinator?
    private var keyboardManager: KeyboardShortcutManager?
    private var panelManager: FloatingPanelManager?
    // HoverTracker removed: hover is handled entirely by NotchContainerView's
    // .onHover with 0.3s dwell/collapse delays. The dual system caused conflicts.

    // MARK: - Lifecycle

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Register UserDefaults defaults
        UserDefaults.standard.register(defaults: [
            "offTaskAlerts": true,
            "offTaskAlertsAlways": false,
        ])

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

        // Set up ambient menu bar indicator (Tier 1/2 notifications)
        AmbientMenuBar.shared.setup()

        // Start the tier manager tick loop
        TierManager.shared.start()

        // Set up floating panel manager and global hotkeys
        setupFloatingPanels()

        // Launch the Notch Island widget
        setupNotchIsland()
    }

    func applicationWillTerminate(_ notification: Notification) {
        permissionTimer?.invalidate()
        coordinator.stopMonitoring()
        TierManager.shared.stop()
        panelManager = nil
        teardownNotchIsland()
    }

    // MARK: - Floating Panel Setup

    private func setupFloatingPanels() {
        let manager = FloatingPanelManager()
        self.panelManager = manager

        KeyboardShortcuts.onKeyUp(for: .brainDump) { [weak manager] in
            manager?.toggleBrainDump()
        }

        KeyboardShortcuts.onKeyUp(for: .ventModal) { [weak manager] in
            manager?.toggleVentModal()
        }

        KeyboardShortcuts.onKeyUp(for: .taskCreation) { [weak manager] in
            manager?.toggleTaskCreation()
        }

        // Intervention action observers — open modals from JITAI intervention buttons
        NotificationCenter.default.addObserver(forName: .openBrainDump, object: nil, queue: .main) { [weak manager] _ in
            manager?.toggleBrainDump()
        }
        NotificationCenter.default.addObserver(forName: .openVentModal, object: nil, queue: .main) { [weak manager] _ in
            manager?.toggleVentModal()
        }
        NotificationCenter.default.addObserver(forName: .openTaskCreation, object: nil, queue: .main) { [weak manager] _ in
            manager?.toggleTaskCreation()
        }
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
            },
            onCapture: { [weak notchCoord] text in
                notchCoord?.sendCapture(text)
            },
            onCompleteTask: { [weak notchCoord] id in
                notchCoord?.completeTask(id)
            },
            onAcknowledgeIntervention: { [weak notchCoord] id in
                notchCoord?.acknowledgeIntervention(id)
            },
            onToggleFocus: { [weak notchCoord] in
                notchCoord?.toggleFocus()
            }
        )

        // NSHostingView with no manual constraints (DynamicNotchKit pattern).
        // Setting it as contentView lets AppKit manage the frame automatically.
        let hostingView = NSHostingView(rootView: containerView)

        let window = NotchWindow(contentView: hostingView)
        // Click-away: clicks on the transparent canvas around the notch close expanded panel
        window.onClickAway = { [weak notchCoord] in
            guard let sm = notchCoord?.stateMachine,
                  sm.currentState == .expanded else { return }
            sm.transition(to: .glanceable)
        }
        // Update window hit-test region when notch state changes
        notchCoord.stateMachine.onStateChange = { [weak window] state in
            window?.visibleContentSize = NotchWindow.contentSize(for: state)
        }

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

        // Wire task creation modal → notch coordinator
        panelManager?.onTaskCreated = { [weak notchCoord] name, duration in
            notchCoord?.createTaskAndStartFocus(name: name, duration: duration)
        }

        // Hover is handled by NotchContainerView's .onHover modifier
    }

    private func teardownNotchIsland() {
        notchCoordinator?.stop()
        keyboardManager?.unregister()
        // HoverTracker removed — hover handled by SwiftUI
        notchWindow?.close()
    }
}
