import Foundation

public struct Message: Codable, Identifiable, Hashable, Sendable {
    public let id: String
    public let channelId: String
    public let senderType: String
    public let senderName: String
    public let content: String
    public let contentType: String
    public let replyToId: String?
    public let sourceMessageId: String?
    public let createdAt: Date
    public let updatedAt: Date

    public var isUserMessage: Bool {
        senderType == "user"
    }

    enum CodingKeys: String, CodingKey {
        case id
        case channelId = "channel_id"
        case senderType = "sender_type"
        case senderName = "sender_name"
        case content
        case contentType = "content_type"
        case replyToId = "reply_to_id"
        case sourceMessageId = "source_message_id"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }

    public init(
        id: String,
        channelId: String,
        senderType: String = "user",
        senderName: String = "Janner",
        content: String,
        contentType: String = "text",
        replyToId: String? = nil,
        sourceMessageId: String? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.channelId = channelId
        self.senderType = senderType
        self.senderName = senderName
        self.content = content
        self.contentType = contentType
        self.replyToId = replyToId
        self.sourceMessageId = sourceMessageId
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}

public struct MessageCreateRequest: Codable, Sendable {
    public let senderType: String
    public let senderName: String
    public let content: String
    public let contentType: String
    public let replyToId: String?
    public let sourceMessageId: String?

    enum CodingKeys: String, CodingKey {
        case senderType = "sender_type"
        case senderName = "sender_name"
        case content
        case contentType = "content_type"
        case replyToId = "reply_to_id"
        case sourceMessageId = "source_message_id"
    }

    public init(
        content: String,
        senderType: String = "user",
        senderName: String = "Janner",
        contentType: String = "text",
        replyToId: String? = nil,
        sourceMessageId: String? = nil
    ) {
        self.senderType = senderType
        self.senderName = senderName
        self.content = content
        self.contentType = contentType
        self.replyToId = replyToId
        self.sourceMessageId = sourceMessageId
    }
}
