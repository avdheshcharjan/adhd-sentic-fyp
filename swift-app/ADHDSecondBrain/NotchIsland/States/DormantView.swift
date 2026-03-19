import SwiftUI

/// Dormant: near-invisible. Tiny colored dot at the right edge.
/// Matches hardware notch appearance.
struct DormantView: View {
    let hasActiveTask: Bool

    var body: some View {
        HStack {
            Spacer()
            Circle()
                .fill(dotColor)
                .frame(width: 6, height: 6)
                .padding(.trailing, ADHDSpacing.sm)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityLabel(
            hasActiveTask ? "Task active" : "No active task"
        )
    }

    private var dotColor: Color {
        hasActiveTask
            ? ADHDColors.Accent.focus
            : ADHDColors.Accent.calm.opacity(0.4)
    }
}
