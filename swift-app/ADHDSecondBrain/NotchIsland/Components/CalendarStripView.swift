import SwiftUI

/// Calendar strip matching Paper design:
/// - 12px radius, 10px vertical / 12px horizontal padding, rgba(28,28,30,0.5) bg
/// - Each row: emoji + title (Lexend Regular 14px) + time (Lexend Regular 12px, #75757B)
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
        // Paper: 10px vertical, 12px horizontal
        .padding(.vertical, 10)
        .padding(.horizontal, ADHDSpacing.cardPadding)
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
                .font(.system(size: 14))

            Text("No upcoming events")
                .font(ADHDTypography.App.body)
                .foregroundStyle(ADHDColors.Text.inverse.opacity(0.5))

            Spacer()

            if let onConnect {
                Button(action: onConnect) {
                    Text("Connect")
                        .font(ADHDTypography.Notch.ambientLabel)
                        .foregroundStyle(ADHDColors.Accent.focusLight)
                        .padding(.horizontal, ADHDSpacing.sm)
                        .padding(.vertical, ADHDSpacing.xxs)
                        .background(ADHDColors.Accent.focusLight.opacity(0.1))
                        .clipShape(RoundedRectangle(cornerRadius: ADHDSpacing.sm))
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
                .font(.system(size: 14))

            // Paper: Lexend Regular 14px (expandedBody)
            Text(event.title)
                .font(ADHDTypography.Notch.expandedBody)
                .foregroundStyle(ADHDColors.Text.inverse)
                .lineLimit(1)

            Spacer()

            // Paper: Lexend Regular 12px, #75757B
            Text(event.startTime)
                .font(ADHDTypography.Notch.ambientLabel)
                .foregroundStyle(ADHDColors.Text.tertiary)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(event.title) at \(event.startTime)")
    }
}
