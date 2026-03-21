import Foundation

/// Drives the Dashboard analytics view with real backend data.
///
/// Polling strategy mirrors BackendBridge:
/// - Slow poll (30s): dashboard stats, weekly report, whoop recovery
///
/// Live metrics (context switches, focus score, etc.) are read directly from
/// MonitorCoordinator.latestMetrics — no extra polling needed.
@Observable
final class DashboardViewModel {

    // MARK: - Dependencies

    private let coordinator: MonitorCoordinator
    private let client: BackendClient

    // MARK: - Polled State

    var dashboardStats: DashboardStats?
    var weeklyReport: WeeklyReport?
    var whoopRecovery: WhoopRecovery?

    // MARK: - Polling Tasks

    private var pollTask: Task<Void, Never>?

    // MARK: - Init

    init(coordinator: MonitorCoordinator, client: BackendClient = BackendClient()) {
        self.coordinator = coordinator
        self.client = client
    }

    // MARK: - Polling Lifecycle

    func startPolling() {
        pollTask = Task { [weak self] in
            while !Task.isCancelled {
                await self?.pollAll()
                try? await Task.sleep(for: .seconds(30))
            }
        }
    }

    func stopPolling() {
        pollTask?.cancel()
        pollTask = nil
    }

    // MARK: - Poll

    private func pollAll() async {
        await fetchDashboardStats()
        await fetchWeeklyReport()
        await fetchWhoopRecovery()
    }

    @MainActor
    private func fetchDashboardStats() async {
        guard let stats = try? await client.fetchDashboardStats() else { return }
        dashboardStats = stats
    }

    @MainActor
    private func fetchWeeklyReport() async {
        guard let report = try? await client.fetchWeeklyReport() else { return }
        weeklyReport = report
    }

    @MainActor
    private func fetchWhoopRecovery() async {
        do {
            whoopRecovery = try await client.fetchWhoopRecovery()
        } catch {
            print("[DashboardViewModel] fetchWhoopRecovery failed: \(error)")
        }
    }

    // MARK: - Computed Properties: Live Metrics (from coordinator)

    var behavioralState: String {
        coordinator.latestMetrics.behavioralState
    }

    var contextSwitchRate: Int {
        Int(coordinator.latestMetrics.contextSwitchRate5min)
    }

    var focusScore: Int {
        Int(coordinator.latestMetrics.focusScore)
    }

    var distractionRatioPercent: Int {
        Int(coordinator.latestMetrics.distractionRatio * 100)
    }

    var currentStreakMinutes: Int {
        Int(coordinator.latestMetrics.currentStreakMinutes)
    }

    var activeApp: String {
        coordinator.latestCategory
    }

    // MARK: - Computed Properties: Today Stats (from dashboardStats)

    var totalFocusMinutes: Int {
        dashboardStats?.totalFocusMinutes ?? 0
    }

    var totalActiveMinutes: Int {
        dashboardStats?.totalActiveMinutes ?? 0
    }

    // MARK: - Computed Properties: Interventions (from dashboardStats)

    var interventionsTriggered: Int {
        dashboardStats?.interventionsTriggered ?? 0
    }

    var interventionsAccepted: Int {
        dashboardStats?.interventionsAccepted ?? 0
    }

    var interventionAcceptancePercent: Int {
        guard let stats = dashboardStats, stats.interventionsTriggered > 0 else { return 0 }
        return Int(Double(stats.interventionsAccepted) / Double(stats.interventionsTriggered) * 100)
    }

    // MARK: - Computed Properties: Focus Timeline (from dashboardStats)

    var focusTimeline: [TimelineSegment] {
        dashboardStats?.focusTimeline ?? []
    }

    var totalTrackedMinutes: Int {
        // Derive from totalActiveMinutes; fall back to 0 when no data yet
        dashboardStats?.totalActiveMinutes ?? 0
    }

    // MARK: - Computed Properties: Emotion Scores (from dashboardStats)

    var emotionScores: EmotionScores? {
        dashboardStats?.emotionScores
    }

    var emotionStateLabel: String {
        guard let scores = dashboardStats?.emotionScores else { return "No data" }
        // Derive a simple label from the dominant score
        let values: [(String, Double)] = [
            ("Focused", scores.attention),
            ("Pleasant", scores.pleasantness),
            ("Sensitive", scores.sensitivity),
            ("Capable", scores.aptitude)
        ]
        guard let dominant = values.max(by: { $0.1 < $1.1 }) else { return "Neutral" }
        return dominant.0
    }

    // MARK: - Computed Properties: Weekly Report

    var weeklyTrend: String {
        weeklyReport?.trend.uppercased() ?? "NO DATA"
    }

    var weeklyAvgFocusPercent: String {
        guard let report = weeklyReport else { return "--" }
        return String(format: "%.1f%%", report.avgFocus * 100)
    }

    var weeklyAvgDistractionPercent: String {
        guard let report = weeklyReport else { return "--" }
        return String(format: "%.1f%%", report.avgDistraction * 100)
    }

    var weeklyTotalInterventions: String {
        guard let report = weeklyReport else { return "--" }
        return "\(report.totalInterventions)"
    }

    var weeklyAcceptanceRatePercent: String {
        guard let report = weeklyReport else { return "--" }
        return String(format: "%.1f%%", report.acceptanceRate * 100)
    }

    var weeklyBestDay: String {
        weeklyReport?.bestDay ?? "--"
    }

    var weeklyWorstDay: String {
        weeklyReport?.worstDay ?? "--"
    }

    var weeklyDays: [DayReport] {
        weeklyReport?.days ?? []
    }
}
