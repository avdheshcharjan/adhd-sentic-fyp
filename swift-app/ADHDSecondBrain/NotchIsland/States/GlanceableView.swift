import SwiftUI

/// Glanceable: wider bar with task name + time remaining.
/// Appears on hover with spring animation.
struct GlanceableView: View {
    let task: TaskItem?
    let timeRemaining: TimeInterval
    let emotion: EmotionState

    var body: some View {
        HStack(spacing: ADHDSpacing.md) {
            TaskNameLabel(name: task?.name ?? "No task")
            Spacer()
            TimeRemainingLabel(seconds: timeRemaining)
        }
        .padding(.horizontal, ADHDSpacing.notchPaddingH)
        .padding(.vertical, ADHDSpacing.notchPaddingV)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityElement(children: .combine)
        .accessibilityLabel(accessibilityText)
    }

    private var accessibilityText: String {
        let taskText = task?.name ?? "No task"
        let minutes = Int(timeRemaining) / 60
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
