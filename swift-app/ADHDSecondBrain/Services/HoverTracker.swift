import AppKit

/// Tracks mouse movement near the notch area to trigger
/// ambient → glanceable transitions.
class HoverTracker {

    private var eventMonitor: Any?
    private weak var stateMachine: NotchStateMachine?

    init(stateMachine: NotchStateMachine) {
        self.stateMachine = stateMachine
    }

    func start() {
        eventMonitor = NSEvent.addGlobalMonitorForEvents(
            matching: .mouseMoved
        ) { [weak self] event in
            self?.handleMouseMoved(event)
        }
    }

    func stop() {
        if let monitor = eventMonitor {
            NSEvent.removeMonitor(monitor)
            eventMonitor = nil
        }
    }

    private func handleMouseMoved(_ event: NSEvent) {
        guard let screen = NSScreen.main,
              let sm = stateMachine else { return }

        let geo = NotchPositionCalculator.geometry(for: screen)
        let mouseLocation = NSEvent.mouseLocation

        let notchRect = NSRect(
            x: geo.origin.x - 20,
            y: geo.origin.y - 10,
            width: geo.notchWidth + 40,
            height: geo.notchHeight + 20
        )

        let isNearNotch = notchRect.contains(mouseLocation)

        if isNearNotch && sm.currentState == .dormant {
            sm.transition(to: .ambient)
        }
    }
}
