import SwiftUI

// MARK: - BrainDumpView

struct BrainDumpView: View {

    @Bindable var viewModel: BrainDumpViewModel
    let onSubmit: () -> Void

    @FocusState private var isTextFocused: Bool

    private var timestampText: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "h:mm a"
        return "Captured at \(formatter.string(from: Date()))"
    }

    var body: some View {
        ZStack {
            VisualEffectBackground(material: .sidebar, blendingMode: .behindWindow)

            VStack(spacing: 0) {
                headerBar

                if viewModel.isCaptured {
                    summaryArea
                } else {
                    textEditorArea
                }

                bottomBar
            }
        }
        .frame(width: 520, height: 340)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .strokeBorder(ADHDColors.Window.borderSubtle, lineWidth: 1)
        )
        .onAppear {
            isTextFocused = true
        }
    }

    // MARK: - Header

    private var headerBar: some View {
        HStack {
            Text(viewModel.isCaptured ? "Captured" : "What's on your mind?")
                .font(Font.custom("Lexend-SemiBold", size: 16))
                .foregroundColor(viewModel.isCaptured ? ADHDColors.Accent.success : ADHDColors.Text.primary)

            Spacer()

            savedIndicator
        }
        .padding(.horizontal, 16)
        .padding(.top, 16)
        .padding(.bottom, 10)
    }

    @ViewBuilder
    private var savedIndicator: some View {
        if viewModel.isCaptured {
            HStack(spacing: 4) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 13))
                    .foregroundColor(ADHDColors.Accent.success)
                Text("Saved")
                    .font(Font.custom("Lexend-Regular", size: 12))
                    .foregroundColor(ADHDColors.Accent.success)
            }
            .transition(.opacity.combined(with: .scale(scale: 0.85)))
        } else if viewModel.isSaved && !viewModel.noteText.isEmpty {
            HStack(spacing: 4) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 13))
                    .foregroundColor(ADHDColors.Text.muted)
                Text("saved")
                    .font(Font.custom("Lexend-Regular", size: 12))
                    .foregroundColor(ADHDColors.Text.muted)
            }
            .transition(.opacity)
        }
    }

    // MARK: - Text Editor

    private var textEditorArea: some View {
        ZStack(alignment: .topLeading) {
            if viewModel.noteText.isEmpty && !viewModel.isSubmitting {
                Text("Capture it before it flies away...")
                    .font(Font.custom("Lexend-Regular", size: 14))
                    .foregroundColor(ADHDColors.Text.muted)
                    .padding(.horizontal, 20)
                    .padding(.top, 8)
                    .allowsHitTesting(false)
            }

            TextEditor(text: Binding(
                get: { viewModel.noteText },
                set: { viewModel.textChanged($0) }
            ))
            .font(Font.custom("Lexend-Regular", size: 14))
            .foregroundColor(ADHDColors.Text.primary)
            .scrollContentBackground(.hidden)
            .background(Color.clear)
            .focused($isTextFocused)
            .padding(.horizontal, 14)
            .padding(.vertical, 4)
            .disabled(viewModel.isSubmitting)
            .accessibilityLabel("Brain dump text field")
            .accessibilityHint("Type your thoughts and press Command Return to capture")
            .onKeyPress(.return, phases: .down) { press in
                if press.modifiers.contains(.command) {
                    Task { await handleSubmit() }
                    return .handled
                }
                return .ignored
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Summary Area (post-capture)

    private var summaryArea: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(alignment: .leading, spacing: 12) {
                if viewModel.summaryText.isEmpty {
                    HStack(spacing: 8) {
                        ProgressView()
                            .progressViewStyle(.circular)
                            .scaleEffect(0.7)
                        Text("Thinking...")
                            .font(Font.custom("Lexend-Regular", size: 13))
                            .foregroundColor(ADHDColors.Text.muted)
                    }
                    .padding(.top, 16)
                } else {
                    Text(viewModel.summaryText)
                        .font(Font.custom("Lexend-Regular", size: 14))
                        .foregroundColor(ADHDColors.Text.secondary)
                        .lineSpacing(5)
                        .animation(.easeIn(duration: 0.15), value: viewModel.summaryText)
                }
            }
            .padding(.horizontal, 18)
            .padding(.vertical, 12)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .transition(.opacity.combined(with: .move(edge: .bottom)))
    }

    // MARK: - Bottom Bar

    private var bottomBar: some View {
        HStack(spacing: 8) {
            if viewModel.isCaptured {
                Text(timestampText)
                    .font(Font.custom("Lexend-Regular", size: 11))
                    .foregroundColor(ADHDColors.Text.muted)

                Spacer()

                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        viewModel.resetForNewDump()
                    }
                } label: {
                    Text("New Dump")
                        .font(Font.custom("Lexend-Medium", size: 13))
                        .foregroundColor(ADHDColors.Text.secondary)
                        .padding(.vertical, 6)
                        .padding(.horizontal, 14)
                        .background(ADHDColors.Background.secondary.opacity(0.6))
                        .cornerRadius(8)
                }
                .buttonStyle(.plain)

                Button {
                    onSubmit()
                    viewModel.resetForNewDump()
                } label: {
                    Text("Done")
                        .font(Font.custom("Lexend-Medium", size: 13))
                        .foregroundColor(.white)
                        .padding(.vertical, 6)
                        .padding(.horizontal, 14)
                        .background(ADHDColors.Accent.focus)
                        .cornerRadius(8)
                }
                .buttonStyle(.plain)
            } else {
                Text(timestampText)
                    .font(Font.custom("Lexend-Regular", size: 11))
                    .foregroundColor(ADHDColors.Text.muted)

                Spacer()

                Text("\u{2318}\u{21A9} to capture")
                    .font(Font.custom("Lexend-Regular", size: 11))
                    .foregroundColor(ADHDColors.Text.muted)

                captureButton
            }
        }
        .padding(.horizontal, 16)
        .padding(.bottom, 14)
        .padding(.top, 8)
    }

    private var captureButton: some View {
        Button {
            Task { await handleSubmit() }
        } label: {
            Group {
                if viewModel.isSubmitting {
                    ProgressView()
                        .progressViewStyle(.circular)
                        .scaleEffect(0.7)
                        .frame(width: 16, height: 16)
                } else {
                    Text("Capture")
                        .font(Font.custom("Lexend-Medium", size: 13))
                }
            }
            .foregroundColor(.white)
            .padding(.vertical, 6)
            .padding(.horizontal, 14)
            .background(ADHDColors.Accent.focus)
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
        .disabled(viewModel.isSubmitting || viewModel.noteText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        .accessibilityLabel("Capture thought")
        .accessibilityHint("Submit the brain dump to the backend")
    }

    // MARK: - Actions

    private func handleSubmit() async {
        await viewModel.submit()
    }
}
