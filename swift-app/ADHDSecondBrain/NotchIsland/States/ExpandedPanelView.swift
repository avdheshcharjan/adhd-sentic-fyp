import SwiftUI

/// Expanded: full panel with timer, task, capture, calendar, modes.
/// Content uses `.fixedSize()` for known-dimension elements.
struct ExpandedPanelView: View {
    let viewModel: NotchViewModel
    var onConnectCalendar: (() -> Void)?
    var onCapture: ((String) -> Void)?
    var onCompleteTask: ((String) -> Void)?
    var onToggleFocus: (() -> Void)?

    var body: some View {
        VStack(spacing: ADHDSpacing.cardSpacing) {
            TopRow(viewModel: viewModel, onCompleteTask: onCompleteTask, onToggleFocus: onToggleFocus)

            QuickCaptureField { text in
                onCapture?(text)
            }

            CalendarStripView(
                events: viewModel.upcomingEvents,
                onConnectCalendar: onConnectCalendar
            )

            ModeSwitcherRow(viewModel: viewModel)
        }
        // Paper design: 20px top, 12px sides, 12px bottom
        .padding(.top, 20)
        .padding(.horizontal, ADHDSpacing.cardPadding)
        .padding(.bottom, ADHDSpacing.cardPadding)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Expanded task panel")
    }
}

private struct TopRow: View {
    let viewModel: NotchViewModel
    var onCompleteTask: ((String) -> Void)?
    var onToggleFocus: (() -> Void)?

    var body: some View {
        HStack(spacing: ADHDSpacing.md) {
            if let session = viewModel.focusSession {
                TimerRingView(
                    session: session,
                    label: session.label,
                    onToggle: onToggleFocus
                )
                .fixedSize()
            }

            if let task = viewModel.currentTask {
                TaskCardView(task: task) {
                    onCompleteTask?(task.id)
                }
            } else {
                NoTaskPlaceholder()
            }
        }
    }
}

private struct NoTaskPlaceholder: View {
    var body: some View {
        Button {
            NotificationCenter.default.post(name: .openTaskCreation, object: nil)
        } label: {
            HStack(spacing: ADHDSpacing.sm) {
                Image(systemName: "plus.circle")
                    .font(.system(size: 14))
                    .foregroundStyle(ADHDColors.Accent.focusLight.opacity(0.6))

                Text("Create a task")
                    .font(ADHDTypography.Notch.expandedBody)
                    .foregroundStyle(ADHDColors.Text.inverse.opacity(0.5))

                Spacer()

                Text("\u{2318}\u{21E7}T")
                    .font(ADHDTypography.Notch.ambientLabel)
                    .foregroundStyle(ADHDColors.Text.tertiary)
            }
            .frame(maxWidth: .infinity)
            .padding(ADHDSpacing.cardPadding)
            .background(ADHDColors.Background.notchInner.opacity(0.3))
            .clipShape(RoundedRectangle(cornerRadius: ADHDSpacing.cardCornerRadius))
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Create a task. Press Command Shift T.")
    }
}

private struct ModeSwitcherRow: View {
    let viewModel: NotchViewModel
    @State private var mode: NotchDisplayMode = .focus

    var body: some View {
        ModeSwitcherView(selectedMode: $mode)
            .onChange(of: mode) { _, newMode in
                viewModel.displayMode = newMode
            }
    }
}
