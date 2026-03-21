import SwiftUI

/// Analytics dashboard matching the Paper design canvas.
/// Dark window with focus timeline, live metrics, emotion radar,
/// whoop recovery, interventions, and weekly report cards.
struct DashboardView: View {
    @ObservedObject var coordinator: MonitorCoordinator

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                DashboardHeader(coordinator: coordinator)
                FocusTimelineCard()
                MetricsEmotionRow(coordinator: coordinator)
                WhoopInterventionsRow(coordinator: coordinator)
                WeeklyReportCard()
            }
        }
        .background(ADHDColors.Background.primary)
        .frame(minWidth: 900, minHeight: 700)
    }
}

// MARK: - Header

private struct DashboardHeader: View {
    @ObservedObject var coordinator: MonitorCoordinator

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(greeting)
                    .font(ADHDTypography.Dashboard.greeting)
                    .foregroundStyle(ADHDColors.Text.primary)
                    .tracking(-0.3)

                Text(subtitleText)
                    .font(ADHDTypography.Dashboard.subtitle)
                    .foregroundStyle(ADHDColors.Text.secondary)
            }

            Spacer()

            LiveBadge()
        }
        .padding(.horizontal, 32)
        .padding(.top, 12)
        .padding(.bottom, 20)
    }

    private var greeting: String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 5..<12: return "Good morning"
        case 12..<17: return "Good afternoon"
        case 17..<21: return "Good evening"
        default: return "Good night"
        }
    }

    private var subtitleText: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "EEEE, d MMMM"
        let date = formatter.string(from: Date())
        let minutes = Int(coordinator.latestMetrics.currentStreakMinutes)
        let hours = minutes / 60
        let mins = minutes % 60
        if hours > 0 {
            return "\(date) — You've been focused for \(hours)h \(mins)m today"
        }
        return "\(date) — You've been focused for \(mins)m today"
    }
}

private struct LiveBadge: View {
    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(ADHDColors.Accent.successBright)
                .frame(width: 6, height: 6)

            Text("LIVE")
                .font(ADHDTypography.App.small)
                .fontWeight(.medium)
                .tracking(0.5)
                .foregroundStyle(ADHDColors.Accent.successBright)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 6)
        .background(ADHDColors.Accent.successBright.opacity(0.12))
        .clipShape(Capsule())
    }
}

// MARK: - Focus Timeline

private struct FocusTimelineCard: View {
    var body: some View {
        DashboardCard {
            VStack(spacing: 14) {
                HStack {
                    Text("Today's Focus Timeline")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)

                    Spacer()

                    Text("154 min tracked")
                        .font(ADHDTypography.App.small)
                        .foregroundStyle(ADHDColors.Text.secondary)
                }

                // Timeline bar
                HStack(spacing: 0) {
                    TimelineSegment(color: ADHDColors.Accent.successBright, width: 0.35)
                    TimelineSegment(color: ADHDColors.Text.muted, width: 0.08)
                    TimelineSegment(color: ADHDColors.Accent.successBright, width: 0.22)
                    TimelineSegment(color: ADHDColors.Accent.warning, width: 0.05)
                    TimelineSegment(color: ADHDColors.Accent.danger, width: 0.12)
                    TimelineSegment(color: ADHDColors.Accent.successBright, width: 0.18)
                }
                .frame(height: 28)
                .clipShape(RoundedRectangle(cornerRadius: 8))

                // Legend
                HStack(spacing: 20) {
                    LegendDot(color: ADHDColors.Accent.successBright, label: "Focused")
                    LegendDot(color: ADHDColors.Accent.danger, label: "Distracted")
                    LegendDot(color: ADHDColors.Accent.warning, label: "Neutral")
                    LegendDot(color: ADHDColors.Text.muted, label: "Idle")
                }
            }
        }
        .padding(.horizontal, 32)
    }
}

private struct TimelineSegment: View {
    let color: Color
    let width: CGFloat

    var body: some View {
        GeometryReader { proxy in
            Rectangle()
                .fill(color)
                .frame(width: proxy.size.width)
        }
        .frame(maxWidth: .infinity)
        .layoutPriority(Double(width * 100))
    }
}

private struct LegendDot: View {
    let color: Color
    let label: String

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            Text(label)
                .font(ADHDTypography.App.tiny)
                .foregroundStyle(ADHDColors.Text.secondary)
        }
    }
}

// MARK: - Metrics + Emotion Row

private struct MetricsEmotionRow: View {
    @ObservedObject var coordinator: MonitorCoordinator

    var body: some View {
        HStack(spacing: 16) {
            LiveMetricsCard(coordinator: coordinator)
            EmotionRadarCard()
        }
        .padding(.horizontal, 32)
        .padding(.top, 16)
    }
}

private struct LiveMetricsCard: View {
    @ObservedObject var coordinator: MonitorCoordinator

    var body: some View {
        DashboardCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Text("Live Metrics")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)
                    Spacer()
                    StateBadge(state: coordinator.latestMetrics.behavioralState)
                }

                VStack(spacing: 0) {
                    MetricRow(label: "Context switches (5 min)", value: "\(Int(coordinator.latestMetrics.contextSwitchRate5min))")
                    MetricRow(label: "Focus score", value: "\(Int(coordinator.latestMetrics.focusScore))%", valueColor: ADHDColors.Accent.successBright)
                    MetricRow(label: "Distraction ratio", value: "\(Int(coordinator.latestMetrics.distractionRatio * 100))%")
                    MetricRow(label: "Current streak", value: "\(Int(coordinator.latestMetrics.currentStreakMinutes)) min")
                    MetricRow(label: "Active app", value: coordinator.latestCategory, isLast: true)
                }

                VStack(spacing: 0) {
                    Text("TODAY")
                        .font(ADHDTypography.App.sectionLabel)
                        .tracking(0.7)
                        .foregroundStyle(ADHDColors.Text.tertiary)
                        .padding(.bottom, 8)

                    MetricRow(label: "Focus time", value: "154 min")
                    MetricRow(label: "Active time", value: "203 min", isLast: true)
                }
            }
        }
    }
}

private struct StateBadge: View {
    let state: String

    var body: some View {
        Text(state.uppercased())
            .font(ADHDTypography.Dashboard.badge)
            .tracking(0.5)
            .foregroundStyle(ADHDColors.Accent.focusLight)
            .padding(.horizontal, 12)
            .padding(.vertical, 4)
            .background(ADHDColors.Accent.focusLight.opacity(0.1))
            .clipShape(Capsule())
    }
}

private struct MetricRow: View {
    let label: String
    let value: String
    var valueColor: Color = ADHDColors.Text.primary
    var isLast: Bool = false

    var body: some View {
        HStack {
            Text(label)
                .font(ADHDTypography.Dashboard.metricLabel)
                .foregroundStyle(ADHDColors.Text.secondary)
            Spacer()
            Text(value)
                .font(ADHDTypography.Dashboard.metricValue)
                .monospacedDigit()
                .foregroundStyle(valueColor)
        }
        .padding(.vertical, 10)
    }
}

// MARK: - Emotion Radar

private struct EmotionRadarCard: View {
    var body: some View {
        DashboardCard {
            VStack(spacing: 16) {
                HStack {
                    Text("Emotion Radar")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)
                    Spacer()
                    Text("Current: Calm Focus")
                        .font(ADHDTypography.App.small)
                        .foregroundStyle(ADHDColors.Text.secondary)
                }

                // Radar visualization
                RadarChartView()
                    .frame(height: 200)

                // Score pills
                HStack(spacing: 16) {
                    ScorePill(value: "72", label: "PLEASANT")
                    ScorePill(value: "85", label: "ATTENTION")
                    ScorePill(value: "38", label: "SENSITIV.")
                    ScorePill(value: "64", label: "APTITUDE")
                }
            }
        }
    }
}

private struct RadarChartView: View {
    var body: some View {
        ZStack {
            // Concentric circles
            ForEach([180, 120, 60], id: \.self) { size in
                Circle()
                    .strokeBorder(
                        ADHDColors.Text.muted.opacity(size == 180 ? 0.4 : size == 120 ? 0.3 : 0.2),
                        lineWidth: 1
                    )
                    .frame(width: CGFloat(size), height: CGFloat(size))
            }

            // Data shape
            RadarShape()
                .fill(ADHDColors.Accent.focusLight.opacity(0.15))
                .overlay(
                    RadarShape()
                        .stroke(ADHDColors.Accent.focusLight.opacity(0.6), lineWidth: 2)
                )
                .frame(width: 140, height: 150)

            // Axis labels
            VStack {
                Text("Pleasantness")
                    .font(ADHDTypography.App.tiny)
                    .fontWeight(.medium)
                    .foregroundStyle(ADHDColors.Text.primary)
                Spacer()
                Text("Sensitivity")
                    .font(ADHDTypography.App.tiny)
                    .fontWeight(.medium)
                    .foregroundStyle(ADHDColors.Text.primary)
            }
            .frame(height: 210)

            HStack {
                Text("Aptitude")
                    .font(ADHDTypography.App.tiny)
                    .fontWeight(.medium)
                    .foregroundStyle(ADHDColors.Text.primary)
                Spacer()
                Text("Attention")
                    .font(ADHDTypography.App.tiny)
                    .fontWeight(.medium)
                    .foregroundStyle(ADHDColors.Text.primary)
            }
            .frame(width: 240)
        }
    }
}

private struct RadarShape: Shape {
    func path(in rect: CGRect) -> Path {
        let center = CGPoint(x: rect.midX, y: rect.midY)
        let maxRadius = min(rect.width, rect.height) / 2

        var path = Path()
        let points: [(angle: Double, radius: Double)] = [
            (-.pi / 2, 0.8),     // Top - Pleasantness
            (0, 0.9),            // Right - Attention
            (.pi / 2, 0.4),      // Bottom - Sensitivity
            (.pi, 0.65),         // Left - Aptitude
        ]

        for (index, point) in points.enumerated() {
            let x = center.x + CGFloat(cos(point.angle)) * maxRadius * CGFloat(point.radius)
            let y = center.y + CGFloat(sin(point.angle)) * maxRadius * CGFloat(point.radius)
            if index == 0 {
                path.move(to: CGPoint(x: x, y: y))
            } else {
                path.addLine(to: CGPoint(x: x, y: y))
            }
        }
        path.closeSubpath()
        return path
    }
}

private struct ScorePill: View {
    let value: String
    let label: String

    var body: some View {
        VStack(spacing: 4) {
            Text(value)
                .font(ADHDTypography.Dashboard.statValue)
                .monospacedDigit()
                .foregroundStyle(ADHDColors.Accent.focusLight)

            Text(label)
                .font(ADHDTypography.Dashboard.statLabel)
                .tracking(0.5)
                .foregroundStyle(ADHDColors.Text.tertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 10)
        .background(ADHDColors.Background.elevated)
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

// MARK: - Whoop + Interventions Row

private struct WhoopInterventionsRow: View {
    @ObservedObject var coordinator: MonitorCoordinator

    var body: some View {
        HStack(spacing: 16) {
            WhoopRecoveryCard()
            InterventionsCard()
        }
        .padding(.horizontal, 32)
        .padding(.top, 16)
    }
}

private struct WhoopRecoveryCard: View {
    var body: some View {
        DashboardCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Text("Whoop Recovery")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)
                    Spacer()
                    HStack(spacing: 6) {
                        Circle()
                            .fill(ADHDColors.Accent.successBright)
                            .frame(width: 8, height: 8)
                        Text("78%")
                            .font(ADHDTypography.App.metricLarge)
                            .monospacedDigit()
                            .foregroundStyle(ADHDColors.Accent.successBright)
                    }
                }

                VStack(spacing: 0) {
                    MetricRow(label: "HRV (rMSSD)", value: "62.3 ms")
                    MetricRow(label: "Resting HR", value: "54 bpm")
                    MetricRow(label: "Sleep performance", value: "85%")
                    MetricRow(label: "Recommended focus block", value: "45 min", valueColor: ADHDColors.Accent.focusLight, isLast: true)
                }
            }
        }
    }
}

private struct InterventionsCard: View {
    var body: some View {
        DashboardCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Text("Interventions")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)
                    Spacer()
                    Text("Today")
                        .font(ADHDTypography.App.small)
                        .foregroundStyle(ADHDColors.Text.secondary)
                }

                VStack(spacing: 0) {
                    MetricRow(label: "Triggered", value: "5")
                    MetricRow(label: "Accepted", value: "4")
                    MetricRow(label: "Acceptance rate", value: "80%", valueColor: ADHDColors.Accent.successBright, isLast: true)
                }

                VStack(spacing: 8) {
                    Text("BEHAVIORAL STATES (MIN)")
                        .font(ADHDTypography.App.sectionLabel)
                        .tracking(0.7)
                        .foregroundStyle(ADHDColors.Text.tertiary)

                    HStack(spacing: 8) {
                        BehaviorPill(value: "98", label: "FOCUSED", color: ADHDColors.Accent.successBright)
                        BehaviorPill(value: "56", label: "HYPERF.", color: ADHDColors.Accent.focusLight)
                        BehaviorPill(value: "24", label: "DISTRACT.", color: ADHDColors.Accent.danger)
                    }
                }
            }
        }
    }
}

private struct BehaviorPill: View {
    let value: String
    let label: String
    let color: Color

    var body: some View {
        VStack(spacing: 4) {
            Text(value)
                .font(ADHDTypography.Dashboard.statValue)
                .monospacedDigit()
                .foregroundStyle(color)

            Text(label)
                .font(ADHDTypography.Dashboard.statLabel)
                .tracking(0.5)
                .foregroundStyle(ADHDColors.Text.tertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 10)
        .background(ADHDColors.Background.elevated)
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

// MARK: - Weekly Report

private struct WeeklyReportCard: View {
    private let dayData: [(day: String, focus: CGFloat, distraction: CGFloat, isToday: Bool)] = [
        ("Mon", 0.65, 0.25, false),
        ("Tue", 0.72, 0.18, false),
        ("Wed", 0.55, 0.35, false),
        ("Thu", 0.80, 0.12, false),
        ("Fri", 0.87, 0.10, true),
        ("Sat", 0.40, 0.08, false),
        ("Sun", 0.35, 0.05, false),
    ]

    var body: some View {
        VStack(spacing: 0) {
            DashboardCard {
                VStack(spacing: 16) {
                    HStack {
                        Text("Weekly Report")
                            .font(ADHDTypography.Dashboard.cardTitle)
                            .foregroundStyle(ADHDColors.Text.primary)
                        Spacer()
                        Text("IMPROVING")
                            .font(ADHDTypography.Dashboard.badge)
                            .tracking(0.5)
                            .foregroundStyle(ADHDColors.Accent.successBright)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 4)
                            .background(ADHDColors.Accent.successBright.opacity(0.12))
                            .clipShape(Capsule())
                    }

                    // Bar chart
                    HStack(alignment: .bottom, spacing: 12) {
                        ForEach(dayData, id: \.day) { item in
                            DayBar(
                                day: item.day,
                                focus: item.focus,
                                distraction: item.distraction,
                                isToday: item.isToday,
                                isFuture: item.focus < 0.5 && !item.isToday
                            )
                        }
                    }
                    .frame(height: 140)
                    .padding(.horizontal, 8)

                    // Legend
                    HStack(spacing: 20) {
                        HStack(spacing: 6) {
                            RoundedRectangle(cornerRadius: 2)
                                .fill(ADHDColors.Accent.successBright)
                                .frame(width: 8, height: 8)
                            Text("Focus")
                                .font(ADHDTypography.App.tiny)
                                .foregroundStyle(ADHDColors.Text.secondary)
                        }
                        HStack(spacing: 6) {
                            RoundedRectangle(cornerRadius: 2)
                                .fill(ADHDColors.Accent.danger)
                                .frame(width: 8, height: 8)
                            Text("Distraction")
                                .font(ADHDTypography.App.tiny)
                                .foregroundStyle(ADHDColors.Text.secondary)
                        }
                    }
                    .padding(.horizontal, 8)

                    // Summary stats
                    HStack(spacing: 16) {
                        WeeklyStat(label: "Avg focus", value: "71.2%")
                        WeeklyStat(label: "Avg distraction", value: "15.4%")
                        WeeklyStat(label: "Total interventions", value: "23")
                        WeeklyStat(label: "Acceptance rate", value: "76.5%")
                    }

                    // Best/worst
                    HStack(spacing: 16) {
                        Text("Best: Thursday")
                            .font(ADHDTypography.App.small)
                            .foregroundStyle(ADHDColors.Text.tertiary)
                        Text("Needs attention: Wednesday")
                            .font(ADHDTypography.App.small)
                            .foregroundStyle(ADHDColors.Text.tertiary)
                    }
                }
            }
        }
        .padding(.horizontal, 32)
        .padding(.top, 16)
        .padding(.bottom, 32)
    }
}

private struct DayBar: View {
    let day: String
    let focus: CGFloat
    let distraction: CGFloat
    let isToday: Bool
    let isFuture: Bool

    var body: some View {
        VStack(spacing: 4) {
            GeometryReader { proxy in
                HStack(alignment: .bottom, spacing: 3) {
                    Spacer()
                    RoundedRectangle(cornerRadius: 4)
                        .fill(ADHDColors.Accent.successBright.opacity(isFuture ? 0.3 : 1))
                        .frame(width: 16, height: proxy.size.height * focus)
                    RoundedRectangle(cornerRadius: 4)
                        .fill(ADHDColors.Accent.danger.opacity(isFuture ? 0.2 : 0.6))
                        .frame(width: 16, height: proxy.size.height * distraction)
                    Spacer()
                }
            }

            Text(day)
                .font(ADHDTypography.Dashboard.statLabel)
                .fontWeight(isToday ? .semibold : .regular)
                .foregroundStyle(isToday ? ADHDColors.Text.primary : ADHDColors.Text.tertiary)
        }
    }
}

private struct WeeklyStat: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(ADHDTypography.Dashboard.metricLabel)
                .foregroundStyle(ADHDColors.Text.secondary)
            Spacer()
            Text(value)
                .font(ADHDTypography.Dashboard.metricValue)
                .monospacedDigit()
                .foregroundStyle(ADHDColors.Text.primary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
    }
}

// MARK: - Dashboard Card Container

private struct DashboardCard<Content: View>: View {
    @ViewBuilder let content: () -> Content

    var body: some View {
        content()
            .padding(20)
            .padding(.horizontal, 4)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(ADHDColors.Background.secondary)
            .clipShape(RoundedRectangle(cornerRadius: 16))
    }
}
