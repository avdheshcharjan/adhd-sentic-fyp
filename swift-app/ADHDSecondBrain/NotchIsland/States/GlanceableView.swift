import SwiftUI

/// Glanceable: wider bar with task name + time remaining.
/// Appears on hover with spring animation.
/// Uses TimelineView to tick the countdown every second.
struct GlanceableView: View {
    let task: TaskItem?
    let session: FocusSession?
    let emotion: EmotionState

    var body: some View {
        TimelineView(.periodic(from: .now, by: 1)) { context in
            let remaining: TimeInterval = {
                guard let session else { return 0 }
                return max(session.total - session.liveElapsed(at: context.date), 0)
            }()

            HStack(spacing: ADHDSpacing.md) {
                TaskNameLabel(name: task?.name ?? "No task")
                Spacer()
                TimeRemainingLabel(seconds: remaining)
            }
            .padding(.horizontal, ADHDSpacing.lg)
            .padding(.vertical, ADHDSpacing.notchPaddingV)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel(accessibilityText)
    }

    private var accessibilityText: String {
        let taskText = task?.name ?? "No task"
        guard let session else { return taskText }
        let remaining = max(session.total - session.liveElapsed(), 0)
        let minutes = Int(remaining) / 60
        return "\(taskText), \(minutes) minutes remaining"
    }
}

private struct TaskNameLabel: View {
    let name: String

    var body: some View {
        Text(name)
            .font(ADHDTypography.Notch.glanceTitle)
            .foregroundStyle(ADHDColors.Text.inverse)
            .lineLimit(1)
    }
}

private struct TimeRemainingLabel: View {
    let seconds: TimeInterval

    var body: some View {
        Text(formatted)
            .font(ADHDTypography.Notch.timerSmall)
            .foregroundStyle(ADHDColors.Text.inverse.opacity(0.8))
            .monospacedDigit()
    }

    private var formatted: String {
        let mins = Int(seconds) / 60
        let secs = Int(seconds) % 60
        return String(format: "%d:%02d", mins, secs)
    }
}
