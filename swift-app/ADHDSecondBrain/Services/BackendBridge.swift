import Foundation

/// Extends BackendClient with notch-specific endpoints and polling.
/// Reuses the existing HTTP client infrastructure.
@Observable
class BackendBridge {

    private let client: BackendClient
    private let baseURL: URL
    private let session: URLSession
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()

    private var fastPollTask: Task<Void, Never>?
    private var slowPollTask: Task<Void, Never>?

    // Polled data
    var currentTask: TaskItem?
    var focusSession: FocusSession?
    var upcomingEvents: [CalendarEvent] = []
    var currentEmotion: EmotionState = .neutral
    var pendingIntervention: InterventionMessage?
    var dailyProgress = DailyProgress(
        tasksCompleted: 0, focusSessions: 0, totalFocusMinutes: 0
    )

    init(client: BackendClient = BackendClient()) {
        self.client = client
        self.baseURL = URL(string: "http://localhost:8420")!

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 5
        config.timeoutIntervalForResource = 10
        self.session = URLSession(configuration: config)
    }

    // MARK: - Polling

    func startPolling() {
        fastPollTask = Task { [weak self] in
            while !Task.isCancelled {
                await self?.pollFast()
                try? await Task.sleep(for: .seconds(5))
            }
        }

        slowPollTask = Task { [weak self] in
            while !Task.isCancelled {
                await self?.pollSlow()
                try? await Task.sleep(for: .seconds(30))
            }
        }
    }

    func stopPolling() {
        fastPollTask?.cancel()
        slowPollTask?.cancel()
    }

    // MARK: - Fast Poll (5s): Emotion + Interventions

    private func pollFast() async {
        await fetchEmotionState()
        await fetchPendingIntervention()
    }

    // MARK: - Slow Poll (30s): Tasks + Calendar + Progress

    private func pollSlow() async {
        await fetchCurrentTask()
        await fetchFocusSession()
        await fetchUpcomingEvents()
        await fetchDailyProgress()
    }

    // MARK: - Fetchers (silent failure)

    @MainActor
    private func fetchCurrentTask() async {
        guard let data = await get("api/v1/tasks/current") else { return }
        currentTask = try? decoder.decode(TaskItem.self, from: data)
    }

    @MainActor
    private func fetchFocusSession() async {
        guard let data = await get("api/v1/focus/session") else { return }
        focusSession = try? decoder.decode(FocusSession.self, from: data)
    }

    @MainActor
    private func fetchUpcomingEvents() async {
        guard let data = await get("api/v1/calendar/upcoming?limit=3") else {
            return
        }
        if let events = try? decoder.decode([CalendarEvent].self, from: data) {
            upcomingEvents = events
        }
    }

    @MainActor
    private func fetchEmotionState() async {
        guard let data = await get("api/v1/emotion/current") else { return }
        if let state = try? decoder.decode(EmotionState.self, from: data) {
            currentEmotion = state
        }
    }

    @MainActor
    private func fetchPendingIntervention() async {
        guard let data = await get("api/v1/interventions/pending") else {
            return
        }
        pendingIntervention = try? decoder.decode(
            InterventionMessage.self, from: data
        )
    }

    @MainActor
    private func fetchDailyProgress() async {
        guard let data = await get("api/v1/progress/today") else { return }
        if let progress = try? decoder.decode(DailyProgress.self, from: data) {
            dailyProgress = progress
        }
    }

    // MARK: - Actions

    func sendQuickCapture(_ text: String) async {
        let body = ["text": text, "source": "notch_quick_capture"]
        await post("api/v1/capture", body: body)
    }

    func acknowledgeIntervention(_ id: String) async {
        await post("api/v1/interventions/\(id)/acknowledge", body: [:] as [String: String])
    }

    func toggleFocusSession() async {
        await post("api/v1/focus/toggle", body: [:] as [String: String])
    }

    func completeTask(_ id: String) async {
        await post("api/v1/tasks/\(id)/complete", body: [:] as [String: String])
    }

    // MARK: - HTTP Helpers

    private func get(_ path: String) async -> Data? {
        let url = baseURL.appendingPathComponent(path)
        do {
            let (data, response) = try await session.data(from: url)
            guard let http = response as? HTTPURLResponse,
                  (200...299).contains(http.statusCode) else {
                return nil
            }
            return data
        } catch {
            return nil
        }
    }

    private func post<T: Encodable>(
        _ path: String, body: T
    ) async {
        let url = baseURL.appendingPathComponent(path)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? encoder.encode(body)
        _ = try? await session.data(for: request)
    }
}
