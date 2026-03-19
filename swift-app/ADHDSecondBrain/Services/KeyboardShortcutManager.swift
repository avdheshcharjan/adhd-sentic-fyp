import AppKit
import Carbon

/// Registers global hotkeys for the notch widget.
/// Cmd+Shift+N toggles expanded/collapsed.
/// Escape closes expanded panel.
class KeyboardShortcutManager {

    private var eventMonitor: Any?
    private weak var stateMachine: NotchStateMachine?

    init(stateMachine: NotchStateMachine) {
        self.stateMachine = stateMachine
    }

    func register() {
        eventMonitor = NSEvent.addLocalMonitorForEvents(
            matching: .keyDown
        ) { [weak self] event in
            self?.handleKeyDown(event) ?? event
        }
    }

    func unregister() {
        if let monitor = eventMonitor {
            NSEvent.removeMonitor(monitor)
            eventMonitor = nil
        }
    }

    private func handleKeyDown(_ event: NSEvent) -> NSEvent? {
        guard let sm = stateMachine else { return event }

        // Escape closes expanded panel
        if event.keyCode == 53, sm.currentState == .expanded {
            sm.transition(to: .glanceable)
            return nil
        }

        // Cmd+Shift+N toggles expanded
        if event.modifierFlags.contains([.command, .shift]),
           event.charactersIgnoringModifiers == "n" {
            if sm.currentState == .expanded {
                sm.transition(to: .glanceable)
            } else {
                sm.transition(to: .expanded)
            }
            return nil
        }

        return event
    }
}
