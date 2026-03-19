import SwiftUI

struct CalendarStripView: View {
    let events: [CalendarEvent]

    var body: some View {
        VStack(alignment: .leading, spacing: ADHDSpacing.xs) {
            ForEach(events.prefix(3)) { event in
                CalendarEventRow(event: event)
            }
        }
        .padding(ADHDSpacing.cardPadding)
        .background(ADHDColors.Background.notchInner.opacity(0.5))
        .clipShape(RoundedRectangle(cornerRadius: ADHDSpacing.cardCornerRadius))
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Upcoming events")
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
