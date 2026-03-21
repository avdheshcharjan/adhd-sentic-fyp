import SwiftUI
import Combine

/// Bridges BackendBridge data into NotchViewModel and manages
/// state transitions based on backend events.
@Observable
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
        syncTask = Task { [weak self] in
            while !Task.isCancelled {
                await self?.sync()
                try? await Task.sleep(for: .seconds(1))
            }
        }
    }

    func stop() {
        bridge.stopPolling()
        syncTask?.cancel()
    }

    @MainActor
    private func sync() {
        viewModel.currentTask = bridge.currentTask
        viewModel.focusSession = bridge.focusSession
        viewModel.upcomingEvents = bridge.upcomingEvents
        viewModel.currentEmotion = bridge.currentEmotion
        viewModel.currentIntervention = bridge.pendingIntervention
        viewModel.dailyProgress = bridge.dailyProgress

        stateMachine.currentEmotion = bridge.currentEmotion

        updateStateFromData()
    }

    @MainActor
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
        .gentle
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
}
