import Foundation
import Observation

// MARK: - BrainDumpViewModel

@MainActor @Observable
final class BrainDumpViewModel {

    // MARK: - State

    var noteText: String = ""
    var isSaved: Bool = false
    var isSubmitting: Bool = false
    var summaryText: String = ""
    var isCaptured: Bool = false
    var capturedEntryId: String?

    // MARK: - Private

    private let draftKey = "brainDumpDraft"
    private var debounceTask: Task<Void, Never>?

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 60
        config.timeoutIntervalForResource = 120
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

    // MARK: - Submit (streaming)

    /// POST the note to the backend streaming endpoint.
    /// Captures the brain dump and streams back an AI summary.
    /// Returns true on success. On failure, the draft is preserved.
    @discardableResult
    func submit() async -> Bool {
        let textToSubmit = noteText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !textToSubmit.isEmpty else { return false }

        isSubmitting = true
        summaryText = ""
        isCaptured = false
        capturedEntryId = nil

        let host = UserDefaults.standard.string(forKey: "backendURL") ?? "localhost:8420"
        guard let url = URL(string: "http://\(host)/api/v1/brain-dump/stream") else {
            preconditionFailure("Brain dump URL is malformed")
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")

        let body = BrainDumpRequest(content: textToSubmit, sessionId: nil)

        do {
            request.httpBody = try JSONEncoder().encode(body)
            let (asyncBytes, response) = try await session.bytes(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                isSubmitting = false
                return false
            }

            // Clear the draft immediately — the backend has captured it
            self.noteText = ""
            UserDefaults.standard.removeObject(forKey: self.draftKey)
            self.isSaved = false

            for try await line in asyncBytes.lines {
                guard line.hasPrefix("data: ") else { continue }
                let data = String(line.dropFirst(6))

                if data == "[DONE]" {
                    break
                }

                guard let jsonData = data.data(using: .utf8) else { continue }

                if let captured = try? JSONDecoder().decode(CapturedEvent.self, from: jsonData),
                   captured.type == "captured" {
                    isCaptured = true
                    capturedEntryId = captured.id
                    continue
                }

                if let summary = try? JSONDecoder().decode(SummaryEvent.self, from: jsonData),
                   summary.type == "summary" {
                    summaryText += summary.token
                }
            }

            isSubmitting = false
            return true
        } catch {
            isSubmitting = false
            return false
        }
    }

    // MARK: - Reset

    func resetForNewDump() {
        summaryText = ""
        isCaptured = false
        capturedEntryId = nil
    }
}

// MARK: - Request / Response Models

private struct BrainDumpRequest: Encodable {
    let content: String
    let sessionId: String?

    enum CodingKeys: String, CodingKey {
        case content
        case sessionId = "session_id"
    }
}

private struct CapturedEvent: Decodable {
    let type: String
    let id: String?
    let emotional_state: String?
}

private struct SummaryEvent: Decodable {
    let type: String
    let token: String
}
