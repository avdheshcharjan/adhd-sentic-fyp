import SwiftUI

// MARK: - VentMessageBubble

struct VentMessageBubble: View {
    let message: VentViewModel.VentMessage

    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private var isUser: Bool { message.role == "user" }

    var body: some View {
        HStack {
            if isUser { Spacer(minLength: 40) }

            bubbleContent
                .frame(maxWidth: .infinity, alignment: isUser ? .trailing : .leading)

            if !isUser { Spacer(minLength: 40) }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(isUser ? "You" : "Assistant"): \(message.content)")
    }

    // MARK: - Bubble

    @ViewBuilder
    private var bubbleContent: some View {
        Group {
            if message.isStreaming && message.content.isEmpty {
                streamingIndicator
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
            } else {
                Text(message.content)
                    .font(Font.custom("Lexend-Regular", size: 14))
                    .foregroundColor(ADHDColors.Text.primary)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .textSelection(.enabled)
            }
        }
        .background(bubbleBackground)
        .clipShape(bubbleShape)
    }

    // MARK: - Streaming Indicator

    @ViewBuilder
    private var streamingIndicator: some View {
        if reduceMotion {
            Text("...")
                .font(Font.custom("Lexend-Regular", size: 14))
                .foregroundColor(ADHDColors.Text.secondary)
        } else {
            ThreeDotPulse()
        }
    }

    // MARK: - Background Color

    private var bubbleBackground: Color {
        isUser
            ? ADHDColors.Accent.focus.opacity(0.15)
            : ADHDColors.Background.elevated
    }

    // MARK: - Bubble Shape (asymmetric corners)

    private var bubbleShape: some Shape {
        isUser
            ? UnevenRoundedRectangle(
                topLeadingRadius: 16,
                bottomLeadingRadius: 16,
                bottomTrailingRadius: 4,
                topTrailingRadius: 16
              )
            : UnevenRoundedRectangle(
                topLeadingRadius: 4,
                bottomLeadingRadius: 16,
                bottomTrailingRadius: 16,
                topTrailingRadius: 16
              )
    }
}

// MARK: - Three Dot Pulse

private struct ThreeDotPulse: View {
    @State private var phase: Int = 0

    var body: some View {
        HStack(spacing: 4) {
            ForEach(0..<3, id: \.self) { index in
                Circle()
                    .fill(ADHDColors.Text.muted)
                    .frame(width: 6, height: 6)
                    .opacity(phase == index ? 1.0 : 0.3)
            }
        }
        .onAppear {
            withAnimation(
                .easeInOut(duration: 0.4)
                .repeatForever(autoreverses: false)
            ) {
                startPulse()
            }
        }
    }

    private func startPulse() {
        let timer = Timer.scheduledTimer(withTimeInterval: 0.4, repeats: true) { _ in
            phase = (phase + 1) % 3
        }
        RunLoop.main.add(timer, forMode: .common)
    }
}
