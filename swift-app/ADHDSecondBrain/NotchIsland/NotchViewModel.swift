import SwiftUI

@Observable
class NotchViewModel {
    var currentTask: TaskItem?
    var focusSession: FocusSession?
    var upcomingEvents: [CalendarEvent] = []
    var currentEmotion: EmotionState = .neutral
    var currentIntervention: InterventionMessage?
    var dailyProgress = DailyProgress(
        tasksCompleted: 0, focusSessions: 0, totalFocusMinutes: 0
    )
    var isOffTask: Bool = false
    var displayMode: NotchDisplayMode = .focus

    var hasActiveTask: Bool { currentTask?.isActive == true }

    var currentTaskName: String {
        currentTask?.name ?? "No active task"
    }

    func focusTimeRemaining(at now: Date = Date()) -> TimeInterval {
        guard let session = focusSession else { return 0 }
        return max(session.total - session.liveElapsed(at: now), 0)
    }

    var nextEventCountdown: String? {
        guard let event = upcomingEvents.first else { return nil }
        return event.startTime
    }
}
