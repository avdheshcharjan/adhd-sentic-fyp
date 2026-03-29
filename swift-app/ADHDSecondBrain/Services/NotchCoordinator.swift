import SwiftUI
import Combine

/// Bridges BackendBridge data into NotchViewModel and manages
/// state transitions based on backend events.
@MainActor @Observable
class NotchCoordinator {
    let bridge: BackendBridge
    let viewModel: NotchViewModel
    let stateMachine: NotchStateMachine

    private var syncTask: Task<Void, Never>?

    init(
        bridge: BackendBridge = BackendBridge(),
        viewModel: NotchViewModel = NotchViewModel(),
        stateMachine: NotchStateMachine = NotchStateMachine()
    ) {
        self.bridge = bridge
        self.viewModel = viewModel
        self.stateMachine = stateMachine
    }

    func start() {
        bridge.startPolling()
        syncTask = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                self?.sync()
                try? await Task.sleep(for: .seconds(1))
            }
        }
    }

    func stop() {
        bridge.stopPolling()
        syncTask?.cancel()
    }

    private func sync() {
        viewModel.currentTask = bridge.currentTask
        viewModel.focusSession = bridge.focusSession
        viewModel.upcomingEvents = bridge.upcomingEvents
        viewModel.currentEmotion = bridge.currentEmotion
        viewModel.currentIntervention = bridge.pendingIntervention
        viewModel.dailyProgress = bridge.dailyProgress
        viewModel.isOffTask = bridge.isOffTask

        stateMachine.currentEmotion = bridge.currentEmotion

        updateStateFromData()
    }

    private func updateStateFromData() {
        if let intervention = bridge.pendingIntervention {
            let tier = tierFromIntervention(intervention)
            if stateMachine.currentState != .expanded {
                stateMachine.transition(to: .alert(tier))
            }
        } else if stateMachine.currentState == .dormant {
            if bridge.currentTask?.isActive == true {
                stateMachine.transition(to: .ambient)
            }
        }
    }

    private func tierFromIntervention(_ msg: InterventionMessage) -> InterventionTier {
        msg.interventionTier
    }

    func openGoogleCalendarAuth() {
        bridge.openGoogleAuth()
    }

    func sendCapture(_ text: String) {
        Task { await bridge.sendQuickCapture(text) }
    }

    func completeTask(_ id: String) {
        Task { await bridge.completeTask(id) }
    }

    func acknowledgeIntervention(_ id: String) {
        Task { await bridge.acknowledgeIntervention(id) }
    }

    func toggleFocus() {
        Task { await bridge.toggleFocusSession() }
    }

    /// Create a new task and start focus — transitions notch to glanceable.
    func createTaskAndStartFocus(name: String, duration: FocusDuration) {
        Task {
            let _ = await bridge.createTaskAndStartFocus(
                name: name,
                durationSeconds: Int(duration.seconds)
            )
            // Force an immediate sync so the notch picks up the new task
            sync()
            // Always transition to glanceable so the user sees the timer immediately
            switch stateMachine.currentState {
            case .dormant, .ambient, .expanded:
                stateMachine.transition(to: .glanceable)
            case .glanceable, .alert:
                break // Already showing task info
            }
        }
    }
}
