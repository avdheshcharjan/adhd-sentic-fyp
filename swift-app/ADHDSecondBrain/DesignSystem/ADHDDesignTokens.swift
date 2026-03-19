import SwiftUI

// MARK: - Color Tokens

enum ADHDColors {

    enum Background {
        static let primary = Color("bg-primary")
        static let secondary = Color("bg-secondary")
        static let elevated = Color("bg-elevated")
        static let notch = Color("bg-notch")
        static let notchInner = Color("bg-notch-inner")
    }

    enum Text {
        static let primary = Color("text-primary")
        static let secondary = Color("text-secondary")
        static let tertiary = Color("text-tertiary")
        static let inverse = Color("text-inverse")
    }

    enum Accent {
        static let focus = Color("accent-focus")
        static let success = Color("accent-success")
        static let warmth = Color("accent-warmth")
        static let alert = Color("accent-alert")
        static let calm = Color("accent-calm")
    }

    enum Intervention {
        static let dormant = Color("intervention-dormant")
        static let ambient = Color("intervention-ambient")
        static let gentle = Color("intervention-gentle")
        static let timely = Color("intervention-timely")
        static let critical = Color("intervention-critical")
    }

    enum Emotion {
        static let joyful = Color("emotion-joyful")
        static let focused = Color("emotion-focused")
        static let frustrated = Color("emotion-frustrated")
        static let anxious = Color("emotion-anxious")
        static let disengaged = Color("emotion-disengaged")
        static let overwhelmed = Color("emotion-overwhelmed")
    }
}

// MARK: - Typography Tokens

enum ADHDTypography {

    static let fontFamily = "Lexend"
    static let fallbackFamily = ".AppleSystemUIFont"

    enum Notch {
        static let glanceTitle = Font.system(size: 13, weight: .semibold)
        static let glanceBody = Font.system(size: 11, weight: .regular)
        static let glanceCaption = Font.system(size: 10, weight: .medium)
        static let expandedTitle = Font.system(size: 16, weight: .semibold)
        static let expandedBody = Font.system(size: 14, weight: .regular)
        static let timer = Font.system(size: 28, weight: .light).monospacedDigit()
        static let timerSmall = Font.system(size: 18, weight: .light).monospacedDigit()
    }

    enum App {
        static let headline = Font.system(size: 22, weight: .semibold)
        static let subheadline = Font.system(size: 17, weight: .medium)
        static let body = Font.system(size: 16, weight: .regular)
        static let caption = Font.system(size: 13, weight: .regular)
        static let tiny = Font.system(size: 11, weight: .medium)
    }

    static let lineSpacingBody: CGFloat = 6
    static let lineSpacingCaption: CGFloat = 4
    static let letterSpacingBody: CGFloat = 0.3
    static let letterSpacingCaption: CGFloat = 0.5
}
