import SwiftUI

/// Ambient: minimal text flanking the notch edges.
/// Left: current task name (truncated). Right: countdown to next event.
struct AmbientView: View {
    let taskName: String
    let nextEventCountdown: String?

    var body: some View {
        HStack {
            Text(truncatedName)
                .font(ADHDTypography.Notch.glanceCaption)
                .foregroundStyle(ADHDColors.Text.inverse.opacity(0.7))
                .lineLimit(1)
                .accessibilityLabel("Current task: \(taskName)")

            Spacer()

            if let countdown = nextEventCountdown {
                Text(countdown)
                    .font(ADHDTypography.Notch.glanceCaption)
                    .foregroundStyle(ADHDColors.Text.inverse.opacity(0.7))
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
