import SwiftUI

/// Intervention banner matching Paper design: emoji + title + body + action button + dismiss.
/// Used inside the notch alert overlay state.
///
/// Paper spec:
/// - Padding: 8px top, 12px sides/bottom
/// - Accept button: 8px radius rounded rectangle, rgba(69,123,157,0.3) background
/// - Emoji: 18px font size
/// - Title: Lexend SemiBold 14px
/// - Body: 12px, #ABABAB
struct InterventionBanner: View {
    let message: InterventionMessage
    let onDismiss: () -> Void
    let onAccept: () -> Void

    var body: some View {
        HStack(spacing: ADHDSpacing.md) {
            Text(message.emoji)
                .font(.system(size: 18))

            MessageContent(message: message)

            Spacer()

            AcceptButton(label: message.actionLabel, action: onAccept)

            DismissButton(action: onDismiss)
        }
        // Paper: 8px top, 12px horizontal, 12px bottom
        .padding(.top, ADHDSpacing.sm)
        .padding(.horizontal, ADHDSpacing.notchPaddingH)
        .padding(.bottom, ADHDSpacing.notchPaddingH)
        .accessibilityElement(children: .combine)
        .accessibilityLabel(
            "\(message.title). \(message.body)"
        )
    }
}

private struct MessageContent: View {
    let message: InterventionMessage

    var body: some View {
        VStack(alignment: .leading, spacing: ADHDSpacing.xxs) {
            // Paper: Lexend SemiBold 14px
            Text(message.title)
                .font(ADHDTypography.Notch.alertTitle)
                .foregroundStyle(ADHDColors.Text.inverse)

            // Paper: 12px, #ABABAB — use ambientLabel (Lexend Regular 12px)
            Text(message.body)
                .font(ADHDTypography.Notch.ambientLabel)
                .foregroundStyle(ADHDColors.Text.notchMuted)
                .lineLimit(2)
        }
    }
}

private struct AcceptButton: View {
    let label: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(ADHDTypography.Notch.glanceCaption)
                .foregroundStyle(ADHDColors.Accent.focusLight)
                .padding(.horizontal, ADHDSpacing.md)
                .padding(.vertical, ADHDSpacing.xs)
                // Paper: 8px radius rounded rectangle (NOT capsule), rgba(69,123,157,0.3) bg
                .background(ADHDColors.Accent.focus.opacity(0.3))
                .clipShape(RoundedRectangle(cornerRadius: ADHDSpacing.sm))
        }
        .buttonStyle(.plain)
        .accessibilityLabel(label)
    }
}

private struct DismissButton: View {
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: "xmark")
                .font(.system(size: 10, weight: .medium))
                .foregroundStyle(ADHDColors.Text.inverse.opacity(0.5))
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Dismiss")
    }
}
