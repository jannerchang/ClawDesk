import Foundation
import Observation

@MainActor @Observable
public final class APIClient {
    public static let shared = APIClient()

    public var baseURLString: String = ProcessInfo.processInfo.environment["CLAWDESK_BASE_URL"] ?? UserDefaults.standard.string(forKey: "clawdesk.baseURL") ?? "http://127.0.0.1:8000" {
        didSet {
            UserDefaults.standard.set(baseURLString, forKey: "clawdesk.baseURL")
        }
    }

    private let session = URLSession.shared

    private var baseURL: URL? {
        URL(string: baseURLString)
    }

    private var decoder: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateStr = try container.decode(String.self)

            let fractional = ISO8601DateFormatter()
            fractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = fractional.date(from: dateStr) {
                return date
            }

            let standard = ISO8601DateFormatter()
            if let date = standard.date(from: dateStr) {
                return date
            }
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Invalid date format: \(dateStr)")
        }
        return decoder
    }

    private var encoder: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }

    public init() {}

    public func checkHealth() async throws -> HealthResponse {
        let url = try makeURL(path: "health")
        let (data, response) = try await session.data(from: url)
        if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.badStatus(http.statusCode, body)
        }
        return try decoder.decode(HealthResponse.self, from: data)
    }

    public func fetchSpaces() async throws -> [Space] {
        let url = try makeURL(path: "spaces")
        let (data, _) = try await session.data(from: url)
        return try decoder.decode([Space].self, from: data)
    }

    public func fetchChannels(spaceId: String) async throws -> [Channel] {
        let url = try makeURL(path: "spaces/\(spaceId)/channels")
        let (data, _) = try await session.data(from: url)
        return try decoder.decode([Channel].self, from: data)
    }

    public func fetchSubchannels(channelId: String) async throws -> [Channel] {
        let url = try makeURL(path: "channels/\(channelId)/subchannels")
        let (data, _) = try await session.data(from: url)
        return try decoder.decode([Channel].self, from: data)
    }

    public func fetchChannelMembers(channelId: String) async throws -> [User] {
        let url = try makeURL(path: "channels/\(channelId)/members")
        let (data, _) = try await session.data(from: url)
        return try decoder.decode([User].self, from: data)
    }

    public func fetchMessages(channelId: String) async throws -> [Message] {
        let url = try makeURL(path: "channels/\(channelId)/messages")
        let (data, _) = try await session.data(from: url)
        return try decoder.decode([Message].self, from: data)
    }

    public func fetchAttachments(messageId: String) async throws -> [Attachment] {
        let url = try makeURL(path: "messages/\(messageId)/attachments")
        let (data, _) = try await session.data(from: url)
        return try decoder.decode([Attachment].self, from: data)
    }

    @discardableResult
    public func sendMessage(channelId: String, content: String, senderName: String = "Janner") async throws -> Message {
        let payload = MessageCreateRequest(content: content, senderName: senderName)
        let url = try makeURL(path: "channels/\(channelId)/messages")
        return try await post(url: url, payload: payload, responseType: Message.self)
    }

    @discardableResult
    public func invokeHermes(
        channelId: String,
        prompt: String? = nil,
        maxContextMessages: Int = 20
    ) async throws -> HermesInvokeResponse {
        let payload = HermesInvokeRequest(prompt: prompt, maxContextMessages: maxContextMessages)
        let url = try makeURL(path: "channels/\(channelId)/agent/hermes")
        return try await post(url: url, payload: payload, responseType: HermesInvokeResponse.self)
    }

    @discardableResult
    public func invokeLocalAgent(
        channelId: String,
        prompt: String,
        agent: String = "shell",
        workspace: String? = nil,
        timeoutSeconds: Int = 120
    ) async throws -> LocalAgentInvokeResponse {
        let payload = LocalAgentInvokeRequest(
            prompt: prompt,
            agent: agent,
            workspace: workspace,
            timeoutSeconds: timeoutSeconds
        )
        let url = try makeURL(path: "channels/\(channelId)/agent/local")
        return try await post(url: url, payload: payload, responseType: LocalAgentInvokeResponse.self)
    }

    @discardableResult
    public func uploadAttachment(messageId: String, fileURL: URL) async throws -> Attachment {
        let fileData = try Data(contentsOf: fileURL)
        let fileName = fileURL.lastPathComponent.isEmpty ? "attachment" : fileURL.lastPathComponent
        let mimeType = mimeTypeForPathExtension(fileURL.pathExtension)
        let boundary = "Boundary-\(UUID().uuidString)"
        var body = Data()
        body.appendString("--\(boundary)\r\n")
        body.appendString("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileName)\"\r\n")
        body.appendString("Content-Type: \(mimeType)\r\n\r\n")
        body.append(fileData)
        body.appendString("\r\n--\(boundary)--\r\n")

        var request = URLRequest(url: try makeURL(path: "messages/\(messageId)/attachments"))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = body

        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.badStatus(http.statusCode, body)
        }
        return try decoder.decode(Attachment.self, from: data)
    }

    @discardableResult
    public func createChannel(spaceId: String, name: String, type: String = "normal", mode: String = "mixed") async throws -> Channel {
        let payload = ChannelCreateRequest(spaceId: spaceId, name: name, type: type, mode: mode)
        let url = try makeURL(path: "channels")
        return try await post(url: url, payload: payload, responseType: Channel.self)
    }

    @discardableResult
    public func createSubchannelFromMessages(
        channelId: String,
        name: String,
        type: String = "normal",
        sourceMessageIds: [String]
    ) async throws -> Channel {
        let payload = SubchannelFromMessagesRequest(name: name, type: type, sourceMessageIds: sourceMessageIds)
        let url = try makeURL(path: "channels/\(channelId)/subchannels/from_messages")
        return try await post(url: url, payload: payload, responseType: Channel.self)
    }

    private func makeURL(path: String) throws -> URL {
        guard let baseURL else {
            throw URLError(.badURL)
        }
        return baseURL.appending(path: path)
    }

    private func mimeTypeForPathExtension(_ ext: String) -> String {
        switch ext.lowercased() {
        case "jpg", "jpeg": return "image/jpeg"
        case "png": return "image/png"
        case "gif": return "image/gif"
        case "heic": return "image/heic"
        case "mp3": return "audio/mpeg"
        case "m4a": return "audio/mp4"
        case "wav": return "audio/wav"
        case "pdf": return "application/pdf"
        case "txt", "md": return "text/plain"
        case "json": return "application/json"
        default: return "application/octet-stream"
        }
    }

    private func post<Payload: Encodable, Response: Decodable>(url: URL, payload: Payload, responseType: Response.Type) async throws -> Response {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(payload)

        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.badStatus(http.statusCode, body)
        }
        return try decoder.decode(responseType, from: data)
    }
}

public struct HealthResponse: Codable, Hashable, Sendable {
    public let ok: Bool
    public let hermesMode: String?

    enum CodingKeys: String, CodingKey {
        case ok
        case hermesMode = "hermes_mode"
    }
}

private extension Data {
    mutating func appendString(_ value: String) {
        if let data = value.data(using: .utf8) {
            append(data)
        }
    }
}

public enum APIError: LocalizedError {
    case badStatus(Int, String)

    public var errorDescription: String? {
        switch self {
        case .badStatus(let status, let body):
            return "HTTP \(status): \(body)"
        }
    }
}
