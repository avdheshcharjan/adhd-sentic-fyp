import Foundation
import Observation

// MARK: - BrainDumpViewModel

@MainActor @Observable
final class BrainDumpViewModel {

    // MARK: - State

    var noteText: String = ""
    var isSaved: Bool = false
    var isSubmitting: Bool = false

    // MARK: - Private

    private let draftKey = "brainDumpDraft"
    private var debounceTask: Task<Void, Never>?

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10
        config.timeoutIntervalForResource = 20
        return URLSession(configuration: config)
    }()

    // MARK: - Init

    init() {
        noteText = UserDefaults.standard.string(forKey: draftKey) ?? ""
    }

    // MARK: - Text Change Handler

    func textChanged(_ newText: String) {
        noteText = newText
        isSaved = false

        debounceTask?.cancel()
        debounceTask = Task {
            do {
                try await Task.sleep(nanoseconds: 1_500_000_000) // 1.5s
            } catch { return } // Task was cancelled
            UserDefaults.standard.set(newText, forKey: self.draftKey)
            self.isSaved = true
        }
    }

    // MARK: - Submit

    /// POST the note to the backend.
    /// Returns true on success. On failure, the draft is preserved.
    @discardableResult
    func submit() async -> Bool {
        let textToSubmit = noteText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !textToSubmit.isEmpty else { return false }

        isSubmitting = true
        defer { isSubmitting = false }

        let host = UserDefaults.standard.string(forKey: "backendURL") ?? "localhost:8420"
        guard let url = URL(string: "http://\(host)/api/v1/brain-dump/") else {
            preconditionFailure("Brain dump URL is malformed")
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = BrainDumpRequest(content: textToSubmit, sessionId: nil)

        do {
            request.httpBody = try JSONEncoder().encode(body)
            let (_, response) = try await session.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                return false
            }

            self.noteText = ""
            UserDefaults.standard.removeObject(forKey: self.draftKey)
            self.isSaved = false
            return true
        } catch {
            return false
        }
    }
}

// MARK: - Request Model

private struct BrainDumpRequest: Encodable {
    let content: String
    let sessionId: String?

    enum CodingKeys: String, CodingKey {
        case content
        case sessionId = "session_id"
    }
}
