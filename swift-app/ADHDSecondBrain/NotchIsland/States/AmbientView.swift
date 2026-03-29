import SwiftUI

/// Ambient: minimal text flanking the notch edges.
///
/// Sized to match hardware notch height (~37pt on notch Macs), slightly wider (200pt).
/// - Left: task name truncated in Lexend Regular 12px, color #ABABAB
/// - Right: countdown (e.g. "23m") in Lexend Regular 12px, color #ABABAB
/// - Horizontal padding: 12px
struct AmbientView: View {
    let taskName: String
    let session: FocusSession?

    var body: some View {
        TimelineView(.periodic(from: .now, by: 60)) { context in
            let remaining: TimeInterval = {
                guard let session else { return 0 }
                return max(session.total - session.liveElapsed(at: context.date), 0)
            }()

            HStack {
                Text(truncatedName)
                    .font(ADHDTypography.Notch.ambientLabel)
                    .foregroundStyle(ADHDColors.Text.notchMuted)
                    .lineLimit(1)
                    .accessibilityLabel("Current task: \(taskName)")

                Spacer()

                if session != nil && remaining > 0 {
                    Text(formatMinutes(remaining))
                        .font(ADHDTypography.Notch.ambientLabel)
                        .foregroundStyle(ADHDColors.Text.notchMuted)
                        .monospacedDigit()
                        .lineLimit(1)
                        .accessibilityLabel("Time remaining: \(formatMinutes(remaining))")
                }
            }
            .padding(.horizontal, ADHDSpacing.notchPaddingH)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }

    private var truncatedName: String {
        taskName.count > 20
            ? String(taskName.prefix(20)) + "..."
            : taskName
    }

    private func formatMinutes(_ seconds: TimeInterval) -> String {
        let mins = Int(seconds) / 60
        if mins >= 60 {
            let hrs = mins / 60
            let remainMins = mins % 60
            return remainMins > 0 ? "\(hrs)h \(remainMins)m" : "\(hrs)h"
        }
        return "\(mins)m"
    }
}
