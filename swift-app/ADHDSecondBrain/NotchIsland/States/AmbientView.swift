import SwiftUI

/// Ambient: minimal text flanking the notch edges.
///
/// Paper spec:
/// - 200×28, pure black background, bottom corners 14px radius
/// - Left: task name truncated in Lexend Regular 12px, color #ABABAB
/// - Right: countdown (e.g. "23m") in Lexend Regular 12px, color #ABABAB
/// - Horizontal padding: 12px
struct AmbientView: View {
    let taskName: String
    let nextEventCountdown: String?

    var body: some View {
        HStack {
            Text(truncatedName)
                .font(ADHDTypography.Notch.ambientLabel)
                .foregroundStyle(ADHDColors.Text.notchMuted)
                .lineLimit(1)
                .accessibilityLabel("Current task: \(taskName)")

            Spacer()

            if let countdown = nextEventCountdown {
                Text(countdown)
                    .font(ADHDTypography.Notch.ambientLabel)
                    .foregroundStyle(ADHDColors.Text.notchMuted)
                    .lineLimit(1)
                    .accessibilityLabel("Next event: \(countdown)")
            }
        }
        .padding(.horizontal, ADHDSpacing.notchPaddingH)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var truncatedName: String {
        taskName.count > 20
            ? String(taskName.prefix(20)) + "..."
            : taskName
    }
}
