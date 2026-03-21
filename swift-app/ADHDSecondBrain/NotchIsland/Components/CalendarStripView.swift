import SwiftUI

/// Calendar strip matching Paper design: emoji + event name (11px) + time (10px).
/// Dark inner card with 12px padding, 12px corner radius.
struct CalendarStripView: View {
    let events: [CalendarEvent]
    var onConnectCalendar: (() -> Void)?

    var body: some View {
        VStack(alignment: .leading, spacing: ADHDSpacing.xs) {
            if events.isEmpty {
                CalendarEmptyState(onConnect: onConnectCalendar)
            } else {
                ForEach(events.prefix(3)) { event in
                    CalendarEventRow(event: event)
                }
            }
        }
        .padding(ADHDSpacing.cardPadding)
        .background(ADHDColors.Background.notchInner.opacity(0.5))
        .clipShape(RoundedRectangle(cornerRadius: ADHDSpacing.cardCornerRadius))
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Upcoming events")
    }
}

private struct CalendarEmptyState: View {
    let onConnect: (() -> Void)?

    var body: some View {
        HStack(spacing: ADHDSpacing.sm) {
            Text("\u{1F4C5}")
                .font(.system(size: 12))

            Text("No upcoming events")
                .font(ADHDTypography.Notch.glanceBody)
                .foregroundStyle(ADHDColors.Text.inverse.opacity(0.5))

            Spacer()

            if let onConnect {
                Button(action: onConnect) {
                    Text("Connect")
                        .font(ADHDTypography.Notch.glanceCaption)
                        .foregroundStyle(ADHDColors.Accent.focusLight)
                        .padding(.horizontal, ADHDSpacing.sm)
                        .padding(.vertical, ADHDSpacing.xxs)
                        .background(ADHDColors.Accent.focusLight.opacity(0.1))
                        .clipShape(Capsule())
                }
                .buttonStyle(.plain)
            }
        }
    }
}

private struct CalendarEventRow: View {
    let event: CalendarEvent

    var body: some View {
        HStack(spacing: ADHDSpacing.sm) {
            Text(event.emoji ?? "\u{1F4C5}")
                .font(.system(size: 12))

            Text(event.title)
                .font(ADHDTypography.Notch.glanceBody)
                .foregroundStyle(ADHDColors.Text.inverse)
                .lineLimit(1)

            Spacer()

            Text(event.startTime)
                .font(ADHDTypography.Notch.glanceCaption)
                .foregroundStyle(ADHDColors.Text.inverse.opacity(0.6))
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(event.title) at \(event.startTime)")
    }
}
