import Foundation
import Observation

// MARK: - VentMessage

extension VentViewModel {
    struct VentMessage: Identifiable {
        let id: UUID
        let role: String   // "user" or "assistant"
        var content: String
        var isStreaming: Bool
    }
}

// MARK: - VentViewModel

@MainActor @Observable
final class VentViewModel {

    // MARK: - State

    var messages: [VentMessage] = []
    var inputText: String = ""
    var isGenerating: Bool = false
    var sessionId: String = UUID().uuidString

    // MARK: - Private

    private var streamTask: Task<Void, Never>?

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 60
        config.timeoutIntervalForResource = 120
        return URLSession(configuration: config)
    }()

    // MARK: - Public Actions

    func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isGenerating else { return }

        inputText = ""
        isGenerating = true

        let userMessage = VentMessage(id: UUID(), role: "user", content: text, isStreaming: false)
        messages.append(userMessage)

        let assistantPlaceholder = VentMessage(id: UUID(), role: "assistant", content: "", isStreaming: true)
        messages.append(assistantPlaceholder)

        streamTask = Task {
            await streamResponse(userMessage: text)
        }
    }

    func startNewSession() {
        streamTask?.cancel()
        messages = []
        sessionId = UUID().uuidString
        isGenerating = false
        inputText = ""
    }

    // MARK: - Streaming

    private var baseURLString: String {
        let host = UserDefaults.standard.string(forKey: "backendURL") ?? "localhost:8420"
        return "http://\(host)"
    }

    private func streamResponse(userMessage: String) async {
        guard let url = URL(string: "\(baseURLString)/api/v1/vent/chat/stream") else {
            preconditionFailure("Vent stream URL is malformed")
        }

        let historyForRequest = messages
            .dropLast() // exclude the empty assistant placeholder
            .filter { $0.role == "user" || ($0.role == "assistant" && !$0.isStreaming) }
            .map { HistoryEntry(role: $0.role, content: $0.content) }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")

        let body = VentStreamRequest(
            message: userMessage,
            sessionId: sessionId,
            history: historyForRequest
        )

        do {
            request.httpBody = try JSONEncoder().encode(body)

            let (asyncBytes, response) = try await session.bytes(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                await appendErrorMessage()
                return
            }

            for try await line in asyncBytes.lines {
                guard !Task.isCancelled else { break }
                guard line.hasPrefix("data: ") else { continue }

                let data = String(line.dropFirst(6))

                if data == "[DONE]" {
                    await finalizeAssistantMessage()
                    break
                }

                if let jsonData = data.data(using: .utf8),
                   let token = try? JSONDecoder().decode(VentTokenResponse.self, from: jsonData) {
                    await appendToken(token.token)
                }
            }

        } catch {
            if !Task.isCancelled {
                await appendErrorMessage()
            }
        }
    }

    private func appendToken(_ token: String) {
        guard let lastIndex = messages.indices.last,
              messages[lastIndex].role == "assistant" else { return }
        messages[lastIndex].content += token
    }

    private func finalizeAssistantMessage() {
        guard let lastIndex = messages.indices.last,
              messages[lastIndex].role == "assistant" else { return }
        messages[lastIndex].isStreaming = false
        isGenerating = false
    }

    private func appendErrorMessage() {
        guard let lastIndex = messages.indices.last,
              messages[lastIndex].role == "assistant" else { return }
        if messages[lastIndex].content.isEmpty {
            messages[lastIndex].content = "I'm having trouble responding right now. Take a deep breath — I'll be back in a moment."
        }
        messages[lastIndex].isStreaming = false
        isGenerating = false
    }
}

// MARK: - Request / Response Models

private struct VentStreamRequest: Encodable {
    let message: String
    let sessionId: String
    let history: [HistoryEntry]

    enum CodingKeys: String, CodingKey {
        case message
        case sessionId = "session_id"
        case history
    }
}

private struct HistoryEntry: Encodable {
    let role: String
    let content: String
}

private struct VentTokenResponse: Decodable {
    let token: String
}
