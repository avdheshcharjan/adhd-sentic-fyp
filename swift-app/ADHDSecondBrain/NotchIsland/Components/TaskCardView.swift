import SwiftUI

struct TaskCardView: View {
    let task: TaskItem
    let onComplete: () -> Void

    var body: some View {
        HStack(spacing: ADHDSpacing.sm) {
            VStack(alignment: .leading, spacing: ADHDSpacing.xxs) {
                Text(task.name)
                    .font(ADHDTypography.Notch.expandedTitle)
                    .foregroundStyle(ADHDColors.Text.inverse)
                    .lineLimit(1)

                ProgressBar(progress: task.progress)
            }

            Spacer()

            CompleteButton(action: onComplete)
        }
        .padding(ADHDSpacing.cardPadding)
        .background(ADHDColors.Background.notchInner.opacity(0.5))
        .clipShape(RoundedRectangle(cornerRadius: ADHDSpacing.cardCornerRadius))
        .accessibilityElement(children: .combine)
        .accessibilityLabel(
            "\(task.name), \(Int(task.progress * 100)) percent complete"
        )
    }
}

private struct ProgressBar: View {
    let progress: Double

    var body: some View {
        GeometryReader { proxy in
            ZStack(alignment: .leading) {
                RoundedRectangle(cornerRadius: 2)
                    .fill(ADHDColors.Background.elevated.opacity(0.3))
                    .frame(height: 4)

                RoundedRectangle(cornerRadius: 2)
                    .fill(ADHDColors.Accent.focus)
                    .frame(
                        width: proxy.size.width * progress,
                        height: 4
                    )
            }
        }
        .frame(height: 4)
    }
}

private struct CompleteButton: View {
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: "checkmark.circle")
                .font(.system(size: 20))
                .foregroundStyle(ADHDColors.Accent.success)
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Complete task")
    }
}
