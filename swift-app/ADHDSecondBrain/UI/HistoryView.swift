import SwiftUI

/// Browse past daily snapshots — date list on the left, detail on the right.
struct HistoryView: View {
    @State private var viewModel = HistoryViewModel()

    var body: some View {
        HStack(spacing: 0) {
            HistorySidebar(viewModel: viewModel)
                .frame(width: 260)

            Divider()
                .overlay(Color.white.opacity(0.06))

            if let selected = viewModel.selectedDate {
                HistoryDetailPane(viewModel: viewModel, date: selected)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                HistoryEmptyState()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .background(ADHDColors.Background.primary)
        .frame(minWidth: 960, minHeight: 700)
        .onAppear { viewModel.load() }
    }
}

// MARK: - ViewModel

@Observable
final class HistoryViewModel {
    private let client = BackendClient()

    var snapshots: [SnapshotSummary] = []
    var selectedDate: String?
    var detail: HistorySnapshot?
    var isLoadingList = false
    var isLoadingDetail = false

    func load() {
        Task { @MainActor in
            isLoadingList = true
            let end = dateString(from: Date())
            let start = dateString(from: Calendar.current.date(byAdding: .day, value: -30, to: Date())!)
            do {
                snapshots = try await client.fetchHistoryList(start: start, end: end)
                if selectedDate == nil, let first = snapshots.first {
                    selectedDate = first.date
                    await loadDetail(first.date)
                }
            } catch {
                print("[HistoryViewModel] load failed: \(error)")
            }
            isLoadingList = false
        }
    }

    func selectDate(_ date: String) {
        selectedDate = date
        Task { @MainActor in
            await loadDetail(date)
        }
    }

    @MainActor
    private func loadDetail(_ date: String) async {
        isLoadingDetail = true
        do {
            detail = try await client.fetchHistoryDetail(date: date)
        } catch {
            print("[HistoryViewModel] detail failed: \(error)")
            detail = nil
        }
        isLoadingDetail = false
    }

    private func dateString(from date: Date) -> String {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f.string(from: date)
    }
}

// MARK: - Sidebar

private struct HistorySidebar: View {
    let viewModel: HistoryViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("History")
                .font(ADHDTypography.Dashboard.greeting)
                .foregroundStyle(ADHDColors.Text.primary)
                .padding(.horizontal, 20)
                .padding(.top, 20)
                .padding(.bottom, 16)

            if viewModel.isLoadingList {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if viewModel.snapshots.isEmpty {
                Text("No snapshots yet")
                    .font(ADHDTypography.App.body)
                    .foregroundStyle(ADHDColors.Text.tertiary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(spacing: 2) {
                        ForEach(viewModel.snapshots) { snapshot in
                            HistoryDateRow(
                                snapshot: snapshot,
                                isSelected: viewModel.selectedDate == snapshot.date
                            )
                            .onTapGesture {
                                viewModel.selectDate(snapshot.date)
                            }
                        }
                    }
                    .padding(.horizontal, 8)
                }
            }
        }
        .background(ADHDColors.Background.elevated)
    }
}

private struct HistoryDateRow: View {
    let snapshot: SnapshotSummary
    let isSelected: Bool

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(formattedDate)
                    .font(isSelected ? ADHDTypography.App.captionMedium : ADHDTypography.App.caption)
                    .foregroundStyle(isSelected ? ADHDColors.Text.primary : ADHDColors.Text.secondary)

                HStack(spacing: 12) {
                    Label("\(Int(snapshot.focusPercentage))%", systemImage: "target")
                        .font(ADHDTypography.App.small)
                        .foregroundStyle(ADHDColors.Accent.successBright)

                    Label("\(Int(snapshot.totalActiveMinutes))m", systemImage: "clock")
                        .font(ADHDTypography.App.small)
                        .foregroundStyle(ADHDColors.Text.tertiary)
                }
            }

            Spacer()

            FocusMiniBar(focusPercent: snapshot.focusPercentage)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(isSelected ? ADHDColors.Accent.focusLight.opacity(0.08) : Color.clear)
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }

    private var formattedDate: String {
        let inputFormatter = DateFormatter()
        inputFormatter.dateFormat = "yyyy-MM-dd"
        guard let date = inputFormatter.date(from: snapshot.date) else { return snapshot.date }
        let outputFormatter = DateFormatter()
        outputFormatter.dateFormat = "EEE, d MMM"
        return outputFormatter.string(from: date)
    }
}

private struct FocusMiniBar: View {
    let focusPercent: Double

    var body: some View {
        GeometryReader { proxy in
            ZStack(alignment: .leading) {
                RoundedRectangle(cornerRadius: 3)
                    .fill(ADHDColors.Background.secondary)

                RoundedRectangle(cornerRadius: 3)
                    .fill(ADHDColors.Accent.successBright)
                    .frame(width: proxy.size.width * min(focusPercent / 100.0, 1.0))
            }
        }
        .frame(width: 40, height: 6)
    }
}

// MARK: - Empty State

private struct HistoryEmptyState: View {
    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "calendar.badge.clock")
                .font(.system(size: 40))
                .foregroundStyle(ADHDColors.Text.muted)

            Text("Select a date to view details")
                .font(ADHDTypography.App.body)
                .foregroundStyle(ADHDColors.Text.tertiary)
        }
    }
}

// MARK: - Detail Pane

private struct HistoryDetailPane: View {
    let viewModel: HistoryViewModel
    let date: String

    var body: some View {
        if viewModel.isLoadingDetail {
            ProgressView()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        } else if let detail = viewModel.detail {
            ScrollView {
                VStack(spacing: 0) {
                    HistoryDetailHeader(detail: detail)
                    HistoryTimelineCard(detail: detail)
                    HistoryMetricsRow(detail: detail)
                    HistoryAppsInterventionsRow(detail: detail)
                }
                .padding(.bottom, 32)
            }
        } else {
            HistoryEmptyState()
        }
    }
}

// MARK: - Detail Header

private struct HistoryDetailHeader: View {
    let detail: HistorySnapshot

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(formattedDate)
                    .font(ADHDTypography.Dashboard.greeting)
                    .foregroundStyle(ADHDColors.Text.primary)

                Text("\(Int(detail.totalActiveMinutes)) minutes active")
                    .font(ADHDTypography.Dashboard.subtitle)
                    .foregroundStyle(ADHDColors.Text.secondary)
            }

            Spacer()

            HStack(spacing: 12) {
                HistoryStatPill(
                    value: "\(Int(detail.focusPercentage))%",
                    label: "Focus",
                    color: ADHDColors.Accent.successBright
                )
                HistoryStatPill(
                    value: "\(Int(detail.distractionPercentage))%",
                    label: "Distraction",
                    color: ADHDColors.Accent.danger
                )
            }
        }
        .padding(.horizontal, 32)
        .padding(.top, 20)
        .padding(.bottom, 16)
    }

    private var formattedDate: String {
        let inputFormatter = DateFormatter()
        inputFormatter.dateFormat = "yyyy-MM-dd"
        guard let date = inputFormatter.date(from: detail.date) else { return detail.date }
        let outputFormatter = DateFormatter()
        outputFormatter.dateFormat = "EEEE, d MMMM yyyy"
        return outputFormatter.string(from: date)
    }
}

private struct HistoryStatPill: View {
    let value: String
    let label: String
    let color: Color

    var body: some View {
        VStack(spacing: 2) {
            Text(value)
                .font(ADHDTypography.App.metricLarge)
                .monospacedDigit()
                .foregroundStyle(color)
            Text(label.uppercased())
                .font(ADHDTypography.Dashboard.statLabel)
                .tracking(0.5)
                .foregroundStyle(ADHDColors.Text.tertiary)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(ADHDColors.Background.secondary)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

// MARK: - Timeline Card

private struct HistoryTimelineCard: View {
    let detail: HistorySnapshot

    var body: some View {
        HistoryCard {
            VStack(spacing: 14) {
                HStack {
                    Text("Focus Timeline")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)
                    Spacer()
                    Text("\(Int(detail.totalActiveMinutes)) min tracked")
                        .font(ADHDTypography.App.small)
                        .foregroundStyle(ADHDColors.Text.secondary)
                }

                if detail.focusTimeline.isEmpty {
                    RoundedRectangle(cornerRadius: 8)
                        .fill(ADHDColors.Background.elevated)
                        .frame(height: 28)
                        .overlay(
                            Text("No timeline data")
                                .font(ADHDTypography.App.tiny)
                                .foregroundStyle(ADHDColors.Text.tertiary)
                        )
                } else {
                    HStack(spacing: 0) {
                        ForEach(detail.focusTimeline) { segment in
                            GeometryReader { proxy in
                                Rectangle()
                                    .fill(colorForCategory(segment.category))
                                    .frame(width: proxy.size.width)
                            }
                            .frame(maxWidth: .infinity)
                            .layoutPriority(Double(segment.duration * 100))
                        }
                    }
                    .frame(height: 28)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                }

                HStack(spacing: 20) {
                    HistoryLegendDot(color: ADHDColors.Accent.successBright, label: "Focused")
                    HistoryLegendDot(color: ADHDColors.Accent.danger, label: "Distracted")
                    HistoryLegendDot(color: ADHDColors.Accent.warning, label: "Neutral")
                    HistoryLegendDot(color: ADHDColors.Text.muted, label: "Idle")
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

private struct HistoryLegendDot: View {
    let color: Color
    let label: String

    var body: some View {
        HStack(spacing: 6) {
            Circle().fill(color).frame(width: 8, height: 8)
            Text(label)
                .font(ADHDTypography.App.tiny)
                .foregroundStyle(ADHDColors.Text.secondary)
        }
    }
}

// MARK: - Metrics Row (Emotion + Core Stats)

private struct HistoryMetricsRow: View {
    let detail: HistorySnapshot

    var body: some View {
        HStack(spacing: 16) {
            // Core metrics card
            HistoryCard {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Metrics")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)

                    VStack(spacing: 0) {
                        HistoryMetricRow(
                            label: "Focus time",
                            value: "\(Int(detail.totalFocusMinutes)) min",
                            valueColor: ADHDColors.Accent.successBright
                        )
                        HistoryMetricRow(
                            label: "Distraction time",
                            value: "\(Int(detail.totalDistractionMinutes)) min"
                        )
                        HistoryMetricRow(
                            label: "Active time",
                            value: "\(Int(detail.totalActiveMinutes)) min"
                        )
                        HistoryMetricRow(
                            label: "Context switches",
                            value: "\(detail.contextSwitches)",
                            isLast: true
                        )
                    }

                    // Behavioral states
                    if !detail.behavioralStates.isEmpty {
                        VStack(spacing: 8) {
                            Text("BEHAVIORAL STATES")
                                .font(ADHDTypography.App.sectionLabel)
                                .tracking(0.7)
                                .foregroundStyle(ADHDColors.Text.tertiary)

                            HStack(spacing: 8) {
                                ForEach(Array(detail.behavioralStates.sorted(by: { $0.value > $1.value }).prefix(3)), id: \.key) { state, minutes in
                                    HistoryBehaviorPill(
                                        value: "\(Int(minutes))",
                                        label: state.uppercased(),
                                        color: behaviorColor(state)
                                    )
                                }
                            }
                        }
                    }
                }
            }

            // Emotion radar card
            HistoryCard {
                VStack(spacing: 16) {
                    Text("Emotion Scores")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)

                    if let scores = detail.emotionScores {
                        HStack(spacing: 16) {
                            HistoryScorePill(value: "\(Int(scores.pleasantness * 100))", label: "PLEASANT")
                            HistoryScorePill(value: "\(Int(scores.attention * 100))", label: "ATTENTION")
                            HistoryScorePill(value: "\(Int(scores.sensitivity * 100))", label: "SENSITIV.")
                            HistoryScorePill(value: "\(Int(scores.aptitude * 100))", label: "APTITUDE")
                        }
                    } else {
                        HStack(spacing: 16) {
                            HistoryScorePill(value: "--", label: "PLEASANT")
                            HistoryScorePill(value: "--", label: "ATTENTION")
                            HistoryScorePill(value: "--", label: "SENSITIV.")
                            HistoryScorePill(value: "--", label: "APTITUDE")
                        }
                    }

                    // Whoop recovery if available
                    if let whoop = detail.whoopRecovery {
                        Divider().overlay(Color.white.opacity(0.06))

                        HStack {
                            Text("Whoop Recovery")
                                .font(ADHDTypography.Dashboard.cardTitle)
                                .foregroundStyle(ADHDColors.Text.primary)
                            Spacer()
                            Text("\(Int(whoop.recoveryScore))%")
                                .font(ADHDTypography.App.metricLarge)
                                .monospacedDigit()
                                .foregroundStyle(recoveryColor(whoop.recoveryScore))
                        }

                        VStack(spacing: 0) {
                            HistoryMetricRow(label: "Sleep score", value: "\(Int(whoop.sleepScore))%")
                            HistoryMetricRow(label: "Strain", value: String(format: "%.1f", whoop.strainScore), isLast: true)
                        }
                    }
                }
            }
        }
        .padding(.horizontal, 32)
        .padding(.top, 16)
    }

    private func behaviorColor(_ state: String) -> Color {
        switch state {
        case "focused": return ADHDColors.Accent.successBright
        case "hyperfocused": return ADHDColors.Accent.focusLight
        case "distracted": return ADHDColors.Accent.danger
        default: return ADHDColors.Accent.warning
        }
    }

    private func recoveryColor(_ score: Double) -> Color {
        switch score {
        case 67...: return ADHDColors.Accent.successBright
        case 34..<67: return ADHDColors.Accent.warning
        default: return ADHDColors.Accent.danger
        }
    }
}

// MARK: - Apps + Interventions Row

private struct HistoryAppsInterventionsRow: View {
    let detail: HistorySnapshot

    var body: some View {
        HStack(spacing: 16) {
            // Top apps
            HistoryCard {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Top Apps")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)

                    if detail.topApps.isEmpty {
                        Text("No app data")
                            .font(ADHDTypography.App.small)
                            .foregroundStyle(ADHDColors.Text.tertiary)
                    } else {
                        VStack(spacing: 0) {
                            ForEach(Array(detail.topApps.enumerated()), id: \.offset) { index, app in
                                HistoryMetricRow(
                                    label: app.appName,
                                    value: "\(Int(app.minutes)) min (\(Int(app.percentage))%)",
                                    isLast: index == detail.topApps.count - 1
                                )
                            }
                        }
                    }
                }
            }

            // Interventions
            HistoryCard {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Interventions")
                        .font(ADHDTypography.Dashboard.cardTitle)
                        .foregroundStyle(ADHDColors.Text.primary)

                    VStack(spacing: 0) {
                        HistoryMetricRow(
                            label: "Triggered",
                            value: "\(detail.interventionsTriggered)"
                        )
                        HistoryMetricRow(
                            label: "Accepted",
                            value: "\(detail.interventionsAccepted)"
                        )
                        HistoryMetricRow(
                            label: "Acceptance rate",
                            value: detail.interventionsTriggered > 0
                                ? "\(Int(Double(detail.interventionsAccepted) / Double(detail.interventionsTriggered) * 100))%"
                                : "--",
                            valueColor: ADHDColors.Accent.successBright,
                            isLast: true
                        )
                    }
                }
            }
        }
        .padding(.horizontal, 32)
        .padding(.top, 16)
    }
}

// MARK: - Reusable Components

private struct HistoryCard<Content: View>: View {
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

private struct HistoryMetricRow: View {
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

private struct HistoryScorePill: View {
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

private struct HistoryBehaviorPill: View {
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
