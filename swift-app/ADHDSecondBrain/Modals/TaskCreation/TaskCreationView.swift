import SwiftUI

/// Spotlight-style task creation modal matching Paper design spec.
///
/// Frosted glass panel: rgba(28,28,30,0.85) background, 20px corner radius.
/// Fields: task name input + preset duration chips.
/// Triggers: Cmd+Shift+T globally, "No active task" in expanded notch.
struct TaskCreationView: View {
    @Bindable var viewModel: TaskCreationViewModel
    let onSubmit: (String, FocusDuration) -> Void
    let onDismiss: () -> Void

    @FocusState private var isInputFocused: Bool

    var body: some View {
        ZStack {
            VisualEffectBackground(material: .sidebar, blendingMode: .behindWindow)

            VStack(spacing: 0) {
                TaskInputRow(
                    taskName: $viewModel.taskName,
                    isInputFocused: $isInputFocused,
                    canSubmit: viewModel.canSubmit,
                    onClear: { viewModel.taskName = "" }
                )

                Divider()
                    .background(Color.white.opacity(0.06))

                DurationSection(selectedDuration: $viewModel.selectedDuration)

                Divider()
                    .background(Color.white.opacity(0.06))

                ActionFooter(
                    canSubmit: viewModel.canSubmit,
                    onSubmit: submitTask
                )
            }
        }
        .frame(width: 480)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .strokeBorder(ADHDColors.Window.borderSubtle, lineWidth: 1)
        )
        .onAppear {
            isInputFocused = true
        }
    }

    private func submitTask() {
        guard viewModel.canSubmit else { return }
        let name = viewModel.taskName.trimmingCharacters(in: .whitespaces)
        let duration = viewModel.selectedDuration
        onSubmit(name, duration)
    }
}

// MARK: - Task Input Row

private struct TaskInputRow: View {
    @Binding var taskName: String
    var isInputFocused: FocusState<Bool>.Binding
    let canSubmit: Bool
    let onClear: () -> Void

    var body: some View {
        HStack(spacing: ADHDSpacing.md) {
            // Focus circle indicator — green when text entered
            Circle()
                .stroke(indicatorColor, lineWidth: 1.5)
                .overlay(
                    Circle()
                        .fill(indicatorColor.opacity(canSubmit ? 1.0 : 0.4))
                        .frame(width: 6, height: 6)
                )
                .frame(width: 20, height: 20)

            TextField("What are you working on?", text: $taskName)
                .font(ADHDTypography.App.subheadline)
                .foregroundStyle(ADHDColors.Text.inverse)
                .textFieldStyle(.plain)
                .focused(isInputFocused)
                .onSubmit {
                    // Enter submits — handled by parent
                }
                .accessibilityLabel("Task name input")

            if !taskName.isEmpty {
                Button(action: onClear) {
                    Image(systemName: "xmark")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundStyle(ADHDColors.Text.tertiary)
                }
                .buttonStyle(.plain)
                .transition(.scale.combined(with: .opacity))
                .accessibilityLabel("Clear task name")
            }
        }
        .padding(.horizontal, 24)
        .padding(.top, 20)
        .padding(.bottom, 16)
        .animation(.easeOut(duration: ADHDAnimations.fast), value: taskName.isEmpty)
    }

    private var indicatorColor: Color {
        canSubmit ? ADHDColors.Accent.success : ADHDColors.Accent.focus
    }
}

// MARK: - Duration Section

private struct DurationSection: View {
    @Binding var selectedDuration: FocusDuration

    var body: some View {
        VStack(alignment: .leading, spacing: ADHDSpacing.md) {
            Text("FOCUS DURATION")
                .font(ADHDTypography.App.micro)
                .foregroundStyle(ADHDColors.Text.tertiary)
                .tracking(0.08 * 11) // 0.08em at 11px

            HStack(spacing: ADHDSpacing.sm) {
                ForEach(FocusDuration.allCases) { duration in
                    DurationChip(
                        duration: duration,
                        isSelected: selectedDuration == duration,
                        action: { selectedDuration = duration }
                    )
                }
            }
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 16)
    }
}

private struct DurationChip: View {
    let duration: FocusDuration
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(duration.label)
                .font(
                    isSelected
                        ? ADHDTypography.App.captionMedium
                        : ADHDTypography.App.caption
                )
                .foregroundStyle(
                    isSelected
                        ? ADHDColors.Text.inverse
                        : ADHDColors.Accent.focusLight
                )
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 10)
                        .fill(
                            ADHDColors.Accent.focus.opacity(isSelected ? 0.3 : 0.12)
                        )
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(
                            ADHDColors.Accent.focus.opacity(isSelected ? 0.5 : 0.25),
                            lineWidth: 1
                        )
                )
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(duration.label) focus duration")
        .accessibilityAddTraits(isSelected ? .isSelected : [])
    }
}

// MARK: - Action Footer

private struct ActionFooter: View {
    let canSubmit: Bool
    let onSubmit: () -> Void

    var body: some View {
        VStack(spacing: ADHDSpacing.md) {
            Button(action: onSubmit) {
                HStack(spacing: ADHDSpacing.sm) {
                    // Play triangle icon
                    Image(systemName: "play.fill")
                        .font(.system(size: 12))
                        .foregroundStyle(
                            canSubmit
                                ? ADHDColors.Text.inverse
                                : ADHDColors.Accent.focusLight
                        )

                    Text("Start Focus")
                        .font(ADHDTypography.App.bodyMedium)
                        .foregroundStyle(
                            canSubmit
                                ? ADHDColors.Text.inverse
                                : ADHDColors.Text.inverse.opacity(0.6)
                        )

                    Text("\u{23CE}")
                        .font(ADHDTypography.App.small)
                        .foregroundStyle(ADHDColors.Text.tertiary)
                        .padding(.leading, ADHDSpacing.sm)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .fill(
                            ADHDColors.Accent.focus.opacity(canSubmit ? 0.4 : 0.25)
                        )
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(
                            ADHDColors.Accent.focus.opacity(canSubmit ? 0.6 : 0.3),
                            lineWidth: 1
                        )
                )
            }
            .buttonStyle(.plain)
            .disabled(!canSubmit)
            .accessibilityLabel("Start focus session")

            HStack(spacing: 16) {
                Text("esc to cancel")
                    .font(ADHDTypography.App.tiny)
                    .foregroundStyle(ADHDColors.Text.muted)

                Text("\u{2318}\u{21E7}T to toggle")
                    .font(ADHDTypography.App.tiny)
                    .foregroundStyle(ADHDColors.Text.muted)
            }
        }
        .padding(.horizontal, 24)
        .padding(.top, 12)
        .padding(.bottom, 20)
    }
}
