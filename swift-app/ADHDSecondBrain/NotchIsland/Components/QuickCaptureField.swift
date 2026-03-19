import SwiftUI

struct QuickCaptureField: View {
    @State private var captureText = ""
    @FocusState private var isFocused: Bool
    let onSubmit: (String) -> Void

    @State private var currentPlaceholder = ""

    private let placeholders = [
        "Quick thought...",
        "What's on your mind?",
        "Capture it before it flies away...",
        "Drop a thought here...",
        "Brain dump zone...",
    ]

    var body: some View {
        HStack(spacing: ADHDSpacing.sm) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 14))
                .foregroundStyle(ADHDColors.Accent.calm)

            TextField(currentPlaceholder, text: $captureText)
                .font(ADHDTypography.Notch.expandedBody)
                .foregroundStyle(ADHDColors.Text.inverse)
                .textFieldStyle(.plain)
                .focused($isFocused)
                .onSubmit(submitCapture)
                .accessibilityLabel(
                    "Brain dump text field. Type a thought and press return to save."
                )

            if !captureText.isEmpty {
                SubmitButton(action: submitCapture)
                    .transition(.scale.combined(with: .opacity))
            }
        }
        .padding(ADHDSpacing.sm)
        .background(ADHDColors.Background.notchInner.opacity(0.5))
        .clipShape(RoundedRectangle(cornerRadius: ADHDSpacing.sm))
        .onAppear {
            currentPlaceholder = placeholders.randomElement() ?? placeholders[0]
        }
    }

    private func submitCapture() {
        let trimmed = captureText.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        onSubmit(trimmed)
        captureText = ""
    }
}

private struct SubmitButton: View {
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: "arrow.up.circle.fill")
                .font(.system(size: 18))
                .foregroundStyle(ADHDColors.Accent.focus)
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Send thought")
    }
}
