import SwiftUI

/// Intervention banner matching Paper design: emoji + title + body + action button + dismiss.
/// Used inside the notch alert overlay state.
struct InterventionBanner: View {
    let message: InterventionMessage
    let onDismiss: () -> Void
    let onAccept: () -> Void

    var body: some View {
        HStack(spacing: ADHDSpacing.md) {
            Text(message.emoji)
                .font(.system(size: 20))

            MessageContent(message: message)

            Spacer()

            AcceptButton(label: message.actionLabel, action: onAccept)

            DismissButton(action: onDismiss)
        }
        .padding(ADHDSpacing.notchPaddingH)
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
            Text(message.title)
                .font(ADHDTypography.Notch.glanceTitle)
                .foregroundStyle(ADHDColors.Text.inverse)

            Text(message.body)
                .font(ADHDTypography.Notch.glanceBody)
                .foregroundStyle(ADHDColors.Text.inverse.opacity(0.8))
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
                .background(ADHDColors.Accent.focusLight.opacity(0.1))
                .clipShape(Capsule())
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
