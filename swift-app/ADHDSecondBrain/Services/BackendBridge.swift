import AppKit
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
    // Google Calendar auth status
    var isCalendarConnected: Bool = false
    // Off-task detection
    var isOffTask: Bool = false
    
    init(client: BackendClient = BackendClient()) {
        self.client = client
        let urlString = UserDefaults.standard.string(forKey: "backendURL").map({ "http://\($0)" }) ?? "http://localhost:8420"
        guard let url = URL(string: urlString) else {
            fatalError("BackendBridge: malformed base URL: \(urlString)")
        }
        self.baseURL = url
        isCalendarConnected=true
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
        await checkCalendarStatus()
        await fetchEmotionState()
        await fetchPendingIntervention()
        await fetchOffTaskStatus()
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
        guard var session = try? decoder.decode(FocusSession.self, from: data) else { return }
        session.fetchedAt = Date()
        focusSession = session
    }

    @MainActor
    private func fetchUpcomingEvents() async {
        guard let data = await get("api/v1/calendar/upcoming") else {
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
    private func fetchOffTaskStatus() async {
        guard let data = await get("api/v1/focus/off-task") else { return }
        struct OffTaskResponse: Decodable {
            let offTask: Bool
            enum CodingKeys: String, CodingKey {
                case offTask = "off_task"
            }
        }
        if let response = try? decoder.decode(OffTaskResponse.self, from: data) {
            isOffTask = response.offTask
        }
    }

    @MainActor
    private func fetchDailyProgress() async {
        guard let data = await get("api/v1/progress/today") else { return }
        if let progress = try? decoder.decode(DailyProgress.self, from: data) {
            dailyProgress = progress
        }
    }



    // MARK: - Actions

    func openGoogleAuth() {
        let url = baseURL.appendingPathComponent("api/auth/google")
        NSWorkspace.shared.open(url)
    }

    @MainActor
    func checkCalendarStatus() async {
        guard let data = await get("api/auth/google/status") else { return }
        struct CalStatus: Decodable { let connected: Bool }
        if let status = try? decoder.decode(CalStatus.self, from: data) {
            isCalendarConnected = status.connected
        }
    }

    func sendQuickCapture(_ text: String) async {
        let body = ["text": text, "source": "notch_quick_capture"]
        await post("api/v1/capture", body: body)
    }

    func acknowledgeIntervention(_ id: String) async {
        struct InterventionResponse: Encodable {
            let action_taken: String
            let dismissed: Bool
        }
        await post(
            "interventions/\(id)/respond",
            body: InterventionResponse(action_taken: "acknowledged", dismissed: false)
        )
    }

    func toggleFocusSession() async {
        await post("api/v1/focus/toggle", body: [:] as [String: String])
    }

    func completeTask(_ id: String) async {
        await post("api/v1/tasks/\(id)/complete", body: [:] as [String: String])
    }

    /// Create a new task and start a focus session.
    /// Returns the created TaskItem if the backend responds with one.
    @MainActor
    func createTaskAndStartFocus(name: String, durationSeconds: Int) async -> TaskItem? {
        struct CreateTaskRequest: Encodable {
            let name: String
            let duration_seconds: Int
            let start_focus: Bool
        }
        let body = CreateTaskRequest(
            name: name,
            duration_seconds: durationSeconds,
            start_focus: true
        )
        guard let data = await postReturning("api/v1/tasks/create", body: body) else {
            return nil
        }
        let task = try? decoder.decode(TaskItem.self, from: data)
        if let task {
            currentTask = task
        }
        // Immediately refresh focus session
        await fetchFocusSession()
        return task
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

    private func postReturning<T: Encodable>(
        _ path: String, body: T
    ) async -> Data? {
        let url = baseURL.appendingPathComponent(path)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? encoder.encode(body)
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse,
                  (200...299).contains(http.statusCode) else {
                return nil
            }
            return data
        } catch {
            return nil
        }
    }
}
