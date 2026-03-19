import Foundation

struct TaskItem: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let progress: Double
    let isActive: Bool

    enum CodingKeys: String, CodingKey {
        case id, name, progress
        case isActive = "is_active"
    }
}

struct FocusSession: Codable, Equatable {
    let elapsed: TimeInterval
    let total: TimeInterval
    let isRunning: Bool
    let label: String

    enum CodingKeys: String, CodingKey {
        case elapsed, total, label
        case isRunning = "is_running"
    }
}

struct CalendarEvent: Codable, Identifiable, Equatable {
    let id: String
    let title: String
    let startTime: String
    let emoji: String?

    enum CodingKeys: String, CodingKey {
        case id, title, emoji
        case startTime = "start_time"
    }
}

struct InterventionMessage: Codable, Identifiable, Equatable {
    let id: String
    let title: String
    let body: String
    let emoji: String
    let actionLabel: String

    enum CodingKeys: String, CodingKey {
        case id, title, body, emoji
        case actionLabel = "action_label"
    }
}

struct DailyProgress: Codable, Equatable {
    let tasksCompleted: Int
    let focusSessions: Int
    let totalFocusMinutes: Int

    enum CodingKeys: String, CodingKey {
        case tasksCompleted = "tasks_completed"
        case focusSessions = "focus_sessions"
        case totalFocusMinutes = "total_focus_minutes"
    }
}

enum NotchDisplayMode: String, CaseIterable {
    case calm
    case focus
    case windDown

    var label: String {
        switch self {
        case .calm: "Calm"
        case .focus: "Focus"
        case .windDown: "Wind Down"
        }
    }

    var emoji: String {
        switch self {
        case .calm: "\u{2600}\u{FE0F}"
        case .focus: "\u{26A1}"
        case .windDown: "\u{1F319}"
        }
    }
}
