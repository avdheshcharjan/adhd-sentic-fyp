import SwiftUI

/// Analytics dashboard matching the Paper design canvas.
/// Dark window with focus timeline, live metrics, emotion radar,
/// whoop recovery, interventions, and weekly report cards.
struct DashboardView: View {
    @ObservedObject var coordinator: MonitorCoordinator
    @State private var viewModel: DashboardViewModel

    init(coordinator: MonitorCoordinator) {
        self.coordinator = coordinator
        self._viewModel = State(initialValue: DashboardViewModel(coordinator: coordinator))
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                DashboardHeader(coordinator: coordinator)
                FocusTimelineCard(viewModel: viewModel)
                MetricsEmotionRow(coordinator: coordinator, viewModel: viewModel)
                WhoopInterventionsRow(viewModel: viewModel)
                WeeklyReportCard(viewModel: viewModel)
            }
        }
        .background(ADHDColors.Background.primary)
        .frame(minWidth: 900, minHeight: 700)
        .onAppear {
            viewModel.startPolling()
        }
        .onDisappear {
            viewModel.stopPolling()
        }
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
    let viewModel: DashboardViewModel

    var body: some View {
        DashboardCard {
            VStack(spacing: 14) {
                HStack {
                    Text("Today's Focus Timeline")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)

                    Spacer()

                    if viewModel.totalTrackedMinutes > 0 {
                        Text("\(viewModel.totalTrackedMinutes) min tracked")
                            .font(ADHDTypography.App.small)
                            .foregroundStyle(ADHDColors.Text.secondary)
                    } else {
                        Text("No data yet")
                            .font(ADHDTypography.App.small)
                            .foregroundStyle(ADHDColors.Text.tertiary)
                    }
                }

                if viewModel.focusTimeline.isEmpty {
                    TimelinePlaceholder()
                } else {
                    // Timeline bar built from real segments
                    HStack(spacing: 0) {
                        ForEach(viewModel.focusTimeline) { segment in
                            TimelineSegmentView(
                                color: colorForCategory(segment.category),
                                width: CGFloat(segment.duration)
                            )
                        }
                    }
                    .frame(height: 28)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                }

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

    private func colorForCategory(_ category: String) -> Color {
        switch category {
        case "focused": return ADHDColors.Accent.successBright
        case "distracted": return ADHDColors.Accent.danger
        case "neutral": return ADHDColors.Accent.warning
        default: return ADHDColors.Text.muted
        }
    }
}

private struct TimelinePlaceholder: View {
    var body: some View {
        RoundedRectangle(cornerRadius: 8)
            .fill(ADHDColors.Background.elevated)
            .frame(height: 28)
            .overlay(
                Text("Activity will appear here once monitoring starts")
                    .font(ADHDTypography.App.tiny)
                    .foregroundStyle(ADHDColors.Text.tertiary)
            )
    }
}

private struct TimelineSegmentView: View {
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
    let viewModel: DashboardViewModel

    var body: some View {
        HStack(spacing: 16) {
            LiveMetricsCard(coordinator: coordinator, viewModel: viewModel)
            EmotionRadarCard(viewModel: viewModel)
        }
        .padding(.horizontal, 32)
        .padding(.top, 16)
    }
}

private struct LiveMetricsCard: View {
    @ObservedObject var coordinator: MonitorCoordinator
    let viewModel: DashboardViewModel

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
                    MetricRow(
                        label: "Context switches (5 min)",
                        value: "\(viewModel.contextSwitchRate)"
                    )
                    MetricRow(
                        label: "Focus score",
                        value: "\(viewModel.focusScore)%",
                        valueColor: ADHDColors.Accent.successBright
                    )
                    MetricRow(
                        label: "Distraction ratio",
                        value: "\(viewModel.distractionRatioPercent)%"
                    )
                    MetricRow(
                        label: "Current streak",
                        value: "\(viewModel.currentStreakMinutes) min"
                    )
                    MetricRow(
                        label: "Active app",
                        value: viewModel.activeApp,
                        isLast: true
                    )
                }

                VStack(spacing: 0) {
                    Text("TODAY")
                        .font(ADHDTypography.App.sectionLabel)
                        .tracking(0.7)
                        .foregroundStyle(ADHDColors.Text.tertiary)
                        .padding(.bottom, 8)

                    MetricRow(
                        label: "Focus time",
                        value: viewModel.totalFocusMinutes > 0
                            ? "\(viewModel.totalFocusMinutes) min"
                            : "--"
                    )
                    MetricRow(
                        label: "Active time",
                        value: viewModel.totalActiveMinutes > 0
                            ? "\(viewModel.totalActiveMinutes) min"
                            : "--",
                        isLast: true
                    )
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
    let viewModel: DashboardViewModel

    var body: some View {
        DashboardCard {
            VStack(spacing: 16) {
                HStack {
                    Text("Emotion Radar")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)
                    Spacer()
                    Text("Current: \(viewModel.emotionStateLabel)")
                        .font(ADHDTypography.App.small)
                        .foregroundStyle(ADHDColors.Text.secondary)
                }

                // Radar visualization
                RadarChartView(scores: viewModel.emotionScores)
                    .frame(height: 200)

                // Score pills
                if let scores = viewModel.emotionScores {
                    HStack(spacing: 16) {
                        ScorePill(value: "\(Int(scores.pleasantness * 100))", label: "PLEASANT")
                        ScorePill(value: "\(Int(scores.attention * 100))", label: "ATTENTION")
                        ScorePill(value: "\(Int(scores.sensitivity * 100))", label: "SENSITIV.")
                        ScorePill(value: "\(Int(scores.aptitude * 100))", label: "APTITUDE")
                    }
                } else {
                    HStack(spacing: 16) {
                        ScorePill(value: "--", label: "PLEASANT")
                        ScorePill(value: "--", label: "ATTENTION")
                        ScorePill(value: "--", label: "SENSITIV.")
                        ScorePill(value: "--", label: "APTITUDE")
                    }
                }
            }
        }
    }
}

private struct RadarChartView: View {
    let scores: EmotionScores?

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

            // Data shape — uses real scores when available
            if let scores = scores {
                RadarShape(
                    top: scores.pleasantness,
                    right: scores.attention,
                    bottom: scores.sensitivity,
                    left: scores.aptitude
                )
                .fill(ADHDColors.Accent.focusLight.opacity(0.15))
                .overlay(
                    RadarShape(
                        top: scores.pleasantness,
                        right: scores.attention,
                        bottom: scores.sensitivity,
                        left: scores.aptitude
                    )
                    .stroke(ADHDColors.Accent.focusLight.opacity(0.6), lineWidth: 2)
                )
                .frame(width: 140, height: 150)
            } else {
                RadarShape(top: 0.5, right: 0.5, bottom: 0.5, left: 0.5)
                    .fill(ADHDColors.Text.muted.opacity(0.08))
                    .overlay(
                        RadarShape(top: 0.5, right: 0.5, bottom: 0.5, left: 0.5)
                            .stroke(ADHDColors.Text.muted.opacity(0.2), lineWidth: 1)
                    )
                    .frame(width: 140, height: 150)
            }

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
    let top: Double
    let right: Double
    let bottom: Double
    let left: Double

    func path(in rect: CGRect) -> Path {
        let center = CGPoint(x: rect.midX, y: rect.midY)
        let maxRadius = min(rect.width, rect.height) / 2

        var path = Path()
        let points: [(angle: Double, radius: Double)] = [
            (-.pi / 2, top),    // Top — Pleasantness
            (0,        right),  // Right — Attention
            (.pi / 2,  bottom), // Bottom — Sensitivity
            (.pi,      left),   // Left — Aptitude
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
    let viewModel: DashboardViewModel

    var body: some View {
        HStack(spacing: 16) {
            WhoopRecoveryCard(viewModel: viewModel)
            InterventionsCard(viewModel: viewModel)
        }
        .padding(.horizontal, 32)
        .padding(.top, 16)
    }
}

private struct WhoopRecoveryCard: View {
    let viewModel: DashboardViewModel

    var body: some View {
        DashboardCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Text("Whoop Recovery")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)
                    Spacer()
                    if let recovery = viewModel.whoopRecovery {
                        HStack(spacing: 6) {
                            Circle()
                                .fill(recoveryColor(recovery.recoveryPercent))
                                .frame(width: 8, height: 8)
                            Text("\(Int(recovery.recoveryPercent))%")
                                .font(ADHDTypography.App.metricLarge)
                                .monospacedDigit()
                                .foregroundStyle(recoveryColor(recovery.recoveryPercent))
                        }
                    } else {
                        Text("--")
                            .font(ADHDTypography.App.metricLarge)
                            .monospacedDigit()
                            .foregroundStyle(ADHDColors.Text.tertiary)
                    }
                }

                VStack(spacing: 0) {
                    MetricRow(
                        label: "HRV (rMSSD)",
                        value: viewModel.whoopRecovery.map { String(format: "%.1f ms", $0.hrv) } ?? "--"
                    )
                    MetricRow(
                        label: "Resting HR",
                        value: viewModel.whoopRecovery.map { "\(Int($0.restingHR)) bpm" } ?? "--"
                    )
                    MetricRow(
                        label: "Sleep performance",
                        value: viewModel.whoopRecovery.flatMap { r in r.sleepPerformance.map { "\(Int($0))%" } } ?? "--"
                    )
                    MetricRow(
                        label: "Recommended focus block",
                        value: viewModel.whoopRecovery.map { "\($0.recommendedFocusBlock) min" } ?? "--",
                        valueColor: ADHDColors.Accent.focusLight,
                        isLast: true
                    )
                }
            }
        }
    }

    private func recoveryColor(_ percent: Double) -> Color {
        switch percent {
        case 67...: return ADHDColors.Accent.successBright
        case 34..<67: return ADHDColors.Accent.warning
        default: return ADHDColors.Accent.danger
        }
    }
}

private struct InterventionsCard: View {
    let viewModel: DashboardViewModel

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
                    MetricRow(
                        label: "Triggered",
                        value: viewModel.dashboardStats != nil
                            ? "\(viewModel.interventionsTriggered)"
                            : "--"
                    )
                    MetricRow(
                        label: "Accepted",
                        value: viewModel.dashboardStats != nil
                            ? "\(viewModel.interventionsAccepted)"
                            : "--"
                    )
                    MetricRow(
                        label: "Acceptance rate",
                        value: viewModel.dashboardStats != nil
                            ? "\(viewModel.interventionAcceptancePercent)%"
                            : "--",
                        valueColor: ADHDColors.Accent.successBright,
                        isLast: true
                    )
                }

                BehavioralStatesSection(viewModel: viewModel)
            }
        }
    }
}

private struct BehavioralStatesSection: View {
    let viewModel: DashboardViewModel

    var body: some View {
        VStack(spacing: 8) {
            Text("BEHAVIORAL STATE")
                .font(ADHDTypography.App.sectionLabel)
                .tracking(0.7)
                .foregroundStyle(ADHDColors.Text.tertiary)

            HStack(spacing: 8) {
                BehaviorPill(
                    value: viewModel.behavioralState == "focused" ? "Active" : "--",
                    label: "FOCUSED",
                    color: ADHDColors.Accent.successBright
                )
                BehaviorPill(
                    value: viewModel.behavioralState == "hyperfocused" ? "Active" : "--",
                    label: "HYPERF.",
                    color: ADHDColors.Accent.focusLight
                )
                BehaviorPill(
                    value: viewModel.behavioralState == "distracted" ? "Active" : "--",
                    label: "DISTRACT.",
                    color: ADHDColors.Accent.danger
                )
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
    let viewModel: DashboardViewModel

    var body: some View {
        VStack(spacing: 0) {
            DashboardCard {
                VStack(spacing: 16) {
                    HStack {
                        Text("Weekly Report")
                            .font(ADHDTypography.Dashboard.cardTitle)
                            .foregroundStyle(ADHDColors.Text.primary)
                        Spacer()
                        TrendBadge(trend: viewModel.weeklyTrend)
                    }

                    if viewModel.weeklyDays.isEmpty {
                        WeeklyChartPlaceholder()
                    } else {
                        // Bar chart
                        HStack(alignment: .bottom, spacing: 12) {
                            ForEach(viewModel.weeklyDays) { day in
                                DayBar(
                                    day: day.day,
                                    focus: CGFloat(day.focusRatio),
                                    distraction: CGFloat(day.distractionRatio),
                                    isToday: day.isToday
                                )
                            }
                        }
                        .frame(height: 140)
                        .padding(.horizontal, 8)
                    }

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
                        WeeklyStat(label: "Avg focus", value: viewModel.weeklyAvgFocusPercent)
                        WeeklyStat(label: "Avg distraction", value: viewModel.weeklyAvgDistractionPercent)
                        WeeklyStat(label: "Total interventions", value: viewModel.weeklyTotalInterventions)
                        WeeklyStat(label: "Acceptance rate", value: viewModel.weeklyAcceptanceRatePercent)
                    }

                    // Best/worst
                    HStack(spacing: 16) {
                        Text("Best: \(viewModel.weeklyBestDay)")
                            .font(ADHDTypography.App.small)
                            .foregroundStyle(ADHDColors.Text.tertiary)
                        Text("Needs attention: \(viewModel.weeklyWorstDay)")
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

private struct TrendBadge: View {
    let trend: String

    var body: some View {
        Text(trend)
            .font(ADHDTypography.Dashboard.badge)
            .tracking(0.5)
            .foregroundStyle(trendColor)
            .padding(.horizontal, 12)
            .padding(.vertical, 4)
            .background(trendColor.opacity(0.12))
            .clipShape(Capsule())
    }

    private var trendColor: Color {
        switch trend.lowercased() {
        case "improving": return ADHDColors.Accent.successBright
        case "declining": return ADHDColors.Accent.danger
        default: return ADHDColors.Accent.focusLight
        }
    }
}

private struct WeeklyChartPlaceholder: View {
    var body: some View {
        RoundedRectangle(cornerRadius: 8)
            .fill(ADHDColors.Background.elevated)
            .frame(height: 140)
            .overlay(
                Text("Weekly data will appear after 24 hours of monitoring")
                    .font(ADHDTypography.App.tiny)
                    .foregroundStyle(ADHDColors.Text.tertiary)
            )
            .padding(.horizontal, 8)
    }
}

private struct DayBar: View {
    let day: String
    let focus: CGFloat
    let distraction: CGFloat
    let isToday: Bool

    var body: some View {
        VStack(spacing: 4) {
            GeometryReader { proxy in
                HStack(alignment: .bottom, spacing: 3) {
                    Spacer()
                    RoundedRectangle(cornerRadius: 4)
                        .fill(ADHDColors.Accent.successBright)
                        .frame(width: 16, height: proxy.size.height * focus)
                    RoundedRectangle(cornerRadius: 4)
                        .fill(ADHDColors.Accent.danger.opacity(0.6))
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
