import Foundation

// MARK: - Request Models

/// Matches Python's ScreenActivityInput
struct ScreenActivityRequest: Codable {
    let appName: String
    let windowTitle: String
    let url: String?
    let isIdle: Bool
    let timestamp: String
    let offTaskAlertsEnabled: Bool
    let offTaskAlertsAlways: Bool

    enum CodingKeys: String, CodingKey {
        case appName = "app_name"
        case windowTitle = "window_title"
        case url
        case isIdle = "is_idle"
        case timestamp
        case offTaskAlertsEnabled = "off_task_alerts_enabled"
        case offTaskAlertsAlways = "off_task_alerts_always"
    }
}

// MARK: - Response Models

/// Matches Python's ScreenActivityResponse
struct ScreenActivityResponse: Codable {
    let category: String
    let metrics: ADHDMetrics
    let intervention: Intervention?
    let offTask: Bool

    enum CodingKeys: String, CodingKey {
        case category
        case metrics
        case intervention
        case offTask = "off_task"
    }
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
    let notificationTier: Int?

    enum CodingKeys: String, CodingKey {
        case type
        case efDomain = "ef_domain"
        case acknowledgment
        case suggestion
        case actions
        case requiresSenticnet = "requires_senticnet"
        case notificationTier = "notification_tier"
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

// MARK: - Dashboard Models

struct DashboardStats: Codable {
    let totalFocusMinutes: Int
    let totalActiveMinutes: Int
    let interventionsTriggered: Int
    let interventionsAccepted: Int
    let focusTimeline: [TimelineSegment]
    let emotionScores: EmotionScores

    enum CodingKeys: String, CodingKey {
        case totalFocusMinutes = "total_focus_minutes"
        case totalActiveMinutes = "total_active_minutes"
        case interventionsTriggered = "interventions_triggered"
        case interventionsAccepted = "interventions_accepted"
        case focusTimeline = "focus_timeline"
        case emotionScores = "emotion_scores"
    }
}

struct TimelineSegment: Codable, Identifiable {
    let id: String
    let category: String   // "focused", "distracted", "neutral", "idle"
    let duration: Double   // fraction 0-1
}

struct EmotionScores: Codable {
    let pleasantness: Double
    let attention: Double
    let sensitivity: Double
    let aptitude: Double
}

/// Matches Python MorningBriefing from /whoop/morning-briefing endpoint.
struct WhoopRecovery: Codable {
    let recoveryPercent: Double
    let recoveryTier: String
    let hrv: Double
    let restingHR: Double
    let sleepPerformance: Double?
    let recommendedFocusBlock: Int

    enum CodingKeys: String, CodingKey {
        case recoveryPercent = "recovery_score"
        case recoveryTier = "recovery_tier"
        case hrv = "hrv_rmssd"
        case restingHR = "resting_hr"
        case sleepPerformance = "sleep_performance"
        case recommendedFocusBlock = "recommended_focus_block_minutes"
    }
}

struct WeeklyReport: Codable {
    let days: [DayReport]
    let avgFocus: Double
    let avgDistraction: Double
    let totalInterventions: Int
    let acceptanceRate: Double
    let bestDay: String
    let worstDay: String
    let trend: String   // "improving", "stable", "declining"

    enum CodingKeys: String, CodingKey {
        case days
        case avgFocus = "avg_focus"
        case avgDistraction = "avg_distraction"
        case totalInterventions = "total_interventions"
        case acceptanceRate = "acceptance_rate"
        case bestDay = "best_day"
        case worstDay = "worst_day"
        case trend
    }
}

struct DayReport: Codable, Identifiable {
    let id: String
    let day: String
    let focusRatio: Double
    let distractionRatio: Double
    let isToday: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case day
        case focusRatio = "focus_ratio"
        case distractionRatio = "distraction_ratio"
        case isToday = "is_today"
    }
}

// MARK: - History / Snapshot Models

struct SnapshotSummary: Codable, Identifiable {
    var id: String { date }
    let date: String
    let focusPercentage: Double
    let distractionPercentage: Double
    let totalActiveMinutes: Double
    let totalFocusMinutes: Double

    enum CodingKeys: String, CodingKey {
        case date
        case focusPercentage = "focus_percentage"
        case distractionPercentage = "distraction_percentage"
        case totalActiveMinutes = "total_active_minutes"
        case totalFocusMinutes = "total_focus_minutes"
    }
}

struct AppUsageItem: Codable {
    let appName: String
    let category: String
    let minutes: Double
    let percentage: Double

    enum CodingKeys: String, CodingKey {
        case appName = "app_name"
        case category
        case minutes
        case percentage
    }
}

struct HistorySnapshot: Codable {
    let date: String
    let totalActiveMinutes: Double
    let totalFocusMinutes: Double
    let totalDistractionMinutes: Double
    let focusPercentage: Double
    let distractionPercentage: Double
    let contextSwitches: Int
    let interventionsTriggered: Int
    let interventionsAccepted: Int
    let topApps: [AppUsageItem]
    let behavioralStates: [String: Double]
    let focusTimeline: [TimelineSegment]
    let emotionScores: EmotionScores?
    let whoopRecovery: SnapshotWhoopData?

    enum CodingKeys: String, CodingKey {
        case date
        case totalActiveMinutes = "total_active_minutes"
        case totalFocusMinutes = "total_focus_minutes"
        case totalDistractionMinutes = "total_distraction_minutes"
        case focusPercentage = "focus_percentage"
        case distractionPercentage = "distraction_percentage"
        case contextSwitches = "context_switches"
        case interventionsTriggered = "interventions_triggered"
        case interventionsAccepted = "interventions_accepted"
        case topApps = "top_apps"
        case behavioralStates = "behavioral_states"
        case focusTimeline = "focus_timeline"
        case emotionScores = "emotion_scores"
        case whoopRecovery = "whoop_recovery"
    }
}

struct SnapshotWhoopData: Codable {
    let recoveryScore: Double
    let sleepScore: Double
    let strainScore: Double
    let metrics: [String: AnyCodable]?

    enum CodingKeys: String, CodingKey {
        case recoveryScore = "recovery_score"
        case sleepScore = "sleep_score"
        case strainScore = "strain_score"
        case metrics
    }
}

/// Type-erased Codable wrapper for heterogeneous JSON values.
struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let double = try? container.decode(Double.self) {
            value = double
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else {
            value = ""
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let double = value as? Double {
            try container.encode(double)
        } else if let int = value as? Int {
            try container.encode(int)
        } else if let string = value as? String {
            try container.encode(string)
        } else if let bool = value as? Bool {
            try container.encode(bool)
        }
    }
}
