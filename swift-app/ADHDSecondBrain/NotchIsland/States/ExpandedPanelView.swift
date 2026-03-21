import SwiftUI

/// Expanded: full panel with timer, task, capture, calendar, modes.
/// Content uses `.fixedSize()` for known-dimension elements.
struct ExpandedPanelView: View {
    let viewModel: NotchViewModel
    var onConnectCalendar: (() -> Void)?
    var onCapture: ((String) -> Void)?

    var body: some View {
        VStack(spacing: ADHDSpacing.cardSpacing) {
            TopRow(viewModel: viewModel)

            QuickCaptureField { text in
                onCapture?(text)
            }

            CalendarStripView(
                events: viewModel.upcomingEvents,
                onConnectCalendar: onConnectCalendar
            )

            ModeSwitcherRow(viewModel: viewModel)
        }
        .padding(ADHDSpacing.cardPadding)
        .padding(.top, ADHDSpacing.sm) // Extra top padding below notch curve
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Expanded task panel")
    }
}

private struct TopRow: View {
    let viewModel: NotchViewModel

    var body: some View {
        HStack(spacing: ADHDSpacing.md) {
            if let session = viewModel.focusSession {
                TimerRingView(
                    elapsed: session.elapsed,
                    total: session.total,
                    label: session.label
                )
                .fixedSize()
            }

            if let task = viewModel.currentTask {
                TaskCardView(task: task) {}
            } else {
                NoTaskPlaceholder()
            }
        }
    }
}

private struct NoTaskPlaceholder: View {
    var body: some View {
        Text("No active task")
            .font(ADHDTypography.Notch.expandedBody)
            .foregroundStyle(ADHDColors.Text.inverse.opacity(0.5))
            .frame(maxWidth: .infinity)
            .padding(ADHDSpacing.cardPadding)
            .background(ADHDColors.Background.notchInner.opacity(0.3))
            .clipShape(RoundedRectangle(cornerRadius: ADHDSpacing.cardCornerRadius))
            .accessibilityLabel("No active task")
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
