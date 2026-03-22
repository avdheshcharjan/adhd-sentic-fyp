import SwiftUI

// MARK: - VentView

struct VentView: View {

    @Bindable var viewModel: VentViewModel
    @FocusState private var isInputFocused: Bool
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        ZStack {
            VisualEffectBackground(material: .sidebar, blendingMode: .behindWindow)

            VStack(spacing: 0) {
                headerBar
                chatArea
                lockIndicator
                inputBar
            }
        }
        .frame(width: 440, height: 560)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .strokeBorder(ADHDColors.Window.borderSubtle, lineWidth: 1)
        )
        .onAppear {
            isInputFocused = true
        }
    }

    // MARK: - Header

    private var headerBar: some View {
        HStack(spacing: 10) {
            // Icon
            Image(systemName: "bubble.left.and.bubble.right.fill")
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(ADHDColors.Accent.calm)

            Text("Vent Space")
                .font(Font.custom("Lexend-SemiBold", size: 16))
                .foregroundColor(ADHDColors.Text.primary)

            Spacer()

            Button {
                viewModel.startNewSession()
            } label: {
                Text("New Session")
                    .font(Font.custom("Lexend-Regular", size: 12))
                    .foregroundColor(ADHDColors.Text.secondary)
                    .padding(.vertical, 5)
                    .padding(.horizontal, 10)
                    .background(ADHDColors.Background.secondary.opacity(0.6))
                    .cornerRadius(8)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Start new vent session")
            .accessibilityHint("Clears the current conversation and starts fresh")
        }
        .padding(.horizontal, 16)
        .padding(.top, 16)
        .padding(.bottom, 10)
    }

    // MARK: - Chat Area

    private var chatArea: some View {
        ScrollViewReader { proxy in
            ScrollView(.vertical, showsIndicators: false) {
                LazyVStack(spacing: 10) {
                    if viewModel.messages.isEmpty {
                        welcomeCard
                            .padding(.top, 16)
                    } else {
                        ForEach(viewModel.messages) { message in
                            VentMessageBubble(message: message)
                                .id(message.id)
                                .padding(.horizontal, 14)
                        }
                        // Scroll anchor at bottom
                        Color.clear
                            .frame(height: 1)
                            .id("bottom")
                    }
                }
                .padding(.vertical, 8)
            }
            .onChange(of: viewModel.messages.count) { _, _ in
                withAnimation(reduceMotion ? nil : .easeOut(duration: 0.25)) {
                    proxy.scrollTo("bottom", anchor: .bottom)
                }
            }
            .onChange(of: viewModel.messages.last?.content) { _, _ in
                withAnimation(reduceMotion ? nil : .easeOut(duration: 0.1)) {
                    proxy.scrollTo("bottom", anchor: .bottom)
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Welcome Card

    private var welcomeCard: some View {
        VStack(spacing: 12) {
            Text("This is your space.")
                .font(Font.custom("Lexend-Medium", size: 14))
                .foregroundColor(ADHDColors.Text.primary)
                .multilineTextAlignment(.center)

            Text("Whatever you share here stays on your device. I'm here to listen — not to judge, fix, or diagnose. Just talk.")
                .font(Font.custom("Lexend-Regular", size: 13))
                .foregroundColor(ADHDColors.Text.secondary)
                .multilineTextAlignment(.center)
                .lineSpacing(4)

            HStack(spacing: 6) {
                Image(systemName: "lock.fill")
                    .font(.system(size: 11))
                    .foregroundColor(ADHDColors.Text.muted)
                Text("On-device only")
                    .font(Font.custom("Lexend-Regular", size: 11))
                    .foregroundColor(ADHDColors.Text.muted)
            }
            .padding(.top, 4)
        }
        .padding(20)
        .background(ADHDColors.Background.elevated.opacity(0.6))
        .cornerRadius(12)
        .padding(.horizontal, 20)
    }

    // MARK: - Lock Indicator

    private var lockIndicator: some View {
        HStack(spacing: 5) {
            Image(systemName: "lock.fill")
                .font(.system(size: 10))
                .foregroundColor(ADHDColors.Text.muted)
            Text("On-device only")
                .font(Font.custom("Lexend-Regular", size: 10))
                .foregroundColor(ADHDColors.Text.muted)
        }
        .padding(.bottom, 6)
    }

    // MARK: - Input Bar

    private var inputBar: some View {
        HStack(spacing: 10) {
            TextField("What's on your mind?", text: $viewModel.inputText)
                .font(Font.custom("Lexend-Regular", size: 14))
                .foregroundColor(ADHDColors.Text.primary)
                .textFieldStyle(.plain)
                .focused($isInputFocused)
                .disabled(viewModel.isGenerating)
                .onSubmit {
                    viewModel.sendMessage()
                }
                .accessibilityLabel("Vent message field")
                .accessibilityHint("Type what's on your mind and press Return to send")

            sendButton
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(ADHDColors.Background.elevated.opacity(0.7))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .padding(.horizontal, 12)
        .padding(.bottom, 12)
    }

    // MARK: - Send Button

    private var sendButton: some View {
        Button {
            viewModel.sendMessage()
        } label: {
            Image(systemName: "arrow.up")
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(viewModel.isGenerating ? ADHDColors.Text.muted : .white)
                .frame(width: 28, height: 28)
                .background(
                    Circle()
                        .fill(viewModel.isGenerating ? ADHDColors.Background.secondary : ADHDColors.Accent.focus)
                )
        }
        .buttonStyle(.plain)
        .disabled(viewModel.isGenerating || viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        .accessibilityLabel("Send message")
        .accessibilityHint("Send your message to the vent assistant")
    }
}
