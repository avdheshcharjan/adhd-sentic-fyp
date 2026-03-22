import SwiftUI

// MARK: - Color Tokens (Paper Canvas — exact hex values)

enum ADHDColors {

    enum Background {
        static let primary = Color(hex: 0x0E0E10)
        static let secondary = Color(hex: 0x19191D)
        static let elevated = Color(hex: 0x131316)
        static let notch = Color(hex: 0x000000)
        static let notchInner = Color(hex: 0x1C1C1E)
        static let surface = Color(hex: 0xEAE6D2)
    }

    enum Text {
        static let primary = Color(hex: 0xE5E5E7)
        static let secondary = Color(hex: 0xABAAB1)
        /// Ambient/muted notch labels — Paper spec exact value #ABABAB
        static let notchMuted = Color(hex: 0xABABAB)
        static let tertiary = Color(hex: 0x75757B)
        static let inverse = Color(hex: 0xE5E5E7)
        static let muted = Color(hex: 0x47474D)
    }

    enum Accent {
        static let focus = Color(hex: 0x457B9D)
        static let focusLight = Color(hex: 0x99CDF0)
        static let success = Color(hex: 0x73C8A9)
        static let successBright = Color(hex: 0x28C840)
        static let warmth = Color(hex: 0xFFE3B4)
        static let alert = Color(hex: 0xFF6F61)
        static let calm = Color(hex: 0xB8C9E0)
        static let warning = Color(hex: 0xEAB308)
        static let danger = Color(hex: 0xEF4444)
    }

    enum Intervention {
        static let dormant = Color(hex: 0x457B9D).opacity(0.4)
        static let ambient = Color(hex: 0x457B9D).opacity(0.6)
        static let gentle = Color(hex: 0xFFE3B4)
        static let timely = Color(hex: 0xFF6F61).opacity(0.7)
        static let critical = Color(hex: 0xFF6F61)
    }

    enum Emotion {
        static let joyful = Color(hex: 0x73C8A9)
        static let focused = Color(hex: 0x457B9D)
        static let frustrated = Color(hex: 0xFF8A80)
        static let anxious = Color(hex: 0xFFE3B4)
        static let disengaged = Color(hex: 0x8E8E93)
        static let overwhelmed = Color(hex: 0xFF6F61)
    }

    enum Window {
        static let trafficRed = Color(hex: 0xFF5F57)
        static let trafficYellow = Color(hex: 0xFEBC2E)
        static let trafficGreen = Color(hex: 0x28C840)
        static let borderSubtle = Color.white.opacity(0.06)
    }
}

// MARK: - Typography Tokens (Paper Canvas — Lexend primary)

enum ADHDTypography {

    static let fontFamily = "Lexend"

    enum Notch {
        static let glanceTitle = Font.custom("Lexend-SemiBold", size: 13)
        static let glanceBody = Font.custom("Lexend-Regular", size: 11)
        static let glanceCaption = Font.custom("Lexend-Medium", size: 10)
        /// Ambient state: task name + countdown — Lexend Regular 12px, color #ABABAB
        static let ambientLabel = Font.custom("Lexend-Regular", size: 12)
        /// Alert banner title — Lexend SemiBold 14px (Paper spec)
        static let alertTitle = Font.custom("Lexend-SemiBold", size: 14)
        static let expandedTitle = Font.custom("Lexend-SemiBold", size: 16)
        static let expandedBody = Font.custom("Lexend-Regular", size: 14)
        static let timer = Font.custom("Lexend-Light", size: 28).monospacedDigit()
        static let timerSmall = Font.custom("Lexend-Light", size: 18).monospacedDigit()
        static let timerInRing = Font.custom("Lexend-Light", size: 16)
        static let timerLabel = Font.custom("Lexend-Medium", size: 9)
    }

    enum App {
        static let displayLarge = Font.custom("Lexend-SemiBold", size: 22)
        static let headline = Font.custom("Lexend-SemiBold", size: 22)
        static let subheadline = Font.custom("Lexend-SemiBold", size: 18)
        static let title = Font.custom("Lexend-SemiBold", size: 20)
        static let cardTitle = Font.custom("Lexend-SemiBold", size: 15)
        static let body = Font.custom("Lexend-Regular", size: 14)
        static let bodyMedium = Font.custom("Lexend-Medium", size: 14)
        static let caption = Font.custom("Lexend-Regular", size: 13)
        static let captionMedium = Font.custom("Lexend-Medium", size: 13)
        static let small = Font.custom("Lexend-Regular", size: 12)
        static let tiny = Font.custom("Lexend-Medium", size: 11)
        static let micro = Font.custom("Lexend-Medium", size: 10)
        static let metricValue = Font.custom("Lexend-SemiBold", size: 16)
        static let metricLarge = Font.custom("Lexend-Bold", size: 20)
        static let metricHuge = Font.custom("Lexend-SemiBold", size: 18)
        static let sectionLabel = Font.custom("Lexend-Medium", size: 11)
    }

    enum Dashboard {
        static let greeting = Font.custom("Lexend-SemiBold", size: 22)
        static let subtitle = Font.custom("Lexend-Regular", size: 13)
        static let cardTitle = Font.custom("Lexend-SemiBold", size: 15)
        static let metricLabel = Font.custom("Lexend-Regular", size: 13)
        static let metricValue = Font.custom("Lexend-SemiBold", size: 16)
        static let statValue = Font.custom("Lexend-SemiBold", size: 18)
        static let statLabel = Font.custom("Lexend-Regular", size: 10)
        static let badge = Font.custom("Lexend-SemiBold", size: 11)
        static let badgeSmall = Font.custom("Lexend-Medium", size: 12)
    }

    static let lineSpacingBody: CGFloat = 6
    static let lineSpacingCaption: CGFloat = 4
    static let letterSpacingBody: CGFloat = 0.3
    static let letterSpacingCaption: CGFloat = 0.5
}

// MARK: - Color Hex Initializer

extension Color {
    init(hex: UInt, alpha: Double = 1.0) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: alpha
        )
    }
}
