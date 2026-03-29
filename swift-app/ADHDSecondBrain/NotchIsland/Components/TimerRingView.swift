import SwiftUI

/// Timer ring matching Paper design: 56x56 circle with 4px border.
/// Blue (#457B9DCC) when <75%, green (#73C8A9) when >=75%.
/// Center: timer digits (Lexend Light 16px) + label (Lexend Medium 9px).
///
/// Uses TimelineView to tick every second for real-time countdown.
struct TimerRingView: View {
    let session: FocusSession
    let label: String
    var onToggle: (() -> Void)?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        TimelineView(.periodic(from: .now, by: 1)) { context in
            let now = context.date
            let elapsed = session.liveElapsed(at: now)
            let progress = session.total > 0 ? min(elapsed / session.total, 1.0) : 0
            let remaining = max(session.total - elapsed, 0)
            let ringColor = progress < 0.75
                ? ADHDColors.Accent.focus.opacity(0.8)
                : ADHDColors.Accent.success

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
                    Text(formatTime(remaining))
                        .font(ADHDTypography.Notch.timerInRing)
                        .foregroundStyle(ADHDColors.Text.inverse)
                        .monospacedDigit()

                    Text(label)
                        .font(ADHDTypography.Notch.timerLabel)
                        .foregroundStyle(ADHDColors.Text.inverse.opacity(0.6))
                }
            }
            .frame(width: 56, height: 56)
        }
        .onTapGesture { onToggle?() }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(accessibilityText)
        .accessibilityAddTraits(.isButton)
    }

    private var accessibilityText: String {
        let remaining = max(session.total - session.liveElapsed(), 0)
        let minutes = Int(remaining) / 60
        return "\(label) timer: \(minutes) minutes remaining"
    }

    private func formatTime(_ seconds: TimeInterval) -> String {
        let mins = Int(seconds) / 60
        let secs = Int(seconds) % 60
        return String(format: "%d:%02d", mins, secs)
    }
}
