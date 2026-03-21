import SwiftUI

/// Task card matching Paper design: dark inner card with title, progress bar, and checkmark.
/// Background: #1C1C1E at 50% opacity, corner radius 12px, padding 12px.
struct TaskCardView: View {
    let task: TaskItem
    let onComplete: () -> Void

    var body: some View {
        HStack(spacing: ADHDSpacing.sm) {
            VStack(alignment: .leading, spacing: ADHDSpacing.xs) {
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
            ZStack {
                Circle()
                    .stroke(ADHDColors.Accent.success, lineWidth: 1.5)
                    .frame(width: 20, height: 20)

                Path { path in
                    path.move(to: CGPoint(x: 6, y: 10))
                    path.addLine(to: CGPoint(x: 9, y: 13))
                    path.addLine(to: CGPoint(x: 14, y: 7))
                }
                .stroke(
                    ADHDColors.Accent.success,
                    style: StrokeStyle(lineWidth: 1.5, lineCap: .round, lineJoin: .round)
                )
                .frame(width: 20, height: 20)
            }
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Complete task")
    }
}
