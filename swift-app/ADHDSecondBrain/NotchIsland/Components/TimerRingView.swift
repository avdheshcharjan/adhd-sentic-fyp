import SwiftUI

/// Timer ring matching Paper design: 56x56 circle with 4px border.
/// Blue (#457B9DCC) when <75%, green (#73C8A9) when >=75%.
/// Center: timer digits (Lexend Light 16px) + label (Lexend Medium 9px).
struct TimerRingView: View {
    let elapsed: TimeInterval
    let total: TimeInterval
    let label: String
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private var progress: Double {
        guard total > 0 else { return 0 }
        return min(elapsed / total, 1.0)
    }

    private var timeString: String {
        let remaining = max(total - elapsed, 0)
        let minutes = Int(remaining) / 60
        let seconds = Int(remaining) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }

    private var ringColor: Color {
        progress < 0.75
            ? ADHDColors.Accent.focus.opacity(0.8)
            : ADHDColors.Accent.success
    }

    var body: some View {
        ZStack {
            Circle()
                .stroke(
                    ADHDColors.Background.elevated.opacity(0.3),
                    lineWidth: 4
                )

            Circle()
                .trim(from: 0, to: progress)
                .stroke(
                    ringColor,
                    style: StrokeStyle(lineWidth: 4, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))
                .animation(
                    reduceMotion ? nil : .linear(duration: 1),
                    value: progress
                )

            VStack(spacing: 0) {
                Text(timeString)
                    .font(ADHDTypography.Notch.timerInRing)
                    .foregroundStyle(ADHDColors.Text.inverse)

                Text(label)
                    .font(ADHDTypography.Notch.timerLabel)
                    .foregroundStyle(ADHDColors.Text.inverse.opacity(0.6))
            }
        }
        .frame(width: 56, height: 56)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(accessibilityText)
    }

    private var accessibilityText: String {
        let remaining = max(total - elapsed, 0)
        let minutes = Int(remaining) / 60
        return "\(label) timer: \(minutes) minutes remaining"
    }
}
