import AppKit
import Carbon

/// Registers global hotkeys and click-away detection for the notch widget.
/// Cmd+Shift+N toggles expanded/collapsed.
/// Escape closes expanded panel.
/// Click outside the notch closes expanded panel (click-away).
class KeyboardShortcutManager {

    private var eventMonitor: Any?
    private var mouseMonitor: Any?
    private weak var stateMachine: NotchStateMachine?

    init(stateMachine: NotchStateMachine) {
        self.stateMachine = stateMachine
    }

    func register() {
        // Use global monitor — local monitor only fires when our app is active,
        // but the notch panel uses .nonactivatingPanel so our app is rarely active.
        // Global monitors cannot consume events (return value is ignored), but they
        // can trigger state transitions.
        eventMonitor = NSEvent.addGlobalMonitorForEvents(
            matching: .keyDown
        ) { [weak self] event in
            self?.handleKeyDown(event)
        }

        // Click-away: close expanded panel when user clicks anywhere outside the notch.
        // Global monitors fire for clicks on OTHER apps' windows (not our own panel).
        mouseMonitor = NSEvent.addGlobalMonitorForEvents(
            matching: .leftMouseDown
        ) { [weak self] _ in
            self?.handleClickAway()
        }
    }

    func unregister() {
        if let monitor = eventMonitor {
            NSEvent.removeMonitor(monitor)
            eventMonitor = nil
        }
        if let monitor = mouseMonitor {
            NSEvent.removeMonitor(monitor)
            mouseMonitor = nil
        }
    }

    private func handleKeyDown(_ event: NSEvent) {
        guard let sm = stateMachine else { return }

        // Escape closes expanded panel
        if event.keyCode == 53, sm.currentState == .expanded {
            DispatchQueue.main.async {
                sm.transition(to: .glanceable)
            }
            return
        }

        // Cmd+Shift+N toggles expanded
        if event.modifierFlags.contains([.command, .shift]),
           event.charactersIgnoringModifiers == "n" {
            DispatchQueue.main.async {
                if sm.currentState == .expanded {
                    sm.transition(to: .glanceable)
                } else {
                    sm.transition(to: .expanded)
                }
            }
        }
    }

    private func handleClickAway() {
        guard let sm = stateMachine,
              sm.currentState == .expanded else { return }
        // Transition to glanceable (the only valid exit from expanded per state machine rules).
        // The hover-collapse logic will then naturally collapse to dormant
        // after the 0.3s delay when the mouse leaves the notch area.
        DispatchQueue.main.async {
            sm.transition(to: .glanceable)
        }
    }
}
