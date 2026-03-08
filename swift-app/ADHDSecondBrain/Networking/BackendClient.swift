import Foundation

/// HTTP client for communicating with the Python FastAPI backend on localhost:8420.
///
/// Design decisions:
/// - 5s timeout on all requests (don't block monitoring)
/// - Silently fails on connection errors (backend may be down)
/// - Uses async/await for clean concurrency
class BackendClient {

    // MARK: - Configuration

    private let baseURL: URL
    private let session: URLSession

    init(baseURL: String = "http://localhost:8420") {
        self.baseURL = URL(string: baseURL)!

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 5
        config.timeoutIntervalForResource = 10
        self.session = URLSession(configuration: config)
    }

    // MARK: - Encoder / Decoder

    private let encoder: JSONEncoder = {
        let e = JSONEncoder()
        return e
    }()

    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        return d
    }()

    // MARK: - Public API

    /// Report screen activity to the backend.
    /// Called every ~2 seconds by MonitorCoordinator.
    func reportActivity(_ activity: ScreenActivityRequest) async throws -> ScreenActivityResponse {
        let url = baseURL.appendingPathComponent("screen/activity")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(activity)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw BackendError.invalidResponse
        }

        return try decoder.decode(ScreenActivityResponse.self, from: data)
    }

    /// Report user response to an intervention.
    func respondToIntervention(
        interventionId: String,
        actionTaken: String,
        dismissed: Bool,
        effectivenessRating: Int? = nil
    ) async throws {
        let url = baseURL.appendingPathComponent("interventions/\(interventionId)/respond")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = InterventionResponseRequest(
            actionTaken: actionTaken,
            dismissed: dismissed,
            effectivenessRating: effectivenessRating
        )
        request.httpBody = try encoder.encode(body)

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw BackendError.invalidResponse
        }
    }

    /// Check backend health.
    func healthCheck() async -> Bool {
        let url = baseURL.appendingPathComponent("health")
        do {
            let (_, response) = try await session.data(from: url)
            return (response as? HTTPURLResponse)?.statusCode == 200
        } catch {
            return false
        }
    }
}

// MARK: - Errors

enum BackendError: LocalizedError {
    case invalidResponse
    case decodingFailed

    var errorDescription: String? {
        switch self {
        case .invalidResponse: return "Invalid response from backend"
        case .decodingFailed: return "Failed to decode backend response"
        }
    }
}
