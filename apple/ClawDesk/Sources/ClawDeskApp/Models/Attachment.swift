import Foundation

public struct Attachment: Codable, Identifiable, Hashable, Sendable {
    public let id: String
    public let messageId: String
    public let kind: String
    public let originalName: String
    public let localPath: String
    public let mimeType: String?
    public let size: Int
    public let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case messageId = "message_id"
        case kind
        case originalName = "original_name"
        case localPath = "local_path"
        case mimeType = "mime_type"
        case size
        case createdAt = "created_at"
    }
}
