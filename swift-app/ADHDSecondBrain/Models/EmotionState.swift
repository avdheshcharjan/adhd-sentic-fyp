import SwiftUI

enum EmotionState: String, Codable, Equatable {
    case joyful
    case focused
    case frustrated
    case anxious
    case disengaged
    case overwhelmed
    case neutral

    var color: Color {
        switch self {
        case .joyful: ADHDColors.Emotion.joyful
        case .focused: ADHDColors.Emotion.focused
        case .frustrated: ADHDColors.Emotion.frustrated
        case .anxious: ADHDColors.Emotion.anxious
        case .disengaged: ADHDColors.Emotion.disengaged
        case .overwhelmed: ADHDColors.Emotion.overwhelmed
        case .neutral: .clear
        }
    }

    var label: String {
        switch self {
        case .joyful: "Joyful"
        case .focused: "Focused"
        case .frustrated: "Frustrated"
        case .anxious: "Anxious"
        case .disengaged: "Disengaged"
        case .overwhelmed: "Overwhelmed"
        case .neutral: "Neutral"
        }
    }
}
