import SwiftUI

/// Dormant: near-invisible. Tiny colored dot at the right edge.
///
/// Sized to match hardware notch (180×~37pt on notch Macs).
/// - Dot: 6px, #457B9D at 50% opacity when no task, 100% when task active
/// - Padding right: 8px
struct DormantView: View {
    let hasActiveTask: Bool

    var body: some View {
        HStack {
            Spacer()
            Circle()
                .fill(dotColor)
                .frame(width: 6, height: 6)
                // Paper: 8px right padding
                .padding(.trailing, ADHDSpacing.sm)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityLabel(
            hasActiveTask ? "Task active" : "No active task"
        )
    }

    private var dotColor: Color {
        // Paper: #457B9D full opacity when task active, 50% when not
        hasActiveTask
            ? ADHDColors.Accent.focus
            : ADHDColors.Accent.focus.opacity(0.5)
    }
}
