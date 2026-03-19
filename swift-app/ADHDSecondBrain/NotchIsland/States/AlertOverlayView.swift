import SwiftUI

struct AlertOverlayView: View {
    let tier: InterventionTier
    let message: InterventionMessage?
    let onAcknowledge: () -> Void

    var body: some View {
        VStack(spacing: ADHDSpacing.sm) {
            if let message {
                InterventionBanner(
                    message: message,
                    onDismiss: onAcknowledge,
                    onAccept: onAcknowledge
                )
            } else {
                FallbackAlert(onAcknowledge: onAcknowledge)
            }
        }
        .interventionPulse(
            color: tierColor,
            isActive: true,
            tier: tier
        )
        .accessibilityElement(children: .contain)
    }

    private var tierColor: Color {
        switch tier {
        case .passive: ADHDColors.Intervention.dormant
        case .gentle: ADHDColors.Intervention.gentle
        case .timeSensitive: ADHDColors.Intervention.timely
        case .actionRequired: ADHDColors.Intervention.timely
        case .critical: ADHDColors.Intervention.critical
        }
    }
}

private struct FallbackAlert: View {
    let onAcknowledge: () -> Void

    var body: some View {
        HStack {
            Text("Heads up")
                .font(ADHDTypography.Notch.glanceTitle)
                .foregroundStyle(ADHDColors.Text.inverse)

            Spacer()

            Button(action: onAcknowledge) {
                Text("Got it")
                    .font(ADHDTypography.Notch.glanceCaption)
                    .foregroundStyle(ADHDColors.Text.inverse)
                    .padding(.horizontal, ADHDSpacing.sm)
                    .padding(.vertical, ADHDSpacing.xs)
                    .background(ADHDColors.Accent.focus.opacity(0.3))
                    .clipShape(
                        RoundedRectangle(cornerRadius: ADHDSpacing.sm)
                    )
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Acknowledge")
        }
        .padding(ADHDSpacing.notchPaddingH)
    }
}
