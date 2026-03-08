import Foundation

// MARK: - Request Models

/// Matches Python's ScreenActivityInput
struct ScreenActivityRequest: Codable {
    let appName: String
    let windowTitle: String
    let url: String?
    let isIdle: Bool
    let timestamp: String

    enum CodingKeys: String, CodingKey {
        case appName = "app_name"
        case windowTitle = "window_title"
        case url
        case isIdle = "is_idle"
        case timestamp
    }
}

// MARK: - Response Models

/// Matches Python's ScreenActivityResponse
struct ScreenActivityResponse: Codable {
    let category: String
    let metrics: ADHDMetrics
    let intervention: Intervention?
}

/// Matches Python's ADHDMetrics
struct ADHDMetrics: Codable {
    var contextSwitchRate5min: Double = 0
    var focusScore: Double = 0
    var distractionRatio: Double = 0
    var currentStreakMinutes: Double = 0
    var hyperfocusDetected: Bool = false
    var behavioralState: String = "unknown"

    enum CodingKeys: String, CodingKey {
        case contextSwitchRate5min = "context_switch_rate_5min"
        case focusScore = "focus_score"
        case distractionRatio = "distraction_ratio"
        case currentStreakMinutes = "current_streak_minutes"
        case hyperfocusDetected = "hyperfocus_detected"
        case behavioralState = "behavioral_state"
    }

    /// Human-readable focus score label
    var focusLabel: String {
        switch focusScore {
        case 70...: return "Deep Focus"
        case 40..<70: return "Moderate"
        case 10..<40: return "Scattered"
        default: return "Starting Up"
        }
    }

    /// Emoji for behavioral state
    var stateEmoji: String {
        switch behavioralState {
        case "focused": return "🎯"
        case "hyperfocused": return "🔥"
        case "multitasking": return "🔄"
        case "distracted": return "💭"
        case "idle": return "😴"
        default: return "🧠"
        }
    }
}

/// Matches Python's Intervention
struct Intervention: Codable {
    let type: String
    let efDomain: String
    let acknowledgment: String
    let suggestion: String
    let actions: [InterventionAction]
    let requiresSenticnet: Bool

    enum CodingKeys: String, CodingKey {
        case type
        case efDomain = "ef_domain"
        case acknowledgment
        case suggestion
        case actions
        case requiresSenticnet = "requires_senticnet"
    }
}

/// Matches Python's InterventionAction
struct InterventionAction: Codable, Identifiable {
    let id: String
    let emoji: String
    let label: String
}

// MARK: - Intervention Response

struct InterventionResponseRequest: Codable {
    let actionTaken: String
    let dismissed: Bool
    let effectivenessRating: Int?

    enum CodingKeys: String, CodingKey {
        case actionTaken = "action_taken"
        case dismissed
        case effectivenessRating = "effectiveness_rating"
    }
}
