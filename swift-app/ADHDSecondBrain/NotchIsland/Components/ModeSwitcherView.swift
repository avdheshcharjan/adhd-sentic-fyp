import SwiftUI

/// Mode switcher matching Paper design: pill buttons with emoji + label.
/// Selected mode: #457B9D at 30% bg, white text. Unselected: 50% white text, no bg.
struct ModeSwitcherView: View {
    @Binding var selectedMode: NotchDisplayMode

    var body: some View {
        HStack(spacing: ADHDSpacing.sm) {
            ForEach(NotchDisplayMode.allCases, id: \.self) { mode in
                ModeButton(
                    mode: mode,
                    isSelected: selectedMode == mode,
                    action: { selectedMode = mode }
                )
            }
        }
    }
}

private struct ModeButton: View {
    let mode: NotchDisplayMode
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: ADHDSpacing.xs) {
                Text(mode.emoji)
                    .font(.system(size: 12))
                Text(mode.label)
                    .font(ADHDTypography.Notch.glanceCaption)
                    .foregroundStyle(
                        isSelected
                            ? ADHDColors.Text.inverse
                            : ADHDColors.Text.inverse.opacity(0.5)
                    )
            }
            .padding(.horizontal, ADHDSpacing.sm)
            .padding(.vertical, ADHDSpacing.xs)
            .background(
                isSelected
                    ? ADHDColors.Accent.focus.opacity(0.3)
                    : Color.clear
            )
            .clipShape(RoundedRectangle(cornerRadius: ADHDSpacing.sm))
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(mode.label) mode")
        .accessibilityAddTraits(isSelected ? .isSelected : [])
    }
}
