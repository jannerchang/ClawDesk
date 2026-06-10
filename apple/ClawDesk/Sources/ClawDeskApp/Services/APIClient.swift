import Foundation
import Observation

@MainActor @Observable
public final class APIClient {
    public static let shared = APIClient()

    public var baseURLString: String = "http://127.0.0.1:8000"

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

    public func fetchMessages(channelId: String) async throws -> [Message] {
        let url = try makeURL(path: "channels/\(channelId)/messages")
        let (data, _) = try await session.data(from: url)
        return try decoder.decode([Message].self, from: data)
    }

    @discardableResult
    public func sendMessage(channelId: String, content: String, senderName: String = "Janner") async throws -> Message {
        let payload = MessageCreateRequest(content: content, senderName: senderName)
        let url = try makeURL(path: "channels/\(channelId)/messages")
        return try await post(url: url, payload: payload, responseType: Message.self)
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

public enum APIError: LocalizedError {
    case badStatus(Int, String)

    public var errorDescription: String? {
        switch self {
        case .badStatus(let status, let body):
            return "HTTP \(status): \(body)"
        }
    }
}
